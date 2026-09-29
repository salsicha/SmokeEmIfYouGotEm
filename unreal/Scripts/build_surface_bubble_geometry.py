"""Render a full cap/cavity/meniscus checkpoint before adapting the foam raft.

Static equilibrium shape study, NOT a simulated bubble formation/foam animation.
No flat water plane is left across the cavity. Cavity and outer meniscus are
one closed water boundary; the thin film is the separate cap interface.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from surface_bubble_shape import shape, meniscus
from build_water_feature_lab import box, material, aim


def revolve_water(model, segments=192, rings=160, equilibrium=None):
    radius, rim = model['gas_radius_m'], model['rim_radius_m']
    outer = 12*model['capillary_length_m']
    rr = np.geomspace(outer, rim, rings)
    if equilibrium is None:
        profile = list(zip(rr, meniscus(rr, model)))
        angles = np.linspace(math.asin(rim/radius), math.pi, rings+1)[1:-1]
        profile += [(radius*math.sin(t), model['cavity_center_z_m']+radius*math.cos(t)) for t in angles]
        bottom_z = model['cavity_center_z_m']-radius
    else:
        exterior = np.asarray(equilibrium['exterior_profile_rz_m'])[::-1]
        profile = list(zip(rr,np.interp(rr,exterior[:,0],exterior[:,1])))
        cavity = np.asarray(equilibrium['cavity_profile_rz_m'])
        arc = np.concatenate(([0.],np.cumsum(np.linalg.norm(np.diff(cavity,axis=0),axis=1))))
        samples = np.linspace(0.,arc[-1],rings+1)
        sampled = np.column_stack([np.interp(samples,arc,cavity[:,i]) for i in (0,1)])
        profile += [tuple(row) for row in sampled[::-1][1:-1]]
        bottom_z = model['cavity_bottom_z_m']
    vertices = [(r*math.cos(2*math.pi*j/segments), r*math.sin(2*math.pi*j/segments), z)
                for r, z in profile for j in range(segments)]
    faces = []
    for i in range(len(profile)-1):
        lo, hi = i*segments, (i+1)*segments
        faces.extend((lo+j, lo+(j+1)%segments, hi+(j+1)%segments, hi+j) for j in range(segments))
    pole = len(vertices)
    vertices.append((0., 0., bottom_z))
    last = (len(profile)-1)*segments
    faces.extend((last+j, last+(j+1)%segments, pole) for j in range(segments))
    bottom = len(vertices)
    depth = .006
    vertices.extend((outer*math.cos(2*math.pi*j/segments), outer*math.sin(2*math.pi*j/segments), -depth) for j in range(segments))
    faces.extend((j, bottom+j, bottom+(j+1)%segments, (j+1)%segments) for j in range(segments))
    center = len(vertices)
    vertices.append((0., 0., -depth))
    faces.extend((bottom+(j+1)%segments, bottom+j, center) for j in range(segments))
    mesh = bpy.data.meshes.new('Connected meniscus and submerged cavity')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    edges = Counter(tuple(sorted((face[j], face[(j+1)%len(face)]))) for face in faces for j in range(len(face)))
    if set(edges.values()) != {2}:
        raise RuntimeError('Water boundary is not closed')
    mesh.calc_loop_triangles()
    volume = sum(mesh.vertices[t.vertices[0]].co.dot(mesh.vertices[t.vertices[1]].co.cross(mesh.vertices[t.vertices[2]].co))/6 for t in mesh.loop_triangles)
    if volume <= 0:
        raise RuntimeError('Water boundary winding is inverted')
    for poly in mesh.polygons:
        poly.use_smooth = True
    return mesh, dict(water_mesh_volume_m3=volume, water_boundary_edges=len(edges),
                      manifold_edges_verified=True, meridian_rings=len(profile), azimuth_segments=segments,
                      outer_radius_m=outer, truncated_meniscus_height_m=float(profile[0][1]))


def film_mesh(model, segments=192, rings=32):
    curvature = model['cap_curvature_radius_m']
    theta = math.asin(model['rim_radius_m']/curvature)
    base = model['rim_height_m']-math.sqrt(curvature**2-model['rim_radius_m']**2)
    vertices = [(0., 0., base+curvature)]
    for t in np.linspace(0., theta, rings+1)[1:]:
        vertices.extend((curvature*math.sin(t)*math.cos(2*math.pi*j/segments),
                         curvature*math.sin(t)*math.sin(2*math.pi*j/segments),
                         base+curvature*math.cos(t)) for j in range(segments))
    faces = [(0, 1+j, 1+(j+1)%segments) for j in range(segments)]
    for ring in range(rings-1):
        lo, hi = 1+ring*segments, 1+(ring+1)*segments
        faces.extend((lo+j,hi+j,hi+(j+1)%segments,lo+(j+1)%segments) for j in range(segments))
    mesh = bpy.data.meshes.new('Thin spherical liquid film')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    assert all(p.normal.z > 0 for p in mesh.polygons)
    # Actual float32 interface seam, not only analytic formulas.
    seam = np.array([v.co[:] for v in mesh.vertices[-segments:]])
    error = max(float(np.max(np.abs(seam[:,2]-model['rim_height_m']))),
                float(np.max(np.abs(np.linalg.norm(seam[:,:2],axis=1)-model['rim_radius_m']))))
    if error > 1e-9:
        raise RuntimeError('Cap rim seam differs from cavity')
    for poly in mesh.polygons:
        poly.use_smooth = True
    return mesh, error


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--radius-mm', type=float, default=1.)
    p.add_argument('--equilibrium', type=Path, help='Use solved Young-Laplace profiles instead of spherical approximation')
    args = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    equilibrium_report = json.loads(args.equilibrium.read_text()) if args.equilibrium else None
    equilibrium = equilibrium_report['solution'] if equilibrium_report else None
    model = equilibrium['model'] if equilibrium else shape(args.radius_mm/1000)
    if equilibrium and abs(model['gas_radius_m']-args.radius_mm/1000) > 1e-12:
        raise ValueError('Radius does not match the solved geometry')
    args.output.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    mesh, audit = revolve_water(model,equilibrium=equilibrium)
    water = bpy.data.objects.new('Water with actual gas cavity', mesh)
    bpy.context.collection.objects.link(water)
    water.data.materials.append(material('Water dielectric', (1.,1.,1.), .008, 1.))
    cap, seam_error = film_mesh(model)
    obj = bpy.data.objects.new('Bubble film', cap)
    bpy.context.collection.objects.link(obj)
    mat = bpy.data.materials.new('450 nm assumed water film')
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (1.,1.,1.,1.)
    bsdf.inputs['Roughness'].default_value = .008
    bsdf.inputs['IOR'].default_value = 1.333
    bsdf.inputs['Transmission Weight'].default_value = 1.
    bsdf.inputs['Thin Wall'].default_value = True
    bsdf.inputs['Thin Film Thickness'].default_value = 450.
    bsdf.inputs['Thin Film IOR'].default_value = 1.333
    obj.data.materials.append(mat)
    floor = box('Neutral tray floor',(-.04,-.04,-.0063),(.04,.04,-.00605))
    floor.data.materials.append(material('Tray',(.16,.20,.24),.6))
    scene.world = bpy.data.worlds.new('Studio')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.6,.7,.85,1.)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .3
    for name, loc, power, size in [('Key',(-.008,-.012,.018),.05,.012),('Rim',(.009,.008,.013),.03,.006)]:
        bpy.ops.object.light_add(type='AREA',location=loc)
        lamp = bpy.context.object
        lamp.name = name
        lamp.data.energy, lamp.data.size = power,size
        aim(lamp,(0,0,0))
    bpy.ops.object.camera_add(location=(.003,-.008,.006))
    scene.camera = bpy.context.object
    aim(scene.camera,(0,0,-.0003))
    scene.camera.data.type = 'ORTHO'
    scene.camera.data.ortho_scale = .008
    scene.camera.data.clip_start = .00001
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 128
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces, scene.cycles.transmission_bounces = 16,12
    scene.render.resolution_x, scene.render.resolution_y = 960,540
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    blend = (args.output/'feature.blend').resolve()
    setup = dict(case='isolated-floating-bubble-geometry', blend=str(blend), model=model,
                 geometry_model='nonlinear-young-laplace' if equilibrium else 'spherical-cavity-approximation',
                 audit=dict(audit, cap_cavity_seam_error_m=seam_error),
                 reference='https://doi.org/10.1017/jfm.2025.11003',
                 reference_license='CC BY 4.0; original implementation, no external figures or data bundled',
                 physical_accuracy_accepted=False, visual_accuracy_accepted=False,
                 limitations=('Static isolated nonlinear Young-Laplace solution, fixed gas volume, massless film and negligible gas density. ' if equilibrium else 'Static low-Bond isolated-bubble approximation. Spherical cavity Rb=R0, linearized meniscus, zero-rim pressure approximation. ')
                 +'Not raft dynamics. Film thickness assumed, no drainage, rupture, surfactant dynamics or physical lifetime. No animation or CFD claim.')
    (args.output/'setup.json').write_text(json.dumps(setup,indent=2))
    if equilibrium_report:
        (args.output/'equilibrium.json').write_text(json.dumps(equilibrium_report,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    if not any(d.type == 'OPTIX' for d in prefs.devices):
        raise RuntimeError('OptiX unavailable; prepared scene retained')
    for device in prefs.devices:
        device.use = device.type == 'OPTIX'
    scene.cycles.device = 'GPU'
    scene.render.filepath = str((args.output/'geometry.png').resolve())
    bpy.ops.render.render(write_still=True)
    print('BUBBLE_GEOMETRY',json.dumps(setup),flush=True)


if __name__ == '__main__':
    main()
