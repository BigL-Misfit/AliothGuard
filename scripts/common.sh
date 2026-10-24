#!/system/bin/sh
# SPDX-License-Identifier: MIT
# Library: source only from files in this module. Never source discovered data.
# Globals here are consumed by compatibility.sh after this library is sourced.
# shellcheck disable=SC2034

ag_clean() {
  # Literal ASCII endpoints work with Toybox and BusyBox (unlike escaped
  # ranges or optional character classes). Strip controls before limiting.
  LC_ALL=C tr -cd ' -~' | cut -c 1-160
}

ag_prop() {
  getprop "$1" 2>/dev/null | ag_clean
}

ag_meta() {
  [ -f "$1" ] && [ ! -L "$1" ] && [ -r "$1" ] || return 0
  head -c 16384 "$1" | awk -v key="$2" 'index($0, key "=") == 1 { print substr($0, length(key) + 2); exit }' | ag_clean
}

ag_line() {
  printf '%s: %s\n' "$1" "$2"
}

ag_init() {
  AG_DATA=/data/adb
  # Test harness only; production runs do not set these variables.
  if [ "${AG_TEST_MODE:-0}" = 1 ]; then
    case ${AG_TEST_ROOT:-} in
      /*) AG_DATA=$AG_TEST_ROOT/data/adb ;;
      *) printf '%s\n' 'ERROR: absolute AG_TEST_ROOT required in test mode.' >&2; return 1 ;;
    esac
  fi
  AG_SCAN_MODULES=1
  AG_SCAN_INTEGRITY_CONFIG=1
  AG_SCAN_ROM_HINTS=1
  AG_EXTERNAL=0
  AG_HIDERS=0
  AG_INTEGRITY=0
  AG_SHAMIKO=0
  AG_ASSISTANT=0
  AG_TRICKY=0
  AG_BUILTIN=unknown
  AG_DENYLIST=unknown
  AG_INVENTORY=unknown
}

ag_config() {
  if [ ! -r "$1" ] || [ -L "$1" ]; then
    ag_line WARNING 'Configuration missing, unreadable or linked; using conservative defaults.'
    return 0
  fi
  while IFS= read -r ag_entry || [ -n "$ag_entry" ]; do
    case "$ag_entry" in ''|'#'*) continue ;; esac
    case "$ag_entry" in
      SCAN_MODULES=0) AG_SCAN_MODULES=0 ;;
      SCAN_MODULES=1) AG_SCAN_MODULES=1 ;;
      SCAN_INTEGRITY_CONFIG=0) AG_SCAN_INTEGRITY_CONFIG=0 ;;
      SCAN_INTEGRITY_CONFIG=1) AG_SCAN_INTEGRITY_CONFIG=1 ;;
      SCAN_ROM_HINTS=0) AG_SCAN_ROM_HINTS=0 ;;
      SCAN_ROM_HINTS=1) AG_SCAN_ROM_HINTS=1 ;;
      *) ag_line WARNING 'Ignored an unrecognized configuration line (not executed).' ;;
    esac
  done < "$1"
}

ag_file_hint() {
  # Deliberately inspect existence only, never configuration/keybox contents.
  if [ -L "$AG_DATA/$1" ]; then
    ag_line "$1" 'symlink; target not inspected'
  elif [ -f "$AG_DATA/$1" ]; then
    ag_line "$1" 'present; contents and effective use NOT inspected'
  else
    ag_line "$1" 'not observed; absence/access failure cannot prove unused'
  fi
}
