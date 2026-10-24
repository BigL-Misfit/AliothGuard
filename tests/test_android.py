"""Host-only fixtures. No real Android paths, services or root operations."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOCK = r'''#!/usr/bin/env python3
import json, os, pathlib, sys
command = pathlib.Path(sys.argv[0]).name
with open(os.environ['AG_COMMAND_LOG'], 'a') as log:
    log.write(json.dumps([command] + sys.argv[1:]) + '\n')
if command == 'getprop':
    props = json.loads(pathlib.Path(os.environ['AG_PROPERTIES']).read_text())
    if len(sys.argv) != 2:
        sys.exit(90)
    print(props.get(sys.argv[1], ''))
elif command == 'id':
    assert sys.argv[1:] == ['-u']
    print(os.environ.get('AG_MOCK_UID', '0'))
elif command == 'magisk':
    args = sys.argv[1:]
    if args == ['-v']:
        print('28.1:TEST')
    elif args == ['-V']:
        print('28100')
    elif args == ['--sqlite', "SELECT key,value FROM settings WHERE key IN ('zygisk','denylist');"]:
        if os.environ.get('AG_SQL_FAIL') == '1':
            sys.exit(1)
        print(os.environ.get('AG_SQL', 'key=zygisk|value=0\nkey=denylist|value=0'))
    else:
        sys.exit(90)
else:
    sys.exit(91)  # Any prohibited operation is an observable test failure.
'''

INSTALLER = r'''
ui_print() { printf '%s\n' "$1"; }
abort() { printf 'ABORT: %s\n' "$1" >&2; exit 72; }
set_perm() {
  case "$1" in "$MODPATH"/*) ;; *) exit 93 ;; esac
  [ "$2:$3" = 0:0 ] || exit 94
  printf '%s|%s\n' "${1#"$MODPATH"/}" "$4" >> "$AG_PERMISSION_LOG"
}
. "$MODPATH/customize.sh"
printf '%s\n' INSTALLER_FINALIZATION_REACHED
'''


class AndroidCases:
    @classmethod
    def setUpClass(cls):
        if cls.busybox:
            binary = os.environ.get('BUSYBOX') or shutil.which('busybox')
            if not binary or not Path(binary).is_file():
                raise RuntimeError('BusyBox is a required test dependency, not an optional skip')
            cls.shell = [binary, 'ash']
        else:
            cls.shell = ['/bin/sh']

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='aliothguard-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.module = self.root / 'installed module'
        self.module.mkdir()
        for name in ('module.prop', 'skip_mount', 'customize.sh', 'action.sh'):
            shutil.copy2(ROOT / name, self.module / name)
        for name in ('scripts', 'config'):
            shutil.copytree(ROOT / name, self.module / name)
        self.data = self.root / 'data/adb'
        (self.data / 'modules').mkdir(parents=True)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.prohibited = {'dd', 'fastboot', 'flash_image', 'setprop', 'resetprop',
                           'magiskpolicy', 'setenforce', 'mount', 'umount', 'rm',
                           'cp', 'mv', 'touch', 'chmod', 'chown', 'curl', 'wget', 'reboot'}
        for command in self.prohibited | {'getprop', 'id', 'magisk'}:
            path = self.bin / command
            path.write_text(MOCK)
            path.chmod(0o755)
        self.props = self.root / 'properties.json'
        self.properties = {
            'ro.product.device': 'alioth', 'ro.product.vendor.device': 'aliothin',
            'ro.product.cpu.abi': 'arm64-v8a', 'ro.board.platform': 'kona',
            'ro.build.version.release': '15', 'ro.build.version.sdk': '35',
            'ro.build.version.security_patch': '2026-10-01',
            'ro.boot.verifiedbootstate': 'orange', 'ro.boot.flash.locked': '0',
        }
        self.log = self.root / 'commands.jsonl'
        self.permissions = self.root / 'permissions.txt'
        self.env = os.environ.copy()
        for key in ('KSU', 'APATCH', 'ZYGISK_ENABLED', 'ASH_STANDALONE', 'AG_SQL', 'AG_SQL_FAIL'):
            self.env.pop(key, None)
        self.env.update({
            'PATH': str(self.bin) + os.pathsep + self.env['PATH'],
            'AG_TEST_MODE': '1', 'AG_TEST_ROOT': str(self.root),
            'AG_PROPERTIES': str(self.props), 'AG_COMMAND_LOG': str(self.log),
            'AG_MOCK_BIN': str(self.bin),
            'AG_PERMISSION_LOG': str(self.permissions), 'AG_MOCK_UID': '0',
            'MODPATH': str(self.module), 'BOOTMODE': 'true',
            'MAGISK_VER_CODE': '28100', 'ARCH': 'arm64', 'API': '35',
        })

    def snapshot(self):
        return {str(p.relative_to(self.data)): (os.readlink(p) if p.is_symlink()
                else (p.read_bytes(), p.stat().st_mode) if p.is_file() else None)
                for p in self.data.rglob('*')}

    def invoke(self, installer=False):
        self.props.write_text(json.dumps(self.properties))
        before = self.snapshot()
        # Some BusyBox builds prefer internal applets to PATH. Function shims
        # explicitly intercept identity and prohibited operations in the harness;
        # text processing still uses the selected shell's actual applets.
        shims = '\n'.join(f'{name}() {{ "$AG_MOCK_BIN/{name}" "$@"; }}'
                          for name in sorted(self.prohibited | {'id'})) + '\n'
        if installer:
            args = ['-c', shims + INSTALLER]
        elif self.busybox:
            entry = str(self.module / 'scripts/diagnose.sh')
            args = ['-c', shims + '. "$0"', entry]
        else:
            args = [str(self.module / 'action.sh')]
        result = subprocess.run(self.shell + args, env=self.env, capture_output=True,
                                text=True, timeout=15, cwd=self.module)
        self.assertEqual(before, self.snapshot(), 'external module/config data changed')
        calls = [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []
        self.assertFalse(self.prohibited.intersection(call[0] for call in calls), calls)
        self.assertFalse(any(call[0] == 'getprop' and len(call) != 2 for call in calls))
        self.assertNotIn('\x1b', result.stdout)
        return result

    def diagnostic(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('END: diagnostic complete', result.stdout)
        return result.stdout

    def add_module(self, name, marker=None, metadata=None, pending=False):
        folder = self.data / ('modules_update' if pending else 'modules') / name
        folder.mkdir(parents=True)
        (folder / 'module.prop').write_text(metadata or f'id={name}\nname=Fixture\nversion=v1\n')
        if marker:
            (folder / marker).touch()
        return folder

    def reject(self, message):
        result = self.invoke(installer=True)
        self.assertEqual(result.returncode, 72, result.stdout + result.stderr)
        self.assertIn(message, result.stderr)
        self.assertNotIn('INSTALLER_FINALIZATION_REACHED', result.stdout)
        self.assertFalse(self.permissions.exists(), 'permissions changed before rejection')

    def test_baseline_report_is_read_only_and_honest(self):
        output = self.diagnostic()
        self.assertIn('matches reported Mi 11X-family', output)
        self.assertIn('Play Integrity verdict: UNKNOWN', output)
        self.assertIn('ROM-integrated spoofing: UNKNOWN', output)
        self.assertNotIn('Multiple external', output)

    def test_real_shared_provider_id_and_builtin_conflict(self):
        self.add_module('zygisksu')
        self.env['AG_SQL'] = 'key=zygisk|value=1\nkey=denylist|value=0'
        output = self.diagnostic()
        self.assertIn('Built-in Zygisk plus external provider', output)
        self.assertIn('shared by provider forks', output)

    def test_multiple_external_providers(self):
        self.add_module('rezygisk')
        self.add_module('zygisksu')
        self.assertIn('Multiple external Zygisk providers', self.diagnostic())

    def test_disabled_and_removed_not_counted_as_enabled(self):
        self.add_module('rezygisk')
        self.add_module('zygisksu', marker='disable')
        self.add_module('zygisk_next', marker='remove')
        output = self.diagnostic()
        self.assertIn('disabled-on-disk', output)
        self.assertIn('pending-removal', output)
        self.assertNotIn('Multiple external', output)
        self.assertIn('do not prove loaded state', output)

    def test_staged_updates_are_not_running_modules(self):
        self.add_module('rezygisk')
        self.add_module('zygisksu', pending=True)
        output = self.diagnostic()
        self.assertIn('Staged module (not counted as running): zygisksu', output)
        self.assertNotIn('Multiple external', output)

    def test_update_marker_explains_metadata_uncertainty(self):
        self.add_module('zygisksu', marker='update')
        self.assertIn('Pending update marker', self.diagnostic())

    def test_assistant_hyphen_id_and_enforced_denylist(self):
        self.add_module('zygisk-assistant')
        self.env['AG_SQL'] = 'key=zygisk|value=1\nkey=denylist|value=1'
        self.assertIn('Enforce DenyList with Assistant/Shamiko', self.diagnostic())

    def test_overlapping_hiders_and_integrity_modules(self):
        for name in ('zygisk-assistant', 'zygisk_shamiko', 'playintegrityfix', 'safetynet-fix'):
            self.add_module(name)
        output = self.diagnostic()
        self.assertIn('Multiple hiding modules', output)
        self.assertIn('Multiple integrity/spoofing modules', output)
        self.assertIn('no known provider is configured', output)

    def test_database_failure_is_unknown(self):
        self.env['AG_SQL_FAIL'] = '1'
        self.assertIn('Built-in Zygisk setting: unknown', self.diagnostic())

    def test_unrecognized_database_output_is_unknown(self):
        self.env['AG_SQL'] = 'zygisk=1\nkey=denylist|value=garbage'
        output = self.diagnostic()
        self.assertIn('Built-in Zygisk setting: unknown', output)
        self.assertIn('Enforce DenyList setting: unknown', output)

    def test_unknown_module_identity_not_guessed(self):
        self.add_module('private-fork', metadata='id=private-fork\nname=Zygisk Next\nversion=x\n')
        output = self.diagnostic()
        self.assertIn('enabled-on-disk; other', output)
        self.assertNotIn('Built-in Zygisk plus external', output)

    def test_metadata_mismatch_is_reported(self):
        self.add_module('zygisksu', metadata='id=not-the-directory\nversion=1\n')
        self.assertIn('identity uncertain', self.diagnostic())

    def test_inaccessible_inventory_is_unknown(self):
        (self.data / 'modules').rmdir()
        output = self.diagnostic()
        self.assertIn('modules directory absent', output)
        self.assertIn('Conflict assessment: UNKNOWN', output)

    def test_symlinked_module_and_metadata_are_skipped(self):
        outside = self.root / 'outside'
        outside.mkdir()
        (outside / 'module.prop').write_text('id=PRIVATE_SECRET\n')
        (self.data / 'modules/zygisksu').symlink_to(outside, target_is_directory=True)
        folder = self.add_module('another')
        (folder / 'module.prop').unlink()
        (folder / 'module.prop').symlink_to(outside / 'module.prop')
        output = self.diagnostic()
        self.assertIn('Linked module directory skipped', output)
        self.assertIn('id=unreadable', output)
        self.assertNotIn('PRIVATE_SECRET', output)

    def test_config_payload_and_metadata_are_never_executed(self):
        sentinel = self.root / 'should-not-exist'
        (self.module / 'config/diagnostics.conf').write_text(f'SCAN_MODULES=1\n$(touch {sentinel})\n')
        self.add_module('untrusted', metadata=f'id=untrusted\nversion=$(touch {sentinel})\n')
        output = self.diagnostic()
        self.assertIn('Ignored an unrecognized configuration line', output)
        self.assertFalse(sentinel.exists())

    def test_output_control_characters_and_long_properties_are_bounded(self):
        self.properties['ro.board.platform'] = '\x1b[31m' + 'X' * 1000
        self.env['ZYGISK_ENABLED'] = '\x1b[31m' + 'Y' * 1000
        output = self.diagnostic()
        for prefix in ('ro.board.platform: ', 'ZYGISK_ENABLED environment hint: '):
            value = next(line[len(prefix):] for line in output.splitlines() if line.startswith(prefix))
            self.assertLessEqual(len(value), 160)

    def test_pif_and_keybox_contents_never_disclosed(self):
        self.add_module('playintegrityfix')
        (self.data / 'modules/playintegrityfix/custom.pif.prop').write_text('FINGERPRINT=PRIVATE_SECRET')
        tricky = self.data / 'tricky_store'
        tricky.mkdir()
        (tricky / 'keybox.xml').write_text('PRIVATE_KEY_SECRET')
        (tricky / 'target.txt').write_text('PRIVATE_APP_SECRET')
        output = self.diagnostic()
        self.assertIn('custom.pif.prop: present', output)
        self.assertIn('tricky_store/target.txt: present', output)
        self.assertNotIn('PRIVATE_', output)

    def test_rom_hint_is_not_a_verdict(self):
        self.properties['persist.sys.pihooks.enable'] = 'true'
        output = self.diagnostic()
        self.assertIn('heuristic, ROM-specific; not proof', output)
        self.assertIn('ROM-integrated spoofing: UNKNOWN', output)

    def test_disabled_scans_do_not_claim_compatibility(self):
        (self.module / 'config/diagnostics.conf').write_text('SCAN_MODULES=0\nSCAN_INTEGRITY_CONFIG=0\nSCAN_ROM_HINTS=0\n')
        self.add_module('private')
        output = self.diagnostic()
        self.assertIn('SKIPPED by configuration', output)
        self.assertIn('Conflict assessment: UNKNOWN', output)
        self.assertNotIn('Module private', output)

    def test_nonroot_diagnostics_warn_and_complete(self):
        self.env['AG_MOCK_UID'] = '2000'
        self.assertIn('Not running as root', self.diagnostic())

    def test_missing_magisk_is_unknown_not_a_pass(self):
        (self.bin / 'magisk').unlink()
        self.assertIn('command unavailable; root manager and Zygisk state UNKNOWN', self.diagnostic())

    def test_missing_android_commands_fail_explicitly(self):
        (self.bin / 'getprop').unlink()
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Android getprop unavailable', result.stdout)

    def test_action_entrypoint_executes_diagnostics(self):
        self.props.write_text(json.dumps(self.properties))
        result = subprocess.run(self.shell + [str(self.module / 'action.sh')],
                                env=self.env, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('END: diagnostic complete', result.stdout)

    def test_install_supported_device_and_allow_magisk_finalization(self):
        result = self.invoke(installer=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('INSTALLER_FINALIZATION_REACHED', result.stdout)
        self.assertEqual(self.permissions.read_text().splitlines(), [
            'action.sh|0755', 'scripts/diagnose.sh|0755',
            'scripts/common.sh|0644', 'scripts/compatibility.sh|0644'])

    def test_install_alioth_fallback_when_vendor_unset(self):
        self.properties.pop('ro.product.vendor.device')
        self.assertEqual(self.invoke(installer=True).returncode, 0)

    def test_install_refuses_recovery(self):
        self.env['BOOTMODE'] = 'false'
        self.reject('Magisk app only')

    def test_install_refuses_unknown_bootmode(self):
        self.env.pop('BOOTMODE')
        self.reject('Magisk app only')

    def test_install_refuses_other_phone_even_if_system_identity_spoofed(self):
        self.properties['ro.product.vendor.device'] = 'different-phone'
        self.reject('Unsupported or unknown device')

    def test_install_refuses_unknown_device(self):
        self.properties.pop('ro.product.vendor.device')
        self.properties.pop('ro.product.device')
        self.reject('Unsupported or unknown device')

    def test_install_refuses_other_api(self):
        self.env['API'] = '34'
        self.reject('Android 15')

    def test_install_refuses_inconsistent_sdk_property(self):
        self.properties['ro.build.version.sdk'] = '34'
        self.reject('does not match API 35')

    def test_install_refuses_non_arm64(self):
        self.env['ARCH'] = 'x64'
        self.reject('Only ARM64')

    def test_install_refuses_old_magisk(self):
        self.env['MAGISK_VER_CODE'] = '27000'
        self.reject('28.0 or newer')

    def test_install_refuses_unknown_magisk(self):
        self.env['MAGISK_VER_CODE'] = 'not-a-version'
        self.reject('Cannot verify')

    def test_install_refuses_other_root_manager(self):
        self.env['KSU'] = 'true'
        self.reject('Magisk only')

    def test_install_refuses_nonroot(self):
        self.env['AG_MOCK_UID'] = '2000'
        self.reject('root installation')

    def test_install_refuses_missing_payload(self):
        (self.module / 'scripts/diagnose.sh').unlink()
        self.reject('Missing or linked module file')

    def test_install_refuses_boot_hook(self):
        (self.module / 'service.sh').write_text('#!/system/bin/sh\n')
        self.reject('Forbidden diagnostic-release payload')

    def test_install_refuses_linked_payload(self):
        path = self.module / 'scripts/diagnose.sh'
        path.unlink()
        path.symlink_to('/does-not-exist')
        self.reject('Missing or linked module file')


class PosixAndroidTests(AndroidCases, unittest.TestCase):
    busybox = False


class BusyBoxAndroidTests(AndroidCases, unittest.TestCase):
    busybox = True
