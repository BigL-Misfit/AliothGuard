#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
set -Eeuo pipefail
cd "$(dirname "$0")/../.."
mkdir -p reports/experimental-emulator
trap 'printf "FAIL: experimental emulator line %s exit %s: %s\n" "$LINENO" "$?" "$BASH_COMMAND" >&2' ERR
# This script installs the dedicated APK ONLY on a verified emulator transport.
serial=$(adb get-serialno)
case $serial in emulator-*) ;; *) printf '%s\n' 'Refusing non-emulator transport.' >&2; exit 1 ;; esac
export ANDROID_SERIAL=$serial
test "$(adb shell getprop ro.kernel.qemu | tr -d '\r')" = 1
test "$(adb shell getprop ro.build.version.sdk | tr -d '\r')" = 35
remote=/data/local/tmp/aliothguard-experimental
adb shell mkdir -p "$remote"
adb push experimental/module "$remote/"
adb shell sh "$remote/module/action.sh" 2>&1 | tee reports/experimental-emulator/status.json
python3 - <<'PY'
import json
from pathlib import Path
p=json.loads(Path('reports/experimental-emulator/status.json').read_text())
assert p['schema']==1 and p['hooks_enabled'] is False
assert p['provider_configuration']=='unknown' and p['provider_runtime']=='UNVERIFIED'
assert p['module_disabled'] is True
assert p['play_integrity']=={'state':'NOT_REQUESTED','basic':None,'device':None,'strong':None}
assert p['root_detection']['hidden'] is None
PY
policy=dist/experimental/emulator-inputs/ag_policy_test
if [ ! -f "$policy" ]; then policy=dist/experimental/libs/x86_64/ag_policy_test; fi
adb push "$policy" "$remote/policy-test"
adb shell chmod 0755 "$remote/policy-test"
adb shell "$remote/policy-test" 2>&1 | tee reports/experimental-emulator/native.txt
grep -Fq AGX_POLICY_PASS reports/experimental-emulator/native.txt
adb install -r -t dist/experimental/AliothGuard-Lab-v0.2.0.apk
adb shell am instrument -w io.github.biglmisfit.aliothguard.test/.SmokeTest 2>&1 | tee reports/experimental-emulator/app.txt
grep -Fq AGX_APP_SMOKE_PASS reports/experimental-emulator/app.txt
grep -Fq 'INSTRUMENTATION_CODE: -1' reports/experimental-emulator/app.txt
grep -Fq '"zygisk_probe":"NOT_OBSERVED"' reports/experimental-emulator/app.txt
printf '%s\n' 'PASS: API35 x86_64 shell, native policy and app/JNI smoke. No Magisk installation, Zygisk injection, ARM64 execution, kernel or attestation validation.' | tee reports/experimental-emulator/result.txt
