#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
set -Eeuo pipefail
cd "$(dirname "$0")/.."
mkdir -p reports
smoke_error() {
  printf 'FAIL: emulator smoke line %s (exit %s): %s\n' "$2" "$1" "$3" | tee -a reports/emulator-errors.txt >&2
  exit "$1"
}
trap 'smoke_error "$?" "$LINENO" "$BASH_COMMAND"' ERR

run_logged() {
  local report=$1
  shift
  local -a status
  if "$@" 2>&1 | tee "$report"; then
    return 0
  else
    status=("${PIPESTATUS[@]}")
  fi
  printf 'FAIL: command <%s>; command exit %s, tee exit %s\n' "$*" "${status[0]}" "${status[1]}" >&2
  if (( status[0] != 0 )); then return "${status[0]}"; fi
  return "${status[1]}"
}

declare -A properties
for key in ro.build.version.sdk ro.build.version.release ro.build.version.security_patch; do
  properties[$key]=$(adb shell getprop "$key" | tr -d '\r')
  printf 'Direct getprop %s: <%s>\n' "$key" "${properties[$key]}"
  test -n "${properties[$key]}"
done
test "${properties[ro.build.version.sdk]}" = 35

remote=/data/local/tmp/aliothguard-smoke
adb shell mkdir -p "$remote"
adb push action.sh scripts config tests/sanitizer.sh "$remote/"
run_logged reports/emulator-toybox.txt adb shell toybox --version
run_logged reports/emulator-sanitizer.txt adb shell "AG_COMMON=$remote/scripts/common.sh sh $remote/sanitizer.sh"
run_logged reports/emulator.txt adb shell sh "$remote/action.sh"
for key in ro.build.version.sdk ro.build.version.release ro.build.version.security_patch; do
  expected="$key: ${properties[$key]}"
  if ! grep -Fxq "$expected" reports/emulator.txt; then
    printf 'FAIL: diagnostic property differs from direct getprop; expected <%s>\n' "$expected" >&2
    exit 1
  fi
done
grep -Fq 'Magisk: command unavailable' reports/emulator.txt
grep -Fq 'END: diagnostic complete' reports/emulator.txt
printf '%s\n' 'PASS: Android 15 x86_64 shell smoke only. No Magisk, ARM64, kernel or hardware-attestation validation.' | tee -a reports/emulator.txt
