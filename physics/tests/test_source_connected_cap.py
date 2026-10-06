import numpy as np
import pytest
import json

from build_troublemaker_source_connected_cap import lower_bins, connected_support, separate_vertex_fans, recover_segment, constrained_extension
from build_troublemaker_dem_rock_cap import close_cap_below_retained_terrain
from shapely.geometry import Polygon


def test_pulse_selection_requires_exact_bound_archive(tmp_path):
    from build_troublemaker_source_connected_cap import pulse_eligibility, RETURNS_SHA, sha
    folder=tmp_path/'tmp';folder.mkdir()
    fields=folder/'fields.npz'
    np.savez(fields,return_number=np.array([1,1,2]),number_of_returns=np.array([1,2,2]))
    manifest=folder/'manifest.json'
    record=dict(schema='raftsim.original_lidar_pulse_fields.v1',source_returns_sha256=RETURNS_SHA,
        archive_count=3,exact_archive_order_xyz_classification=True,fields_path='tmp/fields.npz',fields_sha256=sha(fields))
    manifest.write_text(json.dumps(record))
    mask,report=pulse_eligibility(manifest,3,tmp_path)
    assert mask.tolist()==[True,False,True] and report['original_classifications_modified'] is False
    for key,value in [('source_returns_sha256','0'*64),('fields_sha256','0'*64),('archive_count',2),('exact_archive_order_xyz_classification',False)]:
        manifest.write_text(json.dumps(record|{key:value}))
        with pytest.raises(ValueError):pulse_eligibility(manifest,3,tmp_path)


def test_lower_bins_keep_actual_lowest_xyz_with_original_id_tie():
    xyz=np.array([[.1,.1,2],[.2,.2,1],[.3,.3,1],[1.1,1.1,5.]])
    ids,keys,counts=lower_bins(xyz,np.array([3,2,1,0]))
    assert ids.tolist()==[1] and keys.tolist()==[[0,0]] and counts.tolist()==[3]
    assert np.array_equal(xyz[ids],[[.2,.2,1]])


@pytest.mark.parametrize('ids',[np.array([],int),np.array([0,0]),np.array([-1]),np.array([4]),np.array([0.])])
def test_invalid_original_ids_rejected(ids):
    with pytest.raises(ValueError):lower_bins(np.ones((4,3)),ids)


@pytest.mark.parametrize('count',[0,1.5])
def test_count_is_a_positive_integer(count):
    with pytest.raises(ValueError):lower_bins(np.ones((4,3)),np.arange(4),minimum_count=count)


def test_connectivity_stops_at_actual_low_ground_not_missing_data():
    gaps={(0,0):2.,(1,0):1.,(2,0):.2,(3,0):2.,(1,1):.3,(2,2):4.}
    active,collar,missing=connected_support(gaps,[(0,0)])
    assert active=={(0,0),(1,0)}
    assert collar=={(2,0),(1,1)}
    assert ((0,0),(-1,0)) in missing
    assert (3,0) not in active and (2,2) not in active


def test_diagonal_contact_does_not_connect_unrelated_outcrop():
    active,collar,_=connected_support({(0,0):1.,(1,1):1.},[(0,0)])
    assert active=={(0,0)} and collar==set()


def test_forced_old_seed_is_retained_even_if_lower_same_bin_observation_exists():
    active,_,_=connected_support({(0,0):0.,(1,0):1.},[(0,0)])
    assert active=={(0,0),(1,0)}


def test_numpy_seed_bins_produce_serializable_missing_support():
    _,_,missing=connected_support({(0,0):1.},np.array([[0,0]],dtype=np.int64))
    assert len(json.loads(json.dumps(missing)))==4


def test_disconnected_fans_are_exact_geometry_not_filled_holes():
    xyz=np.array([[0,0,2],[1,0,2],[0,1,2],[-1,0,3],[0,-1,3.]])
    faces=np.array([[0,1,2],[0,3,4]])
    with pytest.raises(ValueError,match='nonmanifold'):
        close_cap_below_retained_terrain(xyz,faces,0.)
    vertices,new_faces,source_indices=separate_vertex_fans(xyz,faces)
    assert len(vertices)==6 and source_indices.tolist()==[0,1,2,3,4,0]
    assert np.array_equal(vertices[new_faces],xyz[faces])
    _,_,_,report=close_cap_below_retained_terrain(vertices,new_faces,0.)
    assert report['volume_m3']==pytest.approx(7/3)


