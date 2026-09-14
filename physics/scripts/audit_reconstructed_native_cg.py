"""Check actual native GPU/CPU solves against the original factored operator.

No evolved/native geometry, production cost or scene acceptance. Re-captures
the same original actual nonlinear RHS and checks fixture identity before using
the immutable factored operator for true and depth-weighted residuals.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import numpy as np
import total_depth_bank_replay as bank
from audit_reconstructed_polynomial_sweep import source_fields, capture_systems
from reconstructed_pressure_adapter import reconstructed_pressure
from reconstructed_damped_polynomial_reference import DampedPolynomialSystem
from export_reconstructed_polynomial_fixture import encode_case


def read_native(data):
    if len(data) < 12 or struct.unpack_from('<III', data) != (0x52534347, 1, 6):
        raise ValueError('Complete six-case native CG output required')
    offset, cases = 12, []
    for tag in range(6):
        if offset+32 > len(data): raise ValueError('Truncated native case header')
        actual_tag, n, failures, iterations, active, zero, milliseconds = struct.unpack_from('<IIIIIId', data, offset)
        offset += 32
        if (actual_tag != tag or not 1 <= n <= 524288 or iterations > 40 or active > 1 or zero > 1
                or not np.isfinite(milliseconds) or (milliseconds < 0 and milliseconds != -1)
                or offset+16*n > len(data)):
            raise ValueError('Invalid native case; no silent input repair')
        gpu = np.frombuffer(data, dtype='<f8', count=n, offset=offset); offset += 8*n
        cpu = np.frombuffer(data, dtype='<f8', count=n, offset=offset); offset += 8*n
        if not np.isfinite(gpu).all() or not np.isfinite(cpu).all(): raise ValueError('Nonfinite native solution')
        cases.append(dict(tag=tag, n=n, failures=failures, iterations=iterations, active=active,
            zero_rhs=zero, gpu_single_shared_load_ms=milliseconds, gpu=gpu, cpu=cpu))
    if offset != len(data): raise ValueError('Trailing native data')
    return cases


def compare(system, rhs, native):
    candidate = DampedPolynomialSystem(system, 1)
    reference, stats = candidate.solve(rhs)
    initial_peak = float(abs(rhs).max()) or 1.
    normalized_rhs = rhs/initial_peak
    root = np.sqrt(system.h); root /= float(root.max()) or 1.
    outputs = {}
    for backend in ('gpu', 'cpu'):
        value = native[backend].reshape(rhs.shape)
        residual = system.apply(value)/initial_peak-normalized_rhs
        relative = float(np.linalg.norm(residual)/np.linalg.norm(normalized_rhs))
        physical_error = root[..., None]*residual
        physical_rhs = root[..., None]*normalized_rhs
        physical_scale = max(float(abs(physical_error).max()), float(abs(physical_rhs).max())) or 1.
        physical = float(np.linalg.norm(physical_error/physical_scale)
            /(np.linalg.norm(physical_rhs/physical_scale) or 1.))
        reference_scale = float(abs(reference).max()) or 1.
        difference = float(np.linalg.norm(value/reference_scale-reference/reference_scale)
            /(np.linalg.norm(reference/reference_scale) or 1.))
        outputs[backend] = dict(original_factored_true_relative_residual=relative,
            original_depth_weighted_relative_residual=physical,
            relative_solution_difference_from_original_operator_cg=difference,
            unchanged_residual_gate_passed=bool(relative < 2e-5 and physical < 2e-5),
            reference_parity_passed=bool(difference < 1e-9))
    return dict(reference_stats=stats, backends=outputs, passed=bool(native['failures'] == 0
        and native['iterations'] <= 40 and stats['relative_residual'] < 2e-5
        and all(v['unchanged_residual_gate_passed'] and v['reference_parity_passed'] for v in outputs.values())))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--fixture-manifest', type=Path, required=True)
    parser.add_argument('--native-output', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists(): raise FileExistsError(args.report)
    raw = args.native_output.read_bytes(); native = read_native(raw)
    manifest_raw = args.fixture_manifest.read_bytes(); manifest = json.loads(manifest_raw)
    if manifest.get('schema') != 'raftsim.reconstructed_polynomial_native_fixture.v1':
        raise ValueError('Original fixture manifest required')
    binary = Path(manifest['binary_path'])
    if hashlib.sha256(binary.read_bytes()).hexdigest() != manifest['binary_sha256']:
        raise ValueError('Original native fixture changed')
    paths = sorted(Path(__file__).parent.glob('*.py'))
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    results = []
    for source_index, case in enumerate(('solitary', 'wet_2d', 'captured')):
        state, bed, dx, kwargs, metadata = source_fields(case, args.input if case == 'captured' else None)
        source = manifest['sources'][source_index]
        if (hashlib.sha256(state.tobytes()).hexdigest() != source['state_sha256']
                or hashlib.sha256(bed.tobytes()).hexdigest() != source['bed_sha256'] or source['case'] != case
                or metadata != source['metadata']):
            raise ValueError('Original state/bed fixture mismatch')
        state.flags.writeable = bed.flags.writeable = False
        records = []
        with capture_systems(records), reconstructed_pressure():
            bank.rate(state, bed, dx, second_order=True, **kwargs, dispersive=True,
                pressure_model='rational_sgn', pressure_interpolation='depth_weighted',
                pressure_formulation='kinematic', pressure_bed_slope='geometry', shoreline_limiter='unscaled')
        if len(records) != 2: raise ValueError('Missing original pole')
        for pole, (system, rhs, _, _, _) in enumerate(records):
            tag = source_index*2+pole
            payload, info = encode_case(system, rhs, tag)
            if info['binary_sha256'] != manifest['cases'][tag]['binary_sha256'] or native[tag]['n'] != rhs.size:
                raise ValueError('Original operator/RHS fixture mismatch')
            result = compare(system, rhs, native[tag])
            result.update(tag=tag, source_case=case, length=system.length, unknowns=rhs.size,
                native_diagnostics={k: v for k, v in native[tag].items() if k not in ('gpu', 'cpu')})
            results.append(result); print(json.dumps(result, allow_nan=False), flush=True)
        if (hashlib.sha256(state.tobytes()).hexdigest() != source['state_sha256']
                or hashlib.sha256(bed.tobytes()).hexdigest() != source['bed_sha256']):
            raise ValueError('Original input changed during native verification')
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest() != h for p, h in hashes.items()):
        raise RuntimeError('Implementation changed during native audit')
    result = dict(schema='raftsim.reconstructed_native_cg_audit.v1', scope=__doc__,
        native_output_sha256=hashlib.sha256(raw).hexdigest(),
        fixture_manifest_sha256=hashlib.sha256(manifest_raw).hexdigest(),
        fixture_binary_sha256=manifest['binary_sha256'], implementation_hashes=hashes,
        cases=results, passed=all(c['passed'] for c in results),
        native_geometry_qualified=False, history_qualified=False, native_cost_qualified=False, scene_accepted=False)
    encoded = json.dumps(result, indent=2, allow_nan=False)
    with args.report.open('x') as out: out.write(encoded)
    if not result['passed']: raise SystemExit(1)


if __name__ == '__main__': main()
