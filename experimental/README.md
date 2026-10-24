# AliothGuard Experimental v0.2.0

This separate laboratory module (`aliothguard_experimental`) and APK establish
a testable native foundation for future root-hiding and Play Integrity
compatibility work. **There is no root hiding, property spoofing, keybox handling,
certificate modification or Play Integrity request in this version.** Stable
`aliothguard` v0.1.0 is unchanged and independently built.

Target configuration supplied by the owner: Mi 11X / aliothin, AxionOS
`1.6-FINAL-20250621-OFFICIAL-GMS-alioth`, API 35, Magisk 30.7, SELinux Enforcing,
kernel `4.19.246-N0kernel.16.1`, OrangeFox. These are **not locally verified
device measurements**. The installer checks API, architecture, device family,
Magisk and enforcing SELinux. No matching kernel/ROM build is inferred from them.

## What works now

- Read-only JSON status and conservative provider/configuration conflict gates.
- Public Zygisk API v5 integration using the pinned official sample header and
  official NDK ARM64 builds. No proprietary provider binaries are bundled.
- Built-in Magisk Zygisk and separately installed Zygisk Next configurations are
  supported by the controller. It **never enables, disables or switches a
  provider**. Multiple known providers, unknown Magisk settings, pending changes
  and ambiguous provider identities block arming. `zygisksu` is shared by forks;
  a Next metadata label is evidence, not authenticated identity or runtime proof.
- A native probe only for exact process
  `io.github.biglmisfit.aliothguard.test`, matching package/user data path and normal app UIDs, no child zygotes or
  system_server. The library requests unloading after specialization for every
  process. No JNI/PLT hooks, companion daemon or unmount options are used.
- The explicit probe sets a **process-local environment marker**, after UID
  specialization, that the dedicated app's separate JNI reader can observe.
  It does not change Android system properties or write app/system files.
- Optional WebUI: status, provider selection for a temporary test session,
  conflict display and rollback. It uses a KernelSU-style exec bridge offered
  by compatible Magisk WebUI hosts; Magisk itself has no WebUI. No host bundled.
  A normal browser displays the page without root execution capabilities.

## Defaults and limits

The module ZIP ships a `disable` marker and no probe session. The configuration
records `hooks=0` and `probe=0`; there is no option to enable hiding hooks.
Only an explicit `arm builtin|next --lab-device` command can create a temporary
session. It expires after **300 seconds**, is bound to the current boot ID and
is checked before each eligible process starts. Reboot, expiry, missing/invalid
session, UID mismatch or unavailable reads make the probe inert.

The controller checks provider configuration at arming time. Zygisk's public API
does not authenticate the provider or expose Magisk's current database setting
to the app callback. This is **not a continuous exclusivity monitor**. Do not
change providers during a session; rollback first. Renamed/private providers
can evade inventory. We cannot prevent changes made outside AliothGuard.
Existing app processes retain their marker until they exit; expiry/rollback
prevents future probes. A marker can be forged by code inside the same app:
it is a diagnostic observation, never attestation.

AxionOS 1.6 source includes PIF settings and Tricky-Store-derived framework
keybox hooks. See [AXIONOS_1_6.md](docs/AXIONOS_1_6.md) for dated evidence and
uncertainty. ROM keybox/PIF settings and other modules are never changed or
read for secret contents. Existing integrity modules are reported as potential
overlap, not proof of a verdict. Hiding modules block this isolated probe test.

**Do not use the owner's only phone as the first native-injection test device.**
A green hosted build/emulator cannot validate actual Magisk/Next injection,
ARM64 execution, this kernel, SELinux compatibility, boot safety, OrangeFox data
decryption, or Google hardware attestation. There is no bootloop-proof claim.
With no spare recoverable device, leave real-injection testing pending.

## Laboratory-only validation path

After code/test review and a separate decision on a recoverable test device:
install the separate ZIP and lab APK there, review status, and manually choose
exactly one provider in its existing manager. AliothGuard does not configure it.
The ZIP starts disabled. Enabling this experimental module is a separate manual
manager action and normally requires a reboot. No arming session survives it.
Then use the WebUI or the controller's `arm` command, and start a fresh lab-app
process within five minutes. `OBSERVED_IN_THIS_PROCESS` is the expected probe
result; `NOT_OBSERVED` is honest absence/denial, not proof of provider failure.

Rollback uses `scripts/control.sh rollback`: remove only our session, create
only our `disable` marker, never reboot or kill apps automatically. See
[RECOVERY.md](docs/RECOVERY.md). Root-path visibility observations in the app are
separate from Play Integrity, which remains `NOT_REQUESTED` with null verdicts.

## Build and review from Chrome on Android

Open this PR's **Files changed** and **Checks**. In **Actions**, select
**Experimental native laboratory**, choose **Run workflow**, select the
experimental branch, and enable the emulator option. Use Chrome's Desktop site
if GitHub hides the controls. After completion, open the run and download:

- `AliothGuard-Experimental-v0.2.0`: separate Magisk ZIP, lab APK, SHA256SUMS.
- `AliothGuard-Experimental-reports`: host/native/packaging reports.
- `AliothGuard-Experimental-emulator`: Android shell, native and app smoke reports.

The outer GitHub artifact ZIP is a container, not a Magisk installer. Downloading
does not require installation. Do not confuse this experiment with the stable
`AliothGuard-v0.1.0.zip`. No paid tools/runners are required; account quotas apply.

Local/CI dependencies: Python 3.10+, GCC, Node, ShellCheck, actionlint, JDK 17+,
official Android platform 35, build-tools 35.0.0, NDK 27.2.12479018. Set
`ANDROID_HOME` and `JAVA_HOME`, then run `bash experimental/tools/check.sh`.
All outputs are in ignored `dist/experimental` and `reports/experimental`.
The module ZIP is deterministic for identical native/toolchain/source inputs;
the lab APK uses a fresh debug signing key per workspace and is not a
reproducible production-signed artifact. Debug keys are not uploaded or shipped.

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for remaining development gates.
