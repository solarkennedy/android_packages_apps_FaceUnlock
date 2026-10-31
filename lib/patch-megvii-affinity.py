#!/usr/bin/env python3
"""Re-apply the pepito affinity patch to a pristine libMegviiUnlock.so.

The Megvii engine pins its detect/liveness threads with sched_setaffinity. The mask
is computed once per session (libMegviiUnlock.so .text 0x1cf58) as

    mask = (LiteConfig.bigCpuCore == 4) ? 0xf0 : 0x0f      // cmp w8,#4 ; cinv w1,w9,ne

i.e. the library assumes cpus 4-7 are the fast cluster. On MSM8937 (pepito) it is the
other way round: cpus 0-3 run at 1.4 GHz, cpus 4-7 at 1.09 GHz. Setting bigCpuCore
through setConfig() does not help because the per-frame path then takes the
complement. Flipping the condition (cinv ne -> cinv eq) puts the work on cpus 0-3:
detect ~90 ms/frame instead of ~103 ms, liveness ~430 ms instead of ~500 ms.

Usage: patch-megvii-affinity.py <pristine.so> <out.so>
Pristine md5: 909ab3a420dc0a991dc0315cef68df4b
"""
import struct, sys
src, dst = sys.argv[1], sys.argv[2]
d = bytearray(open(src, "rb").read())
# file offset of .text+0x1cf58 in this build of the library
OFF = 0x1cf58
before = d[OFF:OFF + 4]
assert before == bytes.fromhex("2101895a"), f"unexpected bytes {before.hex()} at {OFF:#x}"
d[OFF:OFF + 4] = bytes.fromhex("2111895a")  # cinv w1, w9, ne -> cinv w1, w9, eq
open(dst, "wb").write(d)
print("patched")
