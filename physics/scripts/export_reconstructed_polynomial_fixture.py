"""Export unchanged actual-RHS FP64 sparse-action/preconditioner fixtures.

This qualifies neither a GPU solve nor an evolved scene. The original factored
operator supplies the expected fine action; no manufactured A*x right hand side
replaces the actual nonlinear forcing. Binary doubles preserve small coefficients
that an FP32 upload would discard. No production adapter is modified.
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
from diagnose_reconstructed_pressure_convergence import assembled_matrix


MAGIC = 0x52535044


def range_record(value):
    value = np.asarray(value)
    if not np.isfinite(value).all(): raise ValueError('Nonfinite fixture')
    positive = np.abs(value[value != 0])
    with np.errstate(over='ignore', under='ignore'):
        narrow = value.astype(np.float32)
    return dict(nonzero=int(positive.size), minimum_nonzero=float(positive.min()) if positive.size else 0.,
        maximum=float(positive.max()) if positive.size else 0.,
        fp32_lost_nonzero=int(np.count_nonzero((value != 0) & (narrow == 0))),
        fp32_nonfinite=int(np.count_nonzero(~np.isfinite(narrow))))


def encode_case(system, rhs, tag):
    wrapper = DampedPolynomialSystem(system, 1)
    matrix = assembled_matrix(system).tocsr(); matrix.sort_indices()
    scaled = wrapper.scaled.copy(); scaled.sort_indices()
    if not (np.array_equal(matrix.indptr, scaled.indptr) and np.array_equal(matrix.indices, scaled.indices)):
        raise ValueError('Scaling changed sparse support; no coefficient dropping allowed')
    n = rhs.size; rhs = rhs.ravel()
    expected_action = system.apply(rhs.reshape((*system.h.shape, 2))).ravel()
    expected_precondition = wrapper.precondition(rhs.reshape((*system.h.shape, 2))).ravel()
    # Componentwise scales retain tiny rows and cancellation. These describe
    # arithmetic verification, not a change to the 2e-5 physical residual gate.
    action_scale = np.asarray(abs(matrix)@abs(rhs))
    normalized = rhs*wrapper.inverse_root
    precondition_scale = wrapper.omega*wrapper.inverse_root*(2*abs(normalized)
        +wrapper.omega*(abs(scaled)@abs(normalized)))
    arrays = [('row_offsets', matrix.indptr, '<u4'), ('columns', matrix.indices, '<u4'),
        ('matrix', matrix.data, '<f8'), ('scaled', scaled.data, '<f8'),
        ('inverse_root', wrapper.inverse_root, '<f8'), ('rhs', rhs, '<f8'),
        ('expected_action', expected_action, '<f8'), ('expected_precondition', expected_precondition, '<f8'),
        ('action_scale', action_scale, '<f8'), ('precondition_scale', precondition_scale, '<f8')]
    payload = struct.pack('<IIIId', n, matrix.nnz, 1, tag, wrapper.omega)
    ranges = {}
    for name, values, dtype in arrays:
        values = np.asarray(values, dtype=dtype)
        if dtype == '<f8': ranges[name] = range_record(values)
        payload += values.tobytes()
    relative = float(np.linalg.norm(matrix@rhs-expected_action)/np.linalg.norm(expected_action))
    if relative > 1e-12: raise ValueError('Assembled action differs from original factored operator')
    return payload, dict(tag=tag, unknowns=n, nonzeros=matrix.nnz, degree=1,
        length=system.length, omega=wrapper.omega, ranges=ranges,
        original_action_assembly_relative_error=relative,
        binary_sha256=hashlib.sha256(payload).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    binary = args.output.with_suffix('.bin'); manifest = args.output.with_suffix('.json')
    if binary.exists() or manifest.exists(): raise FileExistsError('Preserve prior evidence')
    # Hash all source modules in this isolated process; existing live histories
    # keep their own frozen dependency sets and are not patched by this exporter.
    paths = sorted(Path(__file__).parent.glob('*.py'))
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    payloads, cases, sources = [], [], []
    for source_index, case in enumerate(('solitary', 'wet_2d', 'captured')):
        state, bed, dx, kwargs, metadata = source_fields(case, args.input if case == 'captured' else None)
        before = state.copy(); bed_before = bed.copy(); state.flags.writeable = bed.flags.writeable = False
        records = []
        with capture_systems(records), reconstructed_pressure():
            bank.rate(state, bed, dx, second_order=True, **kwargs, dispersive=True,
                pressure_model='rational_sgn', pressure_interpolation='depth_weighted',
                pressure_formulation='kinematic', pressure_bed_slope='geometry', shoreline_limiter='unscaled')
        if len(records) != 2 or not np.array_equal(before, state) or not np.array_equal(bed_before, bed):
            raise ValueError('Source changed or poles missing')
        sources.append(dict(case=case, metadata=metadata,
            state_sha256=hashlib.sha256(state.tobytes()).hexdigest(),
            bed_sha256=hashlib.sha256(bed.tobytes()).hexdigest()))
        for pole, (system, rhs, _, stats, _) in enumerate(records):
            payload, info = encode_case(system, rhs, source_index*2+pole)
            info.update(source_case=case, original_stats=stats)
            payloads.append(payload); cases.append(info)
            print(json.dumps(info, allow_nan=False), flush=True)
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest() != h for p, h in hashes.items()):
        raise RuntimeError('Implementation changed during export')
    raw = struct.pack('<III', MAGIC, 1, len(payloads))+b''.join(payloads)
    record = dict(schema='raftsim.reconstructed_polynomial_native_fixture.v1', scope=__doc__,
        binary_path=str(binary.resolve()), binary_sha256=hashlib.sha256(raw).hexdigest(),
        sources=sources, cases=cases, implementation_hashes=hashes,
        native_solve_qualified=False, native_cost_qualified=False, scene_accepted=False)
    encoded = json.dumps(record, indent=2, allow_nan=False)
    with binary.open('xb') as out: out.write(raw)
    with manifest.open('x') as out: out.write(encoded)


if __name__ == '__main__': main()
