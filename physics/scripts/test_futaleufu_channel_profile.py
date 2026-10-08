import numpy as np
import pytest
import json
from unittest.mock import patch
from build_futaleufu_channel_profile import fit_stage,choose_stage,fill_spans,stage_anchors


def test_branch_fit_keeps_raw_input_and_exact_junction_constraint():
    raw=np.array([215.,210.,212.,204.]);before=raw.copy()
    fitted=fit_stage(raw,np.ones(4),206.,True)
    np.testing.assert_array_equal(raw,before)
    np.testing.assert_array_equal(fitted,[215,211,211,206])
    assert np.all(np.diff(fitted)<=0)
    out=fit_stage([208,205,207,200],np.ones(4),206.,False)
    np.testing.assert_array_equal(out,[206,206,206,200])


def test_weighted_fit_prefers_stronger_support():
    fit=fit_stage([200,210],[10,1],190,True)
    np.testing.assert_allclose(fit,[(200*10+210)/11]*2)


@pytest.mark.parametrize('raw,w,j', [([1],[1],1),([2,1],[0,1],1),([np.nan,1],[1,1],1),([2,1],[1,1],np.inf)])
def test_invalid_stage_evidence_is_refused(raw,w,j):
    with pytest.raises(ValueError):fit_stage(raw,w,j,True)


def test_support_hierarchy_and_fallback_are_explicit():
    assert choose_stage([200,202],[400,402],[500,502])==(201,2,'interior_water_dsm')
    assert choose_stage([200],[210,212],[500,502])==(211,.5,'edge_water_dsm')
    value,weight,kind=choose_stage([],[],[200,210,220])
    assert value==202 and weight==.03 and kind=='near_route_dsm_fallback'
    with pytest.raises(ValueError):choose_stage([],[],[200])


def test_span_gaps_and_endpoint_extension_are_flagged():
    lo,hi,inferred=fill_spans([0,50,100,150,200],[np.nan,-10,np.nan,-30,np.nan],
                            [np.nan,10,np.nan,30,np.nan])
    np.testing.assert_array_equal(lo,[-10,-10,-20,-30,-30])
    np.testing.assert_array_equal(hi,[10,10,20,30,30])
    np.testing.assert_array_equal(inferred,[True,False,True,False,True])
    with pytest.raises(ValueError):fill_spans([0,1],[np.nan,0],[np.nan,10])
    with pytest.raises(ValueError):fill_spans([0,1],[10,20],[5,10])


def test_coarse_anchors_do_not_average_canopy_into_water():
    records=[]
    for i,z in enumerate([300,301,210,209,207,206,205,204]):
        records.append(dict(start_m=i*50,end_m=(i+1)*50,raw_dsm_stage_m=z,
            weight=100 if i<2 else 1,kind='near_route_dsm_fallback' if i<2 else 'edge_water_dsm'))
    anchors=stage_anchors(records,400,200,True)
    assert len(anchors)==2 and anchors[0]['kind']=='edge_water_dsm'
    assert anchors[0]['raw_stage_m']==209 and anchors[0]['support_sections']==2
    assert anchors[1]['raw_stage_m']==205


def test_canopy_only_anchor_is_explicit_lowest_supported_fallback():
    records=[dict(start_m=i*50,end_m=(i+1)*50,raw_dsm_stage_m=z,weight=1,
                  kind='near_route_dsm_fallback') for i,z in enumerate([280,290,295,285,270,275,280,272])]
    anchors=stage_anchors(records,400,260,True)
    assert [a['raw_stage_m'] for a in anchors]==[280,270]
    assert all(a['kind']=='near_route_dsm_fallback' for a in anchors)


def test_three_arm_builder_has_exact_common_stage_and_source_guards(tmp_path):
    from build_futaleufu_channel_profile import build,sha
    source=tmp_path/'source';source.mkdir()
    raw={k:np.full((100,100),v,dtype='u2') for k,v in
         dict(blue=1200,green=1800,red=1400,nir=1100).items()}
    raw['valid']=np.ones((100,100),bool)
    optical=[]
    for i in range(3):
        path=source/f'optical{i}.npz';np.savez_compressed(path,**raw)
        optical.append(dict(file=path.name,sha256=sha(path)))
    dsm=np.broadcast_to((100+np.arange(995,0,-10)*.01)[:,None],(100,100)).copy()
    np.savez_compressed(source/'dsm.npz',dsm_m=dsm)
    manifest=dict(schema='raftsim.futaleufu_continuous_sources.v1',sources_sha256={},
        grid=dict(epsg=32718,shape=[100,100],transform=[10,0,0,0,-10,1000]),optical=optical,
        dsm=dict(file='dsm.npz',sha256=sha(source/'dsm.npz'),license_url='fixture'),
        optical_attribution='fixture',optical_license='fixture')
    mp=source/'manifest.json';mp.write_text(json.dumps(manifest))
    network=dict(schema='raftsim.futaleufu_confluence_network.v1',
        sources_sha256={'source/manifest.json':sha(mp)},junction=dict(easting_northing_m=[500,500]),
        rights='fixture',branches={name:dict(points_station_easting_northing_m=points) for name,points in dict(
            rio_azul=[[0,100,800],[500,500,500]],upstream_mainstem=[[0,500,900],[400,500,500]],
            downstream_mainstem=[[0,500,500],[400,500,100]]).items()})
    npth=tmp_path/'network.json';npth.write_text(json.dumps(network))
    with patch('build_futaleufu_channel_profile.ROOT',tmp_path):
        result=build(source,npth,tmp_path/'out')
        assert result['installed_in_engine'] is False and result['bed_constructed'] is False
        with np.load(tmp_path/'out/profile.npz') as arrays:
            ends=[]
            for name in network['branches']:
                stage=arrays[name+'_stage_m']
                assert np.isfinite(stage).all() and np.all(np.diff(stage)<=0)
                assert np.all(arrays[name+'_right_m']>arrays[name+'_left_m'])
                ends.append(stage[0 if name=='downstream_mainstem' else -1])
            assert ends==[result['junction_stage_m']]*3
        with pytest.raises(ValueError,match='Fresh'):build(source,npth,tmp_path/'out')
        with (source/'optical0.npz').open('ab') as f:f.write(b'changed')
        with pytest.raises(ValueError,match='Changed optical'):build(source,npth,tmp_path/'refused')
        assert not (tmp_path/'refused').exists()
