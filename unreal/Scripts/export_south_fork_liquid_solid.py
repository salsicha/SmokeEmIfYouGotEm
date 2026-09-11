"""Blender export of the sealed registered crux patch; no changed topography."""
from pathlib import Path
import hashlib
import json
import sys
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
WINDOW_NAME='SouthForkLiquidControlCentered20260909' if '--control-centered' in sys.argv else 'SouthForkLiquidWindow20260908'
SOURCE = ROOT/'unreal/SourceArt/RaftSim'/WINDOW_NAME
manifest = json.loads((SOURCE/'manifest.json').read_text())
source = SOURCE/'collision_solid.npz'
assert hashlib.sha256(source.read_bytes()).hexdigest() == manifest['solid_sha256']
path = SOURCE/'SM_SouthForkLiquidCollisionSolid.fbx'
assert not path.exists(), 'Preserve earlier export evidence'
data = np.load(source)
vertices = data['vertices_local_m'].copy()*100
vertices[:,1] *= -1  # same FBX handedness convention as the full source mesh
faces = data['triangles']
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system='METRIC'
bpy.context.scene.unit_settings.scale_length=.01
mesh = bpy.data.meshes.new('SouthForkExactClippedTopWithExternalSeal')
mesh.from_pydata(vertices.tolist(), [], faces.tolist())
mesh.update()
obj = bpy.data.objects.new('SM_SouthForkLiquidCollisionSolid',mesh)
bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active=obj
obj.select_set(True)
for polygon in mesh.polygons:
    polygon.use_smooth=False
bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},
    global_scale=1.,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
    axis_forward='Y',axis_up='Z',bake_anim=False,add_leaf_bones=False,use_mesh_modifiers=True)
(SOURCE/'fbx_export.json').write_text(json.dumps({
    'fbx_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'solid_sha256': manifest['solid_sha256'], 'triangles': len(faces),
    'vertices': len(vertices), 'expected_local_bounds_cm': [
        (data['vertices_local_m'].min(axis=0)*100).tolist(),
        (data['vertices_local_m'].max(axis=0)*100).tolist()],
    'topology_changed':False, 'production_promoted':False},indent=2)+'\n')
print('Exact registered crux solid exported; no source terrain changed',flush=True)
