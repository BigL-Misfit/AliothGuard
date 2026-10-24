import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from project import ARCHIVE, FILES, metadata  # noqa: E402
from validate import scan_shell, validate_tree, validate_zip  # noqa: E402


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='aliothguard-release-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fixture = self.root / 'source with spaces'
        self.fixture.mkdir()
        for name in FILES:
            target = self.fixture / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        shutil.copytree(ROOT / 'tools', self.fixture / 'tools', ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copy2(ROOT / 'build.sh', self.fixture / 'build.sh')

    def build(self, name='output', extra_env=None):
        output = self.root / name
        env = os.environ.copy()
        env.pop('SOURCE_DATE_EPOCH', None)
        env.update(extra_env or {})
        result = subprocess.run(['sh', str(self.fixture / 'build.sh'), '--output', str(output)],
                                cwd=self.root, env=env, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return output / ARCHIVE

    def test_tree_contract(self):
        self.assertEqual(validate_tree()['status'], 'passed')

    def test_metadata_rejects_duplicates_bad_id_crlf_and_version(self):
        good = (ROOT / 'module.prop').read_bytes()
        for bad in (good + b'id=evil\n', good.replace(b'id=aliothguard', b'id=../evil'),
                    good.replace(b'\n', b'\r\n'), good.replace(b'versionCode=100', b'versionCode=x'),
                    good.replace(b'version=v0.1.0', b'version=v9.9.9')):
            with self.subTest(data=bad[:20]), self.assertRaises(ValueError):
                metadata(bad)

    def test_safety_scanner_rejects_partition_property_network_and_write_operations(self):
        for command in ('dd if=a of=/dev/block/by-name/boot', 'fastboot flashing lock',
                        'setprop ro.foo x', 'resetprop ro.foo x', 'magiskpolicy --live x',
                        'setenforce 0', 'rm -rf /data', 'echo bad > /system/build.prop',
                        'echo bad >> /data/adb/modules/other/disable', 'curl https://example.com',
                        'eval "$payload"', 'magisk --sqlite "DELETE FROM settings;"',
                        'true;rm -rf /data', '(dd if=x of=y)', 'value=$(curl https://example.com)'):
            with self.subTest(command=command), self.assertRaises(ValueError):
                scan_shell('scripts/diagnose.sh', command)

    def test_safety_scanner_accepts_readonly_reporter(self):
        for name in FILES:
            if name.endswith('.sh'):
                scan_shell(name, (ROOT / name).read_text())

    def test_reject_boot_payload(self):
        (self.fixture / 'service.sh').write_text('#!/system/bin/sh\n')
        with self.assertRaisesRegex(ValueError, 'forbidden'):
            validate_tree(self.fixture)

    def test_reject_symlinked_package_source(self):
        path = self.fixture / 'action.sh'
        path.unlink()
        path.symlink_to(ROOT / 'action.sh')
        with self.assertRaisesRegex(ValueError, 'nonregular'):
            validate_tree(self.fixture)

    def test_build_checksum_permissions_and_exact_contents(self):
        archive = self.build()
        self.assertEqual(validate_zip(archive, self.fixture)['status'], 'passed')
        expected = hashlib.sha256(archive.read_bytes()).hexdigest() + f'  {ARCHIVE}\n'
        self.assertEqual((archive.parent / 'SHA256SUMS.txt').read_text(), expected)
        with zipfile.ZipFile(archive) as z:
            self.assertEqual(z.namelist(), sorted(FILES))
            self.assertEqual(z.getinfo('action.sh').external_attr >> 16, 0o100755)
            self.assertEqual(z.getinfo('module.prop').external_attr >> 16, 0o100644)
            self.assertEqual(z.read('skip_mount'), b'')

    def test_reproducible_despite_mtime_permissions_timezone_and_output_path(self):
        first = self.build('first', {'TZ': 'Pacific/Honolulu'}).read_bytes()
        for name in FILES:
            path = self.fixture / name
            os.utime(path, (1800000000, 1800000000))
            path.chmod(0o600)
        second = self.build('different path', {'TZ': 'Asia/Kolkata'}).read_bytes()
        self.assertEqual(first, second)

    def test_source_date_epoch_is_explicit_and_reproducible(self):
        default = self.build('default').read_bytes()
        first = self.build('epoch1', {'SOURCE_DATE_EPOCH': '1735689600'}).read_bytes()
        second = self.build('epoch2', {'SOURCE_DATE_EPOCH': '1735689600'}).read_bytes()
        self.assertEqual(first, second)
        self.assertNotEqual(first, default)

    def test_bad_source_date_epoch_refused(self):
        result = subprocess.run(['sh', str(self.fixture / 'build.sh'), '--output', str(self.root / 'out')],
                                env={**os.environ, 'SOURCE_DATE_EPOCH': '0'}, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('outside the ZIP date range', result.stderr)

    def test_zip_extra_paths_traversal_duplicate_and_bad_mode_refused(self):
        clean = self.build()
        for extra in ('../escape', '/absolute', 'service.sh', 'module.prop'):
            with self.subTest(extra=extra):
                target = self.root / 'mutated.zip'
                shutil.copy2(clean, target)
                with zipfile.ZipFile(target, 'a') as z:
                    z.writestr(extra, 'unexpected')
                with self.assertRaises(ValueError):
                    validate_zip(target, self.fixture)
        target = self.root / 'bad-mode.zip'
        with zipfile.ZipFile(clean) as source, zipfile.ZipFile(target, 'w') as dest:
            for info in source.infolist():
                data = source.read(info)
                if info.filename == 'action.sh':
                    info.external_attr = 0o100644 << 16
                dest.writestr(info, data)
        with self.assertRaisesRegex(ValueError, 'permissions'):
            validate_zip(target, self.fixture)
