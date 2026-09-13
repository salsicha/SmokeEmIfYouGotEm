"""Verify all on-disk full-river numerical inputs before native cooking."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'tmp/south-fork-coupled-flow-input-v2-20260912'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source=BASE/'manifest.json'
    output=BASE/'input_audit.json'
    assert not output.exists(), 'Preserve existing input audit'
    manifest=json.loads(source.read_text())
    geometry_path=ROOT/manifest['geometry_manifest']
    assert sha(geometry_path)==manifest['geometry_manifest_sha256']
    geometry=json.loads(geometry_path.read_text())
    assert len(manifest['packages'])==len(geometry['regions'])==826
    total_q=0.
    count=0
    for package,record,original in zip(manifest['packages'],manifest['inputs'],geometry['regions']):
        directory=BASE/package
        for name,digest in record['files'].items():
            assert sha(directory/name)==digest
        scenario=json.loads((directory/'scenario.json').read_text())
        assert scenario['metadata']['generator_version']=='20260912-v2'
        assert 'analytic_fixture_id' not in scenario['metadata']['provenance']
        assert scenario['metadata']['provenance']['source_geometry_sha256']==original['geometry_sha256']
        bed=np.load(directory/'bed.npy',allow_pickle=False)
        with np.load(ROOT/original['geometry_file'],allow_pickle=False) as arrays:
            expected=arrays['bed_navd88_m']-manifest['vertical_datum_navd88_m']
        assert np.array_equal(bed,expected)
        with np.load(directory/'initial_state.npz',allow_pickle=False) as state:
            h,u,v=state['depth'],state['u'],state['v']
            assert h.shape==u.shape==v.shape==(80,80)
            assert np.isfinite(h).all() and np.isfinite(u).all() and np.isfinite(v).all()
            assert h.min()>=0. and h.max()<=10. and np.hypot(u,v).max()<=20.
            assert np.array_equal(state['eta'],bed+h)
            assert np.array_equal(state['hu'],h*u) and np.array_equal(state['hv'],h*v)
            assert state['wet'].dtype==np.bool_ and np.array_equal(state['wet'],h>1.e-6)
        for boundary in scenario['boundaries']:
            if boundary['kind']!='discharge_profile':
                continue
            profile=np.asarray(boundary['ghost_cells'])
            assert profile.shape==(160,4) and np.isfinite(profile).all()
            edge=boundary['edge']; sign=1. if edge in ('west','south') else -1.
            q=sign*profile[:80,1]*profile[:80,2 if edge in ('west','east') else 3]
            assert (q>=0.).all()
            total_q+=float(q.sum())
        count+=bed.size
    assert abs(total_q-manifest['target_discharge_m3s'])<1.e-12
    report=dict(manifest_sha256=sha(source),packages_checked=len(manifest['packages']),
        cells_checked=count,all_array_file_hashes_verified=True,bed_exact_in_declared_datum=True,
        finite_initial_states=True,combined_inlet_discharge_m3s=total_q,passed=True,
        settled_hydraulics=False,normal_map_integrated=False)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    main()
