"""Validated CPU correction-state handoff, never an implicit native restart."""
import hashlib
import json
from pathlib import Path
import numpy as np


def load_state(directory,package,native_hash,meta,particle_count):
    directory=Path(directory).resolve();package=Path(package).resolve()
    report_path=directory/'report.json';r=json.loads(report_path.read_text())
    if (not r.get('candidate_map_and_inverse_valid') or r.get('algorithm_sources_changed') or
        r.get('native_stages_sha256')!=native_hash or Path(r['input_package']).resolve()!=package or
        r.get('input_manifest_sha256')!=hashlib.sha256((package/'manifest.json').read_bytes()).hexdigest()):
        raise ValueError('Matching verified CPU map/interface handoff required')
    path=(directory/r['candidate_state_file']).resolve()
    if path.parent!=directory or hashlib.sha256(path.read_bytes()).hexdigest()!=r['candidate_state_sha256']:
        raise ValueError('Correction state file changed or escaped its package')
    cells=np.array(meta['cells']);shape=tuple(cells[::-1])
    expected=dict(positions_world_cm=(particle_count,3),positions_local_cm=(particle_count,3),
        phi=shape,boundary=(*shape,4),particle_density=shape)
    with np.load(path,allow_pickle=False) as saved:
        if set(saved.files)!=set(expected):raise ValueError('Known complete correction state arrays required')
        arrays={key:saved[key].copy() for key in expected}
    if any(a.shape!=expected[key] or not np.isfinite(a).all() for key,a in arrays.items()):
        raise ValueError('Finite complete state with unchanged particle count/grid required')
    axes=np.array(meta['world_axes']);lower=np.array(meta['world_lower_cm'])
    recovered=(arrays['positions_world_cm']-lower)@axes.T
    if not np.allclose(recovered,arrays['positions_local_cm'],rtol=0,atol=1e-7):
        raise ValueError('State changed the physical world/local coordinate frame')
    b=arrays['boundary'];rho=arrays['particle_density']
    if not np.isin(b[...,3],[0,1,2,3]).all() or (b[...,:3]!=0).any() or (rho<0).any():
        raise ValueError('Known phase labels, zero prescribed correction and nonnegative density required')
    return arrays,dict(directory=str(directory),report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        candidate_state_sha256=r['candidate_state_sha256'],input_package=str(package))
