"""Render every native pair pose at its reference-condition physical clock."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
import bpy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    blend = Path(bpy.data.filepath)
    root = blend.parent
    setup = json.loads((root/'setup.json').read_text())
    migration = json.loads((root/'migration.json').read_text())
    audit = json.loads((root/'native-animation-audit.json').read_text())
    assert setup['case'] == 'bubble-pair-reference' and audit['saved_scene_checked']
    assert len(audit['evaluated_poses']) == 2*len(migration['frames'])-1
    scene = bpy.context.scene
    assert scene.render.fps == migration['fps'] and scene.render.fps_base == 1
    assert scene.frame_start == 1 and scene.frame_end == len(migration['frames'])
    if shutil.disk_usage(root).free < 1024**3:
        raise RuntimeError('Less than 1 GiB disk reserve; no render started')
    args.output.mkdir(parents=True, exist_ok=False)
    for filename in ('feature.blend', 'migration.json', 'native-animation-audit.json'):
        shutil.copyfile(root/filename, args.output/filename)
    setup['blend'] = str((args.output/'feature.blend').resolve())
    (args.output/'setup.json').write_text(json.dumps(setup, indent=2))
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    if not any(device.type == 'OPTIX' for device in prefs.devices):
        raise RuntimeError('OptiX unavailable')
    for device in prefs.devices:
        device.use = device.type == 'OPTIX'
    scene.cycles.device = 'GPU'
    frames = []
    report = dict(complete=False, simulation_fps=migration['fps'], frames=frames,
                  source_blend_sha256=hashlib.sha256(blend.read_bytes()).hexdigest(),
                  model=setup['model'], limitations=setup['limitations'],
                  physical_accuracy_accepted=False, visual_accuracy_accepted=False)
    (args.output/'frames.json').write_text(json.dumps(report, indent=2))
    for row in migration['frames']:
        if shutil.disk_usage(args.output).free < 1024**3:
            raise RuntimeError('Disk reserve reached; preserve partial frames')
        scene.frame_set(row['frame'])
        image = (args.output/f'frame-{row["frame"]:04d}.png').resolve()
        scene.render.filepath = str(image)
        start = time.monotonic()
        bpy.ops.render.render(write_still=True)
        frames.append(dict(frame=row['frame'], seconds=row['seconds'], image=str(image),
                           sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                           render_seconds=time.monotonic()-start))
        report['complete'] = len(frames) == len(migration['frames'])
        (args.output/'frames.json').write_text(json.dumps(report, indent=2))
        print('PAIR_CLIP_FRAME', json.dumps(frames[-1]), flush=True)


if __name__ == '__main__':
    main()
