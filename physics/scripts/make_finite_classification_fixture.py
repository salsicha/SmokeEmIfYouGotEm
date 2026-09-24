import argparse
import math
from pathlib import Path
import random
import struct

rng = random.Random(20260924)
special = [0, 0x80000000, 1, 0x80000001, 0x007fffff, 0x00800000,
           0x7f7fffff, 0xff7fffff, 0x7f800000, 0xff800000,
           0x7f800001, 0xff800001, 0x7fc00000, 0xffc00000]
parser = argparse.ArgumentParser(description='Independent FP32 finite-classification GPU fixture')
parser.add_argument('output', type=Path)
out = parser.parse_args().output
with out.open('xb') as f:
    f.write(struct.pack('<III', 0x52534650, 11, 65536))
    for i in range(65536):
        bits = [special[(4*i+j) % len(special)] if i < 64 else rng.getrandbits(32) for j in range(4)]
        flags = [int(math.isfinite(struct.unpack('<f', struct.pack('<I', b))[0])) for b in bits]
        mask = sum(v << j for j, v in enumerate(flags))
        mask |= flags[0] << 4
        mask |= (flags[0] | (flags[1] << 1)) << 5
        mask |= (flags[0] | (flags[1] << 1) | (flags[2] << 2)) << 7
        f.write(struct.pack('<IIIII', *bits, mask))
print(out)
