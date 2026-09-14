import hashlib
import json
import numpy as np
import pytest
from audit_recorded_evolution_steps import checkpoint


def fixture(tmp_path, *, bad=None):
    first=dict(native_seconds=1.25,origin_x=2.,origin_y=3.,ny=2,nx=3)
    source=json.dumps(dict(observations=[first,{}])).encode()
    digest=hashlib.sha256(source).hexdigest()
    rows=[dict(native_seconds=1.25,origin_meters=[2.,3.])]
    state=np.ones((2,3,3),dtype=np.float64)
    if bad=='source':digest='different'
    if bad=='time':rows[0]['native_seconds']+=.01
    if bad=='origin':rows[0]['origin_meters']=[3.,2.]
    if bad=='duplicate':rows*=2
    if bad=='shape':state=state[:1]
    if bad=='dtype':state=state.astype(np.float32)
    if bad=='depth':state[0,0,0]=-1
    if bad=='dry_momentum':state[0,0,0]=0
    if bad=='nonfinite':state[0,0,1]=np.nan
    path=tmp_path/'checkpoint.npz'
    np.savez(path,checkpoint_0=state,source_sha256=np.array(digest),checkpoints_json=np.array(json.dumps(rows)))
    return path,source,state


def test_independent_checkpoint_preserves_the_actual_evolved_state(tmp_path):
    path,source,expected=fixture(tmp_path)
    state,meta=checkpoint(path,source,0)
    np.testing.assert_array_equal(state,expected)
    assert meta['native_seconds']==1.25 and meta['checkpoint']==0
    assert meta['sha256']==hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize('bad',['source','time','origin','duplicate','shape','dtype','depth','dry_momentum','nonfinite'])
def test_mismatched_or_invalid_independent_checkpoint_rejected(tmp_path,bad):
    path,source,_=fixture(tmp_path,bad=bad)
    with pytest.raises(ValueError):checkpoint(path,source,0)
