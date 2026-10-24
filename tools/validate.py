#!/usr/bin/env python3
"""Conservative release gates; a static scan is not proof of device safety."""
import argparse
import json
import re
import shlex
import stat
import zipfile
from pathlib import Path

from project import FILES, FORBIDDEN, ROOT, metadata

DANGEROUS = {
    "dd", "fastboot", "flash_image", "flash_erase", "nandwrite", "reboot",
    "mkfs", "mke2fs", "wipefs", "blkdiscard", "fstrim", "parted", "sgdisk",
    "sfdisk", "fdisk", "blockdev", "format", "setprop", "resetprop",
    "magiskpolicy", "setenforce", "mount", "umount", "rm", "mv", "cp",
    "touch", "tee", "mkdir", "chmod", "chown", "chcon", "restorecon",
    "curl", "wget", "nc", "netcat", "eval", "su", "truncate", "shred",
}


def scan_shell(name: str, text: str) -> None:
    for number, line in enumerate(text.splitlines(), 1):
        lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        words = list(lexer)
        for word in words:
            command = word.rstrip(";").split("/")[-1]
            if command in DANGEROUS or command.startswith("mkfs."):
                raise ValueError(f"{name}:{number}: forbidden diagnostic token {command}")
        code = line.split("#", 1)[0]
        if re.search(r"/dev/(block|mmcblk|sd[a-z]|nvme)|/by-name/", code):
            raise ValueError(f"{name}:{number}: partition path")
        # Only discard stderr/stdout or forward to stderr. No file writes.
        code = re.sub(r"[12]?>/dev/null|[12]?>&[12]", "", code)
        if ">" in code:
            raise ValueError(f"{name}:{number}: unexpected output redirection")
        if "--sqlite" in code and '"SELECT key,value FROM settings WHERE key IN (\'zygisk\',\'denylist\');"' not in code:
            raise ValueError(f"{name}:{number}: unapproved Magisk database operation")
        if "set_perm" in code and name != "customize.sh":
            raise ValueError(f"{name}:{number}: permissions outside installer")


def validate_tree(root: Path = ROOT) -> dict:
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if relative.parts[0] in {".git", "dist", "reports", "__pycache__"}:
            continue
        if path.name in FORBIDDEN:
            raise ValueError(f"forbidden v1 payload: {relative}")
    for name in FILES:
        path = root / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"missing/nonregular package file: {name}")
        for parent in path.parents:
            if parent == root:
                break
            if parent.is_symlink():
                raise ValueError(f"linked package parent: {name}")
        data = path.read_bytes()
        if b"\r" in data or b"\x00" in data:
            raise ValueError(f"invalid text/line endings: {name}")
        if name.endswith(".sh"):
            if not data.startswith(b"#!/system/bin/sh\n"):
                raise ValueError(f"invalid Android shebang: {name}")
            scan_shell(name, data.decode("utf-8"))
    metadata((root / "module.prop").read_bytes())
    if (root / "skip_mount").read_bytes():
        raise ValueError("skip_mount must be an empty marker")
    return {"status": "passed", "package_files": len(FILES), "scope": "static gates, not device safety"}


def validate_zip(path: Path, root: Path = ROOT) -> dict:
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if names != sorted(FILES) or len(names) != len(set(names)):
            raise ValueError("ZIP entries must exactly match the ordered release allowlist")
        if archive.comment or archive.testzip() is not None:
            raise ValueError("ZIP comment or CRC failure")
        dates = set()
        for entry in entries:
            mode = entry.external_attr >> 16
            if not stat.S_ISREG(mode) or stat.S_IMODE(mode) != FILES[entry.filename]:
                raise ValueError(f"incorrect ZIP permissions/type: {entry.filename}")
            if entry.create_system != 3 or entry.extra or entry.comment or entry.flag_bits & 1:
                raise ValueError("unexpected ZIP metadata/encryption")
            if entry.compress_type != zipfile.ZIP_STORED:
                raise ValueError("ZIP must use deterministic stored entries")
            if archive.read(entry) != (root / entry.filename).read_bytes():
                raise ValueError(f"ZIP/source content mismatch: {entry.filename}")
            dates.add(entry.date_time)
        if len(dates) != 1:
            raise ValueError("inconsistent ZIP timestamps")
        metadata(archive.read("module.prop"))
    return {"status": "passed", "archive": path.name, "entries": len(entries), "permissions": "verified"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = {"tree": validate_tree()}
    if args.zip:
        result["zip"] = validate_zip(args.zip)
    output = json.dumps(result, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output)
    print(output, end="")


if __name__ == "__main__":
    main()
