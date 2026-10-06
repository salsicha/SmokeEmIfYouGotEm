"""Reopen native control, audit full/half poses and render without caption shadows."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
import bpy
import numpy as np


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    source = Path(bpy.data.filepath)
    root = source.parent
    raw = json.loads((root/'trajectories.json').read_text())
    dynamics = json.loads((root/'dynamics.json').read_text())
    if args.output.exists() or digest(source) != dynamics['source_blend_sha256']:
        raise ValueError('Fresh render and unchanged audited native scene required')
    scene = bpy.context.scene
    assert scene.render.fps == 24 and scene.frame_end == 49
    worst, half_residual = 0., 0.
    for frame in np.arange(1., 49.5, .5):
        whole, fraction = int(frame), frame-int(frame)
        scene.frame_set(whole, subframe=fraction)
        for label, key, center in [('Corrected', 'corrected', [-.044, 0., .031]),
                                   ('Projection only', 'projection_only', [.044, 0., .031])]:
            for index in range(4):
                obj = bpy.data.objects[f'{label} marker {index}']
                first = np.array(raw[key][whole-1]['positions'][index])
                expected = first if not fraction else (first+raw[key][whole]['positions'][index])/2
                position = np.array(obj.matrix_world.translation)-center
                worst = max(worst, float(np.linalg.norm(position-expected)))
                half_residual = max(half_residual, abs(np.linalg.norm(position)-.03))
    assert worst < 1e-8
    args.output.mkdir(parents=True, exist_ok=False)
    audit = dict(complete=True, accepted=False, saved_scene_reopened=True,
                 full_and_half_poses_checked=97, markers=8, maximum_position_error_m=worst,
                 maximum_half_frame_constraint_error_m=half_residual,
                 source_blend_sha256=digest(source), trajectories_sha256=digest(root/'trajectories.json'),
                 scope='Native full/half-frame timeline equals numerical trajectories. Linear chord interpolation is not exactly on the surface; deviation is reported. Not wet foam, liquid dynamics or optical acceptance.')
    (args.output/'native-animation-audit.json').write_text(json.dumps(audit, indent=2))
    for obj in bpy.data.objects:
        if obj.type == 'FONT':
            obj.visible_shadow = False
            obj.visible_diffuse = False
            obj.visible_glossy = False
            obj.visible_transmission = False
    rows = []
    original = json.loads((root/'frames.json').read_text())
    report = dict(original, complete=False, frames=rows, diagnostics_only=True,
        caption_render_correction='Caption objects visible to camera only, no cast shadows/reflections. No simulation/marker/sphere/camera/light geometry change.',
        native_animation_audit_sha256=digest(args.output/'native-animation-audit.json'))
    for frame in range(1, 48, 2):
        if shutil.disk_usage(args.output).free < 1024**3:
            raise RuntimeError('Disk reserve reached; partial render preserved')
        scene.frame_set(frame)
        image = (args.output/f'frame-{frame:04d}.png').resolve()
        scene.render.filepath = str(image)
        start = time.monotonic()
        bpy.ops.render.render(write_still=True)
        rows.append(dict(frame=frame, image=str(image), sha256=digest(image),
                         render_seconds=time.monotonic()-start))
        report['complete'] = len(rows) == 24
        (args.output/'frames.json').write_text(json.dumps(report, indent=2))
        print('MANIFOLD_VERIFIED_FRAME', json.dumps(rows[-1]), flush=True)
    assert digest(source) == audit['source_blend_sha256']
    print('REOPENED_MANIFOLD_AUDIT', json.dumps(audit), flush=True)


if __name__ == '__main__':
    main()
