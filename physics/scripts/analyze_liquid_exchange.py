"""Profile-weighted collocated exchange audit, NOT a conserved mass budget.

The physical interface lies halfway between its ghost and interior cell centres.
Use their average normal velocity and the native bed/stage wet aperture. An
outlet-stage ghost is not a prescribed velocity boundary. Actual liquid occupancy
and time-integrated storage still require separate measurement.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from analyze_liquid_grid_readback import load_fields
from liquid_outlet_stage import outlet_pressure_grid


def audit_exchange(fields, profile):
    outlet_pressure_grid(profile)  # Reject profiles for other fixture geometry.
    packed = np.asarray(profile['packed_vectors'], dtype=float)
    velocity = np.asarray(fields['Velocity'], dtype=float)
    boundary = np.asarray(fields['SolidVelocity_Boundary'], dtype=float)
    if velocity.shape != (24, 68, 68, 3) or boundary.shape != (24, 68, 68, 4):
        raise ValueError('Registered collocated fixture fields required')
    if not np.isfinite(velocity).all() or not np.isfinite(boundary).all():
        raise ValueError('Finite exchange fields required')
    dx, _, floor = packed[2]
    dz = packed[3, 0]
    lower = floor+np.arange(24)[:, None]*dz
    result = []
    for index, (name, axis, sign, ghost, inner) in enumerate([
            ('west', 0, 1, 1, 2), ('east', 0, -1, 66, 65),
            ('south', 1, 1, 1, 2), ('north', 1, -1, 66, 65)]):
        rows = packed[4+index*64:4+(index+1)*64]
        wet_height = np.maximum(0., np.minimum(lower+dz, rows[None, :, 1])-
                               np.maximum(lower, rows[None, :, 0]))
        area_m2 = wet_height*dx/10000
        centres = lower+.5*dz
        quantized_area = ((centres > rows[None, :, 0]) &
                          (centres < rows[None, :, 1]))*dx*dz/10000
        if axis == 0:
            vg, vi = velocity[:, 2:66, ghost, axis], velocity[:, 2:66, inner, axis]
            types = boundary[:, 2:66, inner, 3]
        else:
            vg, vi = velocity[:, ghost, 2:66, axis], velocity[:, inner, 2:66, axis]
            types = boundary[:, inner, 2:66, 3]
        midpoint = sign*(vg+vi)*.5/100
        native = rows[None, :, 2]/100
        result.append(dict(face=name, native_wet_area_m2=float(area_m2.sum()),
            # Profile speed is normalized for centre-selected whole cells. A
            # fractional-aperture integral of that speed is NOT the native Q.
            profile_velocity_over_partial_aperture_inward_m3s=float((native*area_m2).sum()),
            quantized_prescribed_target_inward_m3s=float((native*quantized_area).sum()),
            midpoint_quantized_wet_inward_m3s=float((midpoint*quantized_area).sum()),
            midpoint_profile_weighted_inward_m3s=float((midpoint*area_m2).sum()),
            interior_profile_weighted_inward_m3s=float((sign*vi/100*area_m2).sum()),
            ghost_profile_weighted_inward_m3s=float((sign*vg/100*area_m2).sum()),
            native_aperture_adjacent_solid_m2=float(area_m2[np.rint(types) == 1].sum()),
            native_aperture_adjacent_air_m2=float(area_m2[np.rint(types) == 2].sum())))
    return dict(method='collocated midpoint normal velocity over native bed/stage aperture',
        sign='positive inward', faces=result,
        quantized_prescribed_net_inward_m3s=sum(f['quantized_prescribed_target_inward_m3s'] for f in result),
        midpoint_quantized_net_inward_m3s=sum(f['midpoint_quantized_wet_inward_m3s'] for f in result),
        midpoint_profile_weighted_net_inward_m3s=sum(f['midpoint_profile_weighted_inward_m3s'] for f in result),
        physical_volume_calibrated=False, time_integrated_mass_budget=False,
        actual_free_surface_aperture_measured=False, production_promoted=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('grids', type=Path)
    parser.add_argument('profile', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = audit_exchange(load_fields(args.grids), json.loads(args.profile.read_text()))
    result['source_grids'] = str(args.grids)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(result, indent=2, allow_nan=False))
