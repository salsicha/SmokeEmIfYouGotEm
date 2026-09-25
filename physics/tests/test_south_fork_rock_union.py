"""Shared physical-height union and immutable dependency checks."""
import json
import numpy as np
import pytest
from south_fork_rock_union import SourceRockUnion,sha
from build_troublemaker_dem_rock_cap import close_cap_below_retained_terrain


@pytest.fixture
def source(tmp_path):
    xyz=np.array([[0,0,3],[1,0,4],[0,1,3.]])
    origin=np.array([100.,200.,20.]);faces=np.array([[0,1,2]])
    parent=tmp_path/'parent.npz';returns=tmp_path/'returns.npz';cap=tmp_path/'cap.npz'
    np.savez(parent,z_m=np.array([[2.,2.],[2.,2.]]))
    absolute=xyz+origin
    np.savez(returns,utm_easting_m=absolute[:,0],utm_northing_m=absolute[:,1],
        navd88_m=absolute[:,2],classification=np.ones(3,dtype=np.uint8))
    v,t,k,_=close_cap_below_retained_terrain(xyz,faces,1.)
    np.savez(cap,vertices_m=xyz,triangles=faces,original_return_index=np.arange(3),
        original_classification=np.ones(3,dtype=np.uint8),solid_vertices_m=v,solid_triangles=t,solid_face_kind=k)
    manifest=dict(schema='raftsim.original_return_rock_cap.v1',
        origin_utm_and_vertical_datum_m=origin.tolist(),inferred_solid=dict(internal_floor_m=1.))
    for name,path in [('source_mesh',parent),('original_returns',returns),('cap',cap)]:
        manifest[name+'_path']=path.name;manifest[name+'_sha256']=sha(path)
    path=tmp_path/'manifest.json';path.write_text(json.dumps(manifest))
    return tmp_path,path,parent,manifest


def load(source):
    root,path,parent,_=source
    return SourceRockUnion(path,root,parent,[100,200],20)


def test_union_preserves_parent_and_shapes_and_reports_only_real_changes(source):
    union=load(source);parent=np.array([[22.,25.,22.]])
    out,changed=union.apply([[100.1,100.8,102]],[[200.1,200.1,202]],parent)
    assert out.shape==parent.shape and changed.shape==parent.shape
    assert out.tolist()[0]==pytest.approx([23.1,25,22])
    assert changed.tolist()==[[True,False,False]]
    assert np.array_equal(parent,[[22,25,22]])
    assert not union.identity['original_terrain_modified']
    assert not union.identity['hydraulics_recooked']


def test_union_never_fills_outside_triangle_inside_bounding_box(source):
    out,changed=load(source).apply(100.9,200.9,22.)
    assert out==22 and not changed


def test_retained_union_uses_previous_descriptor_and_rejects_stale_identity(source):
    from prepare_south_fork_rock_union_geometry import retained_union
    root,path,_,_=source
    geometry=dict(rock_cap_manifest=path.name,terrain_union=load(source).identity)
    assert retained_union(geometry,root).identity==geometry['terrain_union']
    geometry['terrain_union']=dict(geometry['terrain_union'],cap_manifest_sha256='stale')
    with pytest.raises(ValueError,match='Previous union dependencies'):
        retained_union(geometry,root)