def test_connected_fan_is_unchanged():
    xyz=np.array([[0,0,2],[1,0,2],[1,1,3],[0,1,2.]])
    faces=np.array([[0,1,2],[0,2,3]])
    vertices,new_faces,mapping=separate_vertex_fans(xyz,faces)
    assert np.array_equal(vertices,xyz) and np.array_equal(new_faces,faces)
    assert mapping.tolist()==[0,1,2,3]


def test_nonmanifold_edge_is_not_silently_removed():
    xyz=np.array([[0,0,1],[1,0,1],[0,1,1],[0,-1,1],[.5,.5,1.]])
    with pytest.raises(ValueError,match='Nonmanifold source edge'):
        separate_vertex_fans(xyz,np.array([[0,1,2],[1,0,3],[0,1,4]]))


def test_segment_recovery_flips_crossing_diagonal_without_new_vertices():
    xyz=np.array([[0,0,3],[1,0,1],[1,1,3],[0,1,1.]])
    faces=np.array([[0,1,3],[1,2,3]])
    result=recover_segment(xyz,faces,0,2)
    assert len(result)==2 and set(result.ravel())=={0,1,2,3}
    assert all(0 in f and 2 in f for f in result)


def test_preserved_nonplanar_roof_faces_remain_exact():
    xyz=np.array([[0,0,3],[1,0,1],[1,1,3],[0,1,1],[-1,-1,0],[2,-1,0],[2,2,0],[-1,2,0.]])
    old=np.array([[0,1,2],[0,2,3]])
    result=constrained_extension(xyz,old,maximum_edge_m=5.)
    assert np.array_equal(result[:2],old)
    assert len(result)>2
    assert np.array_equal(xyz[result[:2]],xyz[old])


def test_recover_existing_segment_is_bit_exact_noop():
    xyz=np.array([[0,0,1],[1,0,1],[0,1,2.]])
    faces=np.array([[0,1,2]])
    assert np.array_equal(recover_segment(xyz,faces,0,1),faces)


def test_extension_never_bridges_review_exclusion_and_keeps_original_roof():
    xyz=np.array([[0,0,3],[1,0,1],[1,1,3],[0,1,1],[-1,-1,0],[2,-1,0],[2,2,0],[-1,2,0.]])
    old=np.array([[0,1,2],[0,2,3]])
    allowed=Polygon([[-1,0],[0,0],[0,1],[2,1],[2,2],[-1,2]])
    result=constrained_extension(xyz,old,maximum_edge_m=5.,allowed_region=allowed)
    assert np.array_equal(result[:2],old)
    assert len(result)>2
    region=allowed.union(Polygon(xyz[old[0],:2])).union(Polygon(xyz[old[1],:2]))
    assert all(region.covers(Polygon(xyz[f,:2])) for f in result[2:])
    assert not any(4 in f or 5 in f for f in result)


def test_reviewed_region_is_bound_to_sources_and_cannot_claim_measurement(tmp_path,monkeypatch):
    import build_troublemaker_source_connected_cap as module
    monkeypatch.setattr(module,'ROOT',tmp_path)
    source={k:'original' for k in ('source_mesh_sha256','original_returns_sha256','source_naip_sha256','source_naip_export_sha256')}
    source['origin_utm_and_vertical_datum_m']=[1,2,3]
    record=dict(source,schema='raftsim.interpreted_source_selection.v1',measured_outline=False,measured_flanks=False,
        interpreted_selection_polygon_m=[[0,0],[1,0],[0,1]],interpretation='Explicit prior',registration_uncertainty_m=3.)
    path=tmp_path/'selection.json';path.write_text(json.dumps(record))
    region,identity=module.reviewed_region(path,source)
    assert region.area==.5 and not identity['measured_outline']
    path.write_text(json.dumps(dict(record,measured_outline=True)))
    with pytest.raises(ValueError,match='cannot claim measured'):module.reviewed_region(path,source)
    path.write_text(json.dumps(dict(record,source_naip_sha256='changed')))
    with pytest.raises(ValueError,match='different sources'):module.reviewed_region(path,source)
