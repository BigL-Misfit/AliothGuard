#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
set -euo pipefail
cd "$(dirname "$0")/../.."
mkdir -p reports/experimental dist/experimental
shellcheck --external-sources --shell=sh experimental/module/*.sh experimental/module/scripts/*.sh |& tee reports/experimental/shellcheck.txt
shellcheck experimental/tools/*.sh |& tee -a reports/experimental/shellcheck.txt
actionlint |& tee reports/experimental/actionlint.txt
python3 -m unittest discover -s experimental/tests -p 'test_*.py' -v |& tee reports/experimental/tests.txt
node experimental/tests/webui_test.mjs |& tee reports/experimental/webui.txt
g++ -std=c++17 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer \
  -Iexperimental/native/jni experimental/native/jni/policy.cpp experimental/tests/policy_test.cpp \
  -o dist/experimental/policy-host
dist/experimental/policy-host |& tee reports/experimental/native-host.txt
g++ -std=c++17 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer \
  -Iexperimental/native/jni -Iexperimental/native/third_party -I"$JAVA_HOME/include" -I"$JAVA_HOME/include/linux" \
  experimental/native/jni/module.cpp experimental/native/jni/policy.cpp experimental/tests/lifecycle_test.cpp \
  -o dist/experimental/lifecycle-host
dist/experimental/lifecycle-host |& tee -a reports/experimental/native-host.txt
python3 experimental/tools/build.py |& tee reports/experimental/build.txt
python3 experimental/tools/validate.py |& tee reports/experimental/validation.txt
(cd dist/experimental && sha256sum --check SHA256SUMS.txt) |& tee reports/experimental/checksums.txt
