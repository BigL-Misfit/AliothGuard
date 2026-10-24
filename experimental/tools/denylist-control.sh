#!/system/bin/sh
# AliothGuard opt-in Magisk DenyList helper. No boot hooks and no auto changes.
set -eu
usage() {
  echo 'Usage: sh denylist-control.sh status | list | add PACKAGE [PROCESS] | remove PACKAGE [PROCESS]'
  echo 'Explicit opt-in only. Magisk DenyList is not a Play Integrity bypass.'
}
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
valid_name() {
  case "$1" in ''|*[!a-zA-Z0-9_.:]*|.*|*..*|*:) return 1 ;; esac
  case "$1" in *.*) ;; *) return 1 ;; esac
}
[ "$#" -ge 1 ] || { usage; exit 2; }
command -v magisk >/dev/null 2>&1 || fail 'Magisk executable not found.'
case "${1}" in
  status)
    [ "$#" -eq 1 ] || fail 'status takes no arguments'
    magisk -v
    magisk --sqlite "SELECT key,value FROM settings WHERE key IN ('zygisk','denylist');" || fail 'Unable to read Magisk settings'
    printf '%s\n' 'DenyList configuration is not proof of root concealment or an integrity verdict.'
    ;;
  list)
    [ "$#" -eq 1 ] || fail 'list takes no arguments'
    magisk --denylist ls
    ;;
  add|remove)
    if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then usage; exit 2; fi
    [ "$(id -u)" = 0 ] || fail 'Root required to change DenyList.'
    valid_name "$2" || fail 'Invalid package identifier.'
    pkg="$2"
    # Never target central Android services through this convenience helper.
    case "$pkg" in android|com.android.systemui|com.google.android.gms|com.google.android.gsf|com.android.vending|com.topjohnwu.magisk) fail 'Protected system/root/integrity package; manage manually after understanding consequences.' ;; esac
    proc="${3:-$pkg}"
    valid_name "$proc" || fail 'Invalid process identifier.'
    case "$proc" in "$pkg"|"$pkg":*) ;; *) fail 'Process must belong to the requested package.' ;; esac
    # Refuse changes when the installed package cannot be found; don't modify arbitrary entries.
    if command -v pm >/dev/null 2>&1; then
      pm path "$pkg" >/dev/null 2>&1 || fail 'Package not installed or PackageManager unavailable.'
    else
      fail 'PackageManager unavailable.'
    fi
    [ "$(magisk --sqlite "SELECT value FROM settings WHERE key='zygisk';" 2>/dev/null | sed -n 's/^value=//p')" = 1 ] || fail 'Zygisk not confirmed enabled; refusing change.'
    # Enforce is intentionally not toggled: respect existing Magisk settings.
    if [ "$1" = add ]; then magisk --denylist add "$pkg" "$proc"; else magisk --denylist rm "$pkg" "$proc"; fi
    printf 'DenyList %s requested for %s / %s. Confirm actual state with list.\n' "$1" "$pkg" "$proc"
    ;;
  *) usage; exit 2 ;;
esac
