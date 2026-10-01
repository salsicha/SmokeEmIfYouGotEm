"""Sample calibrated grid flux below a nozzle from existing base-liquid data.

Liquid occupancy is reconstructed from level sets bracketing each z face.
Optional bilinear partial-face quadrature refines whole-face sign counting,
but this remains a diagnostic, not a conservative boundary budget/source meter.
"""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from water_feature_plane_flux import partial_face_flux


def plane_flux(phi, solid_phi, velocity_xyz, k, spacing, scale):
    """MAC z component is on the lower face of cell k, not its center.

    Average neighboring level sets to estimate face occupancy. Whole-face
    sign quadrature is deliberately approximate, not a cut-cell budget.
    Arrays here all use VDB (x, y, z) ordering.
    """
    if phi.shape != solid_phi.shape or velocity_xyz.shape != (*phi.shape, 3):
        raise ValueError('Inconsistent grid layout')
    if not 1 <= k < phi.shape[2]:
        raise ValueError('Need two interior cells bracketing the sampled face')
    mask = ((phi[:, :, k-1]+phi[:, :, k]) < 0) & ((solid_phi[:, :, k-1]+solid_phi[:, :, k]) >= 0)
    downward = -velocity_xyz[:, :, k, 2]*scale
    area = float(spacing[0]*spacing[1])
    q = downward[mask]*area
    return dict(occupied_faces=int(mask.sum()), liquid_area_m2=int(mask.sum())*area,
                signed_downward_flux_m3s=float(q.sum()),
                downward_only_flux_m3s=float(q[q > 0].sum()),
                upward_only_flux_m3s=float(-q[q < 0].sum()),
                mean_downward_velocity_mps=float(downward[mask].mean()) if mask.any() else None)


def inlet_extent(phi_inflow, origin, spacing, nozzle_center_xy, inner_radius, nozzle_bottom):
    """Negative inflow cell centers only, not exact source/collider overlap."""
    indices = np.argwhere(phi_inflow < 0)
    row = dict(negative_cells=len(indices), center_bbox_min_m=None, center_bbox_max_m=None,
               negative_centers_below_nozzle=0, negative_centers_outside_inner_radius=0)
    if len(indices):
        world = np.asarray(origin)+(indices+.5)*np.asarray(spacing)
        row.update(center_bbox_min_m=world.min(axis=0).tolist(), center_bbox_max_m=world.max(axis=0).tolist(),
                   negative_centers_below_nozzle=int(np.sum(world[:, 2] < nozzle_bottom)),
                   negative_centers_outside_inner_radius=int(np.sum(np.linalg.norm(world[:, :2]-nozzle_center_xy, axis=1) > inner_radius)))
    return row


