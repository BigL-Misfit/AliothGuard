#!/system/bin/sh
# SPDX-License-Identifier: MIT
# Sourced by Magisk after its normal extraction and default permissions.
# Do not set SKIPUNZIP or exit: Magisk owns staging, cleanup and finalization.

[ "${BOOTMODE:-false}" = true ] || abort '! Install from the Magisk app only; recovery installation is unsupported.'
[ "$(id -u)" = 0 ] || abort '! Magisk root installation is required.'
if [ -n "${KSU:-}" ] || [ -n "${APATCH:-}" ]; then
  abort '! Version 1 supports Magisk only.'
fi
case ${MAGISK_VER_CODE:-} in
  ''|*[!0-9]*) abort '! Cannot verify the Magisk version.' ;;
esac
[ "$MAGISK_VER_CODE" -ge 28000 ] || abort '! Magisk 28.0 or newer is required for the Action workflow.'
[ "${ARCH:-}" = arm64 ] || abort '! Only ARM64 is supported by this release.'
[ "${API:-}" = 35 ] || abort '! This release targets Android 15 (API 35) only.'
if [ -z "${MODPATH:-}" ] || [ ! -d "$MODPATH" ]; then
  abort '! Missing Magisk module staging directory.'
fi

# Prefer vendor identity because ROMs sometimes change the system identity.
ag_install_device=$(getprop ro.product.vendor.device)
[ -n "$ag_install_device" ] || ag_install_device=$(getprop ro.product.device)
case "$ag_install_device" in
  alioth|aliothin) ;;
  *) abort '! Unsupported or unknown device. Expected alioth or aliothin.' ;;
esac
[ "$(getprop ro.build.version.sdk)" = 35 ] || abort '! Android API property does not match API 35.'

for ag_file in module.prop skip_mount action.sh scripts/diagnose.sh scripts/common.sh scripts/compatibility.sh config/diagnostics.conf; do
  if [ ! -f "$MODPATH/$ag_file" ] || [ -L "$MODPATH/$ag_file" ]; then
    abort "! Missing or linked module file: $ag_file"
  fi
done
for ag_forbidden in post-fs-data.sh service.sh boot-completed.sh system.prop sepolicy.rule system vendor product system_ext zygisk; do
  if [ -e "$MODPATH/$ag_forbidden" ] || [ -L "$MODPATH/$ag_forbidden" ]; then
    abort "! Forbidden diagnostic-release payload: $ag_forbidden"
  fi
done

# Only our own extracted files receive permissions through Magisk's helper.
set_perm "$MODPATH/action.sh" 0 0 0755
set_perm "$MODPATH/scripts/diagnose.sh" 0 0 0755
set_perm "$MODPATH/scripts/common.sh" 0 0 0644
set_perm "$MODPATH/scripts/compatibility.sh" 0 0 0644
ui_print '- AliothGuard v0.1.0: manual diagnostics only.'
ui_print '- No boot hooks, property changes, hiding, or partition payloads.'
ui_print '- No other modules or their configuration were changed.'
ui_print '- After installation, use the module Action button to print a report.'
ui_print '- Automated tests do not establish real-device safety.'
