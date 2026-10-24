#!/system/bin/sh
# SPDX-License-Identifier: MIT
# Sourced by Magisk; only extracted files in this separate module are changed.
[ "${BOOTMODE:-false}" = true ] || abort '! Install from Magisk only; OrangeFox is recovery, not the installer.'
[ "$(id -u)" = 0 ] || abort '! Root installation required.'
[ -z "${KSU:-}${APATCH:-}" ] || abort '! Only Magisk is supported.'
case ${MAGISK_VER_CODE:-} in ''|*[!0-9]*) abort '! Unknown Magisk version.' ;; esac
[ "$MAGISK_VER_CODE" -ge 30700 ] || abort '! Requires Magisk 30.7 or newer.'
if [ "${ARCH:-}" != arm64 ] || [ "${API:-}" != 35 ]; then abort '! Only ARM64 Android 15 is supported.'; fi
if [ -z "${MODPATH:-}" ] || [ ! -d "$MODPATH" ] || [ -L "$MODPATH" ]; then abort '! Invalid module staging directory.'; fi
for agx_parent in scripts config zygisk; do
  if [ ! -d "$MODPATH/$agx_parent" ] || [ -L "$MODPATH/$agx_parent" ]; then abort '! Missing or linked payload directory.'; fi
done
for agx_file in module.prop disable skip_mount action.sh config/defaults.conf scripts/control.sh scripts/environment.sh zygisk/arm64-v8a.so; do
  if [ ! -f "$MODPATH/$agx_file" ] || [ -L "$MODPATH/$agx_file" ]; then abort "! Missing or linked payload: $agx_file"; fi
done
# shellcheck source=experimental/module/scripts/environment.sh
. "$MODPATH/scripts/environment.sh"
agx_init
agx_scan "$MODPATH"
agx_target || abort '! Target device, API, Magisk or SELinux requirement not met.'
case $AGX_PROVIDER in builtin|next|none) ;; *) abort "! Provider state refused: $AGX_PROVIDER ($AGX_REASON)." ;; esac
[ ! -L "$MODPATH/state" ] || abort '! Linked state directory.'
mkdir -p "$MODPATH/state"
# Reinstallation must never restore an armed session from an old version.
[ ! -L "$MODPATH/state/session" ] || abort '! Linked session file.'
rm -f -- "$MODPATH/state/session"
set_perm "$MODPATH/state" 0 0 0700
set_perm "$MODPATH/action.sh" 0 0 0755
set_perm "$MODPATH/scripts/control.sh" 0 0 0755
set_perm "$MODPATH/zygisk/arm64-v8a.so" 0 0 0644
ui_print '- AliothGuard Experimental v0.2.0 is disabled by default.'
ui_print '- No provider has been enabled or changed. No hiding or attestation hooks exist in this build.'
ui_print '- Review experimental/README.md and use only a separate recoverable laboratory device.'
