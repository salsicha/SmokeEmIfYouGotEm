"""Prepare a closed pool with a submerged piston driving a transient upwelling.

Synthetic boundary-forced experiment, not an accepted natural boil or a
reproduction of a measured vortex-ring experiment. No animated water mesh.
"""
import argparse
import json
import math
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_water_feature_lab import box, solid, material, aim


def piston_top(frame):
    phase = min(1., max(0., (frame-25)/12))
    return .1+.24*.5*(1-math.cos(math.pi*phase))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--resolution', type=int, default=80)
    parser.add_argument('--frames', type=int, default=144)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if not 64 <= args.resolution <= 160 or not 72 <= args.frames <= 240:
        parser.error('Use resolution 64..160 and frames 72..240')
    args.output.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.gravity = (0., 0., -9.80665)
    scene.render.fps = 24
    scene.frame_end = args.frames
    stone = material('Warm neutral stone', (.26, .235, .195), .8)
    solid('Pool floor', (-.15, -1.65, -.25), (3.15, 1.65, 0.), stone)
    solid('Far wall', (-.15, 1.5, 0.), (3.15, 1.65, .85), stone)
    # Side/front walls are domain collision boundaries, invisible for viewing.
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=.35, depth=.5,
                                       location=(1.5, 0., -.15))
    piston = bpy.context.object
    piston.name = 'Submerged displacement piston'
    piston.data.materials.append(stone)
    piston.modifiers.new('Moving physical solid', 'FLUID').fluid_type = 'EFFECTOR'
    initial = box('Initially still pool', (.015, -1.485, .015), (2.985, 1.485, .60))
    cut = initial.modifiers.new('Exclude piston from initial water', 'BOOLEAN')
    cut.operation = 'DIFFERENCE'
    cut.solver = 'EXACT'
    cut.object = piston
    bpy.context.view_layer.objects.active = initial
    bpy.ops.object.modifier_apply(modifier=cut.name)
    flow = initial.modifiers.new('Initial pool only; no continuous inlet', 'FLUID')
    flow.fluid_type = 'FLOW'
    flow.flow_settings.flow_type = 'LIQUID'
    flow.flow_settings.flow_behavior = 'GEOMETRY'
    initial.hide_render = True
    # Sample the cosine piston stroke every simulation frame. Linear segments
    # prevent keyframe-handle overshoot; it remains well below the free surface.
    for frame in range(1, args.frames+1):
        piston.location.z = piston_top(frame)-.25
        piston.keyframe_insert(data_path='location', frame=frame)
    action = piston.animation_data.action
    for layer in action.layers:
        for strip in layer.strips:
            bag = strip.channelbag(piston.animation_data.action_slot)
            for curve in bag.fcurves:
                for key in curve.keyframe_points:
                    key.interpolation = 'LINEAR'
    scene.frame_set(1)
    domain = box('Feature liquid', (0., -1.5, -.1), (3., 1.5, 2.8))
    mod = domain.modifiers.new('3D FLIP water', 'FLUID')
    mod.fluid_type = 'DOMAIN'
    s = mod.domain_settings
    s.domain_type = 'LIQUID'
    s.resolution_max = args.resolution
    s.cache_type = 'ALL'
    s.cache_frame_start, s.cache_frame_end = 1, args.frames
    s.cache_directory = str((args.output/'cache').resolve())
    s.cache_resumable = True
    s.flip_ratio = .95
    s.use_mesh = True
    s.mesh_scale = 2
    s.use_spray_particles = s.use_foam_particles = s.use_bubble_particles = True
    s.use_adaptive_timesteps = True
    s.timesteps_min, s.timesteps_max, s.cfl_condition = 2, 8, 2.
    s.use_fractions = False
    s.use_collision_border_top = False
    water = material('Clear water IOR 1.333', (.88, .98, .97), .075, 1.)
    absorb = water.node_tree.nodes.new('ShaderNodeVolumeAbsorption')
    absorb.inputs['Color'].default_value = (.36, .77, .70, 1.)
    absorb.inputs['Density'].default_value = .32
    water.node_tree.links.new(absorb.outputs['Volume'], water.node_tree.nodes.get('Material Output').inputs['Volume'])
    domain.data.materials.append(water)
    for polygon in domain.data.polygons:
        polygon.use_smooth = True
    foam = material('Secondary whitewater approximation', (.93, .96, .95), .45)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1., location=(0., 0., -20.))
    particle = bpy.context.object
    particle.name = 'Subgrid whitewater render instance'
    particle.data.materials.append(foam)
    for ps in domain.particle_systems:
        if any(name in ps.name.lower() for name in ('foam', 'spray', 'bubble')):
            ps.settings.render_type = 'OBJECT'
            ps.settings.instance_object = particle
            ps.settings.particle_size = .012
            ps.settings.size_random = .5
        else:
            ps.settings.render_type = 'NONE'
    stage = box('Studio floor', (-200., -200., -.4), (200., 200., -.3))
    stage.data.materials.append(material('Backdrop', (.10, .13, .16), .85))
    scene.world = bpy.data.worlds.new('Soft studio sky')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.6, .72, .9, 1.)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .45
    for name, pos, energy in [('Key', (0., -3., 7.), 1600), ('Rim', (3., 3., 5.), 2200)]:
        bpy.ops.object.light_add(type='AREA', location=pos)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy, lamp.data.size = energy, 4.
        aim(lamp, (1.5, 0., .6))
    bpy.ops.object.camera_add(location=(4.5, -5., 5.5))
    scene.camera = bpy.context.object
    aim(scene.camera, (1.5, 0., .55))
    scene.camera.data.type = 'ORTHO'
    scene.camera.data.ortho_scale = 4.9
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = 960, 540
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    bpy.ops.object.select_all(action='DESELECT')
    domain.select_set(True)
    bpy.context.view_layer.objects.active = domain
    blend = (args.output/'feature.blend').resolve()
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    report = dict(case='boil', experiment='submerged-piston transient upwelling',
        source_script=str(Path(__file__).resolve()), blend=str(blend), blender_version=bpy.app.version_string,
        dimensions_m=[3., 3., 2.9], resolution=args.resolution, approximate_cell_m=3/args.resolution,
        frames=args.frames, fps=24, gravity_mps2=9.80665, initial_depth_m=.60,
        piston_center_xy_m=[1.5, 0.], piston_radius_m=.35, piston_top_initial_m=.10,
        piston_stroke_m=.24, piston_stroke_frames=[25, 37],
        piston_displaced_volume_m3=math.pi*.35**2*.24,
        inlet=None, outlet=None, initial_transient=True, fractional_obstacles=False,
        physical_accuracy_accepted=False, visual_accuracy_accepted=False, game_integrated=False,
        boundaries='Closed pool; submerged cosine-stroke solid; no liquid source/sink after initial fill.',
        limitations='Synthetic transient upwelling, not measured natural boil or validated vortex-ring experiment. Moving-solid coupling, radial surface divergence, mass conservation, wall reflections and subgrid whitewater require checks.')
    (args.output/'setup.json').write_text(json.dumps(report, indent=2))
    print('BOIL_PREPARED', json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
