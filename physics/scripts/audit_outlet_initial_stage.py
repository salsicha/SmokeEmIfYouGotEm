"""Read-only comparison of imposed outlet stage with captured and initial edges."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest',type=Path)
    parser.add_argument('report',type=Path)
    args=parser.parse_args()
    assert not args.report.exists()
    manifest=json.loads(args.manifest.read_text())
    inputs={r['name']:r for r in manifest['inputs']}
    datum=manifest['vertical_datum_navd88_m']
    stage=manifest['inferred_outlet_stage_relative_datum_m']
    slices=dict(west=(slice(None),0),east=(slice(None),-1),south=(0,slice(None)),north=(-1,slice(None)))
    rows=[];hashes={str(args.manifest):sha(args.manifest)}
    for probe in manifest['boundary_probes']:
        if probe['role']!='downstream':continue
        name=manifest['packages'][probe['tile_index']];package=args.manifest.parent/name
        for file,digest in inputs[name]['files'].items():
            path=package/file
            assert sha(path)==digest, str(path)
            hashes[str(path)]=digest
        scenario=json.loads((package/'scenario.json').read_text())
        source=scenario['metadata']['provenance']
        path=ROOT/source['source_geometry_file']
        assert sha(path)==source['source_geometry_sha256']
        hashes[str(path)]=sha(path)
        boundary=next(b for b in scenario['boundaries'] if b['edge']==probe['edge'])
        assert boundary['kind']=='outflow' and boundary['stage']==stage
        index=slices[probe['edge']]
        with np.load(path) as data:
            captured=data['captured_surface_navd88_m'][index]-datum
            mask=data['captured_water_mask'][index].astype(bool)
        with np.load(package/'initial_state.npz') as data:
            depth=data['depth'][index];eta=data['eta'][index]
        bed=np.load(package/'bed.npy')[index]
        wet=depth>1e-6
        assert wet.any() and np.isfinite(np.concatenate([captured,depth,eta,bed])).all()
        rows.append(dict(package=name,edge=probe['edge'],wet_cells=int(wet.sum()),
            differing_initial_stage_cells=int(np.count_nonzero(stage!=eta[wet])),
            initial_stage_jump_over_1cm_cells=int(np.count_nonzero(np.abs(stage-eta[wet])>.01)),
            captured_water_cells=int(mask.sum()),wet_outside_source_mask=int((wet & ~mask).sum()),
            source_stage_range_navd88_m=[float(captured[wet].min()+datum),float(captured[wet].max()+datum)],
            imposed_minus_source_m=(stage-captured[wet]).tolist(),
            imposed_minus_initial_m=(stage-eta[wet]).tolist(),
            imposed_depth_minus_initial_m=(np.maximum(stage-bed[wet],0)-depth[wet]).tolist()))
    assert rows
    for path,digest in hashes.items():assert sha(Path(path))==digest
    result=dict(input_hashes=hashes,imposed_stage_navd88_m=stage+datum,edges=rows,
        maximum_initial_stage_jump_m=max(abs(v) for r in rows for v in r['imposed_minus_initial_m']),
        maximum_captured_stage_difference_m=max(abs(v) for r in rows for v in r['imposed_minus_source_m']),
        boundary_modified=False,solver_steps=0,calibrated_reservoir_stage=False,settling_accepted=False)
    args.report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('input_hashes','edges')}))


if __name__=='__main__':main()
