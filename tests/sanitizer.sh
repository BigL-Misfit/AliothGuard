#!/system/bin/sh
# SPDX-License-Identifier: MIT
# Shared by host tests and the real Android emulator; never packaged in the ZIP.
set -eu
# shellcheck source=scripts/common.sh
. "${AG_COMMON:?Set AG_COMMON to the common.sh under test}"

check_clean() {
  ag_actual=$(ag_clean)
  if [ "$ag_actual" != "$2" ]; then
    printf 'FAIL: sanitizer %s; expected <%s>, got <%s>\n' "$1" "$2" "$ag_actual" >&2
    exit 1
  fi
  printf 'PASS: sanitizer %s\n' "$1"
}

for ag_value in 15 35 2026-10-01 alioth aliothin arm64-v8a 'AP3A.241005.015.A2' 'name=Module v1.0 ~'; do
  printf '%s\n' "$ag_value" | check_clean "property $ag_value" "$ag_value"
done

# Literal expected alphabet, independent of tr's range/class parser.
ag_ascii=" !\"#\$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_\`abcdefghijklmnopqrstuvwxyz{|}~"
all_bytes() {
  ag_byte=0
  while [ "$ag_byte" -le 255 ]; do
    printf '%b' "\\$(printf '%03o' "$ag_byte")"
    ag_byte=$((ag_byte + 1))
  done
}
all_bytes | check_clean 'all 256 byte values' "$ag_ascii"
printf '\000\001\t\n\r\033\037A\177B\200\377' | check_clean 'mixed controls and high bytes' AB
printf '\000\t\n\r\033\177' | check_clean 'only controls' ''
printf '' | check_clean 'empty input' ''

ag_80=01234567890123456789012345678901234567890123456789012345678901234567890123456789
ag_160=$ag_80$ag_80
printf '%s' "${ag_160%?}" | check_clean '159 characters' "${ag_160%?}"
printf '%s' "$ag_160" | check_clean '160 characters' "$ag_160"
printf '%sx' "$ag_160" | check_clean '161 characters truncated' "$ag_160"
printf '%s\n\t\033%sEXCESS' "$ag_80" "$ag_80" | check_clean 'limit after control removal' "$ag_160"