def test_explicit_cap_replacement_reconstructs_source_fields(source,monkeypatch):
    import prepare_south_fork_rock_union_geometry as module
    root,path,_,manifest=source
    monkeypatch.setattr(module,'ROOT',root)
    (root/'tmp').mkdir()
    fields=dict(bed_navd88_m=np.full((80,80),22.),captured_surface_navd88_m=np.full((80,80),23.),
                captured_water_mask=np.zeros((80,80),np.uint8),terrain_owner=np.full((80,80),2,np.uint8))
    original=root/'original.npz';np.savez_compressed(original,**fields)
    values,_=module.union_fields(fields,[100,200],load(source))
    core=root/'core.npz';np.savez_compressed(core,**values)
    record=dict(name='region',center_utm_m=[100,200],geometry_file=core.name,geometry_sha256=sha(core),
                source_geometry_file=original.name,source_geometry_sha256=sha(original),
                source_slice_row_column=[0,0],original_core_geometry_file=original.name,
                original_core_geometry_sha256=sha(original),terrain_union=load(source).identity)
    geometry=dict(completed=True,regions=[record],terrain_union=load(source).identity,
                  rock_cap_manifest=path.name,vertical_datum_navd88_m=20.,grid_spacing_m=1.,open_geometry_edges=[])
    gp=root/'geometry.json';gp.write_text(json.dumps(geometry))
    flow=root/'flow.json';flow.write_text(json.dumps(dict(geometry_manifest=gp.name,
        geometry_manifest_sha256=sha(gp),packages=['region'],boundary_probes=[])))
    candidate=root/'candidate.json';candidate.write_text(json.dumps(dict(manifest,status='replacement')))
    output=root/'tmp/new'
    audit=module.prepare(flow,candidate,output,replace_union=True)
    assert audit['passed'] and not audit['hydraulic_state_solved']
    result=json.loads((output/'manifest.json').read_text())
    assert result['terrain_union']['cap_manifest_sha256']==sha(candidate)
    assert result['retained_geometry_manifest_sha256']==sha(gp)
    with np.load(root/result['regions'][0]['geometry_file']) as saved:
        for key in module.FIELDS:assert np.array_equal(saved[key],values[key])
    # Tampering with a current core, even with its hash updated, must fail
    # source reconstruction before any replacement directory is created.
    values['bed_navd88_m'][0,0]+=1
    np.savez_compressed(core,**values);record['geometry_sha256']=sha(core)
    gp.write_text(json.dumps(geometry))
    f=json.loads(flow.read_text());f['geometry_manifest_sha256']=sha(gp);flow.write_text(json.dumps(f))
    rejected=root/'tmp/rejected'
    with pytest.raises(ValueError,match='Retained core differs'):
        module.prepare(flow,candidate,rejected,replace_union=True)
    assert not rejected.exists()


def test_interpreted_selection_hash_and_sources_are_part_of_union(source):
    root,path,_,manifest=source
    manifest.update(source_naip_sha256='image',source_naip_export_sha256='registration')
    record={key:manifest[key] for key in ('source_mesh_sha256','original_returns_sha256','source_naip_sha256',
        'source_naip_export_sha256','origin_utm_and_vertical_datum_m')}
    record.update(schema='raftsim.interpreted_source_selection.v1',measured_outline=False,measured_flanks=False)
    selection=root/'selection.json';selection.write_text(json.dumps(record))
    manifest['reviewed_extension_selection']=dict(path=selection.name,sha256=sha(selection))
    path.write_text(json.dumps(manifest))
    assert load(source).identity['interpreted_selection_sha256']==sha(selection)
    selection.write_text(json.dumps(dict(record,source_naip_sha256='other-image')))
    with pytest.raises(ValueError,match='interpreted selection'):load(source)
    manifest['reviewed_extension_selection']['sha256']=sha(selection);path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='source/frame mismatch'):load(source)
    selection.write_text(json.dumps(dict(record,measured_outline=True)))
    manifest['reviewed_extension_selection']['sha256']=sha(selection);path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='cannot claim measured'):load(source)


@pytest.mark.parametrize('field',['source_mesh','original_returns','cap'])
def test_modified_dependency_is_rejected(source,field):
    root,_,_,manifest=source
    with (root/manifest[field+'_path']).open('ab') as output:output.write(b'changed')
    with pytest.raises(ValueError,match='dependency'):load(source)


def test_frame_mismatch_and_different_parent_fail(source):
    root,path,parent,_=source
    with pytest.raises(ValueError,match='frames'):SourceRockUnion(path,root,parent,[100,201],20)
    with pytest.raises(ValueError,match='different retained'):SourceRockUnion(path,root,root/'other.npz',[100,200],20)


def test_missing_parent_support_and_exposed_bottom_fail(source):
    union=load(source)
    with pytest.raises(ValueError,match='Finite'):union.apply(100.1,200.1,np.nan)
    with pytest.raises(ValueError,match='bottom exposed'):union.apply(100.1,200.1,20.)


def test_rehashed_cap_cannot_change_the_physical_solid(source):
    root,path,_,manifest=source
    cap=root/manifest['cap_path']
    with np.load(cap) as data:arrays={k:data[k] for k in data.files}
    arrays['solid_vertices_m']=arrays['solid_vertices_m'].copy()
    arrays['solid_vertices_m'][0,2]+=.01
    np.savez(cap,**arrays);manifest['cap_sha256']=sha(cap);path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='do not match'):load(source)


def test_rehashed_cap_cannot_move_captured_roof(source):
    root,path,_,manifest=source
    cap=root/manifest['cap_path']
    with np.load(cap) as data:arrays={k:data[k] for k in data.files}
    arrays['vertices_m']=arrays['vertices_m'].copy();arrays['vertices_m'][0,0]+=.01
    np.savez(cap,**arrays);manifest['cap_sha256']=sha(cap);path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='moved'):load(source)


