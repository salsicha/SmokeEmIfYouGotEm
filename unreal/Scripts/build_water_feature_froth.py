"""Prepare a standalone finite plunging-jet pulse into a closed impact tank.

Actual 3D FLIP liquid; subgrid foam/bubbles/spray are not resolved air volume.
No pre-authored splash, cavity or froth animation.
"""
import argparse
import json
import math
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_water_feature_lab import box, solid, flow, material, aim


def nozzle_mesh():
    verts, faces = [], []
    n = 64
    for z, r in ((1.45, .15), (1.45, .19), (1.75, .15), (1.75, .19)):
        verts.extend((1+r*math.cos(j*2*math.pi/n), r*math.sin(j*2*math.pi/n), z) for j in range(n))
    for j in range(n):
        k = (j+1) % n
        faces.extend(((j, k, n+k, n+j), (2*n+j, 3*n+j, 3*n+k, 2*n+k),
                      (j, 2*n+j, 2*n+k, k), (n+j, n+k, 3*n+k, 3*n+j)))
    mesh = bpy.data.meshes.new('Hollow nozzle shared render collider')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    return mesh


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--resolution', type=int, default=96)
    p.add_argument('--frames', type=int, default=120)
    p.add_argument('--fractional-obstacles', action='store_true',
                   help='Controlled solver boundary comparison; no geometry or inlet change')
    p.add_argument('--liquid-particle-radius', type=float, default=1.,
                   help='Primary liquid reconstruction radius in cell units, not mesh or optical radius')
    args = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    if not 80 <= args.resolution <= 160 or not 96 <= args.frames <= 168:
        p.error('Use resolution 80..160 and frames 96..168')
    if not .75 <= args.liquid_particle_radius <= 1.25:
        p.error('Use liquid particle radius .75..1.25 for controlled comparisons')
    args.output.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.gravity = (0., 0., -9.80665)
    scene.render.fps, scene.frame_end = 24, args.frames
    stone = material('Neutral impact tank', (.22, .24, .25), .65)
    solid('Pool floor', (-.15, -.95, -.25), (2.15, .95, 0.), stone)
    solid('Far wall', (-.15, .8, 0.), (2.15, .95, .85), stone)
    # Three side walls use closed domain collision boundaries, invisible for
    # an unobstructed view of impact and the entrained-particle cloud.
    flow('Initially still pool', (.02, -.78, .02), (1.98, .78, .35), 'GEOMETRY')
    tube = bpy.data.objects.new('Hollow inlet nozzle', nozzle_mesh())
    bpy.context.collection.objects.link(tube)
    tube.data.materials.append(material('Nozzle ceramic', (.08, .10, .12), .35))
    tube.modifiers.new('Shared physical nozzle', 'FLUID').fluid_type = 'EFFECTOR'
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=.145, depth=.23,
                                       location=(1., 0., 1.535))
    source = bpy.context.object
    source.name = 'Finite downward jet source'
    mod = source.modifiers.new('Prescribed new-liquid velocity only', 'FLUID')
    mod.fluid_type = 'FLOW'
    settings = mod.flow_settings
    settings.flow_type, settings.flow_behavior = 'LIQUID', 'INFLOW'
    settings.use_initial_velocity = True
    settings.velocity_coord = (0., 0., -1.8)
    settings.surface_distance = .5
    for frame, enabled in ((1, True), (72, True), (73, False), (args.frames, False)):
        settings.use_inflow = enabled
        settings.keyframe_insert(data_path='use_inflow', frame=frame)
    source.hide_render = True
    scene.frame_set(1)
    domain = box('Feature liquid', (0., -.8, -.1), (2., .8, 2.8))
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
    s.use_fractions = args.fractional_obstacles
    s.particle_radius = args.liquid_particle_radius
    s.use_collision_border_top = False
    water = material('Clear water IOR 1.333', (.98, .995, 1.), .035, 1.)
    absorb = water.node_tree.nodes.new('ShaderNodeVolumeAbsorption')
    absorb.inputs['Color'].default_value = (.65, .85, .88, 1.)
    absorb.inputs['Density'].default_value = .12
    water.node_tree.links.new(absorb.outputs['Volume'], water.node_tree.nodes.get('Material Output').inputs['Volume'])
    domain.data.materials.append(water)
    for poly in domain.data.polygons:
        poly.use_smooth = True
    foam = material('Secondary whitewater approximation', (.93, .96, .95), .45)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1., location=(0., 0., -20.))
    instance = bpy.context.object
    instance.name = 'Subgrid whitewater render instance'
    instance.data.materials.append(foam)
    for ps in domain.particle_systems:
        if ps.name.lower() in ('foam', 'spray', 'bubbles'):
            ps.settings.render_type = 'OBJECT'
            ps.settings.instance_object = instance
            ps.settings.particle_size = .002
            ps.settings.size_random = .5
        else:
            ps.settings.render_type = 'NONE'
    stage = box('Studio floor', (-20., -20., -.4), (20., 20., -.3))
    stage.data.materials.append(material('Backdrop', (.10, .13, .16), .85))
    scene.world = bpy.data.worlds.new('Soft studio sky')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.6, .72, .9, 1.)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .45
    for name, loc, energy, size in [('Key', (0., -3., 5.), 800, 3.), ('Rim', (2., 3., 4.), 1000, 3.)]:
        bpy.ops.object.light_add(type='AREA', location=loc)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy, lamp.data.size = energy, size
        aim(lamp, (1., 0., .6))
    bpy.ops.object.camera_add(location=(3.1, -4., 2.6))
    scene.camera = bpy.context.object
    aim(scene.camera, (1., 0., .7))
    scene.camera.data.type, scene.camera.data.ortho_scale = 'ORTHO', 3.25
    scene.render.engine = 'CYCLES'
    scene.cycles.samples, scene.cycles.use_denoising = 48, True
    scene.render.resolution_x, scene.render.resolution_y = 960, 540
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    bpy.ops.object.select_all(action='DESELECT')
    domain.select_set(True)
    bpy.context.view_layer.objects.active = domain
    blend = (args.output/'feature.blend').resolve()
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    report = dict(case='froth', experiment='finite circular plunging jet into closed pool',
                  blend=str(blend), source_script=str(Path(__file__).resolve()),
                  blender_version=bpy.app.version_string, dimensions_m=[2., 1.6, 2.9],
                  resolution=args.resolution, approximate_cell_m=2.9/args.resolution,
                  frames=args.frames, fps=24, initial_depth_m=.35,
                  jet_center_xy_m=[1., 0.], emitter_radius_m=.145,
                  emitter_z_bounds_m=[1.42, 1.65], nozzle_inner_radius_m=.15,
                  nozzle_outer_radius_m=.19, nozzle_z_bounds_m=[1.45, 1.75],
                  inlet_velocity_mps=[0., 0., -1.8], inflow_frames=[1, 72],
                  nominal_flux_m3s=math.pi*.145**2*1.8, actual_flux_measured=False,
                  gravity_mps2=9.80665, outlet=None, fractional_obstacles=args.fractional_obstacles,
                  liquid_particle_radius_cells=float(s.particle_radius),
                  physical_accuracy_accepted=False, visual_accuracy_accepted=False,
                  boundaries='Closed bottom/sides, open top; finite inflow. Front/side collision boundaries invisible. Pool level rises; no fixed-head drain.',
                  limitations='Synthetic startup/pulse experiment, not measured jet or calibrated CFD. No resolved gas phase, film breakup or air-volume fraction. Secondary particles are heuristic samples; number and radius are not measured bubble population. Boundary and nozzle voxelization, mass budget and resolution dependence remain open.')
    (args.output/'setup.json').write_text(json.dumps(report, indent=2))
    print('FROTH_PREPARED', json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
