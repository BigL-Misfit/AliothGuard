#!/usr/bin/env python3
"""Compile with pinned official NDK; package a separate module and a lab-only APK."""
import hashlib
import os
import shutil
import stat
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / 'experimental'
OUT = ROOT / 'dist/experimental'
NDK_VERSION = '27.2.12479018'
ABIS = ('arm64-v8a', 'x86_64')
ARCHIVE = 'AliothGuard-Experimental-v0.2.0.zip'
APK = 'AliothGuard-Lab-v0.2.0.apk'
MODULE_FILES = {
    'module.prop': 0o644, 'disable': 0o644, 'skip_mount': 0o644,
    'action.sh': 0o755, 'customize.sh': 0o755, 'config/defaults.conf': 0o644,
    'scripts/environment.sh': 0o644, 'scripts/control.sh': 0o755,
    'webroot/index.html': 0o644, 'webroot/style.css': 0o644, 'webroot/app.mjs': 0o644,
}

def run(*args):
    subprocess.run([str(arg) for arg in args], check=True, cwd=ROOT)

def payload():
    result = {name: ((EXP / 'module' / name).read_bytes(), mode) for name, mode in MODULE_FILES.items()}
    result.update({
        'README.md': ((EXP / 'README.md').read_bytes(), 0o644),
        'docs/RECOVERY.md': ((EXP / 'docs/RECOVERY.md').read_bytes(), 0o644),
        'docs/AXIONOS_1_6.md': ((EXP / 'docs/AXIONOS_1_6.md').read_bytes(), 0o644),
        'docs/ARCHITECTURE.md': ((EXP / 'docs/ARCHITECTURE.md').read_bytes(), 0o644),
        'LICENSE': ((ROOT / 'LICENSE').read_bytes(), 0o644),
        'THIRD_PARTY.md': ((EXP / 'native/third_party/README.md').read_bytes(), 0o644),
        'zygisk/arm64-v8a.so': ((OUT / 'libs/arm64-v8a/libaliothguard_experimental.so').read_bytes(), 0o644),
    })
    return result

def package(path):
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, (data, mode) in sorted(payload().items()):
            info = zipfile.ZipInfo(name, (2024, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | mode) << 16
            archive.writestr(info, data)

def build_apk(sdk):
    tools = sdk / 'build-tools/35.0.0'
    android = sdk / 'platforms/android-35/android.jar'
    classes = OUT / 'classes'
    dex = OUT / 'dex'
    # Only disposable build output, never runtime/module/phone paths.
    for directory in (classes, dex):
        if directory.exists(): shutil.rmtree(directory)
        directory.mkdir(parents=True)
    run(tools / 'aapt2', 'link', '-o', OUT / 'base.apk', '-I', android,
        '--manifest', EXP / 'test-app/AndroidManifest.xml')
    java = Path(os.environ['JAVA_HOME']) / 'bin'
    sources = sorted((EXP / 'test-app/src').rglob('*.java'))
    run(java / 'javac', '-source', '8', '-target', '8', '-Xlint:-options',
        '-bootclasspath', android, '-d', classes, *sources)
    run(tools / 'd8', '--lib', android, '--min-api', '26', '--output', dex,
        *sorted(classes.rglob('*.class')))
    unsigned = OUT / 'unsigned.apk'
    shutil.copyfile(OUT / 'base.apk', unsigned)
    with zipfile.ZipFile(unsigned, 'a', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(dex / 'classes.dex', 'classes.dex')
        for abi in ABIS:
            archive.write(OUT / f'libs/{abi}/libag_test_reader.so', f'lib/{abi}/libag_test_reader.so')
    run(tools / 'zipalign', '-f', '-P', '16', '4', unsigned, OUT / 'aligned.apk')
    key = OUT / 'lab-debug.keystore'
    if not key.exists():
        run(java / 'keytool', '-genkeypair', '-keystore', key, '-storepass', 'android',
            '-keypass', 'android', '-alias', 'androiddebugkey', '-keyalg', 'RSA',
            '-keysize', '2048', '-validity', '3650', '-dname', 'CN=AliothGuard Lab Debug')
    run(tools / 'apksigner', 'sign', '--ks', key, '--ks-key-alias', 'androiddebugkey',
        '--ks-pass', 'pass:android', '--key-pass', 'pass:android', '--out', OUT / APK, OUT / 'aligned.apk')
    run(tools / 'apksigner', 'verify', '--verbose', OUT / APK)

def main():
    sdk = Path(os.environ.get('ANDROID_HOME') or os.environ['ANDROID_SDK_ROOT'])
    ndk = sdk / 'ndk' / NDK_VERSION
    if f'Pkg.Revision = {NDK_VERSION}' not in (ndk / 'source.properties').read_text():
        raise RuntimeError('Pinned NDK revision required')
    OUT.mkdir(parents=True, exist_ok=True)
    run(ndk / 'ndk-build', '-C', EXP / 'native', f'NDK_OUT={OUT / "obj"}',
        f'NDK_LIBS_OUT={OUT / "libs"}', '-j2')
    package(OUT / ARCHIVE)
    package(OUT / 'reproducibility.zip')
    if (OUT / ARCHIVE).read_bytes() != (OUT / 'reproducibility.zip').read_bytes():
        raise RuntimeError('Module ZIP is not reproducible from identical inputs')
    build_apk(sdk)
    sums = ''.join(f'{hashlib.sha256((OUT / name).read_bytes()).hexdigest()}  {name}\n'
                   for name in (ARCHIVE, APK))
    (OUT / 'SHA256SUMS.txt').write_text(sums)
    print(sums, end='')

if __name__ == '__main__':
    main()
