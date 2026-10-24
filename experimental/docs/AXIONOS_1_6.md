# AxionOS 1.6 research — checked 2026-10-24

**Conclusion:** public AxionOS Android 15 source associated with the June 2025
1.6 FINAL release already has PIF configuration/UI support and integrated
Tricky-Store-derived keybox hooks. This is not evidence that the separately
distributed closed-source Tricky Store Magisk module is installed. We did not
download or inspect the owner's exact ROM ZIP, installed framework, private key
material or current settings. Feature availability in source does not prove it
is enabled, configured, effective or identical in that device build.

## Dated primary evidence

| Evidence | What it establishes |
| --- | --- |
| [vendor version commit, 2025-06-19](https://github.com/AxionAOSP/android_vendor_lineage/commit/1dfc7eb7a48ae6fe1a076ce7de98a312b0a4ecac) | Changes major/minor to 1.6 and release type to FINAL. |
| [1.6 changelog, 2025-06-19](https://github.com/AxionAOSP/axion_changelogs/commit/760c78f9ce588ba6d8b81fcb73248ec89ec38538) | Identifies the June final release. Its preceding 1.5 changelog already lists importing keyboxes. |
| [1.5 June update](https://github.com/AxionAOSP/axion_changelogs/blob/e274663516951ee4e2a8f4260157f5f23534461f/README.md) | Keybox import predates 1.6; do not infer absence from 1.6's incremental changelog. |
| [Personalizations Spoof.java at pre-build commit f512198](https://github.com/AxionAOSP/android_packages_apps_Personalizations/blob/f512198f454295fc71191794ece200a8570cba04/src/com/custom/settings/fragments/Spoof.java) and [spoof.xml](https://github.com/AxionAOSP/android_packages_apps_Personalizations/blob/f512198f454295fc71191794ece200a8570cba04/res/xml/spoof.xml) | On 2025-06-20, GMS spoof toggle `persist.sys.pixelprops.gms`, PIF import/update/view, and keybox import/clear UI exist. PIF JSON is stored as `Settings.System` `pif_props_data`; keybox data as `custom_keybox_data`. |
| [framework addition, 2025-06-14](https://github.com/AxionAOSP/android_frameworks_base/commit/63df8fb59f50771f2ffb185a01bc13371fc41a18) | Commit explicitly attributes key-pair/keybox code to `5ec1cff/TrickyStore`, before 1.6 FINAL. This is ROM framework integration, not evidence of a bundled standalone Magisk module. |
| [KeyProviderManager at pre-build framework commit 4aa2e3f](https://github.com/AxionAOSP/android_frameworks_base/blob/4aa2e3ff73c7422b1e8ec7628724c0b052d1d7c5/core/java/com/android/internal/util/custom/KeyProviderManager.java) | The provider loads `custom_keybox_data` from `Settings.System`, not the standalone module's `/data/adb/tricky_store` configuration. |
| [KeyStore2](https://github.com/AxionAOSP/android_frameworks_base/blob/4aa2e3ff73c7422b1e8ec7628724c0b052d1d7c5/keystore/java/android/security/KeyStore2.java), [KeyStoreSecurityLevel](https://github.com/AxionAOSP/android_frameworks_base/blob/4aa2e3ff73c7422b1e8ec7628724c0b052d1d7c5/keystore/java/android/security/KeyStoreSecurityLevel.java) | Actual call sites use `custom.KeyboxImitationHooks`; this is not just an unused Settings label. |

The inspected framework/Personalizations commits are the latest public branch
commits before 2025-06-22, not an authenticated frozen manifest for the owner's
20250621 alioth image. The recursive framework tree response was truncated;
specific cited files and keystore call sites were then retrieved directly.
No claim of a complete ROM code audit is made.

## Compatibility decisions

1. Treat AxionOS 1.6 as potentially owning both property-spoof configuration and
   framework attestation interception. Do not install a second implementation
   automatically or suggest stacked fixes based on a root-detection result.
2. Read only selected public property hints and module metadata. Never query
   `custom_keybox_data`, dump Settings, read keybox XML, enable keybox debug logs,
   fetch the upstream keybox directory, or alter PIF JSON. Presence/validity and
   active behavior remain unknown.
3. The test-app probe changes only that app process's environment marker. It
   neither enters GMS/Play Store processes nor invokes attestation/key-generation
   interception. Existing integrity-module IDs are reported for review; they are
   not disabled or reconfigured.
4. Any future configuration or hiding feature needs a dedicated-device matrix
   for ROM feature state, exact Magisk/Next version, other modules, process,
   operation and separately verified Play Integrity responses.

## Upstream contracts consulted

- [Official Zygisk sample/API v5, pinned commit](https://github.com/topjohnwu/zygisk-module-sample/tree/8ce26128f81baaed0b969aaf7f52f886b61af4ab): lifecycle, unloading, STL restrictions and 0BSD permission.
- [Zygisk Next README](https://github.com/Dr-TSNG/ZygiskNext): Magisk's built-in Zygisk must be off; no multiple root implementations; current proprietary redistribution restrictions. No Next source/binaries copied.
- [Tricky Store README](https://github.com/5ec1cff/TrickyStore): closed-source since 1.1.0, separate module configuration. No implementation or key material copied.
- [KernelSU WebUI contract](https://github.com/tiann/KernelSU/blob/main/website/docs/guide/module-webui.md) and [exec adapter](https://github.com/tiann/KernelSU/blob/main/js/index.js); [WebUI X Portable](https://github.com/MMRLApp/WebUI-X-Portable) documents Magisk host support. Our small bridge adapter is original; real host testing remains pending.
- Google's [Play Integrity verdict documentation](https://developer.android.com/google/play/integrity/verdicts) remains the contract for future API reporting. Direct access was blocked in this workspace; current page content was not verified. No Google verdict functionality is implemented or claimed here.
