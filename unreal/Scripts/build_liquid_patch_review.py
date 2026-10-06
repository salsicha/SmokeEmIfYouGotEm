"""Blender CLI: build/bake an isolated Mantaflow case from an audited river patch.

Not a game asset or seamless loop. Closed lateral boundaries and a free outlet
are diagnostic approximations; do not call this a calibrated rapid.
Run: blender -b --threads 6 --python this.py -- --input patch.json --output NEWDIR [--bake]
"""
import argparse
import json
from pathlib import Path
import sys
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parent))
from liquid_review_geometry import height_volume_geometry


def closed_height_mesh(name, heights, dx, dy, lower):
    vertices, faces = height_volume_geometry(heights, lower, dx, dy)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def box(name, lower, upper):
    bpy.ops.mesh.primitive_cube_add(size=1, location=[(a+b)/2 for a,b in zip(lower, upper)])
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = [b-a for a,b in zip(lower,upper)]
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def flow(obj, behavior, velocity=(0.,0.,0.)):
    modifier = obj.modifiers.new('Liquid source', 'FLUID')
    modifier.fluid_type = 'FLOW'
    settings = modifier.flow_settings
    settings.flow_type = 'LIQUID'
    settings.flow_behavior = behavior
    settings.use_initial_velocity = True
    settings.velocity_coord = velocity
    obj.hide_render = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--resolution', type=int, default=80)
    parser.add_argument('--frames', type=int, default=144)
    parser.add_argument('--initial-velocity-cells', type=int, default=2)
    parser.add_argument('--tailwater-drain-depth', type=float,
        help='Experimental level drain: remove only above source outlet stage minus this depth (m)')
    parser.add_argument('--bake', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if not 32 <= args.resolution <= 160 or not 30 <= args.frames <= 600:
        parser.error('Resolution 32–160, frame count 30–600 required')
    if not 1 <= args.initial_velocity_cells <= 8:
        parser.error('Initial velocity tiles must span 1–8 source cells')
    if args.tailwater_drain_depth is not None and not .1 <= args.tailwater_drain_depth <= 1.:
        parser.error('Experimental tailwater drain depth must be 0.1–1.0 m')
    data = json.loads(args.input.read_text())
    if data['schema'] != 'raftsim.local_liquid_review.v1' or data['production_promoted']:
        raise ValueError('Expected an isolated audited patch')
    args.output.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.gravity = (0.,0.,-9.80665)
    scene.render.fps = 30
    scene.frame_end = args.frames
    dx, dy, nx, ny = (data[k] for k in ('dx','dy','nx','ny'))
    length, width = dx*(nx-1), dy*(ny-1)
    top = max(max(row) for row in data['eta'])+2.
    bed = closed_height_mesh('Exact source bed', data['bed'], dx, dy, [[-.5]*nx for _ in range(ny)])
    collider = bed.modifiers.new('Bed collision', 'FLUID')
    collider.fluid_type = 'EFFECTOR'
    # Preserve the accelerating jet and slower runout rather than initializing
    # the entire volume at one average speed. These are bounded piecewise-
    # constant source velocities, not a full 3D velocity reconstruction.
    tiles = []
    step = args.initial_velocity_cells
    for j in range(0, ny-1, step):
        for i in range(0, nx-1, step):
            i1, j1 = min(i+step, nx-1), min(j+step, ny-1)
            eta = [row[i:i1+1] for row in data['eta'][j:j1+1]]
            lower = [[z+.025 for z in row[i:i1+1]] for row in data['bed'][j:j1+1]]
            initial = closed_height_mesh(f'Initial water {i:02d} {j:02d}', eta, dx, dy, lower)
            initial.location = (i*dx, j*dy, 0.)
            count = (i1-i+1)*(j1-j+1)
            velocity = [sum(sum(row[i:i1+1]) for row in data[key][j:j1+1])/count for key in ('u','v')]
            flow(initial, 'GEOMETRY', (*velocity,0.))
            tiles.append(dict(i=i,j=j,i1=i1,j1=j1,velocity_mps=velocity))
    for j in range(ny-1):
        lower = .5*(data['bed'][j][0]+data['bed'][j+1][0])
        upper = .5*(data['eta'][j][0]+data['eta'][j+1][0])
        u = .5*(data['u'][j][0]+data['u'][j+1][0])
        v = .5*(data['v'][j][0]+data['v'][j+1][0])
        inlet = box(f'Inlet band {j:02d}', (.02,j*dy,lower), (.45,(j+1)*dy,upper))
        flow(inlet, 'INFLOW', (u,v,0.))
    if args.tailwater_drain_depth is None:
        outlet = box('Downstream removal', (length-.4,0.,-.25), (length+.2,width,top))
        flow(outlet, 'OUTFLOW')
    else:
        # Diagnostic reservoir control, not a discharge/characteristic boundary.
        # Preserves a downstream pool instead of deleting the entire water
        # column. Actual stage and mass balance still need measurement.
        for j in range(ny-1):
            drain_floor = .5*(data['eta'][j][-1]+data['eta'][j+1][-1])-args.tailwater_drain_depth
            outlet = box(f'Tailwater level drain {j:02d}',
                (length-.4,j*dy,drain_floor), (length+.2,(j+1)*dy,top))
            flow(outlet, 'OUTFLOW')
    domain = box('Liquid review domain', (0.,0.,-.2), (length,width,top))
    modifier = domain.modifiers.new('Mantaflow liquid', 'FLUID')
    modifier.fluid_type = 'DOMAIN'
    settings = modifier.domain_settings
    settings.domain_type = 'LIQUID'
    settings.resolution_max = args.resolution
    settings.cache_type = 'ALL'
    settings.cache_frame_start = 1
    settings.cache_frame_end = args.frames
    settings.cache_directory = str((args.output/'cache').resolve())
    settings.cache_resumable = True
    settings.flip_ratio = .95
    settings.use_mesh = True
    settings.mesh_scale = 2
    settings.use_spray_particles = True
    settings.use_foam_particles = True
    settings.use_bubble_particles = True
    settings.use_adaptive_timesteps = True
    settings.timesteps_min = 1
    settings.timesteps_max = 8
    settings.cfl_condition = 2.
    settings.use_collision_border_top = False
    bpy.ops.object.select_all(action='DESELECT')
    domain.select_set(True)
    bpy.context.view_layer.objects.active = domain
    blend = (args.output/'liquid-review.blend').resolve()
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    report = dict(source_input=str(args.input.resolve()), blend=str(blend),
        blender_version=bpy.app.version_string, resolution=args.resolution, frames=args.frames,
        fps=30, grid_cell_size_estimate_m=max(length,width,top+.2)/args.resolution,
        nominal_source_section_flux_m3s=data['inlet_section_flux_m3s'],
        initial_velocity_tiles=tiles, initial_velocity_tile_cells=step,
        initial_fill_lower_surface='exact source bed + 0.025 m; no solid-bed fill',
        tailwater_drain_depth_m=args.tailwater_drain_depth,
        outlet_model='free removal' if args.tailwater_drain_depth is None else 'experimental level drain, not measured stage/discharge',
        actual_inlet_flux_verified=False, production_promoted=False, photorealism_accepted=False,
        caveats='Closed side boundaries; idealized outlet (see outlet_model); straightened axes; tiled initial velocity; startup transient; no loop or game integration.',
        bake_requested=args.bake, baked_data=False, baked_mesh=False, baked_particles=False)
    (args.output/'setup.json').write_text(json.dumps(report, indent=2))
    print('LIQUID_REVIEW_SETUP', json.dumps({k:v for k,v in report.items() if k != 'initial_velocity_tiles'}), flush=True)
    if args.bake:
        result = bpy.ops.fluid.bake_all()
        report.update(bake_operator_result=list(result), baked_data=settings.has_cache_baked_data,
            baked_mesh=settings.has_cache_baked_mesh, baked_particles=settings.has_cache_baked_particles)
        (args.output/'bake-result.json').write_text(json.dumps(report, indent=2))
        print('LIQUID_REVIEW_BAKE', json.dumps({k:v for k,v in report.items() if k != 'initial_velocity_tiles'}), flush=True)
        if 'FINISHED' not in result or not report['baked_data'] or not report['baked_mesh']:
            raise RuntimeError('Liquid bake did not complete')
        bpy.ops.wm.save_as_mainfile(filepath=str(blend))


if __name__ == '__main__':
    main()
