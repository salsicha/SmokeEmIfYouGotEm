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
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.particle_sizes and not args.point_clouds:
        parser.error('--particle-sizes requires --point-clouds')
    args.output.mkdir(parents=True, exist_ok=False)
    scene = bpy.context.scene
    domain = bpy.data.objects['Feature liquid']
    setup = json.loads((Path(bpy.data.filepath).parent/'setup.json').read_text())
    bubble_material = bpy.data.materials['Secondary whitewater approximation']
    if setup['case'] == 'froth':
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
    for frame in args.frames:
        if not scene.frame_start <= frame <= scene.frame_end:
            raise ValueError('Frame outside configured simulation')
        start = time.monotonic()
        scene.frame_set(frame)
        for cloud, cloud_mesh, cloud_group in clouds:
            bpy.data.objects.remove(cloud, do_unlink=True)
            bpy.data.meshes.remove(cloud_mesh)
            bpy.data.node_groups.remove(cloud_group)
        clouds = []
        evaluated = domain.evaluated_get(bpy.context.evaluated_depsgraph_get())
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
                phase_material = (bpy.data.materials['Clear water IOR 1.333'] if name.lower() == 'spray'
                                  else bubble_material if name.lower() == 'bubbles'
                                  else bpy.data.materials['Secondary whitewater approximation'])
                clouds.append(point_cloud('Cached '+name, coordinates,
                    radii, phase_material))
            evaluated = domain.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        try:
            if len(mesh.vertices) <= 8:
                raise RuntimeError('Missing evaluated liquid mesh/cache')
            mesh.calc_loop_triangles()
            verts = [evaluated.matrix_world @ v.co for v in mesh.vertices]
            # Signed mesh volume is only a reconstruction diagnostic, not a
            # solver mass-conservation proof (topology can be imperfect).
            signed_volume = sum(verts[t.vertices[0]].dot(
                verts[t.vertices[1]].cross(verts[t.vertices[2]]))/6.
                for t in mesh.loop_triangles)
            row = dict(frame=frame, seconds=(frame-1)/scene.render.fps,
                       vertices=len(verts), triangles=len(mesh.loop_triangles),
                       reconstructed_signed_volume_m3=signed_volume,
                       bounds_m=[[min(v[k] for v in verts), max(v[k] for v in verts)] for k in range(3)],
                       particles=[dict(name=p.name, count=len(p.particles)) for p in evaluated.particle_systems])
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
            render_device=scene.cycles.device, camera_fixed=True,
            surface_reflection_strip=args.surface_light,
            view=args.view, secondary_representation='native sphere points' if args.point_clouds else 'icosphere instances',
            secondary_render_radii_m=particle_radii,
            secondary_particles_hidden=args.liquid_only,
            secondary_materials={'spray': 'water dielectric IOR 1.333',
                                 'foam': 'white scattering approximation',
                                 'bubbles': ('air-water glass sphere surrogate, relative IOR 1/1.333; uncalibrated radii' if setup['case'] == 'froth'
                                             else 'white scattering approximation; not resolved air interfaces')},
            per_particle_size_variation=args.particle_sizes,
            physical_accuracy_accepted=False, visual_accuracy_accepted=False,
            complete=len(rows)==len(args.frames), frames=rows), indent=2))
        print('FEATURE_FRAME', json.dumps(row), flush=True)


if __name__ == '__main__':
    main()
