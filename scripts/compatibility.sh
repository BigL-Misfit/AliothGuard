#!/system/bin/sh
# SPDX-License-Identifier: MIT
# Findings are configuration evidence, not proof of runtime injection.

ag_magisk() {
  if ! command -v magisk >/dev/null 2>&1; then
    ag_line Magisk 'command unavailable; root manager and Zygisk state UNKNOWN'
    return 0
  fi
  ag_version=$(magisk -v 2>/dev/null | ag_clean)
  ag_code=$(magisk -V 2>/dev/null | ag_clean)
  ag_line 'Magisk version (reported)' "${ag_version:-unknown} / ${ag_code:-unknown}"
  # SELECT only. No denylist enumeration or database writes.
  if ag_settings=$(magisk --sqlite "SELECT key,value FROM settings WHERE key IN ('zygisk','denylist');" 2>/dev/null); then
    ag_z=$(printf '%s\n' "$ag_settings" | sed -n 's/^key=zygisk|value=\([01]\)$/\1/p')
    ag_d=$(printf '%s\n' "$ag_settings" | sed -n 's/^key=denylist|value=\([01]\)$/\1/p')
    case "$ag_z" in 0|1) AG_BUILTIN=$ag_z ;; esac
    case "$ag_d" in 0|1) AG_DENYLIST=$ag_d ;; esac
  fi
  ag_line 'Built-in Zygisk setting' "$AG_BUILTIN (configured, not verified running)"
  ag_line 'Enforce DenyList setting' "$AG_DENYLIST"
  ag_line 'ZYGISK_ENABLED environment hint' "$(printf '%s' "${ZYGISK_ENABLED:-unset}" | ag_clean)"
}

ag_classify() {
  case "$1" in
    zygisksu|zygisk_next|rezygisk|neozygisk) printf '%s' provider ;;
    shamiko|zygisk_shamiko|zygisk-assistant|zygisk_assistant|zygisksu_assistant|nohello|treatwheel|treat-wheel) printf '%s' hiding ;;
    playintegrityfix|playintegrityfork|safetynet-fix|safetynetfix|integritybox) printf '%s' integrity ;;
    tricky_store|trickystore) printf '%s' attestation ;;
    *) printf '%s' other ;;
  esac
}

ag_inventory() {
  if [ "$AG_SCAN_MODULES" != 1 ]; then
    ag_line 'Module inventory' 'SKIPPED by configuration; conflict assessment incomplete'
    return 0
  fi
  if [ ! -d "$AG_DATA/modules" ] || [ ! -r "$AG_DATA/modules" ] || [ ! -x "$AG_DATA/modules" ] || [ -L "$AG_DATA/modules" ]; then
    ag_line 'Module inventory' 'UNKNOWN: modules directory absent, inaccessible or linked'
    return 0
  fi
  AG_INVENTORY=observed
  for ag_dir in "$AG_DATA/modules"/*; do
    [ -d "$ag_dir" ] || continue
    if [ -L "$ag_dir" ]; then
      ag_line WARNING 'Linked module directory skipped.'
      continue
    fi
    ag_id=${ag_dir##*/}
    ag_display=$(printf '%s' "$ag_id" | ag_clean)
    ag_declared=$(ag_meta "$ag_dir/module.prop" id)
    ag_name=$(ag_meta "$ag_dir/module.prop" name)
    ag_version=$(ag_meta "$ag_dir/module.prop" version)
    ag_state=enabled-on-disk
    [ ! -e "$ag_dir/disable" ] || ag_state=disabled-on-disk
    [ ! -e "$ag_dir/remove" ] || ag_state=pending-removal
    ag_kind=$(ag_classify "$ag_id")
    ag_line "Module $ag_display" "name=${ag_name:-unknown} (unverified label); id=${ag_declared:-unreadable}; version=${ag_version:-unknown}; $ag_state; $ag_kind"
    if [ "$ag_id" = zygisksu ]; then
      ag_line NOTICE 'zygisksu is shared by provider forks (including Next/NeoZygisk); exact implementation is not authenticated.'
    fi
    if [ "$ag_id" != "$ag_declared" ]; then
      ag_line WARNING 'Directory/metadata ID mismatch; classification uses directory only, identity uncertain.'
    fi
    if [ -e "$ag_dir/update" ]; then
      ag_line NOTICE 'Pending update marker; installed metadata may describe a different version from running code.'
    fi
    [ "$ag_state" = enabled-on-disk ] || continue
    case "$ag_kind" in
      provider) AG_EXTERNAL=$((AG_EXTERNAL + 1)) ;;
      hiding) AG_HIDERS=$((AG_HIDERS + 1)) ;;
      integrity) AG_INTEGRITY=$((AG_INTEGRITY + 1)) ;;
      attestation) AG_TRICKY=$((AG_TRICKY + 1)) ;;
    esac
    case "$ag_id" in shamiko|zygisk_shamiko) AG_SHAMIKO=1 ;; esac
    case "$ag_id" in zygisk-assistant|zygisk_assistant|zygisksu_assistant) AG_ASSISTANT=1 ;; esac
  done
  if [ -d "$AG_DATA/modules_update" ] && [ ! -L "$AG_DATA/modules_update" ]; then
    for ag_pending in "$AG_DATA/modules_update"/*; do
      [ -d "$ag_pending" ] || continue
      ag_line 'Staged module (not counted as running)' "$(printf '%s' "${ag_pending##*/}" | ag_clean)"
    done
  fi
  ag_line NOTICE 'Enabled/disabled/remove flags describe disk state; changes may require reboot and do not prove loaded state.'
  ag_line NOTICE 'Unrecognized IDs, renamed modules and private forks may be missed.'
}

