#!/system/bin/sh
# SPDX-License-Identifier: MIT
# No elevated writes, external network calls, global property dumps or app lists.
MODDIR=${0%/*}/..
# shellcheck source=scripts/common.sh
. "$MODDIR/scripts/common.sh"
# shellcheck source=scripts/compatibility.sh
. "$MODDIR/scripts/compatibility.sh"

ag_init || exit 1
ag_config "$MODDIR/config/diagnostics.conf"
printf '%s\n' 'AliothGuard v0.1.0 — manual diagnostic report' 'Observation only. No fixes or integrity verdicts are produced.'
ag_line 'Privilege UID' "$(id -u)"
if [ "$(id -u)" != 0 ]; then
  ag_line WARNING 'Not running as root: module and Magisk observations may be incomplete.'
fi
if ! command -v getprop >/dev/null 2>&1; then
  ag_line ERROR 'Android getprop unavailable; run in Android or the explicit mock harness.'
  exit 1
fi
for ag_device_key in ro.product.device ro.product.vendor.device ro.product.cpu.abi ro.board.platform ro.build.version.release ro.build.version.sdk ro.build.version.security_patch ro.boot.verifiedbootstate ro.boot.flash.locked; do
  ag_device_value=$(ag_prop "$ag_device_key")
  ag_line "$ag_device_key" "${ag_device_value:-unknown}"
done
ag_device=$(ag_prop ro.product.vendor.device)
[ -n "$ag_device" ] || ag_device=$(ag_prop ro.product.device)
case "$ag_device:$(ag_prop ro.build.version.sdk):$(ag_prop ro.product.cpu.abi)" in
  alioth:35:arm64-v8a|aliothin:35:arm64-v8a) ag_line 'Target profile' 'matches reported Mi 11X-family / Android 15 / ARM64 properties' ;;
  *) ag_line WARNING 'Reported device/API/ABI does not match the supported installation profile.' ;;
esac
ag_line NOTICE 'Properties are reported values and can be spoofed; they do not prove hardware identity or boot trust.'
ag_magisk
ag_inventory
ag_conflicts
ag_integrity
ag_rom_hints
printf '%s\n' 'END: diagnostic complete. Warnings are observations, not automatic change requests.'
