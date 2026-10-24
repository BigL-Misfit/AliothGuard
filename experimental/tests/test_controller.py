"""Isolated module/controller tests with mocked Android. Never use real /data."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MOCK = r'''#!/usr/bin/env python3
import json, os, pathlib, sys
name=pathlib.Path(sys.argv[0]).name
args=sys.argv[1:]
with open(os.environ['AGX_LOG'],'a') as out: out.write(json.dumps([name]+args)+'\n')
if name=='magisk':
 if args==['-V']: print(os.environ.get('MAGISK_VER_CODE','30700'))
 elif args==['--sqlite',"SELECT key,value FROM settings WHERE key='zygisk';"]:
  if os.environ.get('SQL_FAIL'): sys.exit(1)
  print(os.environ.get('SQL','key=zygisk|value=1'))
 else: sys.exit(90)
elif name=='getprop':
 assert len(args)==1
 print(json.loads(os.environ['PROPS']).get(args[0],''))
elif name=='getenforce': print(os.environ.get('SELINUX','Enforcing'))
elif name=='id':
 assert args==['-u']; print(os.environ.get('UID_MOCK','0'))
elif name=='pm':
 assert args==['list','packages','-U','io.github.biglmisfit.aliothguard.test']
 if not os.environ.get('NO_APP'): print('package:io.github.biglmisfit.aliothguard.test uid:10123')
else: sys.exit(91)
'''

class ControllerCases:
    busybox = False
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix='agx-test-')
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.modules = self.root / 'data/adb/modules'
        self.module = self.modules / 'aliothguard_experimental'
        shutil.copytree(ROOT / 'experimental/module', self.module)
        (self.module / 'state').mkdir()
        (self.module / 'zygisk').mkdir()
        (self.module / 'zygisk/arm64-v8a.so').write_bytes(b'ELF fixture for installer contract only')
        self.other = self.modules / 'aliothguard'
        self.other.mkdir()
        (self.other / 'sentinel').write_text('stable untouched')
        (self.root / 'proc/sys/kernel/random').mkdir(parents=True)
        (self.root / 'proc/sys/kernel/random/boot_id').write_text('12345678-1234-1234-1234-123456789abc\n')
        (self.root / 'proc/uptime').write_text('100.01 300.5\n')
        self.bin = self.root / 'bin'; self.bin.mkdir()
        for name in ('getprop','magisk','getenforce','id','pm','setprop','resetprop','reboot','dd','settings'):
            path = self.bin / name; path.write_text(MOCK); path.chmod(0o755)
        self.env = {**os.environ, 'PATH': str(self.bin) + os.pathsep + os.environ['PATH'],
                    'AGX_TEST_MODE':'1','AGX_TEST_ROOT':str(self.root),'AGX_LOG':str(self.root / 'commands'),
                    'MAGISK_VER_CODE':'30700','MODPATH':str(self.module),'BOOTMODE':'true','ARCH':'arm64','API':'35'}
        for key in ('KSU','APATCH','SQL','SQL_FAIL','SELINUX','UID_MOCK','NO_APP','ASH_STANDALONE'):
            self.env.pop(key,None)
        self.props = {'ro.product.vendor.device':'aliothin','ro.product.device':'alioth',
                      'ro.product.cpu.abi':'arm64-v8a','ro.build.version.sdk':'35',
                      'ro.axion.version':'1.6-FINAL-20250621-OFFICIAL-GMS-alioth',
                      'persist.sys.pixelprops.gms':'true'}
        self.shell=['/bin/sh']
        if self.busybox:
            binary=os.environ.get('BUSYBOX') or shutil.which('busybox')
            self.assertIsNotNone(binary, 'BusyBox required')
            self.shell=[binary,'ash']

    def snapshot_external(self):
        return {str(p.relative_to(self.modules)): p.read_bytes() for p in self.modules.rglob('*')
                if p.is_file() and not p.is_relative_to(self.module)}

    def invoke(self, *args, installer=False):
        self.env['PROPS']=json.dumps(self.props)
        before=self.snapshot_external()
        shims='id() { "$AGX_TEST_ROOT/bin/id" "$@"; };\n'
        if installer:
            script=shims+'''ui_print() { printf '%s\n' "$*"; }
abort() { printf '%s\n' "$*" >&2; exit 72; }
set_perm() { case "$1" in "$MODPATH"/*) ;; *) exit 90 ;; esac; }
. "$MODPATH/customize.sh"
printf 'FINALIZED\n'
'''
            command=self.shell+['-c',script]
        else:
            script=shims+'. "$0"'
            command=self.shell+['-c',script,str(self.module / 'scripts/control.sh'),*args]
        result=subprocess.run(command,env=self.env,capture_output=True,text=True,timeout=10)
        self.assertEqual(before,self.snapshot_external(),'Another module was modified')
        log = self.root/'commands'
        calls=[json.loads(x) for x in log.read_text().splitlines()] if log.exists() else []
        self.assertFalse({'setprop','resetprop','reboot','dd','settings'} & {x[0] for x in calls})
        return result

    def ready(self):
        (self.module/'disable').unlink()

    def provider(self, folder='zygisksu', name='Zygisk Next', marker=None):
        path=self.modules/folder; path.mkdir()
        (path/'module.prop').write_text(f'id={folder}\nname={name}\n')
        if marker: (path/marker).touch()
        return path

    def test_read_only_status_distinguishes_verdicts(self):
        before={p.relative_to(self.module):p.read_bytes() for p in self.module.rglob('*') if p.is_file()}
        r=self.invoke('status'); self.assertEqual(r.returncode,0,r.stderr)
        report=json.loads(r.stdout)
        self.assertEqual(report['provider_configuration'],'builtin')
        self.assertEqual(report['play_integrity'],{'state':'NOT_REQUESTED','basic':None,'device':None,'strong':None})
        self.assertIsNone(report['root_detection']['hidden'])
        self.assertTrue(report['module_disabled'])
        self.assertEqual(before,{p.relative_to(self.module):p.read_bytes() for p in self.module.rglob('*') if p.is_file()})

    def test_default_disabled_refuses_arm(self):
        r=self.invoke('arm','builtin','--lab-device')
        self.assertNotEqual(r.returncode,0); self.assertIn('Module is disabled',r.stderr)

    def test_builtin_session_is_bounded_and_explicit(self):
        self.ready(); r=self.invoke('arm','builtin','--lab-device')
        self.assertEqual(r.returncode,0,r.stderr)
        session=self.module/'state/session'
        self.assertEqual(session.read_text(),'AG02 builtin 12345678-1234-1234-1234-123456789abc 400\n')
        self.assertEqual(session.stat().st_mode & 0o777,0o600)

    def test_next_requires_builtin_off(self):
        self.ready(); self.provider()
        r=self.invoke('arm','next','--lab-device')
        self.assertNotEqual(r.returncode,0); self.assertIn('multiple_providers',r.stderr)
        self.env['SQL']='key=zygisk|value=0'
        r=self.invoke('arm','next','--lab-device')
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn('AG02 next ',(self.module/'state/session').read_text())

    def test_two_external_providers_refused(self):
        self.ready(); self.provider(); self.provider('rezygisk','ReZygisk')
        self.env['SQL']='key=zygisk|value=0'
        self.assertIn('multiple_providers',self.invoke('arm','next','--lab-device').stderr)

    def test_shared_provider_id_does_not_authenticate_fork(self):
        self.ready(); self.provider(name='NeoZygisk'); self.env['SQL']='key=zygisk|value=0'
        r=self.invoke('arm','next','--lab-device')
        self.assertNotEqual(r.returncode,0); self.assertIn('provider_unknown',r.stderr)

    def test_pending_or_disabled_provider_is_uncertain(self):
        self.ready(); p=self.provider(marker='disable'); self.env['SQL']='key=zygisk|value=0'
        for marker in ('disable','update','remove'):
            with self.subTest(marker=marker):
                for old in ('disable','update','remove'): (p/old).unlink(missing_ok=True)
                (p/marker).touch()
                self.assertIn('pending_module_state',self.invoke('arm','next','--lab-device').stderr)

    def test_staged_update_blocks_arming(self):
        self.ready(); (self.root/'data/adb/modules_update/new_module').mkdir(parents=True)
        self.assertIn('pending_module_state',self.invoke('arm','builtin','--lab-device').stderr)

    def test_sql_failure_and_duplicate_values_refused(self):
        self.ready(); self.env['SQL_FAIL']='1'
        self.assertNotEqual(self.invoke('arm','builtin','--lab-device').returncode,0)
        self.env.pop('SQL_FAIL'); self.env['SQL']='key=zygisk|value=1\nkey=zygisk|value=0'
        self.assertNotEqual(self.invoke('arm','builtin','--lab-device').returncode,0)

    def test_root_and_lab_ack_required(self):
        self.ready()
        self.assertNotEqual(self.invoke('arm','builtin').returncode,0)
        self.env['UID_MOCK']='2000'
        self.assertIn('Root is required',self.invoke('arm','builtin','--lab-device').stderr)

    def test_hiding_overlap_blocks_but_rom_not_modified(self):
        self.ready(); self.provider('zygisk_shamiko','Shamiko')
        r=self.invoke('arm','builtin','--lab-device')
        self.assertIn('Hiding modules',r.stderr)

    def test_integrity_modules_reported_separately(self):
        self.provider('tricky_store','Tricky Store')
        report=json.loads(self.invoke('status').stdout)
        self.assertEqual(report['integrity_module_count'],1)
        self.assertEqual(report['rom']['keybox_configuration'],'NOT_INSPECTED')

    def test_wrong_target_refused(self):
        self.ready()
        for key,value in [('ro.build.version.sdk','34'),('ro.product.vendor.device','other'),('ro.product.cpu.abi','x86_64')]:
            original=self.props[key]; self.props[key]=value
            self.assertNotEqual(self.invoke('arm','builtin','--lab-device').returncode,0)
            self.props[key]=original
        self.env['SELINUX']='Permissive'
        self.assertNotEqual(self.invoke('arm','builtin','--lab-device').returncode,0)

    def test_missing_app_refused(self):
        self.ready(); self.env['NO_APP']='1'
        self.assertIn('not installed',self.invoke('arm','builtin','--lab-device').stderr)

    def test_rollback_only_changes_this_module(self):
        self.ready(); self.assertEqual(self.invoke('arm','builtin','--lab-device').returncode,0)
        r=self.invoke('rollback'); self.assertEqual(r.returncode,0,r.stderr)
        self.assertFalse((self.module/'state/session').exists()); self.assertTrue((self.module/'disable').is_file())
        self.assertEqual(self.invoke('rollback').returncode,0)

    def test_linked_state_refused(self):
        self.ready(); outside=self.root/'outside'; outside.write_text('untouched')
        (self.module/'state/session').symlink_to(outside)
        self.assertNotEqual(self.invoke('arm','builtin','--lab-device').returncode,0)
        self.assertNotEqual(self.invoke('rollback').returncode,0)
        self.assertEqual(outside.read_text(),'untouched')

    def test_linked_provider_refused(self):
        self.ready(); (self.modules/'linked').symlink_to(self.other,target_is_directory=True)
        self.assertNotEqual(self.invoke('arm','builtin','--lab-device').returncode,0)

    def test_injection_arguments_rejected(self):
        self.ready()
        for value in ('builtin; reboot','next$(id)','--help','__proto__'):
            self.assertNotEqual(self.invoke('arm',value,'--lab-device').returncode,0)
        self.assertNotEqual(self.invoke('status','extra').returncode,0)

    def test_status_escapes_metadata(self):
        self.props['ro.axion.version']='a"b\\c\n\x1b'
        r=self.invoke('status'); self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)['rom']['axion_version'],'a"b\\c')

    def test_installer_finishes_disabled_and_clears_session(self):
        (self.module/'state/session').write_text('old session')
        r=self.invoke(installer=True); self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn('FINALIZED',r.stdout); self.assertTrue((self.module/'disable').exists())
        self.assertFalse((self.module/'state/session').exists())

    def test_magisk_own_staging_directory_is_not_a_conflict(self):
        staging=self.root/'data/adb/modules_update/aliothguard_experimental'
        staging.parent.mkdir(parents=True)
        self.module.rename(staging); self.module=staging
        self.env['MODPATH']=str(staging)
        r=self.invoke(installer=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn('FINALIZED',r.stdout)
        (staging.parent/'other_pending_module').mkdir()
        self.assertEqual(self.invoke(installer=True).returncode,72)

    def test_installer_refuses_overlap_before_mutation(self):
        self.provider(); (self.module/'state/session').write_text('sentinel')
        r=self.invoke(installer=True); self.assertEqual(r.returncode,72)
        self.assertEqual((self.module/'state/session').read_text(),'sentinel')

    def test_installer_refuses_linked_payload_parent(self):
        saved = self.root/'linked-scripts'
        (self.module/'scripts').rename(saved)
        (self.module/'scripts').symlink_to(saved, target_is_directory=True)
        r=self.invoke(installer=True)
        self.assertEqual(r.returncode,72)
        self.assertIn('linked payload directory',r.stderr)

    def test_installer_rejects_unsupported_environment(self):
        for key,value in [('BOOTMODE','false'),('ARCH','x86_64'),('API','34'),('MAGISK_VER_CODE','30600'),('SELINUX','Permissive'),('KSU','true')]:
            original=self.env.get(key); self.env[key]=value
            r=self.invoke(installer=True); self.assertEqual(r.returncode,72,(key,r.stdout,r.stderr))
            if original is None: self.env.pop(key)
            else: self.env[key]=original

class PosixControllerTests(ControllerCases, unittest.TestCase):
    pass
class BusyBoxControllerTests(ControllerCases, unittest.TestCase):
    busybox=True
