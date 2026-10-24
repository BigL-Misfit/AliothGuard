# AliothGuard v0.1.0

Manual, diagnostic-only Magisk module for Xiaomi Mi 11X (`alioth` / `aliothin`),
ARM64, Android 15 (API 35), with Magisk 28.0 or newer. Other devices, API levels,
root managers and recovery-mode installation are rejected in this release.

**Review automated test reports before considering installation. A green build
does not prove real-device safety. This module is not bootloop-proof.** Your
only phone has no PC or OTG recovery fallback: read [RECOVERY.md](docs/RECOVERY.md).
This project does not ask you to install an unreviewed build.

## Manual diagnostics

The module's Magisk **Action** button prints a report. It reads selected Android
properties, Magisk's version and two settings using a read-only SQL query, module
metadata/state flags, known configuration-file presence and ROM-specific hints.
It saves no report and makes no network requests. Configuration in
[`config/diagnostics.conf`](config/diagnostics.conf) is parsed as data, never
executed. Switches accept exactly `0` or `1`; unsupported lines generate a
warning, and the last valid value wins for repeated keys.

| Observation | Meaning and limits |
| --- | --- |
| Device, ABI, Android API, patch and boot-state properties | Reported values can be spoofed. Snapdragon 870 shares platform identifiers with related chips; these values are not hardware proof. |
| Built-in Zygisk and Enforce DenyList settings | Configuration only, not proof of runtime injection. Query failure is unknown. |
| Known provider, hiding, integrity and attestation module IDs | On-disk state, including disabled/remove flags; staged updates are separate. Renamed modules/private forks can be missed. Pending changes may differ from running state. |
| Multiple providers, built-in plus external Zygisk, overlapping modules, certain DenyList combinations | Warnings, never automatic fixes. No warning is not proof of compatibility. |
| Known PIF text/JSON and Tricky Store configuration paths | Existence only. Contents, target apps and keys are not opened; validity and actual use remain unknown. |
| ROM spoofing properties | Heuristics. Hidden framework/per-process hooks can be invisible; absent hints do not establish absence. |

This does **not** call Google's Play Integrity API or determine BASIC, DEVICE or
STRONG verdicts. It does not hide root, spoof properties, supply keyboxes, hook
Zygisk or guarantee any attestation result. [Future architecture and researched
upstreams](docs/ARCHITECTURE.md) are separate from the stable module.

## Safety boundary

There are no boot scripts, native libraries, `system.prop`, `sepolicy.rule`,
system overlays, scheduled tasks or automatic boot operations. `skip_mount` is
an empty marker preventing module system mounting. No uninstall script is
needed: the action creates no external files. Magisk owns normal staging,
module permissions, removal and lifecycle state.

`customize.sh` is sourced by Magisk, checks the supported device/environment,
and sets permissions on its own files only. Neither it nor diagnostics changes
another module, properties, SELinux policies, device settings, partitions,
Google app data or bootloader state. Nothing flashes, relocks, wipes, reboots,
kills apps or downloads data. Do not use “disable all modules” as an automatic
AliothGuard step.

The ZIP supports **installation through the Magisk app only**. The [official
Magisk guide](https://topjohnwu.github.io/Magisk/guides.html#magisk-module-installer)
makes `META-INF` optional for app installation; it is deliberately absent.
Recovery installation is unsupported. OrangeFox is a possible manual recovery
path, not the installer for this module.

## GitHub testing and downloadable results

Every push and PR runs `.github/workflows/ci.yml`; manual execution is available.
It uses standard Ubuntu hosted runners, free tools, read-only repository
permissions and commit-pinned actions. No secrets, signing keys or deployment
tokens are needed. It does not publish releases or install anything.

Required checks: ShellCheck, actionlint, structure/metadata validation,
destructive-command/partition-write scanning, mocked Android diagnostics,
isolated installer acceptance/refusal cases, ZIP reproducibility,
content/permission/CRC validation and SHA-256 verification. Static scanning is
a review aid, not a shell security proof. Tests emulate Magisk's documented
customization contract, not its entire installer, kernel or SELinux context.
POSIX `sh` and BusyBox `ash` are exercised; host BusyBox is not Magisk's Android
BusyBox build or standalone mode.

| GitHub artifact container | Contents |
| --- | --- |
| `AliothGuard-v0.1.0` | `AliothGuard-v0.1.0.zip`, `SHA256SUMS.txt` |
| `AliothGuard-test-reports` | JUnit XML, per-test JSON/text, lint logs, metadata/ZIP validation, build and checksum logs |

ZIP entries use an explicit allowlist, sorted paths, fixed UTC timestamps,
regular-file modes and stored compression to avoid zlib-version differences.
Identical inputs yield identical bytes regardless of checkout timestamps/modes.
`SOURCE_DATE_EPOCH` can intentionally override the default 2024-01-01 timestamp.
Module files are at the ZIP root. Tests, workflows, caches, Git metadata,
compiled code and credentials are excluded.

The optional Android 15 **x86_64** emulator job runs only when selected in a
manual run. It checks Android shell execution without Magisk. It does not test
ARM64 injection, Mi 11X hardware/kernel, OrangeFox, boot safety or attestation.
The same sanitizer regression fixture runs on host utilities, BusyBox and
Android Toybox: all 256 byte values, Android property strings and the 160-character
limit. The emulator also compares reported SDK, release and patch values with
direct `getprop` output; reports and failed commands are included in the job log.
It can fail on image availability independently of the required build. Skipped
or unrun checks are not passes.

## Phone-only management

Follow [PHONE_WORKFLOW.md](docs/PHONE_WORKFLOW.md) for exact Chrome steps to edit
files, create branches/PRs, run Actions and download artifacts. Chrome's
**Desktop site** mode helps. No PC, OTG, paid runner or phone compiler is needed.
Use a public repository for free standard hosted runners; private repositories
have account-dependent quotas. Do not enable paid overages or larger runners.

GitHub downloads an **outer artifact-container ZIP**. Use Android's file manager
to extract it once; the inner `AliothGuard-v0.1.0.zip` is the module. Neither the
outer container nor GitHub's source “Download ZIP” is a module installer.
Artifacts expire after 14 days. Review reports/source first; a matching
checksum proves byte consistency, not device safety.

## Development in cloud/CI

Requirements: Python 3.10+, ShellCheck, BusyBox, actionlint 1.7.7, POSIX shell
and Bash. No SDK/NDK is needed for the stable module. From this repository:

```sh
bash tools/check.sh
# Build after reviewing/passing tests:
sh build.sh
python3 tools/validate.py --zip dist/AliothGuard-v0.1.0.zip
```

Tests use temporary directories and mocked Android commands, never a phone.
Reports go to `reports/` and artifacts to `dist/`, both ignored by Git.
`BUSYBOX` may point to a non-default executable for host tests.

After a separately reviewed installation decision, the normal diagnostic entry
point is the Action button. Advanced users can run
`sh /data/adb/modules/aliothguard/action.sh` in an already-authorized root shell.
Read [privacy notes](docs/PRIVACY.md) before sharing output. No automatic report
collection occurs.

`action.sh` calls `scripts/diagnose.sh`; `common.sh` and `compatibility.sh` contain
read-only helpers. `tools/project.py` defines the release contract. Extend
detection with regression fixtures and preserve uncertainty. Future native work
must use a separate experimental module ID/ZIP and a recoverable test device;
the owner's only phone must not be the first native-hook test platform.