ag_conflicts() {
  if [ "$AG_INVENTORY" != observed ]; then
    ag_line 'Conflict assessment' 'UNKNOWN: module inventory unavailable or skipped'
    return 0
  fi
  if [ "$AG_EXTERNAL" -gt 1 ]; then
    ag_line WARNING 'Multiple external Zygisk providers enabled on disk: incompatible configuration risk; running providers unverified.'
  fi
  if [ "$AG_EXTERNAL" -gt 0 ] && [ "$AG_BUILTIN" = 1 ]; then
    ag_line WARNING 'Built-in Zygisk plus external provider: documented incompatible configuration. Verify current manager settings manually.'
  fi
  if [ "$AG_HIDERS" -gt 1 ]; then
    ag_line WARNING 'Multiple hiding modules enabled on disk: overlapping hooks and compatibility unknown.'
  fi
  if [ "$AG_INTEGRITY" -gt 1 ]; then
    ag_line WARNING 'Multiple integrity/spoofing modules enabled on disk: overlapping configuration risk.'
  fi
  if [ "$AG_DENYLIST" = 1 ] && { [ "$AG_ASSISTANT" = 1 ] || [ "$AG_SHAMIKO" = 1 ]; }; then
    ag_line WARNING 'Enforce DenyList with Assistant/Shamiko: upstream configuration conflict; review the exact installed release documentation.'
  fi
  if [ "$AG_INTEGRITY" -gt 0 ] && [ "$AG_DENYLIST" = 1 ]; then
    ag_line NOTICE 'Integrity module with enforced DenyList: excluding its target process can prevent hooks. App membership was NOT inspected.'
  fi
  if [ "$AG_EXTERNAL" = 0 ] && [ "$AG_BUILTIN" = 0 ] && { [ "$AG_HIDERS" -gt 0 ] || [ "$AG_INTEGRITY" -gt 0 ]; }; then
    ag_line WARNING 'Modules may need Zygisk, but no known provider is configured; fork/runtime status remains unverified.'
  fi
  ag_line 'Compatibility conclusion' 'No automatic fixes. Absence of warnings is NOT proof of compatibility.'
}

ag_integrity() {
  if [ "$AG_SCAN_INTEGRITY_CONFIG" != 1 ]; then
    ag_line 'Integrity configuration' 'SKIPPED by configuration'
    return 0
  fi
  for ag_path in pif.json pif.prop playintegrityfix/custom.pif.json playintegrityfix/custom.pif.prop modules/playintegrityfix/pif.json modules/playintegrityfix/pif.prop modules/playintegrityfix/custom.pif.json modules/playintegrityfix/custom.pif.prop tricky_store/target.txt tricky_store/security_patch.txt; do
    ag_file_hint "$ag_path"
  done
  ag_line 'Attestation keys' 'Not opened, copied, validated or supplied; keybox contents are outside this diagnostic.'
  ag_line 'Play Integrity verdict' 'UNKNOWN: no Google API request or hardware attestation test is performed.'
  ag_line NOTICE 'Config-file presence does not establish active settings, validity, provenance or an integrity verdict.'
}

ag_rom_hints() {
  if [ "$AG_SCAN_ROM_HINTS" != 1 ]; then
    ag_line 'ROM spoofing hints' 'SKIPPED by configuration'
    return 0
  fi
  for ag_key in persist.sys.pihooks.enable persist.sys.pihooks.enabled persist.sys.pixelprops.gms persist.sys.pixelprops.gphotos persist.sys.spoof.gms persist.sys.spoof.pif; do
    ag_value=$(ag_prop "$ag_key")
    [ -z "$ag_value" ] || ag_line "ROM hint $ag_key" "$ag_value (heuristic, ROM-specific; not proof)"
  done
  ag_line 'ROM-integrated spoofing' 'UNKNOWN: per-process/framework hooks can be invisible to root-shell properties; missing hints do not mean absent.'
}
