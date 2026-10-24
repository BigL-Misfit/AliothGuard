# Recovery limits for your only phone

**Do not install an unreviewed build. CI does not prove real-device safety.
This module is not bootloop-proof.** With no PC or OTG some failure modes may
be unrecoverable using your available equipment.

Before any later installation decision, verify that your existing OrangeFox
boots and can mount/access `/data/adb` on your current Android 15 ROM. Recovery
FBE/decryption support varies. This guide cannot make an incompatible recovery
decrypt data. Keep your unlock credential available and back up personal files
using a method already known to work. Do not replace recovery or flash boot
images to try this module.

## If Android boots

Use Magisk → Modules → AliothGuard to disable or remove **AliothGuard only**;
follow Magisk's normal lifecycle prompts. No external data cleanup is needed.
Do not automatically change other modules, DenyList settings, Google app data
or bootloader state.

## If Android cannot start but OrangeFox works

1. Enter your already-installed OrangeFox using your established recovery boot
   procedure. Mi 11X commonly uses Power + Volume Up from power-off; use the
   procedure verified for your installation. Do not flash or format anything.
2. Mount/decrypt Data if supported. Confirm that
   `/data/adb/modules/aliothguard` is actually visible. An inaccessible or empty
   tree does not prove the module is absent.
3. In OrangeFox's file manager create an **empty file**, not a directory, named
   `disable` in `/data/adb/modules/aliothguard`. Or use its terminal:

   ```sh
   test -d /data/adb/modules/aliothguard && touch /data/adb/modules/aliothguard/disable
   ls -l /data/adb/modules/aliothguard/disable
   ```

4. If a staged copy already exists, also put the marker in that existing folder:

   ```sh
   if test -d /data/adb/modules_update/aliothguard; then
     touch /data/adb/modules_update/aliothguard/disable
     ls -l /data/adb/modules_update/aliothguard/disable
   fi
   ```

5. After verifying the marker, reboot through OrangeFox's UI. If Android starts,
   leave AliothGuard disabled while investigating. Magisk versions may handle
   staged updates differently; a marker is not an unconditional recovery
   guarantee. A continued failure may involve the ROM/root manager/other modules.

These are **manual recovery instructions**, not module operations. Affect only
AliothGuard, and do not create guessed directories. If OrangeFox cannot access
`/data/adb`, stop. Do not format Data, wipe user data, flash `boot`, `init_boot`,
`vendor_boot`, `recovery`, `vbmeta` or other partitions, or relock the bootloader.
There is no guaranteed phone-only recovery for inaccessible encrypted data.
Seek device-specific assistance instead of making destructive changes.
