"""Render actual cached liquid evolution; never modifies the source blend/cache.

blender -b feature.blend -t 4 --python this.py -- --output NEWDIR --frames 72 96
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import bpy
import numpy as np
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_feature_solid_clip import EDDY_SOLIDS, clipped_surface, remove_surface
from audit_water_feature_mesh_contact import topology
from water_feature_daylight import daylight_study
from water_feature_geometry import world_coordinates


def point_cloud(name, positions, radii, material):
    """Cycles native sphere points, retaining actual cached particle positions."""
    mesh = bpy.data.meshes.new(name)
    mesh.vertices.add(len(positions)//3)
    mesh.vertices.foreach_set('co', positions)
    radius_attribute = mesh.attributes.new('particle_radius', 'FLOAT', 'POINT')
    radius_attribute.data.foreach_set('value', radii)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    group = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    inp = group.nodes.new('NodeGroupInput')
    out = group.nodes.new('NodeGroupOutput')
    points = group.nodes.new('GeometryNodeMeshToPoints')
    radius_node = group.nodes.new('GeometryNodeInputNamedAttribute')
    radius_node.data_type = 'FLOAT'
    radius_node.inputs['Name'].default_value = 'particle_radius'
    group.links.new(radius_node.outputs['Attribute'], points.inputs['Radius'])
    assign = group.nodes.new('GeometryNodeSetMaterial')
    assign.inputs['Material'].default_value = material
    group.links.new(inp.outputs['Geometry'], points.inputs['Mesh'])
    group.links.new(points.outputs['Points'], assign.inputs['Geometry'])
    group.links.new(assign.outputs['Geometry'], out.inputs['Geometry'])
    modifier = obj.modifiers.new(name, 'NODES')
    modifier.node_group = group
    return obj, mesh, group


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--frames', type=int, nargs='+', required=True)
    parser.add_argument('--samples', type=int, default=24)
    parser.add_argument('--width', type=int, default=960)
    parser.add_argument('--cpu', action='store_true')
    parser.add_argument('--point-clouds', action='store_true', help='Render cached secondary particles as native sphere points')
    parser.add_argument('--particle-sizes', action='store_true', help='Preserve evaluated per-particle radius variation in native points')
    parser.add_argument('--liquid-only', action='store_true', help='Diagnostic: hide all secondary particles to inspect the unchanged water surface')
    parser.add_argument('--surface-light', action='store_true', help='Add a real strip area light reflected in the pool to reveal small surface slopes')
    parser.add_argument('--view', choices=['overview', 'close', 'obstacle', 'eddy', 'froth'], default='overview')
    parser.add_argument('--tracer-report', type=Path,
                        help='Diagnostic eddy MAC paths; not foam, dye physics or tracked FLIP identities')
    parser.add_argument('--particle-mapping-report', type=Path,
                        help='Required native coordinate validation for a tracer preview')
    parser.add_argument('--mesh-contact-diagnostic', action='store_true',
                        help='Label the unqualified aligned eddy native mesh; secondary phases unbaked')
    parser.add_argument('--solid-clipped-diagnostic', action='store_true',
                        help='Extract mesh outside shared solids; does not change solver data')
    parser.add_argument('--union-solids', action='store_true', help='Unite overlapping shared solids before extraction')
    parser.add_argument('--contact-materials', action='store_true',
                        help='Use shared solid shaders at new contact closures, not a fictitious water-air boundary')
    parser.add_argument('--daylight-study', action='store_true', help='Declared modeled sky instead of large studio cards; not measured lighting')
    parser.add_argument('--constrained-extraction', action='store_true',
                        help='Vertex-preserving orthonormal-plane triangulation of diagnostic extraction')
    parser.add_argument('--secondary-study', action='store_true',
                        help='Labeled native secondary phases from independently copied aligned eddy cache')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.particle_sizes and not args.point_clouds:
        parser.error('--particle-sizes requires --point-clouds')
    if args.solid_clipped_diagnostic and not args.mesh_contact_diagnostic:
        parser.error('--solid-clipped-diagnostic requires --mesh-contact-diagnostic')
    if args.union_solids and not args.solid_clipped_diagnostic:
        parser.error('--union-solids requires --solid-clipped-diagnostic')
    if args.contact_materials and not args.union_solids:
        parser.error('--contact-materials requires --union-solids')
    if args.daylight_study and (not args.mesh_contact_diagnostic or args.surface_light):
        parser.error('--daylight-study requires a labeled mesh/contact diagnostic without an extra strip light')
    if args.constrained_extraction and not args.contact_materials:
        parser.error('--constrained-extraction requires shared-solid contact extraction')
    if args.secondary_study and (not args.mesh_contact_diagnostic or not args.point_clouds or args.liquid_only or args.tracer_report):
        parser.error('--secondary-study requires mesh/contact diagnostic, native points and visible phases without tracers')
    args.output.mkdir(parents=True, exist_ok=False)
    scene = bpy.context.scene
    illumination = daylight_study(scene) if args.daylight_study else dict(model='authored studio area lamps', measured_lighting=False)
    source_blend_hash = hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()
    source_files = [Path(__file__)] + [Path(__file__).with_name(name) for name in
        ('water_feature_solid_clip.py', 'water_feature_triangulation.py', 'water_feature_polygon.py',
         'water_feature_daylight.py', 'audit_water_feature_mesh_contact.py')]
    source_files.append(Path(__file__).with_name('water_feature_geometry.py'))
    source_code_hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in source_files}
    domain = bpy.data.objects['Feature liquid']
    setup = json.loads((Path(bpy.data.filepath).parent/'setup.json').read_text())
    simulation_correction = None
    if args.mesh_contact_diagnostic:
        if setup['case'] != 'eddy' or args.view != 'eddy' or args.tracer_report or not setup.get('grid_aligned_domain'):
            raise ValueError('Contact diagnostic requires aligned eddy view without tracers')
        if args.secondary_study:
            phase_bake = json.loads((Path(bpy.data.filepath).parent/'bake-particles.json').read_text())
            simulation_correction = phase_bake.get('simulation_correction')
            if simulation_correction and not phase_bake.get('simulation_correction_verified'):
                raise ValueError('Simulation correction requires verified native-stage receipt')
            phase_audit = json.loads((Path(bpy.data.filepath).parent/'secondary-location-v1.json').read_text())
            phase_mapping = json.loads((Path(bpy.data.filepath).parent/'secondary-mapping-v1.json').read_text())
            if (not phase_bake['baked_particles'] or not phase_bake['copied_data_mesh_unchanged']
                    or not phase_bake['originals_unchanged'] or not phase_audit['complete']
                    or not phase_audit['originals_unchanged']
                    or not phase_mapping['complete'] or not phase_mapping['originals_unchanged']
                    or not all(p['all_positions_and_velocities_match'] for row in phase_mapping['frames'] for p in row['phases'])
                    or Path(phase_bake['blend']).resolve() != Path(bpy.data.filepath).resolve()):
                raise ValueError('Completed preserved phase stage and location audit required')
        else:
            mesh_bake = json.loads((Path(bpy.data.filepath).parent/'bake-mesh.json').read_text())
            if (not args.liquid_only or not mesh_bake['baked_mesh'] or mesh_bake['baked_particles']
                    or Path(mesh_bake['blend']).resolve() != Path(bpy.data.filepath).resolve()):
                raise ValueError('Liquid-only contact diagnostic requires completed aligned native mesh')
    tracer_report = None
    tracer_hash = None
    if args.tracer_report:
        if setup['case'] != 'eddy' or args.view != 'eddy' or not args.liquid_only or not args.particle_mapping_report:
            parser.error('Tracer diagnostic requires eddy view, --liquid-only and native mapping report')
        tracer_report = json.loads(args.tracer_report.read_text())
        mapping_report = json.loads(args.particle_mapping_report.read_text())
        if not (tracer_report['complete'] and tracer_report['originals_unchanged']
                and mapping_report['complete'] and mapping_report['originals_unchanged']
                and all(r['isotropic_native_positions_and_velocities_match'] for r in mapping_report['frames'])
                and Path(tracer_report['source_blend']).resolve() == Path(bpy.data.filepath).resolve()):
            raise ValueError('Need complete original-cache and native coordinate validation')
        tracer_hash = hashlib.sha256(args.tracer_report.read_bytes()).hexdigest()
        receipts = {r['frame']: r['original_vdb_sha256'] for r in tracer_report['original_vdb_receipts']}
        for frame in args.frames:
            path = Path(bpy.data.filepath).parent/'cache'/'data'/f'fluid_data_{frame:04d}.vdb'
            if frame not in receipts or hashlib.sha256(path.read_bytes()).hexdigest() != receipts[frame]:
                raise ValueError('Tracer/render frame or original cache mismatch')
    bubble_material = bpy.data.materials['Secondary whitewater approximation']
    if setup['case'] == 'froth' or args.secondary_study:
        # Optical sphere surrogate only: particles are not measured bubbles.
        # Glass IOR is relative to the surrounding water for these internal
        # interfaces. Do not render immersed air with opaque foam material.
        bubble_material = bpy.data.materials.new('Subgrid air-water interface approximation')
        bubble_material.use_nodes = True
        bubble_material.node_tree.nodes.clear()
        glass = bubble_material.node_tree.nodes.new('ShaderNodeBsdfGlass')
        glass.inputs['Color'].default_value = (1., 1., 1., 1.)
        glass.inputs['Roughness'].default_value = .015
        glass.inputs['IOR'].default_value = 1/1.333
        output = bubble_material.node_tree.nodes.new('ShaderNodeOutputMaterial')
        bubble_material.node_tree.links.new(glass.outputs[0], output.inputs['Surface'])
        scene.cycles.max_bounces = 16
        scene.cycles.transmission_bounces = 12
    # Airborne spray droplets are water, not opaque foam. Keep the distinct
    # cached phase and use the liquid's dielectric material. Foam/bubble
    # optical scattering remains an explicit unresolved approximation.
    spray_instance = bpy.data.objects['Subgrid whitewater render instance'].copy()
    spray_instance.data = spray_instance.data.copy()
    spray_instance.name = 'Clear spray render instance'
    spray_instance.data.materials.clear()
    spray_instance.data.materials.append(bpy.data.materials['Clear water IOR 1.333'])
    bpy.context.collection.objects.link(spray_instance)
    bubble_instance = bpy.data.objects['Subgrid whitewater render instance'].copy()
    bubble_instance.data = bubble_instance.data.copy()
    bubble_instance.name = 'Subgrid immersed air render instance'
    bubble_instance.data.materials.clear()
    bubble_instance.data.materials.append(bubble_material)
    bpy.context.collection.objects.link(bubble_instance)
    if args.view == 'froth':
        if setup['case'] != 'froth':
            raise ValueError('Froth framing requires a froth case')
        # Include the entire nozzle and impact tank, not just the waterline.
        scene.camera.location = (3.1, -4., 2.6)
        scene.camera.rotation_euler = (Vector((1., 0., .9))-scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
        scene.camera.data.ortho_scale = 4.6
    elif args.view == 'close':
        scene.camera.location = (6., -7., 4.)
        scene.camera.rotation_euler = (Vector((2.35, 0., .6))-scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
        scene.camera.data.ortho_scale = 4.6
    elif args.view == 'obstacle':
        scene.camera.location = (5.8, -6., 6.)
        scene.camera.rotation_euler = (Vector((3., 0., .35))-scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
        scene.camera.data.ortho_scale = 4.5
    elif args.view == 'eddy':
        # High oblique view exposes the bank return without hiding its collider.
        scene.camera.location = (3.5, -3., 8.)
        scene.camera.rotation_euler = (Vector((3.5, 0., .3))-scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
        scene.camera.data.ortho_scale = 4.7
    tracer_material = tracer_caption = None
    if tracer_report or args.mesh_contact_diagnostic:
        tracer_material = bpy.data.materials.new('Diagnostic tracer markers, not liquid or foam')
        tracer_material.use_nodes = True
        tracer_material.node_tree.nodes.clear()
        emission = tracer_material.node_tree.nodes.new('ShaderNodeEmission')
        emission.inputs['Color'].default_value = (1., .3, .025, 1.)
        emission.inputs['Strength'].default_value = 3.
        output = tracer_material.node_tree.nodes.new('ShaderNodeOutputMaterial')
        tracer_material.node_tree.links.new(emission.outputs[0], output.inputs['Surface'])
        caption_material = tracer_material.copy()
        caption_material.name = 'Diagnostic caption'
        caption_material.node_tree.nodes.get('Emission').inputs['Color'].default_value = (1., 1., 1., 1.)
        caption_material.node_tree.nodes.get('Emission').inputs['Strength'].default_value = 1.
        text = bpy.data.curves.new('Unaccepted tracer diagnostic caption', type='FONT')
        text.size = .095
        tracer_caption = bpy.data.objects.new('Diagnostic only, not accepted eddy', text)
        bpy.context.collection.objects.link(tracer_caption)
        tracer_caption.parent = scene.camera
        tracer_caption.location = (-2.25, 1.16, -1.)
        tracer_caption.data.materials.append(caption_material)
        panel_material = caption_material.copy()
        panel_material.name = 'Dark diagnostic caption backing'
        panel_material.node_tree.nodes.get('Emission').inputs['Color'].default_value = (.008, .013, .020, 1.)
        panel_mesh = bpy.data.meshes.new('Diagnostic caption backing plane')
        panel_mesh.from_pydata([(-2.3, .90, 0), (2.3, .90, 0), (2.3, 1.29, 0), (-2.3, 1.29, 0)], [], [(0, 1, 2, 3)])
        panel = bpy.data.objects.new('Diagnostic caption backing, not fluid geometry', panel_mesh)
        bpy.context.collection.objects.link(panel)
        panel.parent = scene.camera
        panel.location = (0, 0, -1.1)
        panel.data.materials.append(panel_material)
    if args.surface_light:
        # Specular reflection of a real light, not a painted wave/normal map.
        # Match the camera's reflected direction about the horizontal surface.
        setup = json.loads((Path(bpy.data.filepath).parent/'setup.json').read_text())
        if setup['case'] != 'boil':
            raise ValueError('Pool reflection lighting currently supports only the boil case')
        center = Vector((1.5, 0., .62))
        camera_offset = scene.camera.location-center
        light_position = center+Vector((-camera_offset.x, -camera_offset.y, camera_offset.z))
        for name in ('Key', 'Rim'):
            bpy.data.objects[name].data.energy *= .25
        bpy.ops.object.light_add(type='AREA', location=light_position)
        lamp = bpy.context.object
        lamp.name = 'Surface slope reflection strip'
        lamp.data.shape = 'RECTANGLE'
        lamp.data.size = 4.
        lamp.data.size_y = .18
        lamp.data.energy = 600.
        lamp.rotation_euler = (center-lamp.location).to_track_quat('-Z', 'Y').to_euler()
    # Distinguish subgrid air bubbles from centimetre-sized white balls. These
    # radii are an explicit rendering approximation, not simulated bubble sizes.
    particle_radii = {'foam': .003, 'spray': .003, 'bubbles': .0012}
    for ps in domain.particle_systems:
        key = ps.name.lower()
        if key in particle_radii:
            ps.settings.particle_size = particle_radii[key]
            if key == 'spray':
                ps.settings.instance_object = spray_instance
            elif key == 'bubbles':
                ps.settings.instance_object = bubble_instance
            if args.point_clouds or args.liquid_only:
                ps.settings.render_type = 'NONE'
    if not args.cpu:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'OPTIX'
        prefs.get_devices()
        devices = [device for device in prefs.devices if device.type == 'OPTIX']
        if not devices:
            raise RuntimeError('No OptiX device; explicitly use --cpu for CPU rendering')
        for device in prefs.devices:
            device.use = device.type == 'OPTIX'
        scene.cycles.device = 'GPU'
    else:
        scene.cycles.device = 'CPU'
    scene.cycles.samples = args.samples
    scene.render.resolution_x = args.width
    scene.render.resolution_y = round(args.width*9/16)
    rows = []
    clouds = []
    derived_surface = None
    for frame in args.frames:
        if not scene.frame_start <= frame <= scene.frame_end:
            raise ValueError('Frame outside configured simulation')
        start = time.monotonic()
        if derived_surface is not None:
            remove_surface(derived_surface)
            derived_surface = None
        scene.frame_set(frame)
        if args.mesh_contact_diagnostic:
            kind = 'Native secondary-phase study' if args.secondary_study else 'Modeled daylight study' if args.daylight_study else 'Solid-clipped surface' if args.solid_clipped_diagnostic else 'Grid-aligned native mesh'
            if simulation_correction:
                kind = 'Boundary-completed secondary candidate'
            tracer_caption.data.body = (f'{kind} | t={(frame-1)/scene.render.fps:.2f}s\n'
                                        + ('DIAGNOSTIC: phases/flow/optics unqualified' if args.secondary_study else 'DIAGNOSTIC: solver/foam still unqualified'))
        for cloud, cloud_mesh, cloud_group in clouds:
            bpy.data.objects.remove(cloud, do_unlink=True)
            bpy.data.meshes.remove(cloud_mesh)
            bpy.data.node_groups.remove(cloud_group)
        clouds = []
        evaluated = domain.evaluated_get(bpy.context.evaluated_depsgraph_get())
        tracer_count = None
        if tracer_report:
            index = frame-tracer_report['start_frame']
            tracks = tracer_report['tracks']['isotropic_object_centered']['8']
            active = [t for t in tracks if 0 <= index < len(t['positions_m'])]
            if not active:
                raise ValueError('No supported tracer positions at requested frame')
            markers = np.array([t['positions_m'][index] for t in active], np.float32)
            trails = np.array([p for t in active for p in t['positions_m'][max(0, index-12):index]], np.float32)
            clouds.append(point_cloud('Supported diagnostic MAC markers', markers.ravel(),
                          np.full(len(markers), .012, np.float32), tracer_material))
            if len(trails):
                clouds.append(point_cloud('Previous supported positions, 0.5-second history', trails.ravel(),
                              np.full(len(trails), .005, np.float32), tracer_material))
            tracer_count = len(active)
            tracer_caption.data.body = (f'MAC seed/path markers: {tracer_count}/48 | {(frame-tracer_report["start_frame"])/24:.2f}s\n'
                                        'DIAGNOSTIC: foam hidden; circulation unverified')
            evaluated = domain.evaluated_get(bpy.context.evaluated_depsgraph_get())
        phase_render_rows = []
        if args.point_clouds and not args.liquid_only:
            # Copy all evaluated data before adding nodes invalidates depsgraph.
            cached = []
            for ps in evaluated.particle_systems:
                if ps.name.lower() in particle_radii:
                    coordinates = np.empty(len(ps.particles)*3, np.float32)
                    ps.particles.foreach_get('location', coordinates)
                    radii = np.full(len(ps.particles), particle_radii[ps.name.lower()], np.float32)
                    if args.particle_sizes:
                        ps.particles.foreach_get('size', radii)
                        if not np.isfinite(radii).all() or (radii < 0).any():
                            raise ValueError('Invalid evaluated particle sizes')
                    cached.append((ps.name, coordinates, radii))
            for name, coordinates, radii in cached:
                phase_render_rows.append(dict(name=name, count=len(radii),
                    positions_sha256=hashlib.sha256(coordinates.tobytes()).hexdigest(),
                    rendering_radius_quantiles_m=np.quantile(radii, [.05, .5, .95]).tolist() if len(radii) else None))
                phase_material = (bpy.data.materials['Clear water IOR 1.333'] if name.lower() == 'spray'
                                  else bubble_material if name.lower() == 'bubbles'
                                  else bpy.data.materials['Secondary whitewater approximation'])
                clouds.append(point_cloud('Cached '+name, coordinates,
                    radii, phase_material))
            evaluated = domain.evaluated_get(bpy.context.evaluated_depsgraph_get())
        cached_phases = [dict(name=p.name, count=len(p.particles)) for p in evaluated.particle_systems]
        if args.solid_clipped_diagnostic:
            derived_surface = clipped_surface(evaluated, [bpy.data.objects[name] for name in EDDY_SOLIDS],
                                              args.union_solids, args.contact_materials,
                                              args.constrained_extraction, args.constrained_extraction)
            domain.hide_render = True
            evaluated = derived_surface.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        try:
            if len(mesh.vertices) <= 8:
                raise RuntimeError('Missing evaluated liquid mesh/cache')
            mesh.calc_loop_triangles()
            verts = [evaluated.matrix_world @ v.co for v in mesh.vertices]
            measured_vertices = world_coordinates([v.co[:] for v in mesh.vertices], evaluated.matrix_world)
            measured_triangles = np.array([t.vertices[:] for t in mesh.loop_triangles], dtype=np.int64)
            corners = measured_vertices[measured_triangles]
            areas = np.linalg.norm(np.cross(corners[:, 1]-corners[:, 0], corners[:, 2]-corners[:, 0]), axis=1)/2
            # Signed mesh volume is only a reconstruction diagnostic, not a
            # solver mass-conservation proof (topology can be imperfect).
            signed_volume = float(np.sum(np.einsum('ij,ij->i', corners[:, 0],
                                   np.cross(corners[:, 1], corners[:, 2])))/6)
            row = dict(frame=frame, seconds=(frame-1)/scene.render.fps,
                       geometry_sha256=hashlib.sha256(measured_vertices.tobytes()+measured_triangles.tobytes()).hexdigest(),
                       diagnostic_tracer_count=tracer_count,
                       vertices=len(verts), triangles=len(mesh.loop_triangles),
                       topology=topology([tuple(t.vertices) for t in mesh.loop_triangles]),
                       degenerate_triangles=int(np.sum(areas < 1e-12)),
                       exact_zero_area_triangles=int(np.sum(areas == 0)),
                       minimum_triangle_area_m2=float(areas.min()),
                       extraction_triangulation=(json.loads(derived_surface['extraction_triangulation'])
                                                 if args.constrained_extraction else None),
                       reconstructed_signed_volume_m3=signed_volume,
                       bounds_m=[[min(v[k] for v in verts), max(v[k] for v in verts)] for k in range(3)],
                       particles=cached_phases, rendered_phases=phase_render_rows)
        finally:
            evaluated.to_mesh_clear()
        image = args.output/f'frame_{frame:04d}.png'
        scene.render.filepath = str(image.resolve())
        bpy.ops.render.render(write_still=True)
        row.update(image=str(image.resolve()), sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                   evaluation_and_render_seconds=time.monotonic()-start)
        rows.append(row)
        (args.output/'frames.json').write_text(json.dumps(dict(
            source_blend=bpy.data.filepath, simulation_fps=scene.render.fps,
            source_blend_sha256=source_blend_hash, source_code_sha256=source_code_hashes,
            blender_version=bpy.app.version_string, blender_build_hash=bpy.app.build_hash.decode(),
            render_device=scene.cycles.device, camera_fixed=True,
            render_samples=scene.cycles.samples, denoising=scene.cycles.use_denoising,
            illumination=illumination,
            surface_reflection_strip=args.surface_light,
            view=args.view, secondary_representation='native sphere points' if args.point_clouds else 'icosphere instances',
            secondary_render_radii_m=particle_radii,
            secondary_particles_hidden=args.liquid_only,
            secondary_phase_study=args.secondary_study,
            simulation_correction=simulation_correction,
            secondary_phase_placement_accepted=False,
            secondary_materials={'spray': 'water dielectric IOR 1.333',
                                 'foam': 'white scattering approximation',
                                 'bubbles': ('air-water glass sphere surrogate, relative IOR 1/1.333; uncalibrated radii' if setup['case'] == 'froth' or args.secondary_study
                                             else 'white scattering approximation; not resolved air interfaces')},
            per_particle_size_variation=args.particle_sizes,
            physical_accuracy_accepted=False, visual_accuracy_accepted=False,
            diagnostic_tracer_report_sha256=tracer_hash,
            native_mesh_contact_diagnostic=args.mesh_contact_diagnostic,
            solid_clipped_diagnostic=args.solid_clipped_diagnostic,
            shared_solids_united=args.union_solids,
            contact_materials_transferred=args.contact_materials,
            constrained_extraction=args.constrained_extraction,
            geometry_measurement='float64 affine transform of original object-space coordinates before area/volume/hash',
            surface_extraction=('Exact difference of native liquid mesh and unchanged authored colliders; not solver mass/collision correction' if args.solid_clipped_diagnostic else 'Unchanged native liquid mesh'),
            tracer_representation=('Initial seed grid then available n8 isotropic path positions, 12-mm emissive markers with 0.5s history. Missing subsequent positions are hidden, not extended or clamped; not foam or tracked FLIP particles' if tracer_report else None),
            complete=len(rows)==len(args.frames), frames=rows), indent=2))
        print('FEATURE_FRAME', json.dumps(row), flush=True)


if __name__ == '__main__':
    main()
