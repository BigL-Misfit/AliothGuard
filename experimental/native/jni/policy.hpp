// SPDX-License-Identifier: MIT
#pragma once
#include <stddef.h>
#include <stdint.h>

namespace ag {
constexpr const char *kPackage = "io.github.biglmisfit.aliothguard.test";
constexpr const char *kProbe = "ALIOTHGUARD_TEST_PROBE";
constexpr uint64_t kSessionSeconds = 300;
enum class Provider { None, Builtin, Next };
struct Session {
    Provider provider = Provider::None;
    char boot[37] = {};
    uint64_t expires = 0;
};
bool parse_session(const char *data, size_t size, Session &out);
bool valid_app_data_dir(uint32_t uid, const char *path);
bool eligible(const char *process, uint32_t uid, const Session &session,
              const char *boot, uint64_t now);
bool mark_test_process(uint32_t expected_uid);
bool probe_observed();
bool self_test();
}  // namespace ag
