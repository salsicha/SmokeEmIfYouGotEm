"""Native uniform-advection check of the solved bubble, not interacting foam.

The equilibrium water boundary and film translate together at 1 mm/s.
This tests a prescribed uniform-flow/Galilean translation only. The stationary
floor is a visual reference, not a simulated no-slip boundary. No birth,
capillary gathering, drainage or rupture is implied.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
import bpy


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    args = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    root = Path(bpy.data.filepath).parent
    setup = json.loads((root/'setup.json').read_text())
    if setup.get('geometry_model') != 'nonlinear-young-laplace':
        raise ValueError('Solved equilibrium scene required')
    if shutil.disk_usage(root).free < 1024**3:
        raise RuntimeError('Less than 1 GiB disk reserve; no render started')
    args.output.mkdir(parents=True,exist_ok=False)
    scene = bpy.context.scene
    scene.render.fps,scene.frame_end = 24,73
    names = ('Water with actual gas cavity','Bubble film')
    for name in names:
        obj = bpy.data.objects[name]
        if obj.animation_data:
            raise ValueError('Preserve existing animation')
        for frame,x in ((1,-.0015),(73,.0015)):
            obj.location = (x,0.,0.)
            obj.keyframe_insert('location',frame=frame)
        for layer in obj.animation_data.action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:
                            key.interpolation = 'LINEAR'
    error = 0.
    for frame in range(1,74):
        scene.frame_set(frame)
        expected = -.0015+.001*(frame-1)/24
        for name in names:
            got = bpy.data.objects[name].location
            error = max(error,abs(got.x-expected),abs(got.y),abs(got.z))
    if error > 1e-9:
        raise RuntimeError('Native animation is not the prescribed constant translation')
    scene.frame_set(1)
    scene.render.resolution_x,scene.render.resolution_y = 800,450
    scene.cycles.samples = 64
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    if not any(d.type == 'OPTIX' for d in prefs.devices):
        raise RuntimeError('OptiX unavailable')
    for d in prefs.devices:
        d.use = d.type == 'OPTIX'
    scene.cycles.device = 'GPU'
    blend = (args.output/'feature.blend').resolve()
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    for filename in ('equilibrium.json','geometry-audit.json'):
        (args.output/filename).write_bytes((root/filename).read_bytes())
    setup.update(blend=str(blend),frames=73,fps=24,drift_velocity_mps=.001,
                 native_animation_maximum_error_m=error,
                 model='Solved isolated equilibrium under prescribed uniform translation',
                 limitations=setup['limitations'].replace('No animation or CFD claim.','Uniform-advection study only; no CFD, interacting raft, formation or rupture claim.'))
    (args.output/'setup.json').write_text(json.dumps(setup,indent=2))
    rows=[]
    frames=list(range(1,73,2))
    report=dict(complete=False,simulation_fps=24,frames=rows,
                model=setup['model'],limitations=setup['limitations'],
                physical_accuracy_accepted=False,visual_accuracy_accepted=False)
    (args.output/'frames.json').write_text(json.dumps(report,indent=2))
    for frame in frames:
        if shutil.disk_usage(args.output).free < 1024**3:
            raise RuntimeError('Render stopped at 1 GiB disk reserve; preserve partial frames')
        scene.frame_set(frame)
        expected=-.0015+.001*(frame-1)/24
        assert all(abs(bpy.data.objects[name].location.x-expected)<1e-9 for name in names)
        image=(args.output/f'frame-{frame:04d}.png').resolve()
        scene.render.filepath=str(image)
        start=time.monotonic()
        bpy.ops.render.render(write_still=True)
        rows.append(dict(frame=frame,seconds=(frame-1)/24,image=str(image),
                         sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                         render_seconds=time.monotonic()-start))
        report['complete']=len(rows)==len(frames)
        (args.output/'frames.json').write_text(json.dumps(report,indent=2))
        print('EQUILIBRIUM_DRIFT_FRAME',json.dumps(rows[-1]),flush=True)


if __name__=='__main__':
    main()
