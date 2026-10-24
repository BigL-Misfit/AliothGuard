#!/system/bin/sh
# SPDX-License-Identifier: MIT
MODDIR=${0%/*}
exec sh "$MODDIR/scripts/diagnose.sh"
