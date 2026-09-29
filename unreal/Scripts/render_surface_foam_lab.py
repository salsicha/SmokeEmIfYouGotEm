"""Render the analytic foam study, with exact clock and shader-graph checks.

No CFD cache or interacting bubble physics is implied by this renderer.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_surface_foam_lab import coverage


def graph_value(socket, position):
    """Evaluate the actual linked shader math, not a second handwritten map."""
    node = socket.node
    if node.type == 'VALUE':
        return float(socket.default_value)
    if node.type == 'NEW_GEOMETRY' and socket.name == 'Position':
        return position
    if node.type == 'SEPXYZ':
        return input_value(node.inputs[0], position)['XYZ'.index(socket.name)]
    if node.type != 'MATH':
        raise ValueError(f'Unsupported graph node: {node.type}')
    a, b = [input_value(s, position) for s in node.inputs[:2]]
    ops = {'ADD': lambda: a+b, 'SUBTRACT': lambda: a-b,
           'MULTIPLY': lambda: a*b, 'DIVIDE': lambda: a/b,
           'MAXIMUM': lambda: np.maximum(a, b), 'POWER': lambda: a**b}
    return ops[node.operation]()


def input_value(socket, position):
    return (graph_value(socket.links[0].from_socket, position) if socket.is_linked
            else socket.default_value)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--frames', type=int, nargs='+', required=True)
    p.add_argument('--samples', type=int, default=48)
    p.add_argument('--width', type=int, default=960)
    args = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    setup = json.loads((Path(bpy.data.filepath).parent/'setup.json').read_text())
    if setup['case'] not in ('surface-foam', 'surface-bubble'):
        raise ValueError('Expected standalone surface foam scene')
    args.output.mkdir(parents=True, exist_ok=False)
    scene = bpy.context.scene
    mat = bpy.data.materials['Transported effective foam volume']
    nodes = mat.node_tree.nodes
    clock = nodes['Physical time seconds'].outputs[0]
    density = next(n for n in nodes if n.type == 'VOLUME_SCATTER').inputs['Density']
    trajectories = None
    if setup['case'] == 'surface-bubble':
        from build_surface_bubble_lab import install_animation_and_lighting
        root = Path(bpy.data.filepath).parent
        raw = (root/'trajectories.json').read_bytes()
        audit = json.loads((root/'contact-audit.json').read_text())
        if hashlib.sha256(raw).hexdigest() != audit['trajectory_sha256']:
            raise ValueError('Audited trajectories were changed')
        trajectories = json.loads(raw)['positions_xy_m']
        install_animation_and_lighting(trajectories)
        # Validate native timeline playback before explicit per-frame updates.
        for frame in (1, 17, 37, 59, 73):
            scene.frame_set(frame)
            for i, xy in enumerate(trajectories[frame-1]):
                got = bpy.data.objects[f'Bubble cap {i:04d}'].location
                if np.linalg.norm(np.array(got[:2])-xy) > 1e-7:
                    raise RuntimeError('Native timeline differs from audited trajectories')
        scene.frame_set(1)
        native_blend = (args.output/'feature.blend').resolve()
        bpy.ops.wm.save_as_mainfile(filepath=str(native_blend))
        (args.output/'trajectories.json').write_bytes(raw)
        (args.output/'contact-audit.json').write_text(json.dumps(audit, indent=2))
        native_setup = dict(setup, blend=str(native_blend), native_timeline_verified=True)
        (args.output/'setup.json').write_text(json.dumps(native_setup, indent=2))
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    if not any(d.type == 'OPTIX' for d in prefs.devices):
        raise RuntimeError('OptiX device unavailable')
    for d in prefs.devices:
        d.use = d.type == 'OPTIX'
    scene.cycles.device = 'GPU'
    scene.cycles.samples = args.samples
    scene.render.resolution_x = args.width
    scene.render.resolution_y = round(args.width*9/16)
    rows = []
    for frame in args.frames:
        if not 1 <= frame <= setup['frames']:
            raise ValueError('Frame out of range')
        scene.frame_set(frame)
        seconds = (frame-1)/setup['fps']
        clock.default_value = seconds
        if trajectories is not None:
            for i, xy in enumerate(trajectories[frame-1]):
                got = bpy.data.objects[f'Bubble cap {i:04d}'].location
                if np.linalg.norm(np.array(got[:2])-xy) > 1e-7:
                    raise RuntimeError('Rendered native timeline differs from audited trajectory')
        bpy.context.view_layer.update()
        rng = np.random.default_rng(3401)
        x = rng.uniform(.07, .23, 2048)
        y = rng.uniform(-.03, .025, 2048)
        z = rng.uniform(.025, .028, 2048)
        h = (z-.025)/.003
        reference = 1800*coverage(x, y, seconds)*6*h*(1-h)
        actual = input_value(density, (x, y, z))
        error = float(np.max(np.abs(actual-reference)))
        if error > .02:
            raise RuntimeError(f'Shader/reference mismatch {error}')
        start = time.monotonic()
        image = (args.output/f'frame-{frame:04d}.png').resolve()
        scene.render.filepath = str(image)
        bpy.ops.render.render(write_still=True)
        rows.append(dict(frame=frame, seconds=seconds, image=str(image),
                         sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                         render_seconds=time.monotonic()-start,
                         shader_density_max_error_per_m=error if trajectories is None else None,
                         native_bubble_positions_verified=trajectories is not None))
        report = dict(complete=len(rows)==len(args.frames), simulation_fps=setup['fps'],
                      frames=rows, source_blend=bpy.data.filepath,
                      model=setup['model'], limitations=setup['limitations'],
                      physical_accuracy_accepted=False, visual_accuracy_accepted=False,
                      graph_audit_scope='Linked math equivalence at world-space sample points; not a GPU optical or physical foam validation.')
        (args.output/'frames.json').write_text(json.dumps(report, indent=2))
        print('FOAM_FRAME', json.dumps(rows[-1]), flush=True)


if __name__ == '__main__':
    main()
