#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p reports
shellcheck --external-sources --shell=sh action.sh customize.sh scripts/*.sh build.sh tests/*.sh |& tee reports/shellcheck.txt
shellcheck --external-sources tools/check.sh tools/emulator-smoke.sh |& tee -a reports/shellcheck.txt
printf '%s\n' 'PASS: ShellCheck' | tee -a reports/shellcheck.txt
actionlint -color |& tee reports/actionlint.txt
printf '%s\n' 'PASS: actionlint' | tee -a reports/actionlint.txt
python3 tools/validate.py --report reports/validation.json |& tee reports/validation.txt
python3 tests/run.py |& tee reports/tests.txt
./build.sh |& tee reports/build.txt
python3 tools/validate.py --zip dist/AliothGuard-v0.1.0.zip --report reports/package.json
(cd dist && sha256sum --check SHA256SUMS.txt) |& tee reports/checksum.txt
