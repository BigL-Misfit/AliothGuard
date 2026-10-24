// SPDX-License-Identifier: MIT
#include "policy.hpp"
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#define CHECK(x) do { if (!(x)) { fprintf(stderr, "FAIL line %d: %s\n", __LINE__, #x); return 1; } } while (0)
int main() {
    ag::Session s;
    const char good[] = "AG02 builtin 12345678-1234-1234-1234-123456789abc 400\n";
    CHECK(ag::parse_session(good, sizeof(good) - 1, s));
    CHECK(ag::eligible(ag::kPackage, 10123, s, s.boot, 100));
    CHECK(ag::eligible(ag::kPackage, 110123, s, s.boot, 399));
    CHECK(!ag::eligible(ag::kPackage, 10123, s, s.boot, 400));
    CHECK(!ag::eligible(ag::kPackage, 10123, s, s.boot, 99));
    CHECK(!ag::eligible(ag::kPackage, 10123, s, "22345678-1234-1234-1234-123456789abc", 100));
    const char *names[] = {"system_server", "com.google.android.gms", "com.android.vending",
             "io.github.biglmisfit.aliothguard.test:remote", "other.app", ""};
    for (const char *name : names) {
        CHECK(!ag::eligible(name, 10123, s, s.boot, 100));
    }
    const unsigned uids[] = {0u, 1000u, 9999u, 20000u, 99000u, 199000u};
    for (unsigned uid : uids) {
        CHECK(!ag::eligible(ag::kPackage, uid, s, s.boot, 100));
    }
    const char *bad[] = {"", "AG02 builtin", "AG02 both 12345678-1234-1234-1234-123456789abc 400\n",
        "AG02builtin 12345678-1234-1234-1234-123456789abc 400\n",
        "AG02 next 12345678-1234-1234-1234-123456789abc 0400\n",
        "AG02 next 12345678-1234-1234-1234-123456789abc -400\n",
        "AG02 next 12345678-1234-1234-1234-123456789abc 400\nextra",
        "AG02 next 12345678-1234-1234-1234-123456789abz 400\n",
        "AG02 next 12345678-1234-1234-1234-123456789abc 400",
        "AG02 next 12345678-1234-1234-1234-123456789abc 99999999999999999999999\n"};
    for (const char *input : bad) CHECK(!ag::parse_session(input, strlen(input), s));
    CHECK(!ag::parse_session(good, sizeof(good), s));  // Embedded NUL forbidden.
    CHECK(!ag::parse_session(nullptr, 0, s));
    CHECK(ag::valid_app_data_dir(10123, "/data/user/0/io.github.biglmisfit.aliothguard.test"));
    CHECK(ag::valid_app_data_dir(110123, "/data/user_de/1/io.github.biglmisfit.aliothguard.test"));
    CHECK(ag::valid_app_data_dir(10123, "/data/data/io.github.biglmisfit.aliothguard.test"));
    CHECK(!ag::valid_app_data_dir(110123, "/data/user/0/io.github.biglmisfit.aliothguard.test"));
    CHECK(!ag::valid_app_data_dir(10123, "/data/user/0/other.app"));
    CHECK(!ag::valid_app_data_dir(10123, "/data/user/0/io.github.biglmisfit.aliothguard.test/.."));
    CHECK(!ag::valid_app_data_dir(0, "/data/user/0/io.github.biglmisfit.aliothguard.test"));
    CHECK(!ag::valid_app_data_dir(10123, nullptr));
    char next[sizeof(good)];
    const char good_next[] = "AG02 next 12345678-1234-1234-1234-123456789abc 400\n";
    CHECK(ag::parse_session(good_next, sizeof(good_next) - 1, s));
    CHECK(s.provider == ag::Provider::Next);
    // Every one-byte mutation is parsed under ASan/UBSan on the host, and Bionic in CI.
    for (size_t at = 0; at < sizeof(good) - 1; ++at) {
        for (unsigned byte = 0; byte <= 255; ++byte) {
            memcpy(next, good, sizeof(good)); next[at] = static_cast<char>(byte);
            ag::parse_session(next, sizeof(good) - 1, s);
        }
    }
    CHECK(!ag::probe_observed());
    CHECK(!ag::mark_test_process(static_cast<unsigned>(getuid()) + 1));
    CHECK(ag::self_test());
    puts("AGX_POLICY_PASS: scope, providers, boot/expiry, parser mutations, no default probe");
    return 0;
}
