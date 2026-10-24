// SPDX-License-Identifier: MIT
#include "policy.hpp"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

namespace ag {
bool parse_session(const char *data, size_t size, Session &out) {
    out = {};
    if (!data || size == 0 || size >= 128 || memchr(data, '\0', size)) return false;
    char buffer[128] = {}, provider[16] = {}, boot[37] = {}, expiry[16] = {};
    memcpy(buffer, data, size);
    int end = 0;
    if (sscanf(buffer, "AG02 %15s %36s %15s%n", provider, boot, expiry, &end) != 3
        || static_cast<size_t>(end + 1) != size || buffer[end] != '\n') return false;
    Provider selected = Provider::None;
    if (strcmp(provider, "builtin") == 0) selected = Provider::Builtin;
    if (strcmp(provider, "next") == 0) selected = Provider::Next;
    if (selected == Provider::None || strlen(boot) != 36) return false;
    for (size_t i = 0; i < 36; ++i) {
        const bool dash = i == 8 || i == 13 || i == 18 || i == 23;
        if (dash ? boot[i] != '-' : !((boot[i] >= '0' && boot[i] <= '9')
            || (boot[i] >= 'a' && boot[i] <= 'f'))) return false;
    }
    uint64_t until = 0;
    for (size_t i = 0; expiry[i]; ++i) {
        if (expiry[i] < '0' || expiry[i] > '9') return false;
        until = until * 10 + static_cast<unsigned>(expiry[i] - '0');
    }
    if (!until) return false;
    char canonical[128];
    const int canonical_size = snprintf(canonical, sizeof(canonical), "AG02 %s %s %llu\n",
        provider, boot, static_cast<unsigned long long>(until));
    if (canonical_size < 0 || static_cast<size_t>(canonical_size) != size
        || memcmp(buffer, canonical, size) != 0) return false;
    out.provider = selected;
    memcpy(out.boot, boot, sizeof(boot));
    out.expires = until;
    return true;
}

bool valid_app_data_dir(uint32_t uid, const char *path) {
    if (!path || uid % 100000 < 10000 || uid % 100000 > 19999) return false;
    char expected[128];
    const char *roots[] = {"/data/user", "/data/user_de"};
    for (const char *root : roots) {
        snprintf(expected, sizeof(expected), "%s/%u/%s", root, uid / 100000, kPackage);
        if (strcmp(path, expected) == 0) return true;
    }
    snprintf(expected, sizeof(expected), "/data/data/%s", kPackage);
    return uid / 100000 == 0 && strcmp(path, expected) == 0;
}

bool eligible(const char *process, uint32_t uid, const Session &s,
              const char *boot, uint64_t now) {
    const uint32_t app_id = uid % 100000;
    return process && boot && strcmp(process, kPackage) == 0
        && app_id >= 10000 && app_id <= 19999
        && s.provider != Provider::None && strcmp(s.boot, boot) == 0
        && s.expires > now && s.expires - now <= kSessionSeconds;
}

static void marker(char *buffer, size_t size, uint32_t uid) {
    snprintf(buffer, size, "v0.2.0:%ld:%u", static_cast<long>(getpid()), uid);
}

bool mark_test_process(uint32_t expected_uid) {
    if (getuid() != expected_uid || expected_uid % 100000 < 10000
        || expected_uid % 100000 > 19999) return false;
    char value[64];
    marker(value, sizeof(value), expected_uid);
    // Process-local marker only: no Java/system properties, files or hooks.
    return setenv(kProbe, value, 1) == 0;
}

bool probe_observed() {
    char value[64];
    marker(value, sizeof(value), getuid());
    const char *observed = getenv(kProbe);
    return observed && strcmp(value, observed) == 0;
}

bool self_test() {
    Session s;
    const char input[] = "AG02 builtin 12345678-1234-1234-1234-123456789abc 400\n";
    return parse_session(input, sizeof(input) - 1, s)
        && eligible(kPackage, 10123, s, s.boot, 100)
        && !eligible("system_server", 1000, s, s.boot, 100)
        && !eligible("com.google.android.gms", 10123, s, s.boot, 100)
        && !eligible(kPackage, 10123, s, s.boot, 400);
}
}  // namespace ag