def main():
    import bpy
    import openvdb
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--calibration', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--frames', type=int, nargs='+', required=True)
    parser.add_argument('--heights', type=float, nargs='+', default=[1.30, 1.35])
    parser.add_argument('--face-subdivisions', type=int, nargs='+', default=[])
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.output.exists():
        raise FileExistsError(args.output)
    root = Path(bpy.data.filepath).parent
    setup = json.loads((root/'setup.json').read_text())
    calibration = json.loads(args.calibration.read_text())
    assert calibration['passed'] and calibration['blender'] == bpy.app.version_string
    assert calibration['domain_dimensions_m'] == setup['dimensions_m']
    assert calibration['resolution'] == setup['resolution'] and calibration['fps'] == setup['fps']
    assert calibration.get('simulation_method', 'FLIP') == setup.get('simulation_method', 'FLIP')
    scale = calibration['inferred_raw_velocity_to_mps']/setup['resolution']
    rows = []
    source_rows = []
    mapping = None
    for frame in args.frames:
        bpy.context.scene.frame_set(frame)
        obj = bpy.data.objects['Feature liquid'].evaluated_get(bpy.context.evaluated_depsgraph_get())
        state = obj.modifiers[0].domain_settings
        dims = tuple(state.domain_resolution)
        raw = np.asarray(state.velocity_grid[:]).reshape((*dims[::-1], 3))
        assert np.isfinite(raw).all() and raw.size > 0
        path = root/'cache'/'data'/f'fluid_data_{frame:04d}.vdb'
        phi = openvdb.read(str(path), 'phi')
        assert tuple(phi.metadata['file_base_resolution']) == dims
        values = np.empty(dims, np.float32)
        phi.copyToArray(values)
        obstacle = openvdb.read(str(path), 'phi_obstacle')
        solids = np.empty(dims, np.float32)
        obstacle.copyToArray(solids)
        origin = np.array(obj.matrix_world @ state.start_point)
        spacing = np.array(state.cell_size)
        # Blender maps rounded base-resolution cells over its actual object
        # bounds. VDB's isotropic storage transform has no object translation;
        # it is NOT the engine's anisotropic index-to-world mapping.
        np.testing.assert_allclose(np.array(obj.dimensions)/dims, spacing, rtol=1e-5)
        np.testing.assert_allclose(np.array(obj.matrix_world.to_3x3()), np.eye(3), atol=1e-6)
        native_velocity = openvdb.read(str(path), 'velocity')
        assert native_velocity.metadata['class'] == 'staggered'
        velocity = np.empty((*dims, 3), np.float32)
        native_velocity.copyToArray(velocity)
        np.testing.assert_array_equal(raw.transpose(2, 1, 0, 3), velocity)
        assert np.isfinite(values).all() and np.isfinite(solids).all()
        current_mapping = dict(origin_m=origin.tolist(), engine_cell_size_m=spacing.tolist(),
                               vdb_storage_voxel_size_m=list(phi.transform.voxelSize()),
                               vdb_storage_origin=list(phi.transform.indexToWorld((0, 0, 0))),
                               grid_dimensions=list(dims), native_velocity_layout_matches=True)
        if mapping is not None and mapping != current_mapping:
            raise ValueError('Unexpected changing domain mapping')
        mapping = current_mapping
        if frame > 1:  # Frame 1 also contains the initial GEOMETRY pool.
            inflow = np.empty(dims, np.float32)
            openvdb.read(str(path), 'phi_inflow').copyToArray(inflow)
            assert np.isfinite(inflow).all()
            source_rows.append(dict(frame=frame,
                               **inlet_extent(inflow, origin, spacing, setup['jet_center_xy_m'],
                                              setup['nozzle_inner_radius_m'], setup['nozzle_z_bounds_m'][0])))
        for height in args.heights:
            k = int(round((height-origin[2])/spacing[2]))
            if not 1 <= k < dims[2]:
                raise ValueError('Need two interior cells bracketing the plane')
            refined = [partial_face_flux((values[:, :, k-1]+values[:, :, k])*.5,
                                        (solids[:, :, k-1]+solids[:, :, k])*.5,
                                        -velocity[:, :, k, 2]*scale, spacing[:2], n)
                       for n in args.face_subdivisions]
            rows.append(dict(frame=frame, requested_height_m=height,
                             sampled_height_m=float(origin[2]+k*spacing[2]),
                             partial_face_refinement=refined,
                             **plane_flux(values, solids, velocity, k, spacing, scale)))
    report = dict(frames=rows, nominal_source_flux_m3s=setup['nominal_flux_m3s'],
                  inflow_cell_center_extent=source_rows,
                  coordinate_mapping=mapping,
                  raw_grid_to_mps=scale, calibration_gravity_relative_error=calibration['gravity_relative_error'],
                  accepted=False,
                  scope='Staggered z-face velocity, neighboring level-set reconstruction and calibrated readback. Optional bilinear partial-face quadrature refines occupancy, not underlying spatial resolution. Engine cell spacing differs from VDB storage transform. Interface reconstruction, calibration uncertainty and source-region injection/storage accounting remain unresolved. Nominal area times prescribed emitter velocity is not an imposed flux boundary; gravity acts inside the volume emitter. Do not equate plane flux with exact injected volume.')
    args.output.write_text(json.dumps(report, indent=2))
    print('JET_FLUX_DIAGNOSTIC', json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
