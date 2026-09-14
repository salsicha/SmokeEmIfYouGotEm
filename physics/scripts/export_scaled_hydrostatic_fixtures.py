"""Exact rational scaled-polynomial GPU fixtures; no state or gate changes."""
import argparse
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import struct
import numpy as np
from export_exact_hydrostatic_fixtures import polynomial, cases as unscaled_cases
from export_represented_float_fixtures import rounded_bits


def expected(rows):
    values = []
    for depth, bed in ((rows[0], rows[1]), (rows[2], rows[3])):
        h, z = polynomial((*depth[:3], 1), bed)
        base_h, base_z, factor = Q(float(depth[1])), Q(float(bed[1])), Q(float(depth[3]))
        values.append((base_h+factor*(h-base_h), base_z+factor*(z-base_z)))
    (hl, zl), (hr, zr) = values
    a, b = max(Q(0), hl-max(Q(0), zr-zl)), max(Q(0), hr-max(Q(0), zl-zr))
    return [rounded_bits(v) for v in (hl, hr, a, b)]+[int(a>0), int(b>0), 0, 0]


def cases():
    rng = np.random.default_rng(298347)
    factors = (0., 2.**-149, 2.**-126, 2.**-60, .125, .5, .75, 1.)
    for index, (name, rows) in enumerate(unscaled_cases()):
        value = np.asarray(rows, dtype='<f4')
        for slot in (0, 2):
            value[slot, 3] = factors[(index+slot)%len(factors)] if index<160 else \
                np.asarray(rng.integers(0, 0x3f800001, dtype=np.uint32)).view(np.float32).item()
        yield name, value
    # Nearly canceling own/neighbor depth, including exact positive faces that
    # round to zero after multiplication by the smallest representable factor.
    for factor in factors:
        for depth in (2.**-149, 2.**-126, 2.**-40, 1., 2.**100):
            for direction in (-1, 1):
                yield 'scaled_boundary', np.asarray([
                    (depth, 2*depth, 3*depth, factor), (0, 0, 0, direction),
                    (depth, 2*depth, 3*depth, 1-factor), (depth, depth, depth, -direction)], dtype='<f4')


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); manifest = args.output.with_suffix('.json')
    if args.output.exists() or manifest.exists(): raise FileExistsError(args.output)
    records = list(cases()); payload = bytearray(struct.pack('<III', 0x52534650, 9, len(records)))
    for name, rows in records:
        payload.extend(rows.tobytes()); payload.extend(struct.pack('<8I', *expected(rows)))
    with args.output.open('xb') as out: out.write(payload)
    report = dict(scope=__doc__, count=len(records), fixture_sha256=hashlib.sha256(payload).hexdigest(),
        scene_accepted=False, implementation_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('export_scaled_hydrostatic_fixtures.py', 'export_exact_hydrostatic_fixtures.py', 'export_represented_float_fixtures.py')})
    with manifest.open('x') as out: json.dump(report, out, indent=2)
    print(json.dumps(report, indent=2))


if __name__=='__main__': main()
