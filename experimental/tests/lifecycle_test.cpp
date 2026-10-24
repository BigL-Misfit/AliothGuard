// SPDX-License-Identifier: MIT
// Execute actual module callbacks against a fake public-API provider and JNI.
// This is NOT real injection or a substitute for dedicated-device validation.
#include <sys/types.h>
#include <stdint.h>
#include "zygisk.hpp"
#include "policy.hpp"
#include <stdio.h>
#include <stdlib.h>
#define CHECK(x) do { if (!(x)) { fprintf(stderr, "FAIL line %d: %s\n", __LINE__, #x); return 1; } } while (0)

static zygisk::internal::module_abi *module = nullptr;
static int unloads = 0, module_reads = 0, jni_reads = 0, clears = 0;
static bool jni_failure = false;
static bool register_module(zygisk::internal::api_table *, zygisk::internal::module_abi *value) {
    module = value; return value->api_version == 5;
}
static void option(void *, zygisk::Option value) {
    if (value != zygisk::DLCLOSE_MODULE_LIBRARY) abort();
    ++unloads;
}
static int module_dir(void *) { ++module_reads; return -1; }
static const char *get_string(JNIEnv *, jstring text, jboolean *) {
    ++jni_reads; return jni_failure ? nullptr : reinterpret_cast<const char *>(text);
}
static void release_string(JNIEnv *, jstring, const char *) {}
static jboolean exception_check(JNIEnv *) { return jni_failure; }
static void exception_clear(JNIEnv *) { ++clears; }

int main() {
    JNINativeInterface_ functions {};
    functions.GetStringUTFChars = get_string;
    functions.ReleaseStringUTFChars = release_string;
    functions.ExceptionCheck = exception_check;
    functions.ExceptionClear = exception_clear;
    JNIEnv env {&functions};
    zygisk::internal::api_table api {};
    api.registerModule = register_module;
    api.setOption = option;
    api.getModuleDir = module_dir;
    zygisk_module_entry(&api, &env);
    CHECK(module && module->api_version == 5);
    module->preServerSpecialize(module->impl, nullptr);
    module->postServerSpecialize(module->impl, nullptr);
    CHECK(unloads == 1 && module_reads == 0 && jni_reads == 0);
    module->preAppSpecialize(module->impl, nullptr);
    CHECK(unloads == 2 && module_reads == 0);
    jint uid = 10123, gid = 10123, flags = 0, mount = 0;
    jintArray gids = nullptr; jobjectArray limits = nullptr;
    jstring se = nullptr, name = nullptr, instruction = nullptr, data = nullptr;
    jboolean child = false;
    zygisk::AppSpecializeArgs args {uid, gid, gids, flags, limits, mount, se, name,
        instruction, data, nullptr, &child, nullptr, nullptr, nullptr, nullptr, nullptr, nullptr};
    const char *processes[] = {"com.google.android.gms", "com.android.vending", "system_server",
        "other.app", "io.github.biglmisfit.aliothguard.test:remote"};
    for (const char *process : processes) {
        name = reinterpret_cast<jstring>(const_cast<char *>(process));
        module->preAppSpecialize(module->impl, &args);
        module->postAppSpecialize(module->impl, &args);
        CHECK(module_reads == 0 && !ag::probe_observed());
    }
    name = reinterpret_cast<jstring>(const_cast<char *>(ag::kPackage));
    child = true;
    module->preAppSpecialize(module->impl, &args);
    CHECK(module_reads == 0);
    child = false; jni_failure = true;
    module->preAppSpecialize(module->impl, &args);
    CHECK(clears == 1 && module_reads == 0);
    jni_failure = false;
    data = reinterpret_cast<jstring>(const_cast<char *>("/data/user/0/other.app"));
    module->preAppSpecialize(module->impl, &args);
    CHECK(module_reads == 0);  // Matching process name alone is insufficient.
    data = reinterpret_cast<jstring>(const_cast<char *>("/data/user/0/io.github.biglmisfit.aliothguard.test"));
    module->preAppSpecialize(module->impl, &args);
    module->postAppSpecialize(module->impl, &args);
    CHECK(module_reads == 1 && !ag::probe_observed());  // Missing module FD fails closed.
    CHECK(unloads == 11);
    puts("AGX_LIFECYCLE_PASS: official API registration, unload, non-target/child exclusion, JNI failure, missing module FD");
    return 0;
}
