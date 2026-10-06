"""Inspect the isolated boulder: initial solid exclusion or cached flow evidence.

Particle directions and surface heights are diagnostics, not pressure or mass
validation. This file never saves the blend or changes the fluid cache.
"""
import argparse
import json
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def tree(obj):
    mesh = obj.to_mesh()
    try:
        return BVHTree.FromPolygons([obj.matrix_world @ v.co for v in mesh.vertices],
                                   [list(p.vertices) for p in mesh.polygons])
    finally:
        obj.to_mesh_clear()


def inside(bvh, point):
    hit, normal, _, _ = bvh.ray_cast(Vector(point), Vector((0., 0., 1.)))
    return hit is not None and normal.z > 1e-6


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--initial-only', action='store_true')
    parser.add_argument('--frames', type=int, nargs='+', default=[168, 192, 216, 240])
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    setup = json.loads((Path(bpy.data.filepath).parent/'setup.json').read_text())
    if setup['case'] != 'boulder-pillow':
        raise ValueError('Boulder case required')
    center, radii = np.array(setup['obstacle_center_m']), np.array(setup['obstacle_radii_m'])
    rock = bpy.data.objects['Single boulder']
    rock_tree = tree(rock)
    if not any(m.type == 'FLUID' and m.fluid_type == 'EFFECTOR' for m in rock.modifiers):
        raise ValueError('Visible boulder has no physical collider')
    if args.initial_only:
        water = tree(bpy.data.objects['Initial wave flume water'])
        points = [[x,y,z] for x in np.linspace(2.7,3.3,7)
                  for y in np.linspace(-.2,.2,5) for z in [.1,.2,.3]]
        inner = [p for p in points if inside(rock_tree,p)]
        overlap = [p for p in inner if inside(water,p)]
        fluid_control = [inside(water,p) for p in [[2.,0.,.2],[3.,-.6,.2],[3.,.6,.2],[4.,0.,.2]]]
        report = dict(initial_only=True, solid_sample_count=len(inner),
                      initial_water_inside_rock=overlap, fluid_control_samples=fluid_control,
                      passed=bool(inner) and not overlap and all(fluid_control), accepted=False)
        if not report['passed']:
            args.output.write_text(json.dumps(report,indent=2))
            raise ValueError('Initial solid exclusion or surrounding water failed')
    else:
        rows = []
        for frame in args.frames:
            if not 1 <= frame <= bpy.context.scene.frame_end:
                raise ValueError('Frame outside bake')
            bpy.context.scene.frame_set(frame)
            obj = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
            ps = next(p for p in obj.particle_systems if p.name == 'Liquid')
            pos,vel = np.empty(len(ps.particles)*3,np.float32),np.empty(len(ps.particles)*3,np.float32)
            ps.particles.foreach_get('location',pos)
            ps.particles.foreach_get('velocity',vel)
            pos,vel=pos.reshape(-1,3),vel.reshape(-1,3)
            if not len(pos):
                raise ValueError('No liquid cache')
            q = np.linalg.norm((pos-center)/radii,axis=1)
            intrusion_depths = []
            for point in pos[q < 1.01]:
                p = Vector(point)
                hit, normal, _, _ = rock_tree.find_nearest(p)
                if hit is not None:
                    penetration = -(p-hit).dot(normal)
                    if penetration > 0:
                        intrusion_depths.append(penetration)
            near = (pos[:,0]>2.5)&(pos[:,0]<3.)&(pos[:,2]>.1)&(pos[:,2]<.7)
            left=near&(pos[:,1]<-.33)&(pos[:,1]>-.7)
            right=near&(pos[:,1]>.33)&(pos[:,1]<.7)
            surface=tree(obj)
            levels=[]
            for x,y in [(2.3,0.),(2.45,0.),(2.5,0.),(2.5,-.6),(2.5,.6),(3.5,0.)]:
                hit,_,_,_=surface.ray_cast(Vector((x,y,2.8)),Vector((0.,0.,-1.)))
                levels.append(dict(x=x,y=y,z=None if hit is None else hit.z))
            rows.append(dict(frame=frame,liquid_particles=len(pos),
                particles_deep_inside_analytic_ellipsoid=int((q<.75).sum()),
                particles_inside_analytic_ellipsoid=int((q<1).sum()),
                minimum_normalized_ellipsoid_radius=float(q.min()),
                particles_inside_mesh_by_over_1mm=sum(d > .001 for d in intrusion_depths),
                maximum_particle_mesh_intrusion_m=max(intrusion_depths,default=0.),
                left_samples=int(left.sum()),right_samples=int(right.sum()),
                left_mean_velocity_raw=vel[left].mean(axis=0).tolist() if left.any() else None,
                right_mean_velocity_raw=vel[right].mean(axis=0).tolist() if right.any() else None,
                surface_samples=levels))
        report=dict(initial_only=False,frames=rows,accepted=False,
            limitations='Raw velocities: directions only. Narrow-band particles are not volumetric samples. Analytic ellipsoid differs slightly from tessellated collider. Surface ray may hit spray; inspect rendered views.')
    report['source_blend']=bpy.data.filepath
    args.output.write_text(json.dumps(report,indent=2))
    print('OBSTACLE_AUDIT',json.dumps(report),flush=True)


if __name__ == '__main__':
    main()
