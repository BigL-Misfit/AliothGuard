# Zygisk API provenance

`zygisk.hpp` is the **unmodified official API v5 header** from
[topjohnwu/zygisk-module-sample](https://github.com/topjohnwu/zygisk-module-sample/blob/8ce26128f81baaed0b969aaf7f52f886b61af4ab/module/jni/zygisk.hpp),
commit `8ce26128f81baaed0b969aaf7f52f886b61af4ab` (2026-08-04).
SHA-256: `f8d55e8b4f89d418c5941afe62ce6a09ddec1f4afd9a1b0a01eb40a93310dd28`.
The complete 0BSD copyright and permission notice is preserved in the header;
upstream's README explicitly licenses the sample repository under 0BSD.

Our original module follows the documented onLoad/pre/post specialization and
DLCLOSE lifecycle. It uses no companion, hook, namespace-unmount or provider
extension APIs. API v5 requires Magisk 27000 upstream; this experiment requires
Magisk 30700+ and still needs actual provider/device testing. A current separately
installed Zygisk Next must implement the public API. No Next code, binaries or
Tricky Store code/key material are included.

Build: official Android NDK r27c (`27.2.12479018`), C++17, `APP_STL=none`,
no exceptions/RTTI, system `libstdc++` only for the sample API's allocation.
ARM64 is the only module ABI shipped. x86_64 is compiled for CI and the lab APK.
The lab APK's JNI reader is separate from the Zygisk library; it only reads a
process-local marker and runs the policy self-test. It never injects itself.

## Upstream 0BSD notice

Copyright 2022-2023 John "topjohnwu" Wu

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.
