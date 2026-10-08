import numpy as np
import pytest
import json
from unittest.mock import patch
from build_futaleufu_corridor_sources import sha
from build_futaleufu_corridor_water_reference import classify,consensus,route_components


def test_established_native_thresholds_and_zero_nodata():
    raw={name:np.array([values],dtype='u2') for name,values in dict(
        blue=[1200,1200,4000,0],green=[1800,1500,4000,1800],
        red=[1400,1400,3400,1400],nir=[1100,4000,5000,1100]).items()}
    raw['valid']=np.array([[True,True,True,False]])
    valid,wet,bright=classify(raw)
    np.testing.assert_array_equal(valid,[[True,True,True,False]])
    np.testing.assert_array_equal(wet,[[True,False,True,False]])
    np.testing.assert_array_equal(bright,[[False,False,True,False]])
    raw['valid'][0,3]=True
    with pytest.raises(ValueError,match='nodata'):classify(raw)


def test_two_known_dates_can_agree_but_one_cannot_invent_persistence():
    valid=np.array([[[1,1,1]],[[1,0,1]],[[0,0,1]]],dtype=bool)
    wet=np.array([[[1,1,1]],[[1,0,0]],[[0,0,0]]],dtype=bool)
    counts,wc,bc,repeated=consensus(valid,wet,np.zeros_like(wet))
    np.testing.assert_array_equal(counts,[[2,1,3]])
    np.testing.assert_array_equal(wc,[[2,1,1]])
    np.testing.assert_array_equal(repeated,[[True,False,False]])
    assert not bc.any()


def test_disconnected_gaps_and_remote_water_are_not_filled():
    wet=np.zeros((9,9),bool)
    wet[4,1:3]=True;wet[4,4:6]=True;wet[0,0:2]=True
    distance=np.full((9,9),50.);distance[4,:]=0
    associated,groups,count=route_components(wet,distance)
    assert count==3
    assert associated.sum()==4 and not associated[4,3] and not associated[0,:].any()
    assert len(np.unique(groups[associated]))==2
    assert not np.any(associated&~wet)


def test_corridor_limit_cannot_follow_connected_spectral_water_indefinitely():
    wet=np.ones((1,8),bool);distance=np.arange(8)[None,:]*50.
    associated,_,_=route_components(wet,distance)
    np.testing.assert_array_equal(associated,[[1,1,1,1,0,0,0,0]])


def test_inconsistent_inputs_fail_closed():
    a=np.ones((3,2,2),bool)
    with pytest.raises(ValueError):consensus(a[:2],a[:2],a[:2])
    with pytest.raises(ValueError):consensus(a,np.zeros_like(a),a)
    invalid=a.copy();invalid[0,0,0]=False
    with pytest.raises(ValueError):consensus(invalid,a,a)
    with pytest.raises(ValueError):route_components(a[0],np.full((2,2),np.nan))


def test_full_builder_keeps_both_branches_and_binds_sources(tmp_path):
    from build_futaleufu_corridor_water_reference import build
    source=tmp_path/'sources';source.mkdir()
    route=tmp_path/'route';route.mkdir()
    chart=route/'coordinate_map.json'
    chart.write_text(json.dumps(dict(horizontal_origin_m=[0,0],
        points=[[0,10,50,0,1],[50,60,50,0,1],[100,110,50,0,1]])))
    (route/'manifest.json').write_text(json.dumps(dict(source_to_projected_stations_m=[0,50,100],
        confluence=dict(route_station_m=50))))
    raw={k:np.full((20,20),v,dtype='u2') for k,v in dict(blue=1200,green=1800,red=1400,nir=1100).items()}
    raw['valid']=np.ones((20,20),bool)
    optical=[]
    for i in range(3):
        path=source/f'{i}.npz';np.savez_compressed(path,**raw)
        optical.append(dict(file=path.name,sha256=sha(path),datetime=f'202{i}-01-01'))
    np.savez_compressed(source/'dsm.npz',dsm_m=np.full((20,20),150.))
    manifest=dict(schema='raftsim.futaleufu_continuous_sources.v1',route_length_m=100,
        sources_sha256={'route/coordinate_map.json':sha(chart)},
        grid=dict(epsg=32718,shape=[20,20],transform=[10,0,0,0,-10,200,0,0,1]),
        optical=optical,optical_attribution='synthetic fixture',optical_license='fixture',
        dsm=dict(file='dsm.npz',sha256=sha(source/'dsm.npz'),license_url='fixture'))
    (source/'manifest.json').write_text(json.dumps(manifest))
    with patch('build_futaleufu_corridor_water_reference.ROOT',tmp_path), \
            patch('build_futaleufu_corridor_water_reference.ROUTE',chart):
        result=build(source,tmp_path/'out')
        assert [p['branch'] for p in result['profile']]==['rio_azul','futaleufu_mainstem']
        assert result['native_unknown_observations']==0
        assert result['discharge_assigned'] is False and result['installed_in_engine'] is False
        assert result['artifact_sha256']==sha(tmp_path/'out/water_reference.npz')
        with pytest.raises(ValueError,match='Fresh'):build(source,tmp_path/'out')
        with (source/'0.npz').open('ab') as f:f.write(b'changed')
        with pytest.raises(ValueError,match='Changed cropped'):build(source,tmp_path/'refused')
        assert not (tmp_path/'refused').exists()
