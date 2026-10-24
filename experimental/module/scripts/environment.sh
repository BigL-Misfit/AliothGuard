#!/system/bin/sh
# SPDX-License-Identifier: MIT
# Observations only. Never source discovered configuration or module metadata.
# Globals are consumed by control.sh and customize.sh after sourcing this library.
# shellcheck disable=SC2034
agx_clean() { LC_ALL=C tr -cd ' -~' | cut -c 1-160; }
agx_prop() { getprop "$1" 2>/dev/null | agx_clean; }
agx_json() { printf '"%s"' "$(printf '%s' "$1" | agx_clean | sed 's/\\/\\\\/g; s/"/\\"/g')"; }
agx_init() {
  AGX_DATA=/data/adb
  AGX_PROC=/proc
  if [ "${AGX_TEST_MODE:-0}" = 1 ]; then
    case ${AGX_TEST_ROOT:-} in /*) ;; *) return 1 ;; esac
    AGX_DATA=$AGX_TEST_ROOT/data/adb
    AGX_PROC=$AGX_TEST_ROOT/proc
  fi
  AGX_BUILTIN=unknown
  AGX_PROVIDER=unknown
  AGX_EXTERNAL=0
  AGX_NEXT=0
  AGX_PENDING=0
  AGX_HIDERS=0
  AGX_INTEGRITY=0
  AGX_REASON=inventory_unavailable
  AGX_MAGISK=$(magisk -V 2>/dev/null | agx_clean)
  if agx_sql=$(magisk --sqlite "SELECT key,value FROM settings WHERE key='zygisk';" 2>/dev/null); then
    case $agx_sql in key=zygisk\|value=0) AGX_BUILTIN=0 ;; key=zygisk\|value=1) AGX_BUILTIN=1 ;; esac
  fi
}
agx_scan() {
  [ -d "$AGX_DATA/modules" ] && [ -r "$AGX_DATA/modules" ] && [ -x "$AGX_DATA/modules" ] && [ ! -L "$AGX_DATA/modules" ] || return 0
  agx_uncertain=0
  for agx_dir in "$AGX_DATA/modules"/*; do
    [ -d "$agx_dir" ] || continue
    if [ -L "$agx_dir" ]; then agx_uncertain=1; continue; fi
    agx_id=${agx_dir##*/}
    case $agx_id in
      zygisksu|zygisk_next|rezygisk|neozygisk)
        AGX_EXTERNAL=$((AGX_EXTERNAL + 1))
        if [ -e "$agx_dir/disable" ] || [ -e "$agx_dir/remove" ] || [ -e "$agx_dir/update" ]; then AGX_PENDING=1; fi
        agx_name=''
        if [ -f "$agx_dir/module.prop" ] && [ ! -L "$agx_dir/module.prop" ]; then
          agx_name=$(head -c 16384 "$agx_dir/module.prop" | sed -n 's/^name=//p' | agx_clean)
        fi
        case $agx_id:$agx_name in zygisksu:'Zygisk Next'|zygisk_next:'Zygisk Next') AGX_NEXT=$((AGX_NEXT + 1)) ;; esac
        ;;
      shamiko|zygisk_shamiko|zygisk-assistant|zygisk_assistant|treatwheel|nohello)
        [ -e "$agx_dir/disable" ] || AGX_HIDERS=$((AGX_HIDERS + 1)) ;;
      playintegrityfix|playintegrityfork|integritybox|safetynet-fix|tricky_store|trickystore)
        [ -e "$agx_dir/disable" ] || AGX_INTEGRITY=$((AGX_INTEGRITY + 1)) ;;
    esac
  done
  for agx_dir in "$AGX_DATA/modules_update"/*; do
    # Magisk's own staging directory is expected while customize.sh is sourced.
    [ "$agx_dir" != "${1:-}" ] || continue
    [ ! -e "$agx_dir" ] || AGX_PENDING=1
  done
  AGX_REASON=provider_unknown
  if [ "$AGX_BUILTIN" = unknown ] || [ "$agx_uncertain" = 1 ]; then return 0; fi
  if [ "$AGX_EXTERNAL" -gt 1 ] || { [ "$AGX_BUILTIN" = 1 ] && [ "$AGX_EXTERNAL" -gt 0 ]; }; then
    AGX_PROVIDER=conflict; AGX_REASON=multiple_providers; return 0
  fi
  if [ "$AGX_PENDING" = 1 ]; then AGX_REASON=pending_module_state; return 0; fi
  case $AGX_BUILTIN:$AGX_EXTERNAL:$AGX_NEXT in
    1:0:0) AGX_PROVIDER=builtin; AGX_REASON=single_configured_provider ;;
    0:1:1) AGX_PROVIDER=next; AGX_REASON=next_label_not_authenticated ;;
    0:0:0) AGX_PROVIDER=none; AGX_REASON=no_configured_provider ;;
  esac
}
agx_target() {
  case $AGX_MAGISK in ''|*[!0-9]*) return 1 ;; esac
  [ "$AGX_MAGISK" -ge 30700 ] || return 1
  [ -z "${KSU:-}${APATCH:-}" ] || return 1
  [ "$(agx_prop ro.build.version.sdk)" = 35 ] || return 1
  [ "$(agx_prop ro.product.cpu.abi)" = arm64-v8a ] || return 1
  agx_device=$(agx_prop ro.product.vendor.device)
  [ -n "$agx_device" ] || agx_device=$(agx_prop ro.product.device)
  case $agx_device in alioth|aliothin) ;; *) return 1 ;; esac
  [ "$(getenforce 2>/dev/null)" = Enforcing ]
}
