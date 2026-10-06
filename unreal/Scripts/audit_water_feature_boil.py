"""Measure simulated piston-driven upwelling, surface spreading and liquid skin.

No acceptance based on a prescribed piston alone: inspect evolved liquid.
"""
import argparse
import json
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--calibration', type=Path, required=True)
    parser.add_argument('--frames', type=int, nargs='+', default=[24, 28, 31, 34, 37, 43, 49, 61, 85, 120, 144])
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    setup = json.loads((Path(bpy.data.filepath).parent/'setup.json').read_text())
    cal = json.loads(args.calibration.read_text())
    if setup['case'] != 'boil' or not cal['passed'] or any(cal[k] != setup[k] for k in ('resolution', 'fps')) or cal['domain_dimensions_m'] != setup['dimensions_m'] or cal['blender'] != bpy.app.version_string:
        raise ValueError('Wrong experiment or velocity calibration')
    rows = []
    for frame in args.frames:
        if not 1 <= frame <= setup['frames']:
            raise ValueError('Frame outside bake')
        bpy.context.scene.frame_set(frame)
        deps = bpy.context.evaluated_depsgraph_get()
        obj = bpy.data.objects['Feature liquid'].evaluated_get(deps)
        piston = bpy.data.objects['Submerged displacement piston'].evaluated_get(deps)
        top = max((piston.matrix_world @ Vector(corner)).z for corner in piston.bound_box)
        ps = next(p for p in obj.particle_systems if p.name == 'Liquid')
        pos, vel = np.empty(len(ps.particles)*3, np.float32), np.empty(len(ps.particles)*3, np.float32)
        ps.particles.foreach_get('location', pos)
        ps.particles.foreach_get('velocity', vel)
        pos, vel = pos.reshape(-1, 3), vel.reshape(-1, 3)*cal['inferred_raw_velocity_to_mps']
        if not len(pos) or not np.isfinite(pos).all() or not np.isfinite(vel).all():
            raise ValueError('Missing/nonfinite liquid particles')
        radial = pos[:, :2]-np.array(setup['piston_center_xy_m'])
        radius = np.linalg.norm(radial, axis=1)
        radial_speed = np.sum(vel[:, :2]*radial, axis=1)/np.maximum(radius, 1e-9)
        core = (radius < .2) & (pos[:, 2] > top+.05) & (pos[:, 2] < .85)
        # Fixed near-surface band: retain its limits rather than select only
        # samples exhibiting the desired radial sign after seeing the data.
        surface = (radius > .4) & (radius < .9) & (pos[:, 2] > .45) & (pos[:, 2] < .75)
        deep = (radius < setup['piston_radius_m']-.02) & (pos[:, 2] < top-.02) & (pos[:, 2] > 0)
        mesh = obj.to_mesh()
        try:
            if len(mesh.vertices) <= 8:
                raise ValueError('Liquid mesh cache missing')
            verts = [obj.matrix_world @ v.co for v in mesh.vertices]
            bvh = BVHTree.FromPolygons(verts, [list(p.vertices) for p in mesh.polygons])
            mesh.calc_loop_triangles()
            volume = sum(verts[t.vertices[0]].dot(verts[t.vertices[1]].cross(verts[t.vertices[2]]))/6 for t in mesh.loop_triangles)
            rings = []
            for r in (0., .15, .3, .45, .6, .9, 1.2):
                heights = []
                for theta in (np.arange(16)*2*np.pi/16 if r else [0.]):
                    p = Vector((1.5+r*np.cos(theta), r*np.sin(theta), 2.))
                    hit, _, _, _ = bvh.ray_cast(p, Vector((0., 0., -1.)))
                    if hit is not None:
                        heights.append(hit.z)
                rings.append(dict(radius_m=r, hits=len(heights), median_z_m=float(np.median(heights)) if heights else None,
                                  range_z_m=[min(heights), max(heights)] if heights else None))
        finally:
            obj.to_mesh_clear()
        rows.append(dict(frame=frame, seconds=(frame-1)/setup['fps'], piston_top_z_m=top,
            liquid_particles=len(pos), deeply_inside_piston=int(deep.sum()),
            core_count=int(core.sum()), core_mean_vertical_mps=float(np.mean(vel[core, 2])) if core.any() else None,
            annulus_count=int(surface.sum()), annulus_mean_radial_mps=float(np.mean(radial_speed[surface])) if surface.any() else None,
            annulus_outward_fraction=float(np.mean(radial_speed[surface] > 0)) if surface.any() else None,
            reconstructed_signed_volume_m3=volume, radial_surface=rings))
    report = dict(source_blend=bpy.data.filepath, frames=rows, accepted=False,
        limitations='Primary particles are narrow-band samples, not volume means. Mesh volume is reconstruction diagnostic, not exact solver mass. Fixed annulus band may include submerged water; no guaranteed surface-foam transport. Piston motion alone does not prove a boil. Wall reflections, moving-solid coupling, grid/time convergence and natural-feature comparison remain open.')
    args.output.write_text(json.dumps(report, indent=2))
    for row in rows:
        print('BOIL_FRAME', json.dumps({k: v for k, v in row.items() if k != 'radial_surface'}), flush=True)


if __name__ == '__main__':
    main()
