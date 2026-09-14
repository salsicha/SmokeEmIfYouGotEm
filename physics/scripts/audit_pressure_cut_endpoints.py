"""Compare complete original/candidate captured rates, not an evolved history."""
import argparse
from contextlib import nullcontext, contextmanager
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import total_depth_bank_replay as bank
from audit_reconstructed_polynomial_sweep import source_fields, capture_systems
from export_reconstructed_polynomial_fixture import encode_case
from pressure_cut_endpoint_reference import exact_endpoint_cuts
from reconstructed_pressure_adapter import reconstructed_pressure


def digest(data):
    return hashlib.sha256(data).hexdigest()


def exact_record(value):
    """JSON-safe bit identity, including arrays and signed scalar zero."""
    if isinstance(value, np.ndarray):
        if value.dtype.hasobject: raise ValueError('Object array cannot establish numeric bit identity')
        return dict(dtype=value.dtype.str, shape=list(value.shape), sha256=digest(value.tobytes()))
    if isinstance(value, (float, np.floating)):
        return dict(value=float(value), float64_hex=np.float64(value).tobytes().hex())
    if isinstance(value, dict): return {k: exact_record(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)): return [exact_record(v) for v in value]
    if isinstance(value, np.generic): return value.item()
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--fixture-manifest', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--shared-coefficients', action='store_true',
        help='Also check endpoint cuts plus same-geometry two-pole W/V reuse')
    parser.add_argument('--cut-basis', action='store_true',
        help='Compare original against exact partial-cut basis plus shared W/V (requires --shared-coefficients)')
    parser.add_argument('--paired-construction-repeats', type=int, default=0,
        help='Alternate endpoint/shared and basis/shared timing comparisons after one original control (1-5 pairs)')
    args = parser.parse_args()
    if args.report.exists(): raise FileExistsError(args.report)
    if args.cut_basis and not args.shared_coefficients: raise ValueError('Basis comparison requires explicit shared-coefficient mode')
    if not 0 <= args.paired_construction_repeats <= 5 or (args.paired_construction_repeats and not args.cut_basis):
        raise ValueError('Paired construction requires cut-basis mode and at most five pairs')
    hashes = {str(p): digest(p.read_bytes()) for p in Path(__file__).parent.glob('*.py')}
    manifest_raw = args.fixture_manifest.read_bytes(); manifest = json.loads(manifest_raw)
    if digest(Path(manifest['binary_path']).read_bytes()) != manifest['binary_sha256']:
        raise ValueError('Original fixture changed')
    state, bed, dx, kwargs, metadata = source_fields('captured', args.input)
    state_sha, bed_sha = digest(state.tobytes()), digest(bed.tobytes())
    source = manifest['sources'][2]
    if (source['state_sha256'], source['bed_sha256'], source['metadata']) != (state_sha, bed_sha, metadata):
        raise ValueError('Original source identity mismatch')
    state.flags.writeable = bed.flags.writeable = False
    runs = []
    scopes = [('original', nullcontext), ('exact_endpoints', exact_endpoint_cuts)]
    construction_counts = {}; cut_counts = {}
    if args.shared_coefficients:
        from shared_pressure_construction_reference import shared_pressure_coefficients
        @contextmanager
        def combined():
            with exact_endpoint_cuts(), shared_pressure_coefficients(construction_counts): yield
        if args.cut_basis:
            from pressure_cut_basis_reference import exact_cut_basis
            @contextmanager
            def basis_combined():
                with exact_cut_basis(cut_counts), shared_pressure_coefficients(construction_counts): yield
            scopes = [('original', nullcontext), ('exact_cut_basis_shared_coefficients', basis_combined)]
            if args.paired_construction_repeats:
                scopes = [('original', nullcontext)]
                for sample in range(args.paired_construction_repeats):
                    pair = [(f'endpoint_shared_sample{sample}', combined), (f'basis_shared_sample{sample}', basis_combined)]
                    scopes.extend(pair if sample % 2 == 0 else pair[::-1])
        else:
            scopes.append(('exact_endpoints_shared_coefficients', combined))
    for name, scope in scopes:
        records, stages, pressure, boundary = [], [], {}, {}
        begin = time.perf_counter()
        with scope(), capture_systems(records), reconstructed_pressure(on_stage=stages.append):
            rate, cfl = bank.rate(state, bed, dx, second_order=True, **kwargs, dispersive=True,
                pressure_model='rational_sgn', pressure_interpolation='depth_weighted',
                pressure_formulation='kinematic', pressure_bed_slope='geometry', shoreline_limiter='unscaled',
                pressure_diagnostics=pressure, boundary_diagnostics=boundary)
        seconds = time.perf_counter()-begin
        if len(records) != 2 or not np.isfinite(rate).all(): raise ValueError('Missing/invalid full rate')
        poles = []
        for i, (system, rhs, value, stats, scheme) in enumerate(records):
            raw, info = encode_case(system, rhs, 4+i)
            if info['binary_sha256'] != manifest['cases'][4+i]['binary_sha256']:
                raise ValueError('Actual operator/RHS/expected action differs from original fixture')
            poles.append(dict(fixture_sha256=digest(raw), solution_sha256=digest(value.tobytes()),
                stats=exact_record(stats), scheme=scheme,
                diagonal=exact_record(system.diagonal), off_diagonal=exact_record(system.off_diagonal),
                rows=exact_record(system.rows), columns=exact_record(system.columns),
                w=exact_record(system.w_coefficients), v=exact_record(system.v_coefficients)))
        runs.append(dict(name=name, rate_seconds=seconds, rate_sha256=digest(rate.tobytes()),
            cfl_float64_hex=np.float64(cfl).tobytes().hex(), poles=poles,
            stages=exact_record(stages), pressure=exact_record(pressure), boundary=exact_record(boundary),
            construction_counts=dict(construction_counts) if 'shared' in name else {},
            cut_counts=exact_record(cut_counts) if 'basis' in name else {}))
        print(json.dumps(dict(name=name, rate_seconds=seconds, rate_sha256=runs[-1]['rate_sha256'])), flush=True)
    fields = ('rate_sha256', 'cfl_float64_hex', 'poles', 'stages', 'pressure', 'boundary')
    if any(runs[0][k] != run[k] for run in runs[1:] for k in fields):
        raise ValueError('Complete original/candidate rate differs')
    if args.shared_coefficients and construction_counts != dict(builds=1, reuses=1, uncacheable_builds=0):
        raise ValueError('Expected exactly one original construction and one same-geometry reuse')
    if any(run['construction_counts'] != dict(builds=1, reuses=1, uncacheable_builds=0)
           for run in runs if 'shared' in run['name']):
        raise ValueError('A repeated candidate did not use exactly one original construction and one reuse')
    if args.cut_basis and not (cut_counts['partial'] > 0 and cut_counts['cache']['hits'] > 0
                              and cut_counts['cache']['currsize'] <= cut_counts['cache']['maxsize']):
        raise ValueError('Expected bounded exact partial-cut basis reuse')
    if digest(state.tobytes()) != state_sha or digest(bed.tobytes()) != bed_sha:
        raise ValueError('Input mutated')
    if any(digest(Path(p).read_bytes()) != sha for p, sha in hashes.items()):
        raise RuntimeError('Implementation changed during audit')
    report = dict(schema='raftsim.pressure_cut_endpoints.v1', passed=True, scope=__doc__,
        source_metadata=metadata, state_sha256=state_sha, bed_sha256=bed_sha,
        fixture_manifest_sha256=digest(manifest_raw), implementation_hashes=hashes, runs=runs,
        exact_complete_rate_parity=True, live_replays_modified=False, construction_counts=construction_counts,
        cut_counts=cut_counts, paired_construction_repeats=args.paired_construction_repeats,
        history_qualified=False, native_cost_qualified=False, scene_accepted=False)
    with args.report.open('x') as out: out.write(json.dumps(report, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__': main()
