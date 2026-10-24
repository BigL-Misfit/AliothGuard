# Experimental architecture and remaining gates

The stable module is not imported, replaced or upgraded by this experiment.
Its ZIP allowlist, identity, scripts and diagnostics remain unchanged.

| Layer | Implemented boundary | Remaining evidence |
| --- | --- | --- |
| Provider adapters | Read-only Magisk setting + module inventory; builtin/Next selection; refusal of overlap, uncertainty and pending state | Actual Magisk 30.7 and exact Next version tests; provider identity/runtime cannot be authenticated from labels |
| Configuration | Fixed defaults; explicit 300-second boot-bound session; atomic update; module-only rollback | Dedicated-device interruption, filesystem and SELinux testing |
| Native | Official API v5 header; bounded parser; exact test-process/UID gate; post-specialization marker; unload | Real ARM64 and provider injection; no hiding hooks shipped |
| Test app | Independent JNI reader, policy self-test, limited root signals and separately labelled unrequested integrity state | Process-scope isolation observed on rooted lab device |
| WebUI | Offline assets, strict CSP, constant shell-command allowlist, escaped text rendering, explicit lab acknowledgement | Real compatible Magisk WebUI host testing; not a Magisk built-in feature |
| CI | Stable suite; host ASan/UBSan policy and actual-callback tests with a mock provider/JNI, shell/controller tests, JS bridge tests, NDK cross-build, ELF/ZIP/APK checks, unrooted API35 emulator | Mock callbacks and emulator do not exercise real Zygisk injection or Google attestation |

Next work must remain in separate experiments: (1) measure actual provider
lifecycle behavior on a recoverable ARM64 test device; (2) add one opt-in
process-scoped compatibility mechanism at a time, with an observable A/B test in
our own app and reliable unloading/rollback design; (3) assess overlaps with
AxionOS framework spoofing and hiding modules before any new interceptor.
Never enable two providers or mutate their configuration automatically.

Play Integrity integration is a distinct subsystem. A legitimate test app/cloud
project and server-side token validation are needed before reporting genuine
Google verdicts. Root-detection signal changes cannot be translated into BASIC,
DEVICE or STRONG. No keyboxes, synthetic attestation, key extraction, spoofed
certificate chains or universal hardware-integrity claims belong in this release.
Future configuration tooling should propose reviewable changes instead of
overwriting ROM or third-party configuration. No closed-source Next/Tricky Store
components may be bundled. No future interceptor may target GMS, banks, system
services or arbitrary apps simply by editing this probe's package string.

Only module-owned state is written by the manual controller. Native code writes
no files and changes no system properties, policies, partitions or mounts. There
are no service/post-fs-data scripts, root companions, network requests, background
tasks or automatic boot-time commands. Zygisk still loads a native library when
the user manually enables the module; even an inert library can contain defects.
