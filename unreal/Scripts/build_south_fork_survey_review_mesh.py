"""Blender: export the actual captured-geometry candidate, not a visual proxy."""
from pathlib import Path
import json
import hashlib
import argparse
import sys
import bpy
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'physics/scripts'))
from south_fork_mesh_sampling import grid_triangles
from south_fork_geometry_source import geometry_identity, load_registered_mesh
BASE=ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/troublemaker/geometry_candidate'
OUT=ROOT/'unreal/SourceArt/RaftSim/SouthForkSurveyCandidate'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--geometry-dir',type=Path,default=BASE)
    parser.add_argument('--output',type=Path,default=OUT)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    base=args.geometry_dir.resolve();out=args.output.resolve()
    if not base.is_relative_to(ROOT) or not out.is_relative_to(ROOT/'unreal/SourceArt/RaftSim'):
        raise ValueError('Review geometry/export must stay inside the project source-art scope')
    if base!=BASE and (out==OUT or out.exists()):
        raise ValueError('A geometry variant requires a fresh separate export directory')
    source,geometry_path,geometry_sha,registered=geometry_identity(base/'manifest.json',ROOT)
    mesh_path=geometry_path if registered else base/'engine_mesh_source.npz'
    if registered:
        data,sampler=load_registered_mesh(mesh_path)
    else:
        data=np.load(mesh_path)
    out.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    bpy.context.scene.unit_settings.system='METRIC'
    bpy.context.scene.unit_settings.scale_length=.01
    rows,cols=data['z_m'].shape
    # Blender and Unreal differ in handedness. FBX axis conversion below
    # keeps east as +X and maps north to Unreal +Y, with metres -> centimetres.
    vertices=100*np.column_stack([data['east_m'].ravel(),-data['north_m'].ravel(),data['z_m'].ravel()])
    faces=sampler.faces if registered else grid_triangles(rows,cols)
    mesh=bpy.data.meshes.new('TroublemakerCapturedGeometry')
    mesh.from_pydata(vertices.tolist(),[],faces.tolist()); mesh.update()
    obj=bpy.data.objects.new('SM_TroublemakerSurveyCandidate',mesh)
    bpy.context.collection.objects.link(obj); bpy.context.view_layer.objects.active=obj; obj.select_set(True)
    mat=bpy.data.materials.new('SurveyGeometryReview'); mesh.materials.append(mat)
    for polygon in mesh.polygons: polygon.use_smooth=True
    # No decimation or independent rock collision shape: imported collision
    # uses the same triangles as this reconstruction candidate.
    path=out/'SM_TroublemakerSurveyCandidate.fbx'
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},
        global_scale=1.,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
        axis_forward='Y',axis_up='Z',bake_anim=False,add_leaf_bones=False,use_mesh_modifiers=True)
    report={'schema':'raftsim.survey_mesh_export.v1','fbx':path.relative_to(ROOT).as_posix(),
        'fbx_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'source_geometry_sha256':geometry_sha,
        'mesh_source_sha256':hashlib.sha256(mesh_path.read_bytes()).hexdigest(),
        'source_bed_sampling':'registered_triangles' if registered else 'render_triangles',
        'source_geometry_manifest':(base/'manifest.json').relative_to(ROOT).as_posix(),
        'fbx_coordinate_units':'centimetres, baked; independent of reimport unit-conversion preference',
        'vertex_count':len(vertices),'triangle_count':len(faces),
        'expected_unreal_bounds_cm':[[float(data['east_m'].min()*100),float(data['north_m'].min()*100),float(data['z_m'].min()*100)],
            [float(data['east_m'].max()*100),float(data['north_m'].max()*100),float(data['z_m'].max()*100)]],
        'production_promoted':False}
    probes=[]
    interior=np.zeros((rows,cols),dtype=bool); interior[2:-2,2:-2]=True
    for authority in sorted(np.unique(data['authority'])):
        eligible=np.flatnonzero((data['authority'].ravel()==authority)&interior.ravel())
        if not len(eligible):continue
        for index in eligible[np.linspace(0,len(eligible)-1,4).astype(int)]:
            probes.append({'authority':int(authority),'position_cm':[float(data['east_m'].ravel()[index]*100),
                float(data['north_m'].ravel()[index]*100),float(data['z_m'].ravel()[index]*100)]})
    report['collision_probes_cm']=probes
    (out/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
