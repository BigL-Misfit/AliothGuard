LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_MODULE := aliothguard_experimental
LOCAL_SRC_FILES := module.cpp policy.cpp
LOCAL_C_INCLUDES := $(LOCAL_PATH)/../third_party
LOCAL_LDLIBS := -lstdc++
include $(BUILD_SHARED_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE := ag_test_reader
LOCAL_SRC_FILES := reader.cpp policy.cpp
include $(BUILD_SHARED_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE := ag_policy_test
LOCAL_SRC_FILES := ../../tests/policy_test.cpp policy.cpp
LOCAL_C_INCLUDES := $(LOCAL_PATH)
include $(BUILD_EXECUTABLE)
