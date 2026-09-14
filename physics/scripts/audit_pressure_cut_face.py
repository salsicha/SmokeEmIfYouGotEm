"""Inspect exact one-sided column cuts in an existing wetting-limit probe.

This consumes the captured pressure results, not a new evolution. The test case
has reconstructed heights equal to cell heights; reject any case needing an
unprovided pressure reconstruction. The one-sided integrals are NOT a shared
numerical face flux and do not replace either pressure force or bottom traction.
Both actual pressures and fixed-left-pressure geometry probes are reported.
"""
import argparse
import hashlib
import json
from pathlib import Path
from pressure_cut_face_reference import cut_pressure_column, represented_float


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def columns(probe, frozen=None):
    passes = probe['hydrostatic_face_passes']
    cells = probe['pressure']['cells']
    if len(passes) != 1 or len(cells) != 2:
        raise ValueError('Exactly one face reconstruction and two pressure columns required')
    face = passes[0]
    result = []
    for index, (cell, side) in enumerate(zip(cells, ('a', 'b'))):
        if cell['h'] != face['reconstructed_'+side]:
            raise ValueError('Cell/face heights differ: a pressure reconstruction is required')
        profile = cell if frozen is None else frozen[index]
        cut = cut_pressure_column(cell['h'], profile['integrated_nonhydrostatic'],
            profile['bottom_nonhydrostatic'], face['hydrostatic_'+side])
        result.append((cut, dict(yx=cell['yx'], height=cell['h'],
            retained_height=face['hydrostatic_'+side],
            integrated_nonhydrostatic=profile['integrated_nonhydrostatic'],
            bottom_nonhydrostatic=profile['bottom_nonhydrostatic'],
            transmitted=represented_float(cut.transmitted), blocked=represented_float(cut.blocked))))
    return result


def summarize(probe):
    if probe['schema'] != 'raftsim.pressure_wetting_edge_probe.v1':
        raise ValueError('Expected a pressure wetting-edge probe')
    cases = probe['wetting_limit']['cases']
    if not cases:
        raise ValueError('Wetting-limit cases required')
    rows = []
    for case in cases:
        if len(case['probes']) != 2 or case['changed_graph_cells'] != 1:
            raise ValueError('Expected a single-edge closed/open bracket')
        left, right = case['probes']
        if left['edge_open'] or not right['edge_open']:
            raise ValueError('Expected a single-edge closed/open bracket')
        closed, opened = columns(left), columns(right)
        frozen = columns(right, left['pressure']['cells'])
        changes = []
        for a, b in zip(closed, opened):
            changes.append({name: represented_float(getattr(b[0], name)-getattr(a[0], name))
                            for name in ('transmitted', 'blocked')})
        rows.append(dict(maximum_state_difference=case['maximum_state_difference'],
            unchanged_source_force_jump=case['force_jump_at_owner'],
            actual_closed_columns=[v[1] for v in closed],
            actual_open_columns=[v[1] for v in opened],
            fixed_left_pressure_open_geometry_columns=[v[1] for v in frozen],
            actual_integral_changes=changes))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('probe', type=Path)
    parser.add_argument('--trace', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    probe_bytes = args.probe.read_bytes(); probe = json.loads(probe_bytes)
    trace_bytes = args.trace.read_bytes(); trace = json.loads(trace_bytes)
    if (not trace.get('completed') or not trace.get('final_state_exact_to_live') or
            (trace.get('source_evolution_failed') and not trace.get('retained_failure_exact'))):
        raise ValueError('Exact completed diagnostic trace required')
    hashes = dict(trace_sha256=hashlib.sha256(trace_bytes).hexdigest(),
        binary_sha256=digest(Path(trace['binary'])), source_sha256=digest(Path(trace['source'])))
    if any(probe[key] != value for key, value in hashes.items()):
        raise ValueError('Wetting probe does not match current captured source bytes')
    result = dict(schema='raftsim.pressure_cut_column_probe.v1', scope=__doc__,
        input_probe=str(args.probe.resolve()), input_probe_sha256=hashlib.sha256(probe_bytes).hexdigest(),
        **hashes, cases=summarize(probe),
        rate_scope='Snapshot integrals only. No pressure, geometry, or aperture time rates supplied or measured here.',
        qualification='One-sided column integration only; no shared flux, compatible solve, new trajectory, or playable qualification.',
        implementation_hashes={name: digest(Path(__file__).with_name(name)) for name in
            ('pressure_cut_face_reference.py', 'audit_pressure_cut_face.py')})
    with args.report.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(dict(report=str(args.report), last_case=result['cases'][-1]), indent=2))


if __name__ == '__main__':
    main()
