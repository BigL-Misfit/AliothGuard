# Diagnostic data and configuration

AliothGuard prints to Magisk's console without saving or transmitting a report.
Magisk/the UI may retain console logs independently. Do not assume screenshots
or shared logs are private.

The report contains selected device/API/ABI/security-patch/boot-state
properties, UID, Magisk version, two boolean settings, module IDs/versions and
state flags, configuration-path presence and a small ROM-hint allowlist.
Properties and metadata are capped at 160 printable characters; metadata input
is capped at 16 KiB. Symlinked module directories and metadata files are skipped.
Directory IDs are observations, not authenticated module identities.

No IMEI, serial, Android ID, account name, build fingerprint, private key,
keybox content, PIF configuration contents, app target list or attestation token
is read. Inspect/redact module names and ROM information before public sharing.
No other module's scripts are sourced or executed.

`config/diagnostics.conf` disables module, integrity-file and ROM-hint scans
independently. Disabled scans are skipped/unknown, not compatible/passed.
Unsupported lines are never evaluated as shell code. Configuration controls
observation only and never changes another module.

`AG_TEST_MODE` / `AG_TEST_ROOT` redirect the data root only in the isolated host
tests. Do not set them for a real report: fixtures are not evidence about your
phone. Production observations use `/data/adb`.
