"""Blender CLI: reproducible tiny 3D liquid cases, separate from game assets.

blender -b -t 6 --python this.py -- --case waterfall --output NEWDIR --bake
Low-resolution initial cases are uncalibrated prototypes, not accepted CFD.
"""
import argparse
import json
from pathlib import Path
import sys
import time
import math

import bpy
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
from liquid_review_geometry import height_volume_geometry


def box(name, lo, hi):
    bpy.ops.mesh.primitive_cube_add(size=1, location=[(a+b)/2 for a, b in zip(lo, hi)])
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = [b-a for a, b in zip(lo, hi)]
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def material(name, color, roughness, transmission=0.):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1.)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Transmission Weight'].default_value = transmission
    bsdf.inputs['IOR'].default_value = 1.333 if transmission else 1.45
    return mat


def flow(name, lo, hi, behavior, velocity=(0., 0., 0.)):
    obj = box(name, lo, hi)
    mod = obj.modifiers.new('Liquid boundary', 'FLUID')
    mod.fluid_type = 'FLOW'
    s = mod.flow_settings
    s.flow_type = 'LIQUID'
    s.flow_behavior = behavior
    s.use_initial_velocity = True
    s.velocity_coord = velocity
    obj.hide_render = True
    return obj


def solid(name, lo, hi, mat):
    obj = box(name, lo, hi)
    obj.data.materials.append(mat)
    mod = obj.modifiers.new('Physical solid', 'FLUID')
    mod.fluid_type = 'EFFECTOR'
    return obj


def aim(obj, target):
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z', 'Y').to_euler()


