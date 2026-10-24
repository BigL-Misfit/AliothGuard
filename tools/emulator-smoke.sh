#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p reports
test "$(adb shell getprop ro.build.version.sdk | tr -d '\r')" = 35
adb shell mkdir -p /data/local/tmp/aliothguard-smoke
adb push action.sh scripts config /data/local/tmp/aliothguard-smoke/
adb shell sh /data/local/tmp/aliothguard-smoke/action.sh > reports/emulator.txt
grep -q 'ro.build.version.sdk: 35' reports/emulator.txt
grep -q 'Magisk: command unavailable' reports/emulator.txt
grep -q 'END: diagnostic complete' reports/emulator.txt
printf '%s\n' 'PASS: Android 15 x86_64 shell smoke only. No Magisk, ARM64, kernel or hardware-attestation validation.' | tee -a reports/emulator.txt
