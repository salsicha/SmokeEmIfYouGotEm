"""Compare fixed-cohort native reconstruction/advection, keeping all failures.

Three different single-step durations, NOT equal-time temporal convergence.
No change to captured fields, rendered mesh, collision or foam transport.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from water_feature_stage_interfaces import column_interface, stage_displacements


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def quantiles(values):
    return np.quantile(values, [0,.05,.5,.95,1]).tolist() if len(values) else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipts', type=Path, nargs=3, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    ref = json.loads(args.reference.read_text())
    if not ref['complete'] or ref['accepted'] or not ref['originals_unchanged'] or ref['frame'] != 192:
        raise ValueError('Preserved frame192 query cohort required')
    columns = [r['column'] for r in ref['rows']]
    if len(columns) != ref['source_queries'] or len({tuple(c) for c in columns}) != len(columns):
        raise ValueError('Query cohort altered')
    hashes = {str(args.reference.resolve()): digest(args.reference)}
    rows, initial, fractions = [], None, []
    for path in args.receipts:
        r = json.loads(path.read_text())
        if (not all(r[k] for k in ('complete','originals_unchanged','executed_modules_unchanged','live_engine_fields_unchanged'))
                or r['accepted'] or r['frame'] != 192 or not r['exact_function_binding']['exact_code_object']
                or not r['exact_function_binding']['private_globals']):
            raise ValueError('Complete owned native step with original engine inputs unchanged required')
        for p,h in {**r['original_input_sha256'],**r['source_code_sha256'],**r['arrays']}.items():
            if digest(p) != h:
                raise ValueError('Receipt dependency changed: '+p)
            hashes[p] = h
        hashes[str(path.resolve())] = digest(path)
        fractions.append(r['declared_timestep_fraction'])
        stages = [r['stages'][index] for index in (0,2,7,35)]
        if [s['label'] for s in stages] != ['before_liquid_step','after_advectSemiLagrange_phi','before_extrapolateLsSimple','after_liquid_step']:
            raise ValueError('Observed operation order changed')
        fields = [np.load(s['fields']['phi']['path'], allow_pickle=False) for s in stages]
        flags = np.load(stages[0]['fields']['flags']['path'], allow_pickle=False)
        if initial is None:
            initial = fields[0].copy(),flags.copy()
        else:
            np.testing.assert_array_equal(fields[0],initial[0])
            np.testing.assert_array_equal(flags,initial[1])
        if fields[0].shape != (80,21,39):
            raise ValueError('Exact aligned grid required')
        samples, changes = [], []
        for column in columns:
            interfaces = [column_interface(p, flags, column, .075) for p in fields]
            displacement = stage_displacements(interfaces)
            samples.append(dict(column=column, interfaces=interfaces, displacements=displacement, accepted=False))
            if displacement is not None:
                changes.append(displacement)
        row = dict(receipt=str(path.resolve()), timestep_fraction=r['declared_timestep_fraction'],
            physical_substep_seconds=r['physical_substep_seconds'], requested_columns=len(columns),
            supported_columns=len(changes), missing_or_ambiguous_columns=[x['column'] for x in samples if x['displacements'] is None],
            samples=samples, summaries={}, accepted=False)
        for key in ('advection_vertical_displacement_m','join_minus_advection_vertical_displacement_m',
                    'final_minus_advection_vertical_displacement_m','final_minus_join_vertical_displacement_m'):
            values = [x[key] for x in changes]
            row['summaries'][key] = dict(signed_quantiles_m=quantiles(values),
                absolute_quantiles_m=quantiles(np.abs(values)))
        rows.append(row)
        print('NATIVE_INTERFACE_CHANGE', json.dumps({k:v for k,v in row.items() if k != 'samples'}), flush=True)
    if set(fractions) != {1., .5, .25}:
        raise ValueError('Full/half/quarter adapted-step controls required')
    modules = [Path(__file__),Path(__file__).with_name('water_feature_stage_interfaces.py'),
               Path(__file__).with_name('test_water_feature_stage_interfaces.py')]
    code = {str(p.resolve()): digest(p) for p in modules}
    result = dict(complete=True, accepted=False, originals_unchanged=True,
        prior_query_columns=ref['prior_columns'], prior_missing_columns=ref['prior_missing'],
        cohort_count=len(columns), rows=rows, original_input_sha256=hashes, source_code_sha256=code,
        scope=__doc__, limitations='Vertical interpolated base-phi zeros at the fixed54 earlier columns, not rendered mesh normals or material velocities. All endpoint obstacle crossings rejected. Distinct single-step durations start from identical fields/particles, not equal elapsed time; no continuous-time convergence claimed. No host emission/pre-step/source/effectors, mesh extraction or secondary replay. Does not identify a unique cause of the earlier rendered-surface mismatch or qualify liquid-coupled foam.')
    if any(digest(p) != h for p,h in {**hashes,**code}.items()):
        raise ValueError('Input changed during independent analysis')
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)


if __name__ == '__main__':
    main()
