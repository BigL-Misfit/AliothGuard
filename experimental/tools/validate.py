#!/usr/bin/env python3
"""Experimental release gates. Static checks and compilation are not device safety."""
import hashlib
import json
import os
import re
import stat
import struct
import subprocess
import zipfile
from pathlib import Path
from build import ROOT, EXP, OUT, ARCHIVE, APK, NDK_VERSION, payload

HEADER_SHA = 'f8d55e8b4f89d418c5941afe62ce6a09ddec1f4afd9a1b0a01eb40a93310dd28'
FORBIDDEN = {'post-fs-data.sh','service.sh','boot-completed.sh','system.prop','sepolicy.rule',
             'system','vendor','product','system_ext','META-INF'}
COMMANDS = {'dd','fastboot','flash_image','flash_erase','nandwrite','reboot','mkfs','wipefs',
            'blkdiscard','setprop','resetprop','magiskpolicy','setenforce','mount','umount',
            'chcon','restorecon','curl','wget','eval','su','nc','netcat'}

def require(value, message):
    if not value: raise ValueError(message)

def source_checks():
    for line in (EXP / 'stable-files.sha256').read_text().splitlines():
        digest, name = line.split('  ', 1)
        require(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest,
                f'Stable packaged file changed: {name}')
    header = EXP / 'native/third_party/zygisk.hpp'
    require(hashlib.sha256(header.read_bytes()).hexdigest() == HEADER_SHA, 'Official Zygisk header changed')
    for path in (EXP / 'module').rglob('*'):
        require(not path.is_symlink(), f'Linked module source: {path}')
        require(path.name not in FORBIDDEN, f'Forbidden runtime payload: {path}')
        if path.suffix == '.sh':
            import shlex
            text = path.read_text()
            for line in text.splitlines():
                lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
                lexer.whitespace_split = True
                for token in lexer:
                    require(token not in COMMANDS, f'Unexpected destructive/network command: {path}: {token}')
                code=line.split('#',1)[0]
                require(not re.search(r'/dev/(block|mmcblk|sd[a-z]|nvme)|/by-name/',code),f'Partition path in {path}')
                if '--sqlite' in code:
                    require("SELECT key,value FROM settings WHERE key='zygisk';" in code, 'Unapproved database query')
    metadata=dict(line.split('=',1) for line in (EXP/'module/module.prop').read_text().splitlines())
    require(metadata['id']=='aliothguard_experimental' and metadata['version']=='v0.2.0'
            and metadata['versionCode']=='200','Experimental identity/version mismatch')
    require((EXP/'module/disable').read_bytes()==b'', 'Default disable marker must be empty')
    require((EXP/'module/skip_mount').read_bytes()==b'', 'skip_mount must be empty')
    require((EXP/'module/config/defaults.conf').read_text()==
            'schema=1\nhooks=0\nprobe=0\ntest_package=io.github.biglmisfit.aliothguard.test\nsession_seconds=300\n',
            'Experimental defaults changed')
    for name in ('module.cpp','policy.cpp'):
        text=(EXP/'native/jni'/name).read_text()
        require(not re.search(r'\b(system|popen|execve|fork|ptrace|mount|hookJniNativeMethods|pltHookRegister|connectCompanion)\s*\(',text),
                f'Unexpected privileged/hooking API in {name}')
    require('FORCE_DENYLIST_UNMOUNT' not in (EXP/'native/jni/module.cpp').read_text(),'Unmount option forbidden')
    manifest=(EXP/'test-app/AndroidManifest.xml').read_text()
    require('<uses-permission' not in manifest,'Lab app must not request privileged/network permissions')
    return {'stable_files':'unchanged','header':'pinned 0BSD API v5','defaults':'disabled; no hooks','safety_scan':'passed'}

def elf_checks(path, machine, readelf):
    data=path.read_bytes()
    require(data[:6]==b'\x7fELF\x02\x01','Expected little-endian ELF64')
    require(struct.unpack_from('<HH',data,16)==(3,machine),'Wrong ELF type or architecture')
    text=subprocess.check_output([str(readelf),'-l','-d','--dyn-syms','-W',str(path)],text=True)
    require('zygisk_module_entry' in text,'Missing Zygisk entry point')
    require('zygisk_companion_entry' not in text,'Root companion is forbidden')
    require('GNU_RELRO' in text and 'BIND_NOW' in text,'RELRO/bind-now required')
    for line in text.splitlines():
        if line.strip().startswith('GNU_STACK'): require(' E ' not in line and 'RWE' not in line,'Executable stack')
        if line.strip().startswith('LOAD'):
            require('RWE' not in line,'Writable/executable segment')
            require(int(line.split()[-1],16)>=16384,'16K-compatible ELF alignment required')
    needed=set(re.findall(r'Shared library: \[([^]]+)\]',text))
    require(needed <= {'libc.so','libm.so','libdl.so','libstdc++.so'},f'Unexpected native dependency: {needed}')
    return {'machine':machine,'bytes':len(data),'dependencies':sorted(needed),'hardening':'passed'}

def artifact_checks():
    sdk=Path(os.environ.get('ANDROID_HOME') or os.environ['ANDROID_SDK_ROOT'])
    readelf=sdk/'ndk'/NDK_VERSION/'toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf'
    elves={abi:elf_checks(OUT/f'libs/{abi}/libaliothguard_experimental.so',machine,readelf)
           for abi,machine in [('arm64-v8a',183),('x86_64',62)]}
    expected=payload()
    with zipfile.ZipFile(OUT/ARCHIVE) as archive:
        require(archive.namelist()==sorted(expected),'ZIP entries/order differ from explicit allowlist')
        require(archive.testzip() is None and not archive.comment,'Invalid ZIP CRC/comment')
        for info in archive.infolist():
            data,mode=expected[info.filename]
            require(archive.read(info)==data,'ZIP/source mismatch')
            require(info.external_attr >> 16 == stat.S_IFREG | mode,'ZIP mode/type mismatch')
            require(info.create_system==3 and info.date_time==(2024,1,1,0,0,0)
                    and not info.extra and not info.comment and info.compress_type==zipfile.ZIP_STORED,'Unexpected ZIP metadata')
    with zipfile.ZipFile(OUT/APK) as apk:
        require('lib/arm64-v8a/libag_test_reader.so' in apk.namelist() and 'lib/x86_64/libag_test_reader.so' in apk.namelist(),'APK missing JNI reader ABI')
        require(not any('aliothguard_experimental.so' in name for name in apk.namelist()),'APK must not bundle the injector')
        require('classes.dex' in apk.namelist(),'APK missing dex')
    for line in (OUT/'SHA256SUMS.txt').read_text().splitlines():
        digest,name=line.split('  ',1)
        require(name in (ARCHIVE,APK),'Unexpected checksum path')
        require(hashlib.sha256((OUT/name).read_bytes()).hexdigest()==digest,'Checksum mismatch')
    return {'native':elves,'module_zip':'validated; ARM64 only; disabled by default','apk':'separate JNI reader; signature verified by build','checksums':'passed'}

if __name__=='__main__':
    result={'source':source_checks(),'artifacts':artifact_checks(),
            'limits':'No real Zygisk injection, kernel, hardware attestation or phone-safety validation'}
    output=json.dumps(result,indent=2)+'\n'
    reports=ROOT/'reports/experimental'; reports.mkdir(parents=True,exist_ok=True)
    (reports/'validation.json').write_text(output)
    print(output,end='')
