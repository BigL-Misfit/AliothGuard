# Stable diagnostics and future experiments

## Stable contract

`aliothguard` v1 contains only manual shell diagnostics. Keep properties,
on-disk configuration, uncertain runtime state and real verdicts distinct.
Extend known-module signatures with regression fixtures. Never turn an unknown
into “safe”, “hidden” or “integrity passed”. Other modules' scripts are not run.

## Upstream research — checked 2026-10-24

Public Git HEADs and relevant upstream documentation were inspected. Dates show
observed commit activity, not support guarantees, license permission, release
safety or endorsement. These are research references, not installation advice.

| Source | Observed HEAD; commit date | Relevance |
| --- | --- | --- |
| [Magisk](https://github.com/topjohnwu/Magisk), [official guide source](https://github.com/topjohnwu/Magisk/blob/a51dc10f88ea3a8aac7fa02e95ae7589a034730b/docs/guides.md) | `a51dc10f88ea`; 2026-10-22 | Module layout, app-only ZIP, sourced customization, permissions, skip_mount and Action entry point. |
| [Official Zygisk sample](https://github.com/topjohnwu/zygisk-module-sample) | API header inspected this session | Future supported API/lifecycle contract; pin an exact version when implemented. |
| [Play Integrity Fork](https://github.com/osm0sis/PlayIntegrityFork) | `23ec56c2440c`; 2026-10-21 | Maintained configuration docs, PIF prop/JSON and process-scoped behavior; upstream verdict claims are not AliothGuard test results. |
| [ReZygisk](https://github.com/PerformanC/ReZygisk) | `b5aa415c2ce1`; 2026-10-11 | Active independent provider; requires built-in Magisk Zygisk off. Review AGPL-3.0 before any source reuse. |
| [NeoZygisk](https://github.com/JingMatrix/NeoZygisk) | `d161f31c9cfa`; 2026-10-23 | Active provider alternative for compatibility research; no code copied. |
| [Zygisk Next](https://github.com/Dr-TSNG/ZygiskNext) | `cddf38d5b150`; 2026-08-27 | Requires built-in Zygisk off and one root implementation. Do not assume current release source is available or redistribute closed components. |
| [Zygisk Assistant](https://github.com/snake-4/Zygisk-Assistant) | `4c1842f33f25`; 2026-05-04 | MIT source; documents Enforce DenyList off. No hiding implementation copied. |
| [Tricky Store](https://github.com/5ec1cff/TrickyStore) | `55d65f305e04`; 2025-11-30 | README says closed-source since 1.1.0. Only documented config paths are recognized; recent source maintenance is unconfirmed. No redistribution/key material. |

For future integrity work, consult Google's [overview](https://developer.android.com/google/play/integrity/overview),
[verdict definitions](https://developer.android.com/google/play/integrity/verdicts)
and [key attestation documentation](https://developer.android.com/privacy-and-security/security-key-attestation).
Direct access to Google docs and the rendered Magisk docs host was denied in
this environment. Magisk's official Markdown source was read instead. Google's
current page contents were not verified here and must be rechecked before
implementation. GitHub REST API access was also unavailable; archival status
and latest-release metadata were not inferred from it.

Read requirements for the exact installed release. Descriptions can be stale
or forged; an enabled provider directory is not runtime proof. ReZygisk and
Zygisk Next explicitly require built-in Zygisk off. Different hiding modules
have different DenyList requirements. Report overlaps; never disable them.

## Original ARM64 Zygisk plan — not implemented

1. Use a separate branch, module ID (`aliothguard_experimental`), archive and
   explicitly enabled CI. Never make it a stable dependency or silently offer
   it as an update to this diagnostic module.
2. Pin a supported NDK and official Zygisk API/header with its license. Write
   original C++ source beginning with an inert lifecycle probe, not hiding.
   Match provider API/ABI versions. ARM64 does not cover 32-bit processes;
   document exclusions. Do not ship placeholder native binaries.
3. Check API availability, exact process scope and provider capabilities before
   experiments. Use an owner-controlled test-app allowlist; avoid system_server
   and critical system processes. Bound initialization, unload where appropriate,
   avoid global changes and treat unsupported states as refusal/unknown.
4. Use host unit tests, sanitizers/fuzzing and API mocks, then a **separate
   recoverable test device** for injection. Cross-compilation/x86 emulation is
   not Mi 11X safety evidence. A zero hardware budget leaves this gate blocked;
   the only phone must not be the first native-hook test target.
5. Maintain a matrix of exact Magisk/provider/ROM/module versions and observed
   outcomes. Refuse overlapping providers in experiments. Never patch or disable
   another module automatically. Settings changes need a reviewable diff,
   explicit approval and a tested rollback path before writing.

## Root-detection and integrity configuration research

Start with an original test app owned by the user to measure detection signals
and process behavior. A provider adapter should expose capabilities and
uncertainty instead of treating Magisk, KernelSU and APatch as interchangeable.
Keep observation independent of any future interception implementation.

A configuration assistant can first validate owner-supplied syntax/schema
locally and produce proposed changes without applying them. Do not harvest
fingerprints, obtain/distribute keyboxes, read private keys, forge verdicts,
clear app data or automate retries against Google's services. Actual API tests
need a legitimate app/cloud integration and accurate server-side verification.

Hardware trust, boot state, key provenance, revocation and server policy are
outside this module's control. Hiding root does not imply an integrity pass.
There is no claim of universally bypassing Google's hardware integrity checks.
Review licensing/provenance at every dependency update; public availability
does not grant redistribution permission.
