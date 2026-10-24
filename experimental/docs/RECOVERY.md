# Experimental-module rollback and recovery

This is not a promise of boot safety. The owner's only Mi 11X, without a PC/OTG,
must not be the first native-injection target. Keep experimental testing on a
separate recoverable device; otherwise stop at CI/emulator validation.

While Android is usable, use this module's WebUI **Disable this experiment** or
`sh /data/adb/modules/aliothguard_experimental/scripts/control.sh rollback`.
This removes only its session and creates its disable marker. It does not
disable stable `aliothguard`, other modules, Zygisk or ROM features. New probe
callbacks refuse the marker immediately; Magisk stops loading the library on a
subsequent boot. An already-running test-app process keeps its marker until exit.
No automatic reboot, application stop or partition operation occurs.

If Android does not boot, use the already-installed OrangeFox recovery's file
manager or terminal, **if it can decrypt and access `/data`**. Create the empty
file `/data/adb/modules/aliothguard_experimental/disable` (for example,
`touch /data/adb/modules/aliothguard_experimental/disable` in recovery's terminal).
Verify the exact module ID: stable diagnostics use `/data/adb/modules/aliothguard`.
Then make your own reboot decision. Do not format `/data` to get access, relock
the bootloader, flash partitions, or indiscriminately remove/disable modules.

If OrangeFox cannot access decrypted data, this file-based rollback is unavailable.
It is not an emergency guarantee. This is why real injection is not appropriate
on the only phone without a recovery fallback. A session expires at most five
minutes after arming and cannot survive a changed boot ID; default installation
contains no session and ships disabled.
