"""Audit NEW one-sided surface sampling against preserved native eddy fields.

No trajectories, renderer corrections, secondary relabeling or cache writes.
Mesh/field discrepancies are measured, not hidden with marker offsets.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy
import numpy as np
import openvdb
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_feature_surface_mac import SurfaceMacField
from water_feature_geometry import world_coordinates
from water_feature_solid_clip import EDDY_SOLIDS, clipped_surface, remove_surface
from audit_water_feature_mesh_contact import topology


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def quantiles(values):
    return np.quantile(values, [0, .05, .5, .95, 1]).tolist() if values else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--calibration', type=Path, required=True)
    parser.add_argument('--frames', type=int, nargs='+', default=[168, 192, 214])
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    source, root = Path(bpy.data.filepath), Path(bpy.data.filepath).parent
    setup, cal = [json.loads(p.read_text()) for p in (root/'setup.json', args.calibration)]
    if (setup['case'] != 'eddy' or not setup.get('grid_aligned_domain')
            or not cal['passed'] or cal['blender'] != bpy.app.version_string
            or cal['domain_dimensions_m'] != setup['dimensions_m']
            or any(cal[k] != setup[k] for k in ('fps', 'resolution'))
            or cal.get('simulation_method', 'FLIP') != setup.get('simulation_method', 'FLIP')
            or any(not 1 <= f <= setup['frames'] for f in args.frames)):
        raise ValueError('Matched aligned native eddy fields/calibration required')
    hashes = {str(p.resolve()): digest(p) for p in (source, root/'setup.json', args.calibration)}
    rows = []
    for frame in args.frames:
        bpy.context.scene.frame_set(frame)
        native = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        state = native.modifiers[0].domain_settings
        shape = tuple(state.domain_resolution)
        h = max(setup['dimensions_m'])/setup['resolution']
        np.testing.assert_allclose(np.asarray(state.cell_size), h, atol=1e-6, rtol=0)
        origin = np.asarray(native.matrix_world.translation)-np.asarray(shape)*h/2
        data, mesh_path = root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb', root/'cache'/'mesh'/f'fluid_mesh_{frame:04d}.bobj.gz'
        for path in (data, mesh_path):
            hashes[str(path.resolve())] = digest(path)
        arrays = [np.empty(shape, np.float32), np.empty(shape, np.float32), np.empty((*shape, 3), np.float32)]
        for name, array in zip(('phi', 'phi_obstacle', 'velocity'), arrays):
            grid = openvdb.read(str(data), name)
            assert tuple(grid.metadata['file_base_resolution']) == shape
            if name == 'velocity' and grid.metadata['class'] != 'staggered':
                raise ValueError('Staggered native MAC velocity required')
            grid.copyToArray(array)
        np.testing.assert_array_equal(np.asarray(state.velocity_grid[:]).reshape((*shape[::-1], 3)).transpose(2, 1, 0, 3), arrays[2])
        scale = cal['inferred_raw_velocity_to_mps']/setup['resolution']
        fields = [SurfaceMacField(*arrays, origin, (h, h, h), scale, radius_cells=radius) for radius in (2.5, 3.5)]
        derived = clipped_surface(native, [bpy.data.objects[name] for name in EDDY_SOLIDS],
                                  union_solids=True, contact_materials=True, triangulated=True, constrained=True)
        try:
            mesh = derived.data
            mesh.calc_loop_triangles()
            vertices = world_coordinates([v.co[:] for v in mesh.vertices], derived.matrix_world)
            triangles = np.array([t.vertices[:] for t in mesh.loop_triangles], np.int64)
            if topology(triangles) != dict(boundary_edges=0, nonmanifold_edges=0):
                raise ValueError('Require the closed actual render extraction')
            tree = BVHTree.FromPolygons(vertices.tolist(), triangles.tolist(), all_triangles=True)
            samples, no_crossing = [], 0
            # Prespecified regular columns, not selected successful tracers.
            for i in range(12, shape[0]-6, 4):
                for j in range(3, shape[1]-3, 3):
                    profile = arrays[0][i, j]
                    crossings = np.flatnonzero((profile[:-1] < 0) & (profile[1:] >= 0))
                    if not len(crossings):
                        no_crossing += 1
                        continue
                    k = int(crossings[-1])
                    fraction = -float(profile[k])/(float(profile[k+1])-float(profile[k]))
                    p = origin+(np.array((i, j, k), float)+.5)*h
                    p[2] += fraction*h
                    fitted = [field.sample(p) for field in fields]
                    phi = fields[0].surface(p)
                    nearest, _, _, distance = tree.find_nearest(p)
                    ray, _, _, _ = tree.ray_cast((p[0], p[1], origin[2]+shape[2]*h), (0, 0, -1))
                    samples.append(dict(column=[i, j], position_m=p.tolist(),
                        supported_surface=phi is not None,
                        phi_residual_m=float(phi[0]) if phi is not None else None,
                        levelset_normal=phi[1].tolist() if phi is not None else None,
                        nearest_render_surface_distance_m=float(distance) if nearest is not None else None,
                        top_render_height_minus_phi_zero_m=float(ray.z-p[2]) if ray is not None else None,
                        fits=[dict(velocity_mps=value[0].tolist(), diagnostics=value[1]) if value else None for value in fitted],
                        radius_sensitivity_mps=float(np.linalg.norm(fitted[0][0]-fitted[1][0])) if all(value is not None for value in fitted) else None))
            supported = [[s for s in samples if s['fits'][index] is not None] for index in (0, 1)]
            row = dict(frame=frame, total_columns=len(samples)+no_crossing, no_zero_crossing_columns=no_crossing,
                interface_columns=len(samples), supported_fit_counts=[len(group) for group in supported],
                render_geometry_sha256=hashlib.sha256(vertices.tobytes()+triangles.tobytes()).hexdigest(),
                nearest_render_surface_distance_m_quantiles=quantiles([s['nearest_render_surface_distance_m'] for s in samples if s['nearest_render_surface_distance_m'] is not None]),
                top_render_height_minus_phi_zero_m_quantiles=quantiles([s['top_render_height_minus_phi_zero_m'] for s in samples if s['top_render_height_minus_phi_zero_m'] is not None]),
                radius_sensitivity_mps_quantiles=quantiles([s['radius_sensitivity_mps'] for s in samples if s['radius_sensitivity_mps'] is not None]),
                maximum_component_fit_rms_mps=[max((c['weighted_rms_mps'] for s in group for c in s['fits'][index]['diagnostics']['components']), default=None) for index, group in enumerate(supported)],
                samples=samples)
            rows.append(row)
            print('SURFACE_MAC_FRAME', json.dumps({key: value for key, value in row.items() if key != 'samples'}), flush=True)
        finally:
            remove_surface(derived)
    if any(digest(Path(path)) != expected for path, expected in hashes.items()):
        raise ValueError('Preserved original input changed')
    report = dict(complete=True, accepted=False, originals_unchanged=True, source_blend=str(source),
        model='NEW one-sided weighted affine continuation from strict liquid/liquid native MAC faces',
        calibration_sha256=digest(args.calibration), raw_grid_velocity_to_mps=scale,
        original_input_sha256=hashes, source_code_sha256={p.name: digest(p) for p in (Path(__file__), Path(__file__).with_name('water_feature_surface_mac.py'))},
        radius_cells=[2.5, 3.5], frames=rows,
        limitations='Frozen snapshot diagnostics only. Spatial affine continuation is an inferred approximation, not native solver extrapolation or accepted hydrodynamics. Positive sampled solid segments are not exact collider proof. Topmost column crossings and nearest/top rendered distances are sampled geometry comparisons, not enclosed-volume/parity classification. No marker animation, foam phases, time interpolation, source geometry adjustment, mesh offset or cache write. Strict interior sampler unchanged; missing fits stay missing.')
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)


if __name__ == '__main__':
    main()
