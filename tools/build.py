#!/usr/bin/env python3
"""Build a byte-reproducible Magisk-app ZIP using only Python's stdlib."""
import argparse
import datetime
import hashlib
import os
import stat
import zipfile
from pathlib import Path

from project import ARCHIVE, EPOCH, FILES, ROOT
from validate import validate_tree, validate_zip


def build(output: Path) -> Path:
    validate_tree()
    epoch = int(os.environ.get("SOURCE_DATE_EPOCH", str(EPOCH)))
    timestamp = datetime.datetime.fromtimestamp(epoch, datetime.timezone.utc)
    if not 1980 <= timestamp.year <= 2107:
        raise ValueError("SOURCE_DATE_EPOCH is outside the ZIP date range")
    date = timestamp.timetuple()[:5] + (timestamp.second // 2 * 2,)
    output.mkdir(parents=True, exist_ok=True)
    target = output / ARCHIVE
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, mode in sorted(FILES.items()):
            entry = zipfile.ZipInfo(name, date_time=date)
            entry.create_system = 3
            entry.external_attr = (stat.S_IFREG | mode) << 16
            entry.compress_type = zipfile.ZIP_STORED
            archive.writestr(entry, (ROOT / name).read_bytes())
    validate_zip(target)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    (output / "SHA256SUMS.txt").write_text(f"{digest}  {ARCHIVE}\n", encoding="ascii")
    print(f"Built and validated {target}\nSHA-256: {digest}")
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    build(parser.parse_args().output)
