"""Exercise the same byte/property/length fixture used on Android Toybox."""
import os
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SanitizerTests(unittest.TestCase):
    def run_fixture(self, shell, prefix=''):
        result = subprocess.run(
            shell + ['-c', prefix + '. "$1"', 'sanitizer-test',
                     str(ROOT / 'tests/sanitizer.sh')],
            env={**os.environ, 'AG_COMMON': str(ROOT / 'scripts/common.sh'),
                 'AG_BUSYBOX': shell[0]},
            capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('PASS: sanitizer all 256 byte values', result.stdout)
        self.assertIn('PASS: sanitizer limit after control removal', result.stdout)

    def test_host_text_utilities(self):
        self.run_fixture(['/bin/sh'])

    def test_busybox_applets(self):
        busybox = os.environ.get('BUSYBOX') or shutil.which('busybox')
        self.assertIsNotNone(busybox, 'BusyBox is a required dependency')
        # Force these actual applets even when ash's standalone mode is off.
        self.run_fixture([busybox, 'ash'],
                         'tr() { "$AG_BUSYBOX" tr "$@"; }; '
                         'cut() { "$AG_BUSYBOX" cut "$@"; };\n')
