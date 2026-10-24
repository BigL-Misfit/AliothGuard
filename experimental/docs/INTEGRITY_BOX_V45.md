# Integrity Box v45 + Tricky Store 1.4.1 compatibility assessment
Date: 2026-10-24. Target: Mi 11X aliothin, AxionOS 1.6 FINAL Android 15 API35, Magisk 30.7, SELinux Enforcing.

## Scope and evidence
Inspected owner-supplied ZIPs statically only; no binaries, scripts, or key material executed or copied into GitHub.

- Integrity Box archive: `v45-Integrity-Box-18-10-2026.zip`
  - SHA-256: `f217bcaf24d4659bd023f7d44749a5de1251d8b4f6b6da96a8b307b496669c5f`
  - Archive passed CRC and path traversal/symlink checks. **These do not prove authenticity or safety.**
  - `module.prop`: id=`playintegrityfix`, version=v45, versionCode=45000. Includes arm64 Zygisk shared library, Play Integrity spoofing tools, WebUI and boot-time `post-fs-data.sh` + `service.sh`.
- Tricky Store archive: `Tricky-Store-v1.4.1-248-3b07ee3-release.zip`
  - SHA-256: `0bc227c59b9b4baa77d8c46ff310c276a88114e4dcf7ed10d886023924183454`
  - `module.prop`: id=`tricky_store`, version v1.4.1 build 248. Installer bundles a default **software** keybox, not proven trusted hardware-backed credentials. Do not publish private keys.
  - Build 248 provenance is not authenticated to the official upstream release; compatibility should not be assumed solely from version label.

## Concrete interactions found

1. Integrity Box **contains PIF**; its `playintegrityfix` module ID competes with standalone PIF/PIF Fork. Never stack them.
2. Integrity Box's published requirements specify **Tricky Store OOS or TEE Simulator**, plus **Zygisk Next or Meow Zygisk**. The supplied archive is ordinary Tricky Store build 248, *not demonstrated to be OOS*. This exact pair must be treated as unverified until backend-compatibility tests exist.
3. The integrity box installer and boot scripts may change `persist.sys.pihooks.*` / `persist.sys.pixelprops.*` and boot-state/build properties; `post-fs-data.sh` may edit Magisk DenyList membership for Google services.
4. `service.sh` spoofs selected bootloader, verified-boot and property values. Setup scripts write security-patch overrides into `/data/adb/tricky_store/security_patch.txt` and device properties, including a hard-coded `2026-10-05` value in a generated service script. The real ROM reports June 2025 OS/vendor patches; this is not evidence the device is genuinely patched.
5. `webroot/common_scripts/target.sh` creates/overwrites Tricky Store `target.txt`, incorporating **all installed user app packages** and selected Google apps; when SELinux is Enforcing it uses `setenforce 0` temporarily. A failure could leave settings changed. Do not trigger it as a harmless diagnostic.
6. `webroot/common_scripts/key.sh` can download keybox data via wget/curl options that **skip TLS certificate verification** (`--no-check-certificate`, `--insecure`). It may overwrite existing keybox paths and copy material to other backend paths. Do not put secrets into an automated keybox download workflow.
7. `action.sh` includes `reset_tricky_store`, `download_keybox`, `update_targets`, security-patch handling and restarting Google services. It is **not read-only**.
8. AxionOS 1.6 sources already show ROM-integrated PIF and Tricky-Store-derived framework hooks. Their runtime/enabled state on this precise phone has not been verified. Avoid stacking a second framework attestation backend by default.

## Architecture and safe integration choice

- Keep AliothGuard's stable v0.1.0 untouched.
- Treat both uploaded modules as **external optional dependencies**. Do not embed their ZIPs, binary libraries, XML key material, updater URLs, or credentials in AliothGuard.
- Develop an explicit backend ownership decision before any installation:
  **ROM Axion integrated attestation** OR **standalone Tricky Store and Integrity Box**; never claim both are necessarily safe together.
- For an external branch, remove duplicate PIF modules. Use **one** Zygisk runtime provider at once; built-in Magisk Zygisk must be OFF if switching to Zygisk Next. Confirm exact backend compatibility instead of assuming standard Tricky Store satisfies OOS requirements.
- Root-hiding for user apps is a **separate workstream**. Neither keybox nor Play Integrity PIF guarantees an app cannot detect Magisk, installed root tools, or other signals. Track app-specific behavior and do not automatically modify banking/Google processes.
- Do not implement automatic security-patch spoofing or keybox downloads in AliothGuard. A reproducible test report with **UNKNOWN** until real device-side official verdict is better than manufactured success.
- Collect Play Store developer Play Integrity verdicts and app-specific root-detection outcomes only after an independently reviewed, recoverable test plan. **No claim of STRONG** follows from a keybox XML, modified property, CI passing, or checksum.

## Relevant upstream
- https://github.com/MeowDump/Integrity-Box (v45, PIF-included and backend requirements)
- https://github.com/5ec1cff/TrickyStore
- https://developer.android.com/google/play/integrity/verdicts
- See `AXIONOS_1_6.md` and `TRICKY_STORE_BACKEND.md` in this directory.

**Do not flash these unreviewed binary modules on the owner's only phone as a one-shot combination.** Integrity Box can change shared global Magisk/ROM state beyond its module directory. Module-folder deletion may not restore all modifications.
