#!/system/bin/sh
# SPDX-License-Identifier: MIT
set -eu
AGX_MODULE=$(CDPATH='' cd -P -- "$(dirname -- "$0")/.." && pwd)
# shellcheck source=experimental/module/scripts/environment.sh
. "$AGX_MODULE/scripts/environment.sh"
agx_init
agx_scan ''

fail() { printf 'ERROR: %s\n' "$1" >&2; exit 1; }
status() {
  printf '{"schema":1,"version":"0.2.0","hooks_enabled":false,"provider_configuration":'
  agx_json "$AGX_PROVIDER"
  printf ',"provider_reason":'; agx_json "$AGX_REASON"
  printf ',"provider_runtime":"UNVERIFIED","builtin_setting":'; agx_json "$AGX_BUILTIN"
  printf ',"external_provider_count":%s,"hiding_module_count":%s,"integrity_module_count":%s' "$AGX_EXTERNAL" "$AGX_HIDERS" "$AGX_INTEGRITY"
  printf ',"module_disabled":'; if [ -e "$AGX_MODULE/disable" ]; then printf true; else printf false; fi
  printf ',"session_file_present":'; if [ -f "$AGX_MODULE/state/session" ] && [ ! -L "$AGX_MODULE/state/session" ]; then printf true; else printf false; fi
  printf ',"session_effect":"Only a valid unexpired session in this boot can mark the dedicated test process"'
  printf ',"magisk_code":'; agx_json "${AGX_MAGISK:-unknown}"
  printf ',"device":'; agx_json "$(agx_prop ro.product.vendor.device)"
  printf ',"sdk":'; agx_json "$(agx_prop ro.build.version.sdk)"
  printf ',"selinux":'; agx_json "$(getenforce 2>/dev/null || printf unknown)"
  printf ',"kernel":'; agx_json "$(uname -r)"
  printf ',"rom":{"axion_version":'; agx_json "$(agx_prop ro.axion.version)"
  printf ',"gms_spoof_property":'; agx_json "$(agx_prop persist.sys.pixelprops.gms)"
  printf ',"pif_configuration":"NOT_INSPECTED","keybox_configuration":"NOT_INSPECTED","axion_1_6_source":"PIF and Tricky-Store-derived framework hooks present; installed binary and enabled state unverified"}'
  printf ',"root_detection":{"state":"OBSERVATIONS_ONLY","hidden":null},"play_integrity":{"state":"NOT_REQUESTED","basic":null,"device":null,"strong":null}}\n'
}
write_guard() {
  [ "$(id -u)" = 0 ] || fail 'Root is required to change this module state.'
  [ "$AGX_MODULE" = "$AGX_DATA/modules/aliothguard_experimental" ] || fail 'Refusing writes outside the installed experimental module.'
  if [ -L "$AGX_DATA" ] || [ -L "$AGX_DATA/modules" ] || [ -L "$AGX_MODULE" ]; then fail 'Linked module path.'; fi
  if [ ! -d "$AGX_MODULE/state" ] || [ -L "$AGX_MODULE/state" ]; then fail 'Missing or linked state directory.'; fi
  if [ -L "$AGX_MODULE/state/session" ] || [ -L "$AGX_MODULE/disable" ]; then fail 'Linked state file.'; fi
  umask 077
}
case ${1:-status} in
  status) [ "$#" -le 1 ] || fail 'Unexpected arguments.'; status ;;
  arm)
    if [ "$#" != 3 ] || [ "$3" != --lab-device ]; then fail 'Use arm builtin|next --lab-device only on a dedicated recoverable test device.'; fi
    case $2 in builtin|next) ;; *) fail 'Provider must be builtin or next.' ;; esac
    write_guard
    [ ! -e "$AGX_MODULE/disable" ] || fail 'Module is disabled. This command never enables modules or providers.'
    agx_target || fail 'Requires Mi 11X / API 35 / ARM64 / Magisk 30.7+ / SELinux Enforcing.'
    [ "$AGX_PROVIDER" = "$2" ] || fail "Provider gate refused: $AGX_PROVIDER ($AGX_REASON)."
    [ "$AGX_HIDERS" = 0 ] || fail 'Hiding modules could affect the probe; laboratory isolation is required.'
    agx_app=$(pm list packages -U io.github.biglmisfit.aliothguard.test 2>/dev/null)
    case $agx_app in 'package:io.github.biglmisfit.aliothguard.test uid:'*) ;; *) fail 'Dedicated test application is not installed.' ;; esac
    agx_boot=$(cat "$AGX_PROC/sys/kernel/random/boot_id")
    case $agx_boot in ''|*[!0-9a-f-]*) fail 'Invalid boot ID.' ;; esac
    [ "${#agx_boot}" = 36 ] || fail 'Invalid boot ID length.'
    agx_now=$(cut -d . -f 1 "$AGX_PROC/uptime")
    case $agx_now in ''|*[!0-9]*) fail 'Cannot read monotonic uptime.' ;; esac
    agx_tmp=$(mktemp "$AGX_MODULE/state/.session.XXXXXX")
    trap 'rm -f -- "$agx_tmp"' EXIT HUP INT TERM
    printf 'AG02 %s %s %s\n' "$2" "$agx_boot" "$((agx_now + 300))" > "$agx_tmp"
    chmod 0600 "$agx_tmp"
    mv -f -- "$agx_tmp" "$AGX_MODULE/state/session"
    trap - EXIT HUP INT TERM
    printf '%s\n' 'Armed for at most five minutes in this boot; start a fresh test-app process. Provider runtime remains unverified.'
    ;;
  rollback)
    [ "$#" = 1 ] || fail 'Unexpected arguments.'
    write_guard
    # Only our session and our Magisk disable marker. No other module changes.
    rm -f -- "$AGX_MODULE/state/session"
    [ -e "$AGX_MODULE/disable" ] || (set -C; : > "$AGX_MODULE/disable")
    printf '%s\n' 'Probe session removed; this module is disabled for the next boot. Existing test-process markers last until that process exits. No reboot performed.'
    ;;
  *) fail 'Commands: status; arm builtin|next --lab-device; rollback.' ;;
esac
