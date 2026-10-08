"""Reuse captured Colorado cores with one existing inferred-shore policy.

This is construction geometry, not a hydraulic fix or game acceptance. Original
captures, classified water, surveyed bed and inferred wet bed cannot change.
No downloads, solver runs, editor launches or production promotion occur here.
"""
import argparse
import json
from pathlib import Path
import shutil

import numpy as np

from build_colorado_catalog_evidence import ROOT, build, sha
from review_colorado_continuous_bed_seam import review


def unchanged_water_and_ground(before, after, old_clearance):
    mutable = {'bed_ellipsoid_m', 'inferred_shore_stabilization_mask', 'class_code'}
    if set(before) != set(after) or not mutable <= set(before):
        raise ValueError('Construction grid fields changed')
    for key in set(before)-mutable:
        if not np.array_equal(before[key], after[key], equal_nan=True):
            raise ValueError('Protected source/state field changed: '+key)
    a, b = before['bed_ellipsoid_m'], after['bed_ellipsoid_m']
    if a.shape != b.shape or not np.isfinite([old_clearance]).all() or not .15 <= old_clearance <= 1.:
        raise ValueError('Invalid original shore policy or grid')
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Nonfinite bed')
    masks = [before['inferred_shore_stabilization_mask'], after['inferred_shore_stabilization_mask'],
             after['classified_water_mask'], after['measured_pool_bed_mask']]
    if any(m.shape != a.shape or m.dtype.kind != 'b' for m in masks):
        raise ValueError('Aligned boolean source ownership required')
    old, new, wet, measured = masks
    if np.any(old & ~new) or np.any(new & (wet | measured)):
        raise ValueError('Inferred shore cannot replace water or measured bed')
    delta = b.astype(float)-a.astype(float)
    changed = delta != 0
    if np.any(changed & ~new) or np.any(delta < 0) or np.any(delta > 1.-old_clearance+.001):
        raise ValueError('Only bounded inferred dry-shore increase is allowed')
    codes_a, codes_b = before['class_code'], after['class_code']
    if codes_a.shape != a.shape or codes_b.shape != a.shape or not np.array_equal(codes_b[new], np.full(new.sum(), 3)):
        raise ValueError('New inferred shore class ownership changed')
    if not np.array_equal(codes_a[~new], codes_b[~new]):
        raise ValueError('Protected construction class changed')
    return dict(changed_inferred_dry_cells=int(changed.sum()),
                maximum_inferred_raise_m=float(delta.max()),
                classified_water_and_measured_bed_identical=True,
                all_other_source_arrays_identical=True)


