"""Stable diagnostic-release contract shared by builder and validators."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.0"
ARCHIVE = f"AliothGuard-v{VERSION}.zip"
EPOCH = 1704067200  # 2024-01-01 UTC; independent of checkout times and Git history.
FILES = {
    "LICENSE": 0o644,
    "README.md": 0o644,
    "action.sh": 0o755,
    "config/diagnostics.conf": 0o644,
    "customize.sh": 0o755,
    "docs/PRIVACY.md": 0o644,
    "docs/RECOVERY.md": 0o644,
    "module.prop": 0o644,
    "scripts/common.sh": 0o644,
    "scripts/compatibility.sh": 0o644,
    "scripts/diagnose.sh": 0o755,
    "skip_mount": 0o644,
}
FORBIDDEN = {
    "post-fs-data.sh", "service.sh", "boot-completed.sh", "uninstall.sh",
    "system.prop", "sepolicy.rule", "system", "vendor", "product",
    "system_ext", "zygisk", "META-INF", ".replace", "install.sh",
}


def metadata(data: bytes) -> dict[str, str]:
    text = data.decode("utf-8")
    if "\r" in text or not text.endswith("\n"):
        raise ValueError("module.prop must use LF and end in a newline")
    result = {}
    for line in text.splitlines():
        key, sep, value = line.partition("=")
        if not sep or not value or key in result:
            raise ValueError("invalid or duplicate metadata field")
        result[key] = value
    required = {"id", "name", "version", "versionCode", "author", "description"}
    if set(result) != required:
        raise ValueError("unexpected or missing metadata fields")
    if result["id"] != "aliothguard" or result["version"] != f"v{VERSION}":
        raise ValueError("module identity/version does not match release contract")
    if result["versionCode"] != "100":
        raise ValueError("unexpected versionCode")
    return result