def test_hydraulic_packet_retains_captured_stage_mask_and_unaffected_owners(source):
    from prepare_south_fork_rock_union_geometry import union_fields
    fields=dict(bed_navd88_m=np.full((80,80),22.),captured_surface_navd88_m=np.full((80,80),23.),
        captured_water_mask=np.ones((80,80),np.uint8),terrain_owner=np.full((80,80),2,np.uint8))
    updated,changed=union_fields(fields,[100,200],load(source))
    assert changed.sum()==3
    assert np.array_equal(updated['captured_water_mask'],fields['captured_water_mask'])
    assert np.array_equal(updated['captured_surface_navd88_m'],fields['captured_surface_navd88_m'])
    assert np.all(updated['terrain_owner'][changed]==5)
    assert np.all(updated['terrain_owner'][~changed]==2)
    assert np.array_equal(updated['bed_navd88_m'][~changed],fields['bed_navd88_m'][~changed])
    assert np.all(fields['bed_navd88_m']==22.)


def test_fresh_input_gate_rejects_old_depth_and_changed_boundary():
    from audit_south_fork_rock_union_input import validate_fresh_package
    scenario=dict(grid=dict(nx=80,ny=80),boundaries=[dict(edge='east',kind='outflow',stage=3.)],
        roughness=.035,fixed_dt=.05)
    bed=np.full((80,80),2.)
    geometry=dict(bed_navd88_m=bed+20,captured_surface_navd88_m=bed+21,captured_water_mask=np.ones((80,80)))
    h=np.ones_like(bed);u=h*.3;v=h*.2
    state=dict(depth=h,u=u,v=v,eta=bed+h,hu=h*u,hv=h*v,wet=h>1.e-6)
    validate_fresh_package(scenario,scenario,bed,state,geometry,20)
    with pytest.raises(ValueError,match='fresh source-stage'):
        validate_fresh_package(scenario,scenario,bed,dict(state,depth=h*.8),geometry,20)
    with pytest.raises(ValueError,match='physical setup'):
        validate_fresh_package(dict(scenario,boundaries=[]),scenario,bed,state,geometry,20)


def test_runtime_packet_union_preserves_observations_and_outside_samples(source):
    from south_fork_rock_union_packets import packet_fields
    fields=dict(bed_navd88_m=np.full((321,321),22.),captured_surface_navd88_m=np.full((321,321),23.),
        captured_water_mask=np.ones((321,321),np.uint8),terrain_owner=np.full((321,321),2,np.uint8))
    values,changed=packet_fields(fields,[100,200],load(source))
    assert changed.sum()==3
    for key in ('captured_surface_navd88_m','captured_water_mask'):
        assert np.array_equal(values[key],fields[key])
    assert np.array_equal(values['bed_navd88_m'][~changed],fields['bed_navd88_m'][~changed])
    assert np.all(values['terrain_owner'][changed]==5)
    with pytest.raises(ValueError,match='321'):
        packet_fields({k:v[:80,:80] for k,v in fields.items()},[100,200],load(source))


def test_full_map_probe_frame_applies_origin_datum_and_y_reflection_once():
    from prepare_south_fork_union_collision import engine_position
    assert engine_position([101,198],23,[100,200],20)==[100,200,300]


def test_revised_bed_ownership_is_not_inferred_from_height_increase(source):
    from types import SimpleNamespace
    from prepare_south_fork_union_collision import physical_union_samples
    union=load(source)
    union.terrain_revision=SimpleNamespace(apply=lambda x,y,parent:(np.asarray(parent)+2,np.ones_like(parent,dtype=bool)))
    after,rock=physical_union_samples(union,[[100.1,200.1],[102,202]],[22.,22.])
    assert after.tolist()==[24.,24.] and rock.tolist()==[False,False]
    union.terrain_revision=SimpleNamespace(apply=lambda x,y,parent:(np.asarray(parent)-.5,np.ones_like(parent,dtype=bool)))
    after,rock=physical_union_samples(union,[[100.1,200.1]],[23.5])
    assert after[0]==pytest.approx(23.1) and rock[0]


