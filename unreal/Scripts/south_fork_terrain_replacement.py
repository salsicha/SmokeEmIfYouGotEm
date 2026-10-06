"""Explicit source-bound, local-only terrain replacement for native verification."""
import hashlib
import json
import math
import struct
from pathlib import Path

GROUND='/Game/RaftSim/Environment/SouthForkReconstruction/Troublemaker/SM_TroublemakerCapturedGround'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def configuration(path,probes,root):
    root=Path(root).resolve();raw=json.loads(Path(path).read_text())
    revision=probes.get('terrain_revision')
    if not revision or probes.get('terrain_replacement_required') is not True:
        raise ValueError('Explicit revised-terrain probes required')
    geometry=json.loads((root/probes['geometry_manifest']).read_text())
    if (sha(root/probes['geometry_manifest'])!=probes['geometry_manifest_sha256'] or
            geometry.get('terrain_revision')!=revision or
            geometry.get('terrain_union',{}).get('terrain_revision')!=revision or
            revision['original_geometry_sha256']!=probes['parent_mesh_sha256']):
        raise ValueError('Terrain revision and hydraulic provenance differ')
    for key,digest in [('manifest','manifest_sha256'),('mesh_path','revised_geometry_sha256')]:
        source=(root/revision[key]).resolve()
        if not source.is_relative_to(root) or sha(source)!=revision[digest]:
            raise ValueError('Changed terrain revision source')
    directory=(root/raw['export_directory']).resolve()
    if not (directory.is_relative_to(root/'tmp') or
            directory.is_relative_to(root/'unreal/SourceArt/RaftSim')):
        raise ValueError('Local generated terrain export required')
    export=json.loads((directory/'manifest.json').read_text())
    fbx=(root/export['fbx']).resolve()
    if not fbx.is_relative_to(directory) or sha(fbx)!=export['fbx_sha256']:
        raise ValueError('Changed terrain FBX')
    if export.get('source_geometry_sha256')!=revision['revised_geometry_sha256']:
        raise ValueError('Terrain export and hydraulic bed differ')
    if export.get('source_bed_sampling')!='registered_triangles':
        raise ValueError('Exact registered terrain triangles required')
    count=export.get('triangle_count')
    if type(count) is not int or count<=0:raise ValueError('Positive source triangle count required')
    asset=raw['asset']
    if not asset.startswith('/Game/RaftSim/Environment/GeneratedLocalReview/') or any(
            not p or not p.replace('_','').isalnum() for p in asset[1:].split('/')):
        raise ValueError('Only a new regenerable local-review asset is allowed')
    package=root/'unreal/Content'/(asset[6:]+'.uasset')
    saved={}
    keys=('saved_mesh_sha256','saved_source_sha256')
    if any(k in raw for k in keys):
        for k in keys:
            value=raw.get(k)
            if not isinstance(value,str) or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):
                raise ValueError('Both saved terrain package and source hashes required')
            saved[k]=value
        if not package.is_file() or sha(package)!=saved['saved_mesh_sha256']:
            raise ValueError('Saved terrain package changed')
        if raw.get('save_verified_mesh',False):raise ValueError('Saved terrain must not be rewritten')
    elif package.exists():raise ValueError('Terrain import must not overwrite an existing package')
    if type(raw.get('save_verified_mesh',False)) is not bool:raise ValueError('Explicit boolean save policy required')
    return dict(export_directory=directory,asset=asset,package=package,export=export,
        save_verified_mesh=raw.get('save_verified_mesh',False),revision=revision,
        config_sha256=sha(path),export_manifest_sha256=sha(directory/'manifest.json'),**saved)


def native_source(mesh,expected_triangles):
    import unreal
    native=json.loads(unreal.RaftSimGroundSourceLibrary.audit_collision_source(mesh))
    if (native.get('available') is not True or native.get('allow_cpu_access') is not True or
            native.get('triangle_count')!=expected_triangles):
        raise ValueError('Exact CPU collision triangles unavailable')
    return native


def directed_records(vertices,indices):
    """Native float32 corners, cyclic rotation only; preserve winding and XY."""
    if not indices or len(indices)%3:raise ValueError('Complete directed triangles required')
    packed=[]
    for point in vertices:
        if len(point)!=3 or not all(math.isfinite(v) for v in point):raise ValueError('Finite native vertices required')
        packed.append(struct.pack('<3f',*point))
    records=[]
    for start in range(0,len(indices),3):
        ids=indices[start:start+3]
        if any(i<0 or i>=len(packed) for i in ids):raise ValueError('Invalid native vertex index')
        corners=[packed[i] for i in ids]
        first=min(range(3),key=lambda i:corners[i][:8])
        records.append(b''.join(corners[first:]+corners[:first]))
    return sorted(records,key=lambda r:r[:8]+r[12:20]+r[24:32])


def compare_native_records(original,revised,changes,expected_changed_triangles):
    if not original or len(original)!=len(revised):raise ValueError('Native triangle count changed')
    permitted={struct.pack('<2f',*p['before'][:2]):p for p in changes}
    if len(permitted)!=len(changes):raise ValueError('Ambiguous changed source vertices')
    changed_faces=0;changed_xy=set();maximum_error=0.
    for left,right in zip(original,revised):
        for offset in (0,12,24):
            a,b=left[offset:offset+12],right[offset:offset+12]
            if a[:8]!=b[:8]:raise ValueError('Native directed XY/topology changed')
            if a==b:continue
            allowed=permitted.get(a[:8])
            if allowed is None:raise ValueError('Undeclared native height change')
            before,after=struct.unpack('<3f',a),struct.unpack('<3f',b)
            error=max(abs(before[i]-allowed['before'][i]) for i in range(3))
            error=max(error,max(abs(after[i]-allowed['after'][i]) for i in range(3)))
            if error>.001:raise ValueError('Native revised height differs from source')
            maximum_error=max(maximum_error,error);changed_xy.add(a[:8])
        changed_faces+=left!=right
    if changed_faces!=expected_changed_triangles or len(changed_xy)!=len(changes):
        raise ValueError('Native source change coverage mismatch')
    return dict(all_directed_triangles_compared=len(original),changed_triangles=changed_faces,
        changed_source_vertices=len(changed_xy),unmodified_native_corners_bit_exact=True,
        registered_xy_and_winding_bit_exact=True,maximum_source_rounding_error_cm=maximum_error)


def compare_native_meshes(original,revised,probes):
    import unreal
    records=[]
    for mesh in (original,revised):
        if mesh.get_num_sections(0)!=1:raise ValueError('Single source material section required')
        vertices,indices,_,_,_=unreal.ProceduralMeshLibrary.get_section_from_static_mesh(mesh,0,0)
        if len(indices)!=mesh.get_num_triangles(0)*3:raise ValueError('Incomplete native readback')
        records.append(directed_records([(p.x,p.y,p.z) for p in vertices],list(indices)))
    return compare_native_records(*records,probes['terrain_vertex_changes_cm'],probes['changed_triangle_probe_count'])
