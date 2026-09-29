"""Estimate section flux from cached MAC velocities and reconstructed wet area.

Read-only diagnostic. Mesh wet area is not the solver level set, so this is not
an exact conservation residual. Uses a matching free-fall velocity calibration.
"""
import argparse
import json
from pathlib import Path
import sys
import math

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def bed_height(setup, x):
    """Authored collider height, independent of the reconstructed liquid skin."""
    if setup['case'] in ('boulder-pillow', 'eddy'):
        raise ValueError('Height-only bed clipping is invalid through a boulder; use the obstacle audit')
    if setup['case'] == 'standing-wave':
        half_length = setup['bump_length_m']/2
        offset = x-setup['bump_center_x_m']
        bump = setup['bump_height_m']*.5*(1+math.cos(math.pi*offset/half_length)) if abs(offset) < half_length else 0.
        approach = (setup.get('approach_height_m') or 0.)*(1-min(1., max(0., (x-.6)/.9)))
        return approach+bump
    shelf = setup['ledge_height_m']
    if setup['sloped_approach']:
        return shelf*(1-min(1., max(0., (x-.75)/1.45)))
    return shelf if x <= 1.8 else 0.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--calibration', type=Path, required=True)
    parser.add_argument('--frames', type=int, nargs='+', default=[120, 144, 168])
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    setup = json.loads((Path(bpy.data.filepath).parent/'setup.json').read_text())
    cal = json.loads(args.calibration.read_text())
    if not cal['passed'] or cal['resolution'] != setup['resolution'] or cal['fps'] != setup['fps'] or cal['domain_dimensions_m'] != setup['dimensions_m'] or cal['blender'] != bpy.app.version_string:
        raise ValueError('Calibration configuration mismatch')
    # Blender particles_fluid_step multiplies Manta velocity by domain dx
    # (1/resolution_max) before exposing Particle.velocity. The grid accessor
    # returns interleaved xyz without that multiplier. Source reference:
    # blender/blender v5.0.0 blenkernel/intern/particle_system.cc and
    # makesrna/intern/rna_fluid.cc. Cross-check against installed build's data.
    scale = cal['inferred_raw_velocity_to_mps']/setup['resolution']
    rows = []
    for frame in args.frames:
        scene = bpy.context.scene
        if not scene.frame_start <= frame <= scene.frame_end:
            raise ValueError('Frame outside bake')
        scene.frame_set(frame)
        obj = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        settings = obj.modifiers[0].domain_settings
        nx, ny, nz = settings.domain_resolution
        dx, dy, dz = settings.cell_size
        origin = obj.matrix_world @ Vector(settings.start_point)
        # This diagnostic deliberately only supports our applied-scale,
        # axis-aligned fixed-size laboratory cases.
        if not np.allclose(obj.matrix_world.to_3x3(), np.eye(3), atol=1e-6):
            raise ValueError('Rotated/scaled domain not supported')
        grid = np.asarray(settings.velocity_grid[:], dtype=np.float64).reshape(nz, ny, nx, 3)*scale
        if not np.isfinite(grid).all():
            raise ValueError('Nonfinite velocity grid')
        mesh = obj.to_mesh()
        try:
            if len(mesh.vertices) <= 8:
                raise ValueError('Liquid mesh missing')
            verts = [obj.matrix_world @ v.co for v in mesh.vertices]
            bvh = BVHTree.FromPolygons(verts, [list(p.vertices) for p in mesh.polygons])
            sections = []
            for requested_x in [.75, 1.125, 1.35, 1.5, 1.95, 2.25, 2.7, 3.3, 4.5, 5.25]:
                i = int(round((requested_x-origin.x)/dx))
                x = origin.x+i*dx
                wet_area = flux = negative_area = 0.
                outside_solid_area = outside_solid_flux = 0.
                bed_z = bed_height(setup, x)
                upper_area = upper_flux = lower_area = lower_flux = 0.
                wet_width = 0.
                top_heights = []
                for j in range(ny):
                    y = origin.y+(j+.5)*dy
                    top, _, _, _ = bvh.ray_cast(Vector((x, y, 4.)), Vector((0, 0, -1)))
                    if top is None:
                        continue
                    wet_width += dy
                    top_heights.append(top.z)
                    for k in range(nz):
                        area = 0.
                        allowed_area = 0.
                        for sy in (.25, .75):
                            for sz in (.25, .75):
                                p = Vector((x, origin.y+(j+sy)*dy, origin.z+(k+sz)*dz))
                                hit, normal, _, _ = bvh.ray_cast(p, Vector((0, 0, 1)))
                                # First upward intersection exits liquid iff
                                # outward surface normal faces upwards.
                                if hit is not None and normal.z > 1e-5:
                                    area += dy*dz/4
                                    if p.z >= bed_z and -.8 <= p.y <= .8:
                                        allowed_area += dy*dz/4
                        if not area:
                            continue
                        u = float(grid[k, j, i, 0])
                        z = origin.z+(k+.5)*dz
                        wet_area += area
                        flux += area*u
                        outside_solid_area += allowed_area
                        outside_solid_flux += allowed_area*u
                        negative_area += area if u < -.05 else 0.
                        if z > top.z-.18:
                            upper_area += area
                            upper_flux += area*u
                        elif .1 < z < .4 and x > 1.8:
                            lower_area += area
                            lower_flux += area*u
                sections.append(dict(x_m=x, estimated_wet_area_m2=wet_area,
                    authored_bed_z_m=bed_z,
                    estimated_area_outside_solid_m2=outside_solid_area,
                    estimated_flux_outside_solid_m3s=outside_solid_flux,
                    reconstructed_area_inside_solid_m2=wet_area-outside_solid_area,
                    estimated_bed_clipped_froude=(outside_solid_flux/outside_solid_area)/math.sqrt(9.80665*outside_solid_area/wet_width) if outside_solid_area and wet_width else None,
                    estimated_flux_m3s=flux, bulk_velocity_mps=flux/wet_area if wet_area else None,
                    reverse_area_fraction=negative_area/wet_area if wet_area else None,
                    surface_band_mean_u_mps=upper_flux/upper_area if upper_area else None,
                    lower_band_mean_u_mps=lower_flux/lower_area if lower_area else None,
                    mean_top_z_m=float(np.mean(top_heights)) if top_heights else None,
                    hydraulic_depth_m=wet_area/wet_width if wet_width else None))
            rows.append(dict(frame=frame, grid_shape_xyz=[nx, ny, nz],
                             origin_m=list(origin), cell_size_m=[dx, dy, dz], sections=sections))
        finally:
            obj.to_mesh_clear()
    report = dict(case=setup['case'], source_blend=bpy.data.filepath,
        velocity_scale_estimate=scale, frames=rows, physical_accuracy_accepted=False,
        limitations='MAC face samples with 2x2 reconstructed-mesh wet-area quadrature. Separate authored-bed-clipped flux excludes reconstructed liquid skin inside solid; original mesh-only estimates retained. Analytic bed approximates the authored sampled collider. Neither estimate is solver level-set flux or exact mass conservation. Free-fall scale calibration is configuration-specific.')
    args.output.write_text(json.dumps(report, indent=2))
    for row in rows:
        print('SECTION_FRAME', row['frame'], json.dumps(row['sections']))


if __name__ == '__main__':
    main()
