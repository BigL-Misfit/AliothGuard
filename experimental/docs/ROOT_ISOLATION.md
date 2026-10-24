# AliothGuard v0.2 first functional root-isolation milestone

This is an **opt-in Magisk DenyList controller**, not a universal root-hider and not a Play Integrity bypass. The project remains targeted at **Android 15 / API 35 AxionOS 1.6 on Mi 11X**, with existing Magisk 30.7 and built-in Zygisk. It is separate from the experimental native probe and does not require replacing Zygisk.

## What exists
`experimental/tools/denylist-control.sh` provides explicit `status`, `list`, `add PACKAGE [PROCESS]` and `remove PACKAGE [PROCESS]` commands. It never runs on boot and is not packaged into either Magisk module. All changes require root, an installed app and Zygisk configured on. It refuses core Google services and Android/Magisk package targets and never changes Zygisk providers or Enforce DenyList.

## Important limits
DenyList behavior depends on Magisk's actual mode, enforcement, target-app processes and the ROM. A DenyList entry alone **does not guarantee that an app cannot detect root**. Some root-sensitive apps check bootloader, verified boot or other properties. The helper does not manipulate those values, hide native maps, or change Play Integrity attestation. Google BASIC / DEVICE / STRONG verdicts remain untested. Existing AxionOS PIF / Tricky Store features are not toggled or modified.

## Before real-device use
Do not run this on the owner's only phone until CI is reviewed and the current list is recorded for rollback. The `remove` operation affects the named package/process and could remove a user preexisting entry: users should not call remove unless they have checked their prior state. Prefer a disposable user-installed application for testing, never payment/banking/Google services as an initial target. The script uses `magisk --denylist` directly and has no automatic rollback or scheduled action.

Run `python3 -m unittest experimental.tests.test_denylist_control -v` in a safe development environment to check mocked behavior. The existing v0.1.0 ZIP and experimental native ZIP are not changed by this controller.

## Next implementation steps
1. Verify hosted experimental native build and API-35 emulator smoke; no real-device Magisk injection has been tested.
2. Add automated report-only app detection tests in a dedicated lab APK to measure root visibility without assuming success.
3. Map AxionOS 1.6's installed settings to documented PIF/Tricky Store integration points; avoid keyboxes, fabricated attestation, or blanket integrity guarantees.
