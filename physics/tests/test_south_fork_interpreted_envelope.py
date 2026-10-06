import json
import numpy as np
import pytest
from test_south_fork_rock_union import source
from south_fork_rock_union import SourceRockUnion,sha
from south_fork_interpreted_envelope import validate_envelope_arrays
from build_troublemaker_dem_rock_cap import close_cap_below_retained_terrain


def candidate(source):
    root,path,parent,cap=source
    with np.load(root/cap['cap_path']) as a:
        original={k:a[k].copy() for k in a.files}
    roof=original['vertices_m'].copy();roof[1,2]=2.5
    v,t,k,_=close_cap_below_retained_terrain(roof,original['triangles'],1.)
    arrays=dict(solid_vertices_m=v,solid_triangles=t,solid_face_kind=k,
        roof_original_z_m=original['vertices_m'][:,2].copy(),
        roof_lowered_m=original['vertices_m'][:,2]-roof[:,2])
    envelope=root/'envelope.npz';np.savez(envelope,**arrays)
    build=root/'build.json';build.write_text(json.dumps(dict(schema='raftsim.troublemaker_rock_envelope.v2',
        source_cap_sha256=cap['cap_sha256'],output_sha256=sha(envelope),faces_measured=False,
        captured_returns_modified=False,vertices_changed=1,roof_vertices=3)))
    descriptor=root/'envelope.json'
    record=dict(schema='raftsim.inferred_rock_envelope_union_source.v1',faces_measured=False,
        captured_returns_modified=False,origin_utm_and_vertical_datum_m=[100.,200.,20.],
        source_cap_manifest=path.name,source_cap_manifest_sha256=sha(path),
        envelope_file=envelope.name,envelope_file_sha256=sha(envelope),
        build_receipt=build.name,build_receipt_sha256=sha(build))
    descriptor.write_text(json.dumps(record))
    return original,arrays,descriptor,record


def test_envelope_replaces_roof_without_weakening_source_validation(source):
    original,arrays,path,_=candidate(source)
    root,cap,parent,m=source
    before={n:sha(root/m[n+'_path']) for n in ('cap','source_mesh','original_returns')}
    union=SourceRockUnion(cap,root,parent,[100,200],20,interpreted_envelope=path)
    value,changed,owner=union.apply([100.8,102],[200.1,202],[22.,22.],with_owner=True)
    assert value==pytest.approx([22.6,22.])  # Old source roof would be23.8.
    assert changed.tolist()==[True,False] and owner.tolist()==[5,0]
    assert union.identity['schema']=='raftsim.interpreted_envelope_terrain_union.v1'
    assert union.identity['roof_measured'] is False
    assert union.identity['interpreted_envelope']['captured_returns_modified'] is False
    assert before=={n:sha(root/m[n+'_path']) for n in before}
    plain=SourceRockUnion(cap,root,parent,[100,200],20)
    assert plain.apply(100.8,200.1,22.)[0]==pytest.approx(23.8)
    from prepare_south_fork_rock_union_geometry import retained_union
    geometry=dict(rock_cap_manifest=cap.name,interpreted_envelope_manifest=path.name,terrain_union=union.identity)
    assert retained_union(geometry,root).identity==union.identity


@pytest.mark.parametrize('mutation',['xy','floor','raise','below_floor','nan','faces','authority','source_z','lowering'])
def test_malformed_or_source_altering_envelope_refused(source,mutation):
    original,arrays,_,_=candidate(source)
    if mutation=='xy':arrays['solid_vertices_m'][0,0]+=.1
    if mutation=='floor':arrays['solid_vertices_m'][-1,2]+=.1
    if mutation=='raise':arrays['solid_vertices_m'][0,2]+=1
    if mutation=='below_floor':arrays['solid_vertices_m'][0,2]=1
    if mutation=='nan':arrays['solid_vertices_m'][0,2]=np.nan
    if mutation=='faces':arrays['solid_triangles'][0]=arrays['solid_triangles'][0,::-1]
    if mutation=='authority':arrays['solid_face_kind'][0]+=1
    if mutation=='source_z':arrays['roof_original_z_m'][0]+=.1
    if mutation=='lowering':arrays['roof_lowered_m'][0]+=.1
    with pytest.raises(ValueError):validate_envelope_arrays(original,arrays,1.)


@pytest.mark.parametrize('field,value',[
    ('faces_measured',True),('captured_returns_modified',True),
    ('schema','raftsim.original_return_rock_cap.v1'),('origin_utm_and_vertical_datum_m',[100,201,20]),
    ('envelope_file_sha256','wrong'),('source_cap_manifest_sha256','wrong')])
def test_identity_and_authority_fail_closed(source,field,value):
    _,_,path,record=candidate(source)
    record[field]=value;path.write_text(json.dumps(record))
    root,cap,parent,_=source
    with pytest.raises(ValueError):SourceRockUnion(cap,root,parent,[100,200],20,interpreted_envelope=path)


def test_changed_captured_source_still_rejected_before_envelope(source):
    _,_,path,record=candidate(source)
    root,cap,parent,m=source
    with np.load(root/m['cap_path']) as a:values={k:a[k] for k in a.files}
    values['vertices_m'][0,2]-=.1
    np.savez(root/m['cap_path'],**values)
    m['cap_sha256']=sha(root/m['cap_path']);cap.write_text(json.dumps(m))
    record['source_cap_manifest_sha256']=sha(cap);path.write_text(json.dumps(record))
    with pytest.raises(ValueError,match='moved an original'):
        SourceRockUnion(cap,root,parent,[100,200],20,interpreted_envelope=path)
