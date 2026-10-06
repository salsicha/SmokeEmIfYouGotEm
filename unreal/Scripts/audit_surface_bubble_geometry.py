"""Audit saved engine geometry, including the missing-flat-plane regression."""
from collections import Counter
import json
import math
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_surface_bubble_geometry import revolve_water, film_mesh


def closed(mesh):
    edges = Counter(tuple(sorted(edge)) for face in mesh.polygons for edge in face.edge_keys)
    assert set(edges.values()) == {2}


def ray(mesh, x):
    tree = BVHTree.FromPolygons([v.co for v in mesh.vertices], [p.vertices[:] for p in mesh.polygons])
    hit, normal, _, _ = tree.ray_cast((x,0.,.01),(0.,0.,-1.))
    assert hit is not None
    return hit.z, normal.z


def gas_mesh_volume(water, cap, rings, segments):
    # Cavity starts at the shared rim, after the outer meniscus rings.
    start = (rings-1)*segments
    pole = (2*rings-1)*segments
    water.calc_loop_triangles()
    cap.calc_loop_triangles()
    def vol(mesh, triangles):
        return sum(mesh.vertices[t.vertices[0]].co.dot(mesh.vertices[t.vertices[1]].co.cross(mesh.vertices[t.vertices[2]].co))/6 for t in triangles)
    cavity = [t for t in water.loop_triangles if all(start <= v <= pole for v in t.vertices)]
    return vol(cap,cap.loop_triangles)-vol(water,cavity)


root = Path(bpy.data.filepath).parent
report_path = root/'geometry-audit.json'
if report_path.exists():
    raise FileExistsError(report_path)
setup = json.loads((root/'setup.json').read_text())
m = setup['model']
equilibrium = (json.loads((root/'equilibrium.json').read_text())['solution']
               if setup.get('geometry_model') == 'nonlinear-young-laplace' else None)
water = bpy.data.objects['Water with actual gas cavity'].data
cap = bpy.data.objects['Bubble film'].data
closed(water)
cavity_z, cavity_normal = ray(water,0.)
cap_z, cap_normal = ray(cap,0.)
expected_bottom = m['cavity_bottom_z_m'] if equilibrium else m['cavity_center_z_m']-m['gas_radius_m']
np.testing.assert_allclose(cavity_z,expected_bottom,atol=3e-9,rtol=0)
np.testing.assert_allclose(cap_z,m['rim_height_m']+m['cap_height_above_rim_m'],atol=3e-9,rtol=0)
assert cavity_normal > .99 and cap_normal > .99
assert cavity_z < -.001 and cap_z > 0
actual_volume = gas_mesh_volume(water,cap,160,192)
coarse, _ = revolve_water(m,96,80,equilibrium=equilibrium)
coarse_cap, _ = film_mesh(m,96,16)
coarse_volume = gas_mesh_volume(coarse,coarse_cap,80,96)
analytic = m['gas_volume_m3']
assert abs(actual_volume/analytic-1) < .001
assert abs(actual_volume/analytic-1) < abs(coarse_volume/analytic-1)
# Quantify the physical approximation too: a spherical cavity has constant
# curvature while hydrostatic pressure changes with depth. Do not hide this
# error behind the much smaller tessellation error above.
gas_pressure = 4*m['tension_N_m']/m['cap_curvature_radius_m']
cavity_pressure_errors = [gas_pressure+m['density_kg_m3']*m['gravity_m_s2']*z
                         -2*m['tension_N_m']/m['gas_radius_m']
                         for z in (cavity_z,m['rim_height_m'])] if equilibrium is None else None
report = dict(saved_scene_reopened=True, closed_water_boundary=True,
    center_water_ray_z_m=cavity_z, center_cap_ray_z_m=cap_z,
    no_flat_plane_across_cavity=True, fine_mesh_gas_volume_m3=actual_volume,
    coarse_mesh_gas_volume_m3=coarse_volume, analytic_approximation_gas_volume_m3=analytic,
    fine_relative_discretization_error=actual_volume/analytic-1,
    coarse_relative_discretization_error=coarse_volume/analytic-1,
    maximum_spherical_cavity_pressure_residual_Pa=max(abs(e) for e in cavity_pressure_errors) if cavity_pressure_errors else None,
    maximum_spherical_cavity_pressure_residual_over_gas_pressure=max(abs(e) for e in cavity_pressure_errors)/gas_pressure if cavity_pressure_errors else None,
    solved_profile_fd_relative_pressure_residual=equilibrium['independent_fd_relative_pressure_residual'] if equilibrium else None,
    accepted=False, scope='Saved mesh topology, rays and spatial refinement; does not validate full Young-Laplace equilibrium, foam dynamics or optical calibration.')
report_path.write_text(json.dumps(report,indent=2))
print('SAVED_BUBBLE_GEOMETRY_AUDIT',json.dumps(report),flush=True)
