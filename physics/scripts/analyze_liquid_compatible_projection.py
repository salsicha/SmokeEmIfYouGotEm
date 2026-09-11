"""Audit the candidate's actual D M G operator, not stock nearest-cell Poisson."""
import argparse
import json
from pathlib import Path
import numpy as np
from analyze_liquid_grid_readback import load_fields
from liquid_compatible_projection import constrain_velocity, divergence, gradient, shift


def audit(fields, spacing=(32.8125, 32.8125, 800/24), dt=1/60):
    velocity = fields['Velocity']
    pressure = fields['Pressure'][..., 0]
    before = fields['SimFloat'][..., 0]
    fixed, mobility, fluid = constrain_velocity(velocity, fields['SolidVelocity_Boundary'])
    if not all(np.isfinite(a).all() for a in (pressure, before)):
        raise ValueError('Nonfinite pressure or divergence')
    if not fluid.any():
        raise ValueError('No fluid cells to audit')
    stage = np.rint(fields['SolidVelocity_Boundary'][..., 3]) == 3
    # Stage cells carry prescribed hydrostatic pressure; air/solid remain zero.
    p = np.where(fluid | stage, pressure, 0.)
    expected_after = before-dt*divergence(mobility*gradient(p, spacing), spacing)
    actual_after = divergence(velocity, spacing)
    support = np.stack([shift(fluid, 1, 2-c) | shift(fluid, -1, 2-c) for c in range(3)], axis=-1)
    fixed_support = support & (mobility == 0)
    rms = lambda a: float(np.sqrt(np.mean(a*a)))
    return dict(method='collocated masked anisotropic D M G', fluid_cells=int(fluid.sum()),
                before_divergence_rms_per_s=rms(before[fluid]),
                pressure_residual_times_dt_rms_per_s=rms(expected_after[fluid]),
                final_divergence_rms_per_s=rms(actual_after[fluid]),
                predicted_vs_actual_divergence_rms_per_s=rms((expected_after-actual_after)[fluid]),
                fixed_velocity_error_max_cm_s=float(abs(fixed-velocity)[mobility == 0].max(initial=0.)),
                pressure_support_fixed_velocity_error_max_cm_s=float(abs(fixed-velocity)[fixed_support].max()) if fixed_support.any() else 0.,
                external_stage_cell_count=int(stage.sum()),
                nonfluid_nonstage_pressure_max=float(abs(pressure[~fluid & ~stage]).max(initial=0.)),
                production_promoted=False, physical_volume_calibrated=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('grid_directory', type=Path)
    parser.add_argument('report', type=Path)
    parser.add_argument('--stage-profile', type=Path)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    fields = load_fields(args.grid_directory)
    report = audit(fields)
    if args.stage_profile:
        from liquid_outlet_stage import outlet_pressure_grid
        known, expected = outlet_pressure_grid(json.loads(args.stage_profile.read_text()))
        actual = np.rint(fields['SolidVelocity_Boundary'][..., 3]) == 3
        report['stage_classification_mismatch_count'] = int((actual != known).sum())
        report['stage_pressure_max_error_cm2_s2'] = float(abs(fields['Pressure'][..., 0]-expected)[known].max(initial=0.))
    report['source'] = str(args.grid_directory)
    args.report.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps(report, indent=2, allow_nan=False))
