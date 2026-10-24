APP_ABI := arm64-v8a x86_64
APP_PLATFORM := android-26
APP_STL := none
APP_CPPFLAGS := -std=c++17 -fno-exceptions -fno-rtti -fvisibility=hidden -fvisibility-inlines-hidden -Wall -Wextra -Werror
APP_LDFLAGS := -Wl,-z,relro,-z,now,-z,noexecstack -Wl,--build-id=none -Wl,-z,max-page-size=16384
APP_OPTIM := release