def height_volume(name, upper, lower, length=2.2, width=1.6):
    vertices, faces = height_volume_geometry([upper, upper], [lower, lower],
                                           length/(len(upper)-1), width)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location.y = -width/2
    return obj


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['waterfall', 'hole', 'standing-wave', 'boulder-pillow', 'eddy'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--resolution', type=int, default=80)
    parser.add_argument('--frames', type=int, default=168)
    parser.add_argument('--tailwater', type=float, help='Explicit downstream level-drain elevation in meters')
    parser.add_argument('--ledge-height', type=float, help='Upstream ledge elevation in meters')
    parser.add_argument('--inlet-speed', type=float, help='Newly emitted liquid velocity; NOT a guaranteed section velocity')
    parser.add_argument('--chute', action='store_true', help='Slope the approach down to the pool bed instead of a free overfall')
    parser.add_argument('--approach-height', type=float, default=0., help='Wave/obstacle approach bed elevation, tapering to zero by x=1.5 m')
    parser.add_argument('--bake', action='store_true')
    parser.add_argument('--fractional-obstacles', action='store_true', help='Use the solver fractional-cell obstacle boundary for a controlled comparison')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.case in ('standing-wave', 'boulder-pillow', 'eddy') and (args.chute or args.ledge_height is not None):
        parser.error('Wave/obstacle cases use an approach bed, not a ledge/chute')
    if not 0. <= args.approach_height <= .8 or (args.approach_height and args.case not in ('standing-wave', 'boulder-pillow', 'eddy')):
        parser.error('Approach height is 0..0.8 m and only applies to wave/obstacle cases')
    if not 48 <= args.resolution <= 160 or not 48 <= args.frames <= 480:
        parser.error('Use bounded resolution 48..160 and 48..480 frames')
    args.output.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.gravity = (0., 0., -9.80665)
    scene.render.fps = 24
    scene.frame_end = args.frames
    is_fall = args.case == 'waterfall'
    is_wave = args.case == 'standing-wave'
    is_pillow = args.case == 'boulder-pillow'
    is_eddy = args.case == 'eddy'
    is_flume = is_wave or is_pillow or is_eddy
    shelf_z = 1.2 if is_fall else .35
    inlet_depth = .32 if is_fall else .3
    inlet_u = 1.6 if is_fall else 3.0
    tailwater_z = .45 if is_fall else .85
    if is_flume:
        shelf_z, inlet_depth, inlet_u, tailwater_z = args.approach_height, .35, 3.2, .5
    if args.ledge_height is not None:
        if not .2 <= args.ledge_height <= 1.5:
            parser.error('Ledge height must be 0.2..1.5 meters')
        shelf_z = args.ledge_height
    if args.inlet_speed is not None:
        if not .5 <= args.inlet_speed <= 5.:
            parser.error('Inlet speed must be 0.5..5 meters per second')
        inlet_u = args.inlet_speed
    if args.tailwater is not None:
        minimum_tailwater = .05 if is_wave else .2
        if not minimum_tailwater <= args.tailwater <= 1.4:
            parser.error(f'Tailwater must be {minimum_tailwater}..1.4 meters for this case')
        tailwater_z = args.tailwater
    floor = material('Warm neutral stone', (.26, .235, .195), .8)
    # Small, straight, synthetic flume: no claimed surveyed river geometry.
    solid('Flume floor', (-.15, -.9, -.25), (6.15, .9, 0.), floor)
    obstacle = None
    if is_flume:
        # Smooth compact bed obstacle, not a prescribed animated water surface.
        # Geometry is synthetic; the resulting crest must be measured in time.
        bed = [(.1 if is_wave else 0.) * .5 * (1 + math.cos(math.pi*(6*i/120-2.3)/.65))
               if abs(6*i/120-2.3) < .65 else 0. for i in range(121)]
        bed = [z + shelf_z*(1-min(1., max(0., (6*i/120-.6)/.9)))
               for i,z in enumerate(bed)]
        bump = height_volume('Submerged smooth bump' if is_wave else 'Obstacle approach bed', bed, [-.25]*121, length=6.)
        bump.data.materials.append(floor)
        bump.modifiers.new('Physical bump', 'FLUID').fluid_type = 'EFFECTOR'
        # Initial fill only: constant depth over the approach, flat downstream
        # of it, with no stationary-wave train sculpted into the liquid.
        initial_top = [inlet_depth+shelf_z*(1-min(1., max(0., (6*i/120-.6)/.9)))
                       for i in range(121)]
        initial = height_volume('Initial wave flume water', initial_top,
                                [z+.015 for z in bed], length=6.)
        if is_pillow:
            # One authored ellipsoid: identical visible and collision mesh.
            # This is a controlled obstacle, not a scanned natural boulder.
            bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24,
                                               radius=1., location=(3., 0., .28))
            obstacle = bpy.context.object
            obstacle.name = 'Single boulder'
            obstacle.scale = (.45, .33, .60)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            obstacle.data.materials.append(floor)
            for polygon in obstacle.data.polygons:
                polygon.use_smooth = True
        elif is_eddy:
            # A bank-attached spur, not a centered boulder's symmetric wake.
            obstacle = box('Bank spur', (2.45, .05, -.2), (3., .95, 1.1))
            obstacle.data.materials.append(floor)
        if is_pillow or is_eddy:
            # Subtract its volume from the INITIAL liquid before adding the
            # flow modifier. Do not seed water inside the collider.
            cut = initial.modifiers.new('Exclude initial solid volume', 'BOOLEAN')
            cut.operation = 'DIFFERENCE'
            cut.solver = 'EXACT'
            cut.object = obstacle
            bpy.context.view_layer.objects.active = initial
            bpy.ops.object.modifier_apply(modifier=cut.name)
            obstacle.modifiers.new('Physical obstacle', 'FLUID').fluid_type = 'EFFECTOR'
        initial_mod = initial.modifiers.new('Initial liquid', 'FLUID')
        initial_mod.fluid_type = 'FLOW'
        initial_mod.flow_settings.flow_type = 'LIQUID'
        initial_mod.flow_settings.flow_behavior = 'GEOMETRY'
        initial_mod.flow_settings.use_initial_velocity = True
        initial_mod.flow_settings.velocity_coord = (inlet_u, 0., 0.)
        initial.hide_render = True
    elif args.chute:
        bed = [shelf_z*(1-min(1., max(0., (2.2*i/44-.75)/1.45))) for i in range(45)]
        ledge = height_volume('Sloping approach', bed, [-.25]*45)
        ledge.data.materials.append(floor)
        ledge.modifiers.new('Physical chute', 'FLUID').fluid_type = 'EFFECTOR'
        # Continuity/Bernoulli-shaped starting fill reduces (but does not remove)
        # startup transients. It is not used to prescribe the evolved solution.
        depth = [inlet_depth*inlet_u/math.sqrt(inlet_u**2+2*9.80665*(shelf_z-z)) for z in bed]
        initial = height_volume('Initial chute water', [z+h for z,h in zip(bed, depth)],
                                [z+.015 for z in bed])
        initial_mod = initial.modifiers.new('Initial liquid', 'FLUID')
        initial_mod.fluid_type = 'FLOW'
        initial_mod.flow_settings.flow_type = 'LIQUID'
        initial_mod.flow_settings.flow_behavior = 'GEOMETRY'
        initial_mod.flow_settings.use_initial_velocity = True
        initial_mod.flow_settings.velocity_coord = (inlet_u, 0., 0.)
        initial.hide_render = True
    else:
        solid('Ledge', (-.15, -.9, 0.), (1.8, .9, shelf_z), floor)
        flow('Initial upstream water', (.025, -.775, shelf_z+.025),
             (1.78, .775, shelf_z+inlet_depth), 'GEOMETRY', (inlet_u, 0., 0.))
    solid('Far wall', (-.15, .8, 0.), (6.15, .95, 1.85), floor)
    # The front wall is intentionally an invisible domain collision boundary
    # for an unobstructed view. This is not an unconfined natural waterfall.
    if not is_flume:
        flow('Initial downstream pool', (2.225 if args.chute else 1.825, -.775, .025),
             (5.975, .775, tailwater_z), 'GEOMETRY')
    flow('Constant inlet', (.025, -.78, shelf_z+.025),
         (.55, .78, shelf_z+inlet_depth), 'INFLOW', (inlet_u, 0., 0.))
    flow('Level drain', (5.5, -.82, tailwater_z), (6.15, .82, 2.8), 'OUTFLOW')
    domain = box('Feature liquid', (0., -.8, -.1), (6., .8, 2.8))
    mod = domain.modifiers.new('3D FLIP water', 'FLUID')
    mod.fluid_type = 'DOMAIN'
    s = mod.domain_settings
    s.domain_type = 'LIQUID'
    s.resolution_max = args.resolution
    s.cache_type = 'ALL'
    s.cache_frame_start = 1
    s.cache_frame_end = args.frames
    s.cache_directory = str((args.output/'cache').resolve())
    s.cache_resumable = True
    s.flip_ratio = .95
    s.use_mesh = True
    s.mesh_scale = 2
    s.use_spray_particles = True
    s.use_foam_particles = True
    s.use_bubble_particles = True
    s.use_adaptive_timesteps = True
    s.timesteps_min = 2
    s.timesteps_max = 8
    s.cfl_condition = 2.
    s.use_fractions = args.fractional_obstacles
    s.use_collision_border_top = False
    water = material('Clear water IOR 1.333', (.88, .98, .97), .075, 1.)
    absorb = water.node_tree.nodes.new('ShaderNodeVolumeAbsorption')
    absorb.inputs['Color'].default_value = (.36, .77, .70, 1.)
    absorb.inputs['Density'].default_value = .32
    water.node_tree.links.new(absorb.outputs['Volume'],
                              water.node_tree.nodes.get('Material Output').inputs['Volume'])
    domain.data.materials.append(water)
    for polygon in domain.data.polygons:
        polygon.use_smooth = True
    foam_mat = material('Secondary whitewater approximation', (.93, .96, .95), .45)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1., location=(0., 0., -20.))
    particle = bpy.context.object
    particle.name = 'Subgrid whitewater render instance'
    particle.data.materials.append(foam_mat)
    for ps in domain.particle_systems:
        if any(word in ps.name.lower() for word in ('foam', 'spray', 'bubble')):
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
    for name, location, energy, size in [
        ('Key', (1., -3., 7.), 1600, 5.),
        ('Rim', (4., 3., 5.), 2200, 4.)]:
        bpy.ops.object.light_add(type='AREA', location=location)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy, lamp.data.size = energy, size
        aim(lamp, (3., 0., .6))
    bpy.ops.object.camera_add(location=(8.2, -9., 5.7))
    camera = bpy.context.object
    aim(camera, (2.9, 0., .75))
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = 7.8
    scene.camera = camera
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    bpy.ops.object.select_all(action='DESELECT')
    domain.select_set(True)
    bpy.context.view_layer.objects.active = domain
    blend = (args.output/'feature.blend').resolve()
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    report = dict(case=args.case, blender_version=bpy.app.version_string,
                  source_script=str(Path(__file__).resolve()), blend=str(blend),
                  dimensions_m=[6., 1.6, 2.9], gravity_mps2=9.80665,
                  resolution=args.resolution, approximate_cell_m=6/args.resolution,
                  fractional_obstacles=args.fractional_obstacles,
                  inlet_velocity_mps=inlet_u, inlet_depth_m=inlet_depth,
                  nominal_section_flux_m3s=inlet_u*1.56*(inlet_depth-.025),
                  inlet_froude=inlet_u/(9.80665*inlet_depth)**.5,
                  ledge_height_m=shelf_z, nominal_tailwater_m=tailwater_z, sloped_approach=args.chute,
                  bump_height_m=.1 if is_wave else None,
                  bump_center_x_m=2.3 if is_wave else None,
                  bump_length_m=1.3 if is_wave else None,
                  approach_height_m=args.approach_height if is_flume else None,
                  obstacle_center_m=[3., 0., .28] if is_pillow else None,
                  obstacle_radii_m=[.45, .33, .60] if is_pillow else None,
                  obstacle_bounds_m=[[2.45, .05, -.2], [3., .95, 1.1]] if is_eddy else None,
                  obstacle_measured=False,
                  frames=args.frames, fps=24, initial_transient=True,
                  actual_flux_measured=False, physical_accuracy_accepted=False,
                  visual_accuracy_accepted=False, game_integrated=False,
                  secondary_particle_radius_m=.012,
                  boundaries='Closed sides; invisible front wall; prescribed inlet; artificial level drain.',
                  limitations='Uncalibrated coarse FLIP; unresolved bubbles; no two-way air phase; no measured turbulence or mass budget.')
    (args.output/'setup.json').write_text(json.dumps(report, indent=2))
    if args.bake:
        start = time.monotonic()
        result = bpy.ops.fluid.bake_all()
        report.update(bake_seconds=time.monotonic()-start, bake_result=list(result),
                      baked_data=s.has_cache_baked_data, baked_mesh=s.has_cache_baked_mesh,
                      baked_particles=s.has_cache_baked_particles)
        (args.output/'bake.json').write_text(json.dumps(report, indent=2))
        if 'FINISHED' not in result or not s.has_cache_baked_data or not s.has_cache_baked_mesh:
            raise RuntimeError('Incomplete liquid bake')
        bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    print('FEATURE_LAB_RESULT', json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
