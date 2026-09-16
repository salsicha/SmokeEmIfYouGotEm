"""Blender background export of the exact candidate solid; no decimation."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import bpy
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'physics/scripts'))
from rock_corner_normals import corner_normals


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--crease-angle-degrees',type=float,
        help='Opt-in authored shading; retains every source vertex and face')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    source=json.loads(args.manifest.read_text())
    cap=ROOT/source['cap_path'];out=args.output.resolve()
    if not out.is_relative_to(ROOT/'tmp') or out.exists():raise ValueError('Fresh project tmp export required')
    if hashlib.sha256(cap.read_bytes()).hexdigest()!=source['cap_sha256']:raise ValueError('Cap source changed')
    if not source['closed_solid_geometry_verified'] or source['production_promoted']:raise ValueError('Unpromoted closed candidate required')
    with np.load(cap,allow_pickle=False) as data:
        original=data['solid_vertices_m'];faces=data['solid_triangles'];kinds=data['solid_face_kind']
        # Match the retained terrain FBX convention. Unreal import yields
        # east/north mesh axes; the physical actor subsequently reflects Y.
        vertices=original*np.array([100.,-100.,100.])
        reflected_faces=faces[:,[0,2,1]]
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=.01
    mesh=bpy.data.meshes.new('OriginalReturnRockSolid')
    mesh.from_pydata(vertices.tolist(),[],reflected_faces.tolist());mesh.update()
    obj=bpy.data.objects.new('SM_OriginalReturnRockSolid',mesh)
    bpy.context.collection.objects.link(obj);bpy.context.view_layer.objects.active=obj;obj.select_set(True)
    for polygon in mesh.polygons:polygon.use_smooth=False
    shading=None
    if args.crease_angle_degrees is not None:
        normals,shading=corner_normals(vertices,reflected_faces,kinds,args.crease_angle_degrees)
        for polygon in mesh.polygons:polygon.use_smooth=True
        mesh.normals_split_custom_set(normals.reshape(-1,3).tolist())
        # Blender storage is float32; shading may not move or reorder geometry.
        actual=np.array([v.co[:] for v in mesh.vertices],dtype=np.float32)
        actual_faces=np.array([p.vertices[:] for p in mesh.polygons])
        assert np.array_equal(actual,vertices.astype(np.float32))
        assert np.array_equal(actual_faces,reflected_faces)
        shading['source_vertices_sha256']=hashlib.sha256(original.tobytes()).hexdigest()
        shading['source_triangles_sha256']=hashlib.sha256(faces.tobytes()).hexdigest()
        shading['corner_normals_sha256']=hashlib.sha256(normals.tobytes()).hexdigest()
        shading['import_normals_required']=True
    out.mkdir(parents=True)
    path=out/'SM_OriginalReturnRockSolid.fbx'
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},
        global_scale=1.,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
        axis_forward='Y',axis_up='Z',bake_anim=False,add_leaf_bones=False,use_mesh_modifiers=False,
        mesh_smooth_type='OFF')
    report=dict(schema='raftsim.original_return_rock_solid_export.v1',
        cap_manifest=str(args.manifest.resolve().relative_to(ROOT)),source_cap_sha256=source['cap_sha256'],
        fbx=path.relative_to(ROOT).as_posix(),fbx_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        vertex_count=len(vertices),triangle_count=len(faces),
        expected_unreal_bounds_cm=[(original.min(axis=0)*100).tolist(),(original.max(axis=0)*100).tolist()],
        actor_scale=[1,-1,1],all_original_roof_vertices_retained=True,decimated=False,production_promoted=False)
    if shading is not None:report['shading']=shading
    (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
