"""Compare actual GPU virtual-inflow cells against the full native velocity."""
import argparse
import json
from pathlib import Path
import numpy as np
from analyze_liquid_grid_readback import load_fields


def expected_inflow(profile):
    data = np.asarray(profile['packed_vectors'], dtype=float)
    if profile['schema'] != 'raftsim.liquid_grid_boundary.v2' or data.shape != (516, 3) or not np.isfinite(data).all():
        raise ValueError('Expected finite vector boundary profile v2')
    dx, half, floor = data[2]
    dz, count, nz = data[3]
    if not np.allclose([dx, half, floor, dz, count, nz], [32.8125, 1050, 350, 800/24, 64, 24]):
        raise ValueError('Expected registered 68x68x24 review grid')
    z, y, x = np.meshgrid(floor+(np.arange(24)+.5)*dz,
        (np.arange(68)+.5)*dx-(half+2*dx), (np.arange(68)+.5)*dx-(half+2*dx), indexing='ij')
    expected = np.zeros((*x.shape, 3))
    selected = np.zeros(x.shape, dtype=bool)
    face_id = np.full(x.shape, -1, dtype=int)
    for face in range(4):
        normal, along = (x, y) if face < 2 else (y, x)
        side = normal <= -half if face % 2 == 0 else normal >= half
        outside = side & (np.abs(along) < half)
        column = np.clip(np.floor((along+half)/dx).astype(int), 0, 63)
        row = data[4+face*64+column]
        mask = outside & (row[..., 2] >= 0) & (z > row[..., 0]) & (z < row[..., 1])
        selected |= mask
        expected[mask] = data[260+face*64+column[mask]]
        face_id[mask] = face
    return selected, expected, face_id


def audit(fields, profile):
    selected, expected, face_id = expected_inflow(profile)
    boundary = fields['SolidVelocity_Boundary']
    velocity = fields['Velocity']
    if boundary.shape != (*selected.shape, 4) or velocity.shape != expected.shape:
        raise ValueError('Actual grid dimensions do not match boundary profile')
    error = np.abs(boundary[..., :3]-expected)
    # The actual stored RGBA16F values match truncation toward zero on this
    # capture, not NumPy's round-to-nearest conversion. Test exact representable
    # conversions; do not mask a binding error with a physical-speed tolerance.
    source32 = expected.astype(np.float32)
    nearest = source32.astype(np.float16)
    truncated = np.where(np.abs(nearest.astype(float)) > np.abs(source32),
        np.nextafter(nearest, np.float16(0)), nearest).astype(float)
    matches_nearest = boundary[..., :3] == nearest.astype(float)
    matches_truncated = boundary[..., :3] == truncated
    mismatch = int((np.rint(boundary[..., 3])[selected] != 1).sum())
    component_mismatch = int((~(matches_nearest | matches_truncated)[selected]).sum())
    faces = []
    for face, name in enumerate(('west', 'east', 'south', 'north')):
        mask = face_id == face
        faces.append(dict(face=name, cell_count=int(mask.sum()),
            expected_velocity_mean_cm_s=expected[mask].mean(axis=0).tolist() if mask.any() else None,
            actual_boundary_velocity_mean_cm_s=boundary[..., :3][mask].mean(axis=0).tolist() if mask.any() else None,
            actual_final_velocity_mean_cm_s=velocity[mask].mean(axis=0).tolist() if mask.any() else None))
    return dict(inflow_cells=int(selected.sum()), classification_mismatch_count=mismatch,
        velocity_component_mismatch_beyond_half_conversion=component_mismatch,
        component_count_matching_nearest=int(matches_nearest[selected].sum()),
        component_count_matching_toward_zero=int(matches_truncated[selected].sum()),
        compared_component_count=int(selected.sum()*3),
        max_boundary_velocity_error_cm_s=float(error[selected].max(initial=0)),
        boundary_binding_verified=bool(selected.any() and mismatch == 0 and component_mismatch == 0),
        faces=faces, physical_volume_calibrated=False, flow_consistency_accepted=False,
        production_promoted=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('grids', type=Path)
    parser.add_argument('profile', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = audit(load_fields(args.grids), json.loads(args.profile.read_text()))
    result['source_grids'] = str(args.grids)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(result, indent=2))
