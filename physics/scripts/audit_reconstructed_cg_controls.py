"""Exact synthetic GPU/CPU range controls; never source-physics acceptance."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

COUNTS = (1536, 1536, 768, 768, 32768, 32768)
EXPONENTS = (-1074, -1022, -600, 0, 600, 1000)


def audit(data, control):
    if control not in ('zero-rhs', 'identity-range'):
        raise ValueError('Unknown explicit synthetic control')
    if len(data) < 12 or struct.unpack_from('<III', data) != (0x52534343, 1, 6):
        raise ValueError('Separate synthetic-control magic required')
    offset, results = 12, []
    for tag, count in enumerate(COUNTS):
        if offset + 32 > len(data):
            raise ValueError('Truncated control header')
        actual, n, failures, iterations, active, zero, timing = struct.unpack_from('<IIIIIId', data, offset)
        offset += 32
        is_zero = control == 'zero-rhs'
        if (actual != tag or n != count or failures != 0 or iterations != (0 if is_zero else 1)
                or active != 0 or zero != int(is_zero) or not math.isfinite(timing) or timing < 0):
            raise ValueError(f'Control {tag} diagnostics/shape/timing mismatch')
        value = 0. if is_zero else math.ldexp(1., EXPONENTS[tag])
        expected = b''.join(struct.pack('<d', value if i % 3 == 0 else (-value if i % 3 == 1 and not is_zero else 0.))
                            for i in range(n))
        for backend in ('gpu', 'cpu'):
            actual_bytes = data[offset:offset + 8*n]
            offset += 8*n
            if actual_bytes != expected:
                raise ValueError(f'Control {tag} {backend} solution bits mismatch, including tiny rows and zero signs')
        results.append(dict(tag=tag, unknowns=n, exponent=None if is_zero else EXPONENTS[tag],
                            expected_iterations=iterations, gpu_cpu_exact_expected_bits=True))
    if offset != len(data):
        raise ValueError('Trailing control bytes')
    return dict(schema='raftsim.synthetic_native_cg_controls.v1', control=control,
                native_sha256=hashlib.sha256(data).hexdigest(), cases=results, passed=True,
                actual_source_or_physical_history_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control', required=True, choices=('zero-rhs', 'identity-range'))
    parser.add_argument('--native-output', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    result = audit(args.native_output.read_bytes(), args.control)
    result['native_output'] = str(args.native_output)
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(result, allow_nan=False))


if __name__ == '__main__':
    main()