def run(selection_path, out):
    selection_path, out = Path(selection_path).resolve(), Path(out).resolve()
    if out.exists():
        raise ValueError('Fresh output required; preserve prior construction')
    selection_hash = sha(selection_path)
    selection = json.loads(selection_path.read_text())
    if selection.get('schema') != 'raftsim.colorado.shore_source_selection.v1':
        raise ValueError('Explicit source selection required')
    windows = ROOT/selection['windows']
    if sha(windows/'index.json') != selection['index_sha256']:
        raise ValueError('Source index changed')
    index = json.loads((windows/'index.json').read_text())
    from build_colorado_continuous_source_batches import plan_batches
    rows = selection['sources']
    if not rows:
        raise ValueError('Empty source selection')
    start, stop = rows[0]['core'], rows[-1]['core']+1
    expected = [i for batch in plan_batches(index, start, stop) for i in batch]
    if [r['core'] for r in rows] != expected:
        raise ValueError('Source selection must be contiguous, unique and ordered')
    previous = ROOT/selection['previous_evidence']
    if start == 0 or json.loads((previous/'manifest.json').read_text())['name'] != index['windows'][start-1]['name']:
        raise ValueError('Adjacent preceding evidence required')
    protected = {selection_path: selection_hash, windows/'index.json': selection['index_sha256']}
    neighbours=[(previous,start-1)]
    if selection.get('next_evidence'):
        if stop>=len(index['windows']):
            raise ValueError('Following source exceeds route endpoint')
        neighbours.append((ROOT/selection['next_evidence'],stop))
    for folder, i in neighbours:
        manifest_path=folder/'manifest.json';manifest=json.loads(manifest_path.read_text())
        if (manifest['name']!=index['windows'][i]['name'] or
                manifest['parameters']['inferred_dry_shore_clearance_m']!=1. or
                sha(folder/'evidence_grid.npz')!=manifest['evidence_grid_sha256']):
            raise ValueError('Adjacent source must use the unchanged shared shore policy')
        protected[manifest_path]=sha(manifest_path)
        protected[folder/'evidence_grid.npz']=manifest['evidence_grid_sha256']
    prepared = []
    for row in rows:
        old = ROOT/row['evidence']
        manifest_path = old/'manifest.json'
        if sha(manifest_path) != row['manifest_sha256']:
            raise ValueError('Selected evidence changed')
        manifest = json.loads(manifest_path.read_text())
        tile = index['windows'][row['core']]
        if manifest['name'] != tile['name']:
            raise ValueError('Source core identity mismatch')
        if not .15 <= manifest['parameters']['inferred_dry_shore_clearance_m'] < 1.:
            raise ValueError('Selected core does not require the bounded policy increase')
        profile = windows/(tile['tile_id']+'.json')
        captures = {ROOT/p: h for p,h in manifest['source_files_sha256'].items()}
        if captures.get(profile) != sha(profile) or any(sha(p) != h for p,h in captures.items()):
            raise ValueError('Captured source identity changed')
        if sha(old/'evidence_grid.npz') != manifest['evidence_grid_sha256']:
            raise ValueError('Original construction grid changed')
        protected.update(captures)
        protected[manifest_path] = row['manifest_sha256']
        protected[old/'evidence_grid.npz'] = manifest['evidence_grid_sha256']
        def parent(kind, suffix):
            matches = [p.parent for p in captures if p.suffix == suffix and kind in str(p.parent)]
            unique = set(matches)
            if len(unique) != 1:
                raise ValueError('Ambiguous '+kind+' capture parent')
            return unique.pop()
        prepared.append((row, old, manifest, profile, parent('water','.npz'),
                         parent('bed','.npz'), parent('terrain','.tif')))
    def disk_check():
        if shutil.disk_usage(ROOT).free < 40*1024**3:
            raise ValueError('Preserve at least 40 GiB free space; no sources deleted')
    disk_check()
    out.mkdir(parents=True)
    (out/'launch.json').write_text(json.dumps(dict(selection_sha256=selection_hash,
        start=start, stop=stop, shore_clearance_m=1.,
        scope='Existing construction-policy harmonization, not measured banks, native cook or runtime acceptance'),indent=2))
    results=[]
    try:
        for row, old, manifest, profile, water, bed, terrain in prepared:
            disk_check()
            target=out/'evidence'/f"tile{row['core']:04d}"
            result=build(profile,water,bed,terrain,target,shore_clearance_m=1.)
            if result['source_files_sha256'] != manifest['source_files_sha256']:
                raise ValueError('Rebuilt source lineage changed')
            with np.load(old/'evidence_grid.npz',allow_pickle=False) as a, np.load(target/'evidence_grid.npz',allow_pickle=False) as b:
                proof=unchanged_water_and_ground(dict(a),dict(b),manifest['parameters']['inferred_dry_shore_clearance_m'])
            i=row['core'];current=index['windows'][i];prior=index['windows'][i-1]
            seam=review(previous,target,prior['source_halo_interval_m'][0],current['source_halo_interval_m'][0],
                        current['source_core_interval_m'][0],out/'seams'/f'seam{i:04d}.json')
            if not seam['bed_screen_passed']:
                raise ValueError('Source bed/reference handoff failed')
            results.append(dict(core=i,evidence=str(target.relative_to(ROOT)),
                evidence_manifest_sha256=sha(target/'manifest.json'),bed_handoff_passed=True,**proof))
            previous=target
            print(f'CORE {i:04d}: protected wet/measured arrays identical; handoff passed',flush=True)
        next_spec=selection.get('next_evidence')
        if next_spec:
            next_folder=ROOT/next_spec
            if json.loads((next_folder/'manifest.json').read_text())['name'] != index['windows'][stop]['name']:
                raise ValueError('Adjacent following source required')
            seam=review(previous,next_folder,index['windows'][stop-1]['source_halo_interval_m'][0],
                index['windows'][stop]['source_halo_interval_m'][0],index['windows'][stop]['source_core_interval_m'][0],
                out/'seams'/f'seam{stop:04d}.json')
            if not seam['bed_screen_passed']:
                raise ValueError('Following source handoff failed')
        if any(sha(p) != h for p,h in protected.items()):
            raise ValueError('Sources changed during construction')
        completed=dict(results=results,source_core_interval_m=[index['windows'][start]['source_core_interval_m'][0],
            index['windows'][stop-1]['source_core_interval_m'][1]],
            source_files_unchanged=True,hydraulic_accepted=False,engine_accepted=False)
        (out/'completed.json').write_text(json.dumps(completed,indent=2))
        return completed
    except Exception as error:
        (out/'failure.json').write_text(json.dumps(dict(error=str(error),completed_cores=[r['core'] for r in results],
            partial_sources_preserved=True,engine_accepted=False),indent=2))
        raise


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    result=run(args.selection,args.out)
    print('Completed source interval',result['source_core_interval_m'],'not hydraulic/game acceptance',flush=True)
