# Tricky Store external backend candidate — v1.4.1 build 248

**Status: not approved for installation or redistribution.** This is an integration note for the owner's Android 15 / API 35 AxionOS 1.6 Mi 11X, not an installation guide. The owner's only phone has no PC/OTG recovery path.

## User-provided artifact inspected without executing

- Supplied archive: `Tricky-Store-v1.4.1-248-3b07ee3-release.zip`
- Full ZIP SHA-256: `0bc227c59b9b4baa77d8c46ff310c276a88114e4dcf7ed10d886023924183454`.
- `module.prop` identifies `tricky_store`, v1.4.1, code 248. The installer allows Magisk and targets Android SDK >=29, including ARM64.
- CRC and all 21 **embedded** SHA-256 checks passed. Embedded hashes demonstrate internal consistency, **not upstream authenticity**.
- The official upstream `release/update.json` currently advertises v1.4.1 build **245** (`72b2e84`) rather than 248. Therefore build 248's origin and binary equivalence to upstream are **unverified**.
- The payload contains proprietary `libtricky_store.so` binaries, a boot `service.sh` invoking a daemon through `app_process`, `sepolicy.rule`, a test/default `keybox.xml`, and a `target.txt` scope including GMS and Play Store.
- Its installer describes the included `keybox.xml` as a **default software keybox**. The XML includes private-key material. Do not print, extract for telemetry, commit, redistribute, or send that material to CI. This is **not** evidence of a trusted unrevoked hardware keybox or STRONG.

## Integration boundaries

1. AliothGuard **does not bundle** Tricky Store binaries, keybox files, or a download-on-boot mechanism. This maintains licensing/provenance boundaries and avoids exposing attestation secrets in GitHub Actions.
2. AxionOS 1.6's June 2025 framework sources include Tricky-Store-derived keybox hooks backed by `Settings.System` (`custom_keybox_data`). The standalone Magisk module uses `/data/adb/tricky_store/keybox.xml`. They are different stacks that may overlap; do not enable both without isolated testing.
3. Keep the stable diagnostics module read-only. If a future backend adapter is implemented, it must detect installed state and ROM ownership conservatively; refuse automatic installation, replacement, imports, system-property changes, or PIF/keybox modifications.
4. No claim of DEVICE or STRONG integrity follows from a module being installed, a keybox file existing, or certificate metadata looking plausible. A real Google Play Integrity verdict on the exact device is required.
5. The user's ROM reports a 2025-06-01 system/vendor patch. Google's documented STRONG rules on Android 13+ require DEVICE integrity and recent OS/vendor security patches. Neither a standalone module nor the default software keybox guarantees this.
6. Existing Magisk/Zygisk root-hiding behavior is a **separate** concern. Do not infer app root invisibility from an attestation certificate chain.
7. Until a safe recovery path exists, do not flash this binary as an experiment on the sole Mi 11X; independent native keystore hooks can crash critical services or conflict with the ROM.

## Upstream references

- https://github.com/5ec1cff/TrickyStore/releases
- https://github.com/5ec1cff/TrickyStore/blob/release/update.json
- https://developer.android.com/google/play/integrity/verdicts
- See `AXIONOS_1_6.md` for dated evidence of the ROM-integrated hooks.

**No private keys or bundled ZIP contents are committed here.**
