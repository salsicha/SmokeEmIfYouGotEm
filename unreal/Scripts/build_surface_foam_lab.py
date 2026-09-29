"""Standalone passive surface-foam transport/optics control in analytic shear.

Exact prescribed velocity u=(U+G*y,0,0), not a FLIP bake or interacting foam.
The inverse material map transports the effective density field.
"""
import argparse
import json
from pathlib import Path
import sys

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_water_feature_lab import box, material, aim

SPEED = .018
SHEAR = .75


def rest_position(x, y, seconds):
    return x-(SPEED+SHEAR*y)*seconds, y


def coverage(x, y, seconds):
    x, y = rest_position(x, y, seconds)
    q = ((x-.115)/.028)**2+((y+.005)/.018)**2
    return np.maximum(1-q, 0)**2


def audit():
    # Finite-domain integral and moments, independent of the shader graph.
    # Refine quadrature to distinguish integration error from lost material.
    runs = []
    for nx, ny in ((600, 240), (1200, 480)):
        x = (np.arange(nx)+.5)*.3/nx
        y = (np.arange(ny)+.5)*.12/ny-.06
        xx, yy = np.meshgrid(x, y)
        rows = []
        for seconds in (0., .75, 1.5, 2.25, 3.):
            c = coverage(xx, yy, seconds)
            area = c.sum()*.3/nx*.12/ny
            rows.append(dict(seconds=seconds, weighted_area_m2=float(area),
                centroid_xy_m=[float(np.sum(c*xx)/c.sum()), float(np.sum(c*yy)/c.sum())],
                boundary_max=float(max(c[0].max(), c[-1].max(), c[:, 0].max(), c[:, -1].max()))))
        runs.append(dict(grid=[nx, ny], frames=rows,
            relative_area_range=float(np.ptp([r['weighted_area_m2'] for r in rows])/rows[0]['weighted_area_m2'])))
    exact_area = np.pi*.028*.018/3
    error = max(abs(r['weighted_area_m2']/exact_area-1) for run in runs for r in run['frames'])
    centroid_error = max(np.linalg.norm(np.array(r['centroid_xy_m'])-
                         [.115+(SPEED+SHEAR*(-.005))*r['seconds'], -.005]) for run in runs for r in run['frames'])
    if error > 1e-4 or centroid_error > 1e-5 or any(r['boundary_max'] for run in runs for r in run['frames']):
        raise RuntimeError('Analytic transport/conservation check failed')
    return dict(passed=True, exact_weighted_area_m2=exact_area, quadrature=runs,
                maximum_relative_area_error=float(error), maximum_centroid_error_m=float(centroid_error),
                map_determinant=1., scope='Prescribed passive density transport only; not physical foam dynamics or optical validation.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    report = audit()
    args.output.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.render.fps, scene.frame_end = 24, 73
    tray_mat = material('Dark neutral ceramic', (.065, .075, .078), .65)
    box('Tray bottom', (0., -.06, -.007), (.3, .06, 0.)).data.materials.append(tray_mat)
    for name, lo, hi in [('Far shear boundary', (0., .06, 0.), (.3, .065, .035)),
                         ('Near shear boundary', (0., -.065, 0.), (.3, -.06, .035))]:
        box(name, lo, hi).data.materials.append(tray_mat)
    water_mat = material('Water dielectric', (1., 1., 1.), .025, 1.)
    water = box('Flat free surface water', (0., -.06, 0.), (.3, .06, .025))
    water.data.materials.append(water_mat)
    foam = box('Passive foam layer', (.001, -.059, .025), (.299, .059, .028))
    mat = bpy.data.materials.new('Transported effective foam volume')
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    pos = nodes.new('ShaderNodeNewGeometry')
    split = nodes.new('ShaderNodeSeparateXYZ')
    links.new(pos.outputs['Position'], split.inputs[0])
    clock = nodes.new('ShaderNodeValue')
    clock.name = 'Physical time seconds'

    def calc(op, a, b=None):
        node = nodes.new('ShaderNodeMath')
        node.operation = op
        for idx, value in enumerate((a,) if b is None else (a, b)):
            if isinstance(value, (int, float)):
                node.inputs[idx].default_value = value
            else:
                links.new(value, node.inputs[idx])
        return node.outputs[0]

    u = calc('ADD', SPEED, calc('MULTIPLY', SHEAR, split.outputs['Y']))
    rest_x = calc('SUBTRACT', split.outputs['X'], calc('MULTIPLY', u, clock.outputs[0]))
    rx = calc('DIVIDE', calc('SUBTRACT', rest_x, .115), .028)
    ry = calc('DIVIDE', calc('ADD', split.outputs['Y'], .005), .018)
    q = calc('ADD', calc('MULTIPLY', rx, rx), calc('MULTIPLY', ry, ry))
    c = calc('POWER', calc('MAXIMUM', calc('SUBTRACT', 1., q), 0.), 2.)
    # A normalized vertical profile keeps a fixed integrated layer thickness.
    h = calc('DIVIDE', calc('SUBTRACT', split.outputs['Z'], .025), .003)
    profile = calc('MULTIPLY', 6., calc('MULTIPLY', h, calc('SUBTRACT', 1., h)))
    # Effective coefficients are explicit study parameters, not inferred air
    # fraction or resolved individual bubbles. No decorative texture motion.
    density = calc('MULTIPLY', 1800., calc('MULTIPLY', c, profile))
    scatter = nodes.new('ShaderNodeVolumeScatter')
    scatter.inputs['Color'].default_value = (.97, .985, 1., 1.)
    scatter.inputs['Anisotropy'].default_value = .35
    links.new(density, scatter.inputs['Density'])
    links.new(scatter.outputs[0], output.inputs['Volume'])
    foam.data.materials.append(mat)
    for frame in (1, 73):
        clock.outputs[0].default_value = (frame-1)/24
        clock.outputs[0].keyframe_insert('default_value', frame=frame)
    # Rendering sets the exact clock each frame, so no interpolation assumption
    # is needed even if animation interpolation defaults change in Blender.
    scene.world = bpy.data.worlds.new('Soft studio')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.6, .7, .85, 1.)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .3
    for name, loc, energy, size in [('Key', (.07, -.2, .35), 12., .3), ('Rim', (.2, .18, .25), 8., .2)]:
        bpy.ops.object.light_add(type='AREA', location=loc)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy, lamp.data.size = energy, size
        aim(lamp, (.15, 0., .025))
    backdrop = box('Studio floor', (-2., -2., -.014), (2., 2., -.008))
    backdrop.data.materials.append(material('Backdrop', (.11, .13, .16), .8))
    bpy.ops.object.camera_add(location=(.28, -.34, .45))
    scene.camera = bpy.context.object
    aim(scene.camera, (.15, 0., .025))
    scene.camera.data.type = 'ORTHO'
    scene.camera.data.ortho_scale = .36
    scene.camera.data.lens = 50
    scene.camera.data.clip_start = .0001
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = 960, 540
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.frame_set(1)
    blend = (args.output/'feature.blend').resolve()
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    (args.output/'transport-audit.json').write_text(json.dumps(report, indent=2))
    setup = dict(case='surface-foam', blend=str(blend), source_script=str(Path(__file__).resolve()),
        dimensions_m=[.3, .12, .025], layer_thickness_m=.003, effective_scattering_peak_per_m=1800.,
        scattering_anisotropy=.35, speed_mps=SPEED, shear_per_s=SHEAR, fps=24, frames=73,
        physical_accuracy_accepted=False, visual_accuracy_accepted=False,
        model='Analytic incompressible plane shear and passively advected effective foam density',
        boundaries='Idealized driven lateral shear, streamwise open; flat surface and free-slip bottom. Patch remains inside rendered bounds.',
        limitations='Not an interacting bubble raft or two-way foam/water simulation. No formation, merging, bursting, drainage, rupture or surface-tension dynamics. Optical coefficients uncalibrated; first continuum transport/optics control.')
    (args.output/'setup.json').write_text(json.dumps(setup, indent=2))
    print('FOAM_TRANSPORT_PREPARED', json.dumps(setup), flush=True)
    print('TRANSPORT_AUDIT', json.dumps({k:v for k,v in report.items() if k != 'quadrature'}), flush=True)


if __name__ == '__main__':
    main()
