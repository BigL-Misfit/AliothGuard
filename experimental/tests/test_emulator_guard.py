"""Guard the only operation that installs the lab APK: emulator-only adb smoke."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
ADB=r'''#!/usr/bin/env python3
import json,os,sys
args=sys.argv[1:]; scenario=os.environ.get('SCENARIO','')
with open(os.environ['ADB_LOG'],'a') as log: log.write(json.dumps(args)+'\n')
if args==['get-serialno']: print('phone-serial' if scenario=='phone' else 'emulator-5554')
elif args[:2]==['shell','getprop']:
 print(('0' if scenario=='not-qemu' else '1') if args[2]=='ro.kernel.qemu' else ('34' if scenario=='wrong-api' else '35'))
elif args[:2]==['shell','mkdir'] or args[0]=='push' or args[:2]==['shell','chmod']: pass
elif args==['install','-r','-t','dist/experimental/AliothGuard-Lab-v0.2.0.apk']: print('Success')
elif args[:2]==['shell','sh']:
 print(json.dumps({'schema':1,'hooks_enabled':False,'provider_configuration':'unknown','provider_runtime':'UNVERIFIED','module_disabled':True,
  'root_detection':{'hidden':None},'play_integrity':{'state':'NOT_REQUESTED','basic':None,'device':None,'strong':None}}))
elif args==['shell','/data/local/tmp/aliothguard-experimental/policy-test']:
 print('AGX_POLICY_PASS')
 if scenario=='native-fails': sys.exit(7)
elif args[:3]==['shell','am','instrument']:
 if scenario=='app-fails': print('AGX_APP_SMOKE_FAIL')
 else:
  print('AGX_APP_SMOKE_PASS\n{"zygisk_probe":"NOT_OBSERVED"}\nINSTRUMENTATION_CODE: -1')
else: sys.exit('Unexpected adb command: '+repr(args))
'''

class EmulatorGuardTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix='agx-emulator-test-'); self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        (self.root/'experimental/tools').mkdir(parents=True)
        shutil.copy2(ROOT/'experimental/tools/emulator-smoke.sh',self.root/'experimental/tools')
        (self.root/'bin').mkdir(); adb=self.root/'bin/adb'; adb.write_text(ADB); adb.chmod(0o755)

    def invoke(self, scenario):
        env={**os.environ,'PATH':str(self.root/'bin')+os.pathsep+os.environ['PATH'],
             'SCENARIO':scenario,'ADB_LOG':str(self.root/'adb.log')}
        return subprocess.run(['bash',str(self.root/'experimental/tools/emulator-smoke.sh')],
                              env=env,capture_output=True,text=True,timeout=10)

    def test_rejects_phone_before_any_write(self):
        for scenario in ('phone','not-qemu','wrong-api'):
            with self.subTest(scenario=scenario):
                (self.root/'adb.log').write_text('')
                r=self.invoke(scenario); self.assertNotEqual(r.returncode,0)
                calls=[json.loads(s) for s in (self.root/'adb.log').read_text().splitlines()]
                self.assertTrue(all(c==['get-serialno'] or c[:2]==['shell','getprop'] for c in calls),calls)

    def test_unrooted_emulator_path_succeeds(self):
        r=self.invoke(''); self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertIn('No Magisk installation, Zygisk injection',r.stdout)

    def test_native_failure_not_masked_by_tee(self):
        r=self.invoke('native-fails'); self.assertEqual(r.returncode,7,r.stdout+r.stderr)
        calls=[json.loads(s) for s in (self.root/'adb.log').read_text().splitlines()]
        self.assertFalse(any(c[0]=='install' for c in calls))

    def test_app_failure_not_reported_as_success(self):
        r=self.invoke('app-fails'); self.assertNotEqual(r.returncode,0)
        self.assertNotIn('PASS: API35',r.stdout)
