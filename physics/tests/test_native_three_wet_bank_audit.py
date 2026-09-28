"""Audit rejection tests use synthetic packets, not engine/river acceptance."""
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import json
import pytest
from three_wet_bank_envelope import build
from audit_native_three_wet_bank import audit

@pytest.fixture(scope='module')
def packet():
    B=(F(2),F(0),F(0),F(0));H=(F(0),F(1),F(1),F(1))
    r=build(B,H,F(9,10000)) # Strict room for binary64 serialization of this fixture.
    polygon=((F(1),F(1)),(F(1),F(0)),*r['points'],(F(0),F(1)))
    positions={p:i for i,p in enumerate(polygon)}
    numbers=lambda values:[format(float(v),'.17g') for v in values]
    coords=lambda points:[numbers(p) for p in points]
    item=dict(bed=numbers(B),depth=numbers(H),boundary=coords(r['points']),inner=coords(r['inner_points']),
              polygon=coords(polygon),triangles=[[positions[p] for p in t] for t in r['wet_triangles']],
              construction_ms=0,coefficient_tests=0)
    return dict(cases=[dict(deepcopy(item),case=i) for i in range(4)],normal_renderer_integrated=False,gameplay_accepted=False)

def run(tmp_path,data,expected=None):
    path=tmp_path/'native.json';content=json.dumps(data).encode();path.write_bytes(content)
    return audit(path,hashlib.sha256(content).hexdigest() if expected is None else expected)

def test_complete_synthetic_packet_is_proved_without_gameplay_acceptance(tmp_path,packet):
    result=run(tmp_path,packet)
    assert len(result['cases'])==4
    assert all(c['ideal_shared_endpoint_geometry_certified'] and c['dry_band_certified'] for c in result['cases'])
    assert result['whole_river_or_gameplay_accepted'] is False
    assert result['native_world_mapping_and_cache_accepted'] is False
    assert result['isolated_performance_accepted'] is False

def test_changed_export_hash_rejected(tmp_path,packet):
    with pytest.raises(ValueError,match='hash mismatch'):run(tmp_path,packet,'0'*64)

@pytest.mark.parametrize('field',['normal_renderer_integrated','gameplay_accepted'])
def test_native_reference_cannot_promote_itself(tmp_path,packet,field):
    data=deepcopy(packet);data[field]=True
    with pytest.raises(ValueError,match='playable acceptance'):run(tmp_path,data)

@pytest.mark.parametrize('mutation',['missing','duplicate','index','nonfinite','boundary','endpoint','band','case'])
def test_corrupted_native_geometry_is_rejected(tmp_path,packet,mutation):
    data=deepcopy(packet);c=data['cases'][0]
    if mutation=='missing':c['triangles'].pop()
    elif mutation=='duplicate':c['triangles'][-1]=c['triangles'][0]
    elif mutation=='index':c['triangles'][0][0]=99999
    elif mutation=='nonfinite':c['boundary'][1][0]='nan'
    elif mutation=='boundary':c['polygon'][2][0]='.1'
    elif mutation=='endpoint':
        c['boundary'][0][0]='.51';c['polygon'][2][0]='.51'
    elif mutation=='band':c['inner'][1]=['0','0']
    elif mutation=='case':c['case']=1
    with pytest.raises(ValueError):run(tmp_path,data)
