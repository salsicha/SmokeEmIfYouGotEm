"""Surface bubble-cap/contact prototype. Not resolved multiphase foam.

Prescribed shear plus non-overlap projection; explicit thin-wall optical caps.
Cap shape, film thickness and contact mobility are uncalibrated assumptions.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_water_feature_lab import aim
from build_surface_foam_lab import SPEED, SHEAR


def seed():
    rng = np.random.default_rng(281)
    centers, radii = [], []
    for _ in range(12000):
        p = rng.uniform([.09, -.023], [.14, .013])
        r = rng.uniform(.0007, .0014)
        if ((p[0]-.115)/.025)**2+((p[1]+.005)/.018)**2 > .95**2:
            continue
        if centers and np.any(np.linalg.norm(np.array(centers)-p, axis=1) < np.array(radii)+r+.00005):
            continue
        centers.append(p)
        radii.append(r)
        if len(centers) == 220:
            break
    return np.array(centers), np.array(radii)


def evolve(initial, radii, steps_per_frame):
    p = initial.copy()
    frames = [p.copy()]
    a, b = np.triu_indices(len(p), 1)
    rest = radii[a]+radii[b]
    dt = 1/(24*steps_per_frame)
    worst_penetration = 0.
    for step in range(72*steps_per_frame):
        p[:, 0] += (SPEED+SHEAR*p[:, 1])*dt
        if len(a) == 0:
            if (step+1) % steps_per_frame == 0:
                frames.append(p.copy())
            continue
        for iteration in range(80):
            delta = p[b]-p[a]
            distance = np.linalg.norm(delta, axis=1)
            overlap = np.maximum(rest-distance, 0.)
            if overlap.max() < 1e-8:
                break
            active = overlap > 0
            correction = .5*overlap[active, None]*delta[active]/distance[active, None]
            change = np.zeros_like(p)
            np.add.at(change, a[active], -correction)
            np.add.at(change, b[active], correction)
            p += change
        residual = float(np.maximum(rest-np.linalg.norm(p[b]-p[a], axis=1), 0.).max())
        worst_penetration = max(worst_penetration, residual)
        if residual > 2e-8:
            raise RuntimeError('Non-overlap projection failed to converge')
        if (step+1) % steps_per_frame == 0:
            frames.append(p.copy())
    return np.array(frames), worst_penetration


def cap_mesh(radius):
    # Assumed shallow spherical cap: footprint r, height .4r. It is an
    # ABOVE-surface optical study, not a reconstructed submerged gas cavity.
    height = .4*radius
    sphere_radius = (radius*radius+height*height)/(2*height)
    theta_max = np.arcsin(radius/sphere_radius)
    vertices = [(0., 0., height)]
    segments, rings = 24, 8
    for ring in range(1, rings+1):
        theta = theta_max*ring/rings
        rr = sphere_radius*np.sin(theta)
        z = sphere_radius*np.cos(theta)-(sphere_radius-height)
        vertices.extend((rr*np.cos(phi), rr*np.sin(phi), z)
                        for phi in np.arange(segments)*2*np.pi/segments)
    faces = [(0, 1+j, 1+(j+1)%segments) for j in range(segments)]
    for ring in range(rings-1):
        lo, hi = 1+ring*segments, 1+(ring+1)*segments
        faces.extend((lo+j, hi+j, hi+(j+1)%segments, lo+(j+1)%segments)
                     for j in range(segments))
    mesh = bpy.data.meshes.new('Thin cap')
    mesh.from_pydata(vertices, [], faces)
    for poly in mesh.polygons:
        poly.use_smooth = True
    return mesh


def install_animation_and_lighting(positions):
    """Keep normal Blender timeline playback identical to the rendered study."""
    scene = bpy.context.scene
    for i in range(len(positions[0])):
        obj = bpy.data.objects[f'Bubble cap {i:04d}']
        obj.animation_data_clear()
        for frame, row in enumerate(positions, 1):
            obj.location = (*row[i], .025001)
            obj.keyframe_insert(data_path='location', frame=frame, group='Audited contact trajectory')
        action = obj.animation_data.action
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:
                            key.interpolation = 'LINEAR'
    # Keep large area-light reflections off the flat surface: the previous
    # oblique camera placed the patch across a distracting bright rectangle.
    for name, loc, energy, size in [('Key', (-.03, -.1, .2), 6., .25),
                                    ('Rim', (.24, -.08, .22), 4., .20)]:
        lamp = bpy.data.objects[name]
        lamp.location = loc
        lamp.data.energy, lamp.data.size = energy, size
        aim(lamp, (.145, -.005, .025))
    scene.frame_set(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if not bpy.data.filepath:
        raise ValueError('Open the prepared shear tray blend')
    args.output.mkdir(parents=True, exist_ok=False)
    initial, radii = seed()
    coarse, overlap = evolve(initial, radii, 10)
    fine, overlap_fine = evolve(initial, radii, 20)
    difference = np.linalg.norm(coarse-fine, axis=2)
    if difference.max() > .00005:
        raise RuntimeError('Timestep convergence exceeds 50 micrometres')
    if np.any(fine[:, :, 0]-radii < .001) or np.any(fine[:, :, 0]+radii > .299):
        raise RuntimeError('Patch leaves the streamwise tray bounds')
    if np.any(np.abs(fine[:, :, 1])+radii > .059):
        raise RuntimeError('Patch leaves lateral bounds')
    # Contact corrections must be pairwise equal and opposite. Their centroid
    # therefore follows the exact affine shear, despite individual contact drift.
    seconds = np.arange(73)/24
    expected_center = np.tile(initial.mean(axis=0), (73, 1))
    expected_center[:, 0] += (SPEED+SHEAR*initial[:, 1].mean())*seconds
    centroid_error = np.linalg.norm(fine.mean(axis=1)-expected_center, axis=1).max()
    if centroid_error > 1e-10:
        raise RuntimeError('Contact projection changed centroid transport')
    scene = bpy.context.scene
    bpy.data.objects['Passive foam layer'].hide_render = True
    mat = bpy.data.materials.new('Uncalibrated thin water film')
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (1., 1., 1., 1.)
    bsdf.inputs['Roughness'].default_value = .015
    bsdf.inputs['IOR'].default_value = 1.333
    bsdf.inputs['Transmission Weight'].default_value = 1.
    bsdf.inputs['Thin Wall'].default_value = True
    bsdf.inputs['Thin Film Thickness'].default_value = 450.
    bsdf.inputs['Thin Film IOR'].default_value = 1.333
    for i, (xy, radius) in enumerate(zip(initial, radii)):
        obj = bpy.data.objects.new(f'Bubble cap {i:04d}', cap_mesh(radius))
        bpy.context.collection.objects.link(obj)
        obj.location = (*xy, .025001)
        obj.data.materials.append(mat)
        obj['bubble_index'] = i
        obj['footprint_radius_m'] = float(radius)
    scene.camera.location = (.17, -.13, .21)
    aim(scene.camera, (.145, -.005, .025))
    scene.camera.data.ortho_scale = .16
    scene.cycles.max_bounces = 16
    scene.cycles.transmission_bounces = 12
    scene.cycles.transparent_max_bounces = 16
    install_animation_and_lighting(fine)
    trajectory = args.output/'trajectories.json'
    trajectory.write_text(json.dumps(dict(fps=24, positions_xy_m=fine.tolist(),
                                          footprint_radii_m=radii.tolist())))
    audit = dict(bubbles=len(radii), frames=73, timestep_seconds=1/480,
                 maximum_overlap_m=overlap_fine,
                 coarse_maximum_overlap_m=overlap,
                 maximum_timestep_halving_difference_m=float(difference.max()),
                 maximum_centroid_error_m=float(centroid_error),
                 trajectory_sha256=hashlib.sha256(trajectory.read_bytes()).hexdigest(),
                 projected_area_m2=float(np.sum(np.pi*radii*radii)),
                 contact_model='Overdamped equal-mobility hard-disk projection, no fluid feedback',
                 scope='Kinematic/contact invariants only; no validation of physical foam dynamics')
    (args.output/'contact-audit.json').write_text(json.dumps(audit, indent=2))
    blend = (args.output/'feature.blend').resolve()
    setup = dict(case='surface-bubble', blend=str(blend), fps=24, frames=73,
                 model='Prescribed shear, projected non-overlapping disks and shallow thin-film caps',
                 dimensions_m=[.3, .12, .025], cap_height_over_footprint_radius=.4,
                 film_thickness_nm=450, water_ior=1.333,
                 physical_accuracy_accepted=False, visual_accuracy_accepted=False,
                 limitations='Above-surface optical/contact prototype only. Assumed cap shape and film thickness; no submerged cavities or menisci, capillary attraction, drainage, merging, bursting, formation, fluid feedback or multi-layer froth. Not calibrated foam.')
    (args.output/'setup.json').write_text(json.dumps(setup, indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    print('BUBBLE_CAP_PREPARED', json.dumps(audit), flush=True)


if __name__ == '__main__':
    main()
