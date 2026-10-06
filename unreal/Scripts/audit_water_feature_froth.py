"""Audit jet motion, tank fill and phase locations against evolved geometry."""
import argparse
import json
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--calibration', type=Path, required=True)
    p.add_argument('--frames', type=int, nargs='+', default=[1, 12, 24, 48, 72, 84, 96, 120])
    args = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    setup = json.loads((Path(bpy.data.filepath).parent/'setup.json').read_text())
    cal = json.loads(args.calibration.read_text())
    if setup['case'] != 'froth' or not cal['passed'] or any(cal[k] != setup[k] for k in ('resolution', 'fps')) or cal['domain_dimensions_m'] != setup['dimensions_m'] or cal['blender'] != bpy.app.version_string:
        raise ValueError('Wrong case or unmatched calibration')
    if cal.get('simulation_method', 'FLIP') != setup.get('simulation_method', 'FLIP'):
        raise ValueError('Calibration transport method does not match the scene')
    rows = []
    settings = bpy.data.objects['Feature liquid'].modifiers[0].domain_settings
    secondary_settings = {}
    for prop in settings.bl_rna.properties:
        if 'sndparticle' in prop.identifier or prop.identifier.startswith('particle_'):
            value = getattr(settings, prop.identifier)
            if isinstance(value, (str, float, int, bool)):
                secondary_settings[prop.identifier] = value
    for frame in args.frames:
        if not 1 <= frame <= setup['frames']:
            raise ValueError('Frame outside bake')
        bpy.context.scene.frame_set(frame)
        obj = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = obj.to_mesh()
        try:
            if len(mesh.vertices) <= 8:
                raise ValueError('Missing liquid mesh cache')
            verts = [obj.matrix_world @ v.co for v in mesh.vertices]
            bvh = BVHTree.FromPolygons(verts, [list(p.vertices) for p in mesh.polygons])
            mesh.calc_loop_triangles()
            volume = sum(verts[t.vertices[0]].dot(verts[t.vertices[1]].cross(verts[t.vertices[2]]))/6 for t in mesh.loop_triangles)
            phases, jets = [], []
            primary_diagnostics = {}
            for ps in obj.particle_systems:
                count = len(ps.particles)
                pos = np.empty(count*3, np.float32)
                ps.particles.foreach_get('location', pos)
                pos = pos.reshape(-1, 3)
                if not np.isfinite(pos).all():
                    raise ValueError('Nonfinite particle locations')
                if ps.name.lower() == 'liquid':
                    raw = np.empty(count*3, np.float32)
                    ps.particles.foreach_get('velocity', raw)
                    vel = raw.reshape(-1, 3)*cal['inferred_raw_velocity_to_mps']
                    radial = np.linalg.norm(pos[:, :2]-[1., 0.], axis=1)
                    for z in (.65, .9, 1.15):
                        selected = (np.abs(pos[:, 2]-z) < .03) & (radial < .2)
                        jets.append(dict(z_m=z, count=int(selected.sum()),
                            mean_vertical_mps=float(vel[selected, 2].mean()) if selected.any() else None,
                            downward_fraction=float(np.mean(vel[selected, 2] < 0)) if selected.any() else None,
                            median_radius_m=float(np.median(radial[selected])) if selected.any() else None))
                    wall = (radial > .165) & (radial < .175) & (pos[:, 2] > 1.47) & (pos[:, 2] < 1.73)
                    primary_diagnostics = dict(particles=count, deeply_below_floor=int(np.sum(pos[:, 2] < -.02)),
                                               inside_nozzle_midwall=int(wall.sum()))
                    continue
                if ps.name.lower() not in ('foam', 'spray', 'bubbles'):
                    continue
                distances = []
                # Deterministic distributed sample; no selection by desired sign.
                for i in np.linspace(0, count-1, min(count, 4096), dtype=int):
                    near, normal, _, distance = bvh.find_nearest(Vector(pos[i]))
                    if near is not None:
                        distances.append(float(distance if (Vector(pos[i])-near).dot(normal) >= 0 else -distance))
                d = np.array(distances)
                phases.append(dict(name=ps.name, count=count, sampled=len(d),
                    z_quantiles_m=np.quantile(pos[:, 2], [.05, .5, .95]).tolist() if count else None,
                    signed_nearest_mesh_distance_quantiles_m=np.quantile(d, [.05, .5, .95]).tolist() if len(d) else None,
                    fraction_within_two_cells=float(np.mean(np.abs(d) < 2*setup['approximate_cell_m'])) if len(d) else None,
                    fraction_outside_over_one_cell=float(np.mean(d > setup['approximate_cell_m'])) if len(d) else None,
                    fraction_inside_over_one_cell=float(np.mean(d < -setup['approximate_cell_m'])) if len(d) else None))
            ring = []
            for r in (.3, .5, .7):
                hits = []
                for theta in np.arange(24)*2*np.pi/24:
                    hit, _, _, _ = bvh.ray_cast(Vector((1+r*np.cos(theta), r*np.sin(theta), 1.3)), Vector((0, 0, -1)))
                    if hit is not None:
                        hits.append(hit.z)
                ring.append(dict(radius_m=r, hits=len(hits), median_height_m=float(np.median(hits)) if hits else None))
            rows.append(dict(frame=frame, seconds=(frame-1)/24,
                reconstructed_signed_volume_m3=volume, mesh_vertices=len(verts),
                primary=primary_diagnostics, jet_bands=jets, pool_rings=ring, phases=phases))
        finally:
            obj.to_mesh_clear()
        print('FROTH_AUDIT_FRAME', json.dumps(rows[-1]), flush=True)
        args.output.write_text(json.dumps(dict(complete=len(rows)==len(args.frames), source_blend=bpy.data.filepath,
            accepted=False, frames=rows, secondary_settings=secondary_settings,
            limitations='Nearest-mesh normal signs are a reconstruction diagnostic, not exact phase fractions. Primary particles are narrow-band samples. Mesh volume is not solver mass. Secondary velocities are not calibrated by primary free fall. No air volume or bubble size distribution has been measured.'), indent=2))


if __name__ == '__main__':
    main()
