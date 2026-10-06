"""Reopenable native-timeline verification; not a dynamic-foam acceptance test."""
import hashlib
import json
from pathlib import Path
import bpy
import numpy as np

root=Path(bpy.data.filepath).parent
out=root/'native-animation-audit.json'
if out.exists():
    raise FileExistsError(out)
setup=json.loads((root/'setup.json').read_text())
assert setup['geometry_model']=='nonlinear-young-laplace'
names=('Water with actual gas cavity','Bubble film')
def mesh_hash(obj):
    data=np.empty(len(obj.data.vertices)*3,dtype=np.float32)
    obj.data.vertices.foreach_get('co',data)
    return hashlib.sha256(data.tobytes()).hexdigest()
original={name:mesh_hash(bpy.data.objects[name]) for name in names}
worst=0.
for frame in range(1,74):
    bpy.context.scene.frame_set(frame)
    expected=-.0015+setup['drift_velocity_mps']*(frame-1)/setup['fps']
    for name in names:
        obj=bpy.data.objects[name]
        worst=max(worst,float(np.linalg.norm(np.array(obj.matrix_world.translation)-[expected,0.,0.])))
        np.testing.assert_allclose(obj.scale,(1,1,1),atol=0,rtol=0)
        np.testing.assert_allclose(obj.rotation_euler,(0,0,0),atol=0,rtol=0)
        assert not obj.modifiers and not obj.data.shape_keys
        assert mesh_hash(obj)==original[name]
assert worst<1e-9
result=dict(saved_scene_reopened=True,frames_verified=73,maximum_translation_error_m=worst,
            unchanged_mesh_sha256=original,velocity_mps=setup['drift_velocity_mps'],
            water_and_film_share_translation=True,accepted=False,
            scope='Native uniform translation of unchanged solved interfaces; not birth, gathering, deformation, drainage or rupture.')
out.write_text(json.dumps(result,indent=2))
print('NATIVE_EQUILIBRIUM_ANIMATION',json.dumps(result),flush=True)
