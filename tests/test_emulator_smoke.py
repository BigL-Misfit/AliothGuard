"""Test smoke-test failures using a fake adb, never a connected device."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADB = r'''#!/usr/bin/env python3
import os, sys
args = sys.argv[1:]
scenario = os.environ.get('AG_SMOKE_SCENARIO', '')
props = {'ro.build.version.sdk': '35', 'ro.build.version.release': '15',
         'ro.build.version.security_patch': '2026-10-01'}
if scenario == 'wrong-sdk':
    props['ro.build.version.sdk'] = '36'
if args[:2] == ['shell', 'getprop']:
    print(props[args[2]], end='\r\n')
elif args[:3] == ['shell', 'mkdir', '-p'] or args[0] == 'push':
    pass
elif args == ['shell', 'toybox', '--version']:
    print('toybox fixture')
elif len(args) == 2 and args[0] == 'shell' and 'sanitizer.sh' in args[1]:
    if scenario == 'sanitizer-fails':
        print('FAIL: sanitizer property 35', file=sys.stderr)
        sys.exit(43)
    print('PASS: sanitizer fixture')
elif args == ['shell', 'sh', '/data/local/tmp/aliothguard-smoke/action.sh']:
    for key, value in props.items():
        if key == os.environ.get('AG_CORRUPT_KEY'):
            value = '--' if key.endswith('security_patch') else 'unknown'
        print(f'{key}: {value}')
    print('Magisk: command unavailable')
    if scenario != 'missing-end':
        print('END: diagnostic complete. Warnings are observations, not automatic change requests.')
    if scenario == 'diagnostic-fails':
        print('remote diagnostic failed', file=sys.stderr)
        sys.exit(42)
else:
    sys.exit('Unexpected fake adb command: ' + repr(args))
'''


class EmulatorSmokeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='aliothguard-smoke-test-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / 'tools').mkdir()
        shutil.copy2(ROOT / 'tools/emulator-smoke.sh', self.root / 'tools')
        (self.root / 'bin').mkdir()
        adb = self.root / 'bin/adb'
        adb.write_text(ADB)
        adb.chmod(0o755)

    def invoke(self, scenario='', corrupt_key=''):
        return subprocess.run(
            ['bash', str(self.root / 'tools/emulator-smoke.sh')],
            env={**os.environ, 'PATH': str(self.root / 'bin') + os.pathsep + os.environ['PATH'],
                 'AG_SMOKE_SCENARIO': scenario, 'AG_CORRUPT_KEY': corrupt_key},
            capture_output=True, text=True, timeout=15)

    def test_success(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('PASS: Android 15', result.stdout)
        self.assertIn('PASS: sanitizer', (self.root / 'reports/emulator-sanitizer.txt').read_text())

    def test_complete_but_corrupted_properties_fail_with_expected_value(self):
        for suffix, value in [('sdk', '35'), ('release', '15'), ('security_patch', '2026-10-01')]:
            with self.subTest(property=suffix):
                key = 'ro.build.version.' + suffix
                result = self.invoke(corrupt_key=key)
                self.assertEqual(result.returncode, 1)
                self.assertIn(f'expected <{key}: {value}>', result.stderr)
                self.assertIn('END: diagnostic complete', result.stdout)
                self.assertNotIn('PASS: Android 15', result.stdout)

    def test_missing_completion_identifies_failing_assertion(self):
        result = self.invoke('missing-end')
        self.assertEqual(result.returncode, 1)
        self.assertIn("grep -Fq 'END: diagnostic complete'", result.stderr)
        self.assertIn('FAIL: emulator smoke line ', result.stderr)

    def test_remote_failure_status_and_stderr_survive_tee(self):
        result = self.invoke('diagnostic-fails')
        self.assertEqual(result.returncode, 42)
        self.assertIn('exit 42', result.stderr)
        self.assertIn('command <adb shell sh /data/local/tmp/aliothguard-smoke/action.sh>', result.stderr)
        self.assertIn('remote diagnostic failed', (self.root / 'reports/emulator.txt').read_text())

    def test_sanitizer_failure_stops_before_diagnostics(self):
        result = self.invoke('sanitizer-fails')
        self.assertEqual(result.returncode, 43)
        self.assertIn('FAIL: sanitizer property 35', result.stdout)
        self.assertFalse((self.root / 'reports/emulator.txt').exists())

    def test_wrong_sdk_stops_with_raw_value_visible(self):
        result = self.invoke('wrong-sdk')
        self.assertEqual(result.returncode, 1)
        self.assertIn('Direct getprop ro.build.version.sdk: <36>', result.stdout)
        self.assertIn('FAIL: emulator smoke line ', result.stderr)
        self.assertFalse((self.root / 'reports/emulator.txt').exists())
