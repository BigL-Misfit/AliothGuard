// SPDX-License-Identifier: MIT
// Lifecycle follows the pinned official Zygisk sample. No hooking APIs used.
#include <sys/types.h>
#include <stdint.h>
#include "zygisk.hpp"
#include "policy.hpp"
#include <fcntl.h>
#include <errno.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

namespace {
ssize_t read_regular(int fd, char *buffer, size_t size, bool root_owned) {
    struct stat st {};
    if (fd < 0) return -1;
    bool ok = fstat(fd, &st) == 0 && S_ISREG(st.st_mode)
        && (!root_owned || (st.st_uid == 0 && !(st.st_mode & 0022)));
    const ssize_t length = ok ? read(fd, buffer, size - 1) : -1;
    char extra;
    ok = length > 0 && read(fd, &extra, 1) == 0;
    close(fd);
    if (ok) buffer[length] = '\0';
    return ok ? length : -1;
}

class AliothGuard final : public zygisk::ModuleBase {
 public:
    void onLoad(zygisk::Api *api, JNIEnv *env) override { api_ = api; env_ = env; }
    void preServerSpecialize(zygisk::ServerSpecializeArgs *) override { unload(); }
    void preAppSpecialize(zygisk::AppSpecializeArgs *args) override {
        armed_ = false;
        unload();  // Also unload after the optional post-specialization probe.
        if (!args || !args->nice_name || (args->is_child_zygote && *args->is_child_zygote)) return;
        const char *name = env_->GetStringUTFChars(args->nice_name, nullptr);
        if (!name) { if (env_->ExceptionCheck()) env_->ExceptionClear(); return; }
        const bool target = strcmp(name, ag::kPackage) == 0;
        env_->ReleaseStringUTFChars(args->nice_name, name);
        if (!target) return;
        if (!args->app_data_dir) return;
        const char *data_dir = env_->GetStringUTFChars(args->app_data_dir, nullptr);
        if (!data_dir) { if (env_->ExceptionCheck()) env_->ExceptionClear(); return; }
        uid_ = static_cast<uint32_t>(args->uid);
        const bool own_data = ag::valid_app_data_dir(uid_, data_dir);
        env_->ReleaseStringUTFChars(args->app_data_dir, data_dir);
        if (!own_data) return;
        int module = api_->getModuleDir();
        if (module < 0) return;
        // A rollback marker prevents new probes even before Magisk's next boot.
        struct stat st {};
        bool disabled = fstatat(module, "disable", &st, AT_SYMLINK_NOFOLLOW) == 0 || errno != ENOENT;
        int state = openat(module, "state", O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
        close(module);
        if (state < 0) return;
        int fd = disabled ? -1 : openat(state, "session", O_RDONLY | O_NOFOLLOW | O_CLOEXEC);
        close(state);
        char data[128] = {}, boot[64] = {};
        const ssize_t length = read_regular(fd, data, sizeof(data), true);
        if (length < 0) return;
        ag::Session session;
        if (!ag::parse_session(data, static_cast<size_t>(length), session)) return;
        fd = open("/proc/sys/kernel/random/boot_id", O_RDONLY | O_CLOEXEC);
        if (read_regular(fd, boot, sizeof(boot), false) < 0) return;
        boot[strcspn(boot, "\n")] = '\0';
        struct timespec now {};
        if (clock_gettime(CLOCK_BOOTTIME, &now) != 0) return;
        armed_ = ag::eligible(ag::kPackage, uid_, session, boot, now.tv_sec);
    }
    void postAppSpecialize(const zygisk::AppSpecializeArgs *) override {
        if (armed_) ag::mark_test_process(uid_);
    }
 private:
    void unload() { api_->setOption(zygisk::DLCLOSE_MODULE_LIBRARY); }
    zygisk::Api *api_ = nullptr;
    JNIEnv *env_ = nullptr;
    uint32_t uid_ = 0;
    bool armed_ = false;
};
}  // namespace
REGISTER_ZYGISK_MODULE(AliothGuard)