def test_full_map_probe_samples_actual_union_without_discarding_buried_source():
    from prepare_south_fork_union_collision import visible_union_roof_probe
    original=dict(kind='source_vertex',world_position_cm=[10,-20,300],outward_normal=[.1,.2,.9],ray_half_length_cm=100.)
    shift=np.array([1000,2000,0])
    exposed=visible_union_roof_probe(original,2.,shift)
    assert exposed['expected_candidate'] and exposed['world_position_cm']==[1010,1980,300]
    covered=visible_union_roof_probe(original,3.2,shift)
    assert not covered['expected_candidate'] and covered['world_position_cm']==[1010,1980,320]
    assert covered['retained_original_source_position_cm']==[10,-20,300]
    assert covered['outward_normal']==[0,0,1] and original['world_position_cm']==[10,-20,300]


@pytest.fixture
def packet_export(source):
    from south_fork_rock_union_packets import packet_fields,changed_record
    root,cap_path,_,_=source;union=load(source)
    directory=root/'original';directory.mkdir();derived=root/'derived';derived.mkdir()
    fields=dict(bed_navd88_m=np.full((321,321),22.),captured_surface_navd88_m=np.full((321,321),23.),
        captured_water_mask=np.ones((321,321),np.uint8),terrain_owner=np.full((321,321),2,np.uint8))
    original_path=directory/'region_0000.npz';np.savez_compressed(original_path,**fields)
    record=dict(name='region_0000',geometry_file='original/region_0000.npz',geometry_sha256=sha(original_path),
        center_utm_m=[100,200],grid_origin_local_m=[-160,-160],shape=[321,321],owner_cell_counts={'2':321*321})
    original=dict(regions=[record],world_origin_utm_m=[100,200],vertical_datum_navd88_m=20,grid_spacing_m=1.)
    original_manifest=directory/'manifest.json';original_manifest.write_text(json.dumps(original))
    geometry=dict(regions=[dict(source_geometry_file=record['geometry_file'])],source_manifest_sha256=sha(original_manifest),
        rock_cap_manifest=cap_path.name,terrain_union=union.identity)
    geometry_path=root/'geometry.json';geometry_path.write_text(json.dumps(geometry))
    values,changed=packet_fields(fields,[100,200],union);path=derived/'region_0000.npz'
    np.savez_compressed(path,**values)
    result=dict(original,schema='raftsim.cartesian_source_packet_union.v1',
        regions=[changed_record(record,path,values,changed,union,root)],terrain_union=union.identity,
        hydraulic_geometry_manifest_sha256=sha(geometry_path),retained_source_manifest_sha256=sha(original_manifest))
    manifest=derived/'manifest.json';manifest.write_text(json.dumps(result))
    return root,geometry_path,manifest,path,result


def test_compound_packet_verification_reconstructs_all_changed_fields(packet_export):
    from south_fork_rock_union_packets import verify
    root,geometry,manifest,_,expected=packet_export
    assert verify(manifest,geometry,root)==expected


@pytest.mark.parametrize('field',['bed_navd88_m','captured_surface_navd88_m','captured_water_mask'])
def test_rehashed_compound_packet_cannot_change_source_or_roof(packet_export,field):
    from south_fork_rock_union_packets import verify
    root,geometry,manifest,path,result=packet_export
    with np.load(path) as data:values={k:data[k] for k in data.files}
    values[field]=values[field].copy();values[field][10,10]=0
    np.savez_compressed(path,**values);result['regions'][0]['geometry_sha256']=sha(path)
    manifest.write_text(json.dumps(result))
    with pytest.raises(ValueError,match='differs from source-exact'):verify(manifest,geometry,root)


@pytest.mark.parametrize('kind',['frame','cook','coverage'])
def test_compound_packets_reject_relabelled_frame_cook_or_coverage(packet_export,kind):
    from south_fork_rock_union_packets import verify
    root,geometry,manifest,_,result=packet_export
    if kind=='frame':result['world_origin_utm_m'][0]+=1
    elif kind=='cook':result['hydraulic_geometry_manifest_sha256']='different'
    else:result['regions']=[]
    manifest.write_text(json.dumps(result))
    with pytest.raises(ValueError):verify(manifest,geometry,root)


@pytest.mark.parametrize('depth,solver,presentation',[(0,False,False),(1.e-6,False,False),
    (2.e-6,True,False),(1.e-4,True,False),(np.nextafter(1.e-4,np.inf),True,True)])
def test_native_sample_visibility_and_solver_wetness_are_distinct_contracts(depth,solver,presentation):
    from prepare_south_fork_union_runtime import wet_flags
    assert wet_flags(depth)==dict(solver_wet=solver,native_sample_wet=presentation)
