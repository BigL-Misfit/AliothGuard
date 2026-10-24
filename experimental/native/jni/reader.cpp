// SPDX-License-Identifier: MIT
#include <jni.h>
#include "policy.hpp"
extern "C" JNIEXPORT jboolean JNICALL
Java_io_github_biglmisfit_aliothguard_test_MainActivity_nativeSelfTest(JNIEnv *, jclass) {
    return ag::self_test();
}
extern "C" JNIEXPORT jboolean JNICALL
Java_io_github_biglmisfit_aliothguard_test_MainActivity_nativeProbeObserved(JNIEnv *, jclass) {
    return ag::probe_observed();
}
