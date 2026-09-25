import hashlib
import numpy as np
import pytest
import laspy
from pyproj import CRS,Transformer
from pyproj.crs import CompoundCRS
from south_fork_mixed_cap_sources import validate_mixed_sources

@pytest.fixture
def mixed(tmp_path):
    h=laspy.LasHeader(point_format=6,version='1.4')
    h.scales=np.array([.01,.01,.01]); h.offsets=np.array([683000.,4296000.,200.])
    h.add_crs(CompoundCRS('survey',[CRS.from_epsg(6339),CRS.from_epsg(5703)]))
    las=laspy.LasData(h); las.x=[683786.11];las.y=[4296696.03];las.z=[228.37]
    las.classification=[1];las.return_number=[1];las.number_of_returns=[1]
    path=tmp_path/'source.las';las.write(path)
    old=dict(utm_easting_m=np.array([100.]),utm_northing_m=np.array([200.]),
        navd88_m=np.array([20.]),classification=np.array([2],dtype=np.uint8))
    origin=np.array([100.,200.,20.]); x,y=Transformer.from_crs(6339,32610,always_xy=True).transform(683786.11,4296696.03)
    data=dict(vertices_m=np.array([[0.,0.,0.],np.array([x,y,228.37])-origin]),
        source_dataset=np.array([0,1]),source_point_index=np.array([0,0]),source_classification=np.array([2,1]))
    manifest=dict(independent_source=dict(path='source.las',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),vertical_adjustment_m=0))
    return data,old,manifest,tmp_path,origin

def test_source_exact_rows_pass(mixed):
    result=validate_mixed_sources(*mixed)
    assert result['source_vertices']==1
    assert not result['semantic_rock_classification_verified']

@pytest.mark.parametrize('case',['moved','class','unknown','negative','old_bounds','new_bounds','dtype','legacy','offset','hash'])
def test_forged_provenance_rejected(mixed,case):
    d,o,m,r,origin=mixed
    if case=='moved':d['vertices_m'][1,2]+=.01
    if case=='class':d['source_classification'][1]=2
    if case=='unknown':d['source_dataset'][1]=2
    if case=='negative':d['source_point_index'][1]=-1
    if case=='old_bounds':d['source_point_index'][0]=1
    if case=='new_bounds':d['source_point_index'][1]=1
    if case=='dtype':d['source_point_index']=d['source_point_index'].astype(float)
    if case=='legacy':d['original_return_index']=np.array([0,0])
    if case=='offset':m['independent_source']['vertical_adjustment_m']=.08
    if case=='hash':m['independent_source']['sha256']='bad'
    with pytest.raises(ValueError):validate_mixed_sources(*mixed)

def test_rehashed_withheld_point_rejected(mixed):
    d,o,m,r,origin=mixed;path=r/'source.las';las=laspy.read(path)
    las.withheld=[1];las.write(path)
    m['independent_source']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError,match='withheld'):validate_mixed_sources(*mixed)
