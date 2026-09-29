"""Independent reference-condition equilibrium and pair-migration checks.

Numerical consistency is not experimental validation of water foam.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from solve_surface_bubble_equilibrium import solve
from surface_bubble_pair import migration_rate, physical_inputs, trajectory
from test_surface_bubble_equilibrium import audit


def check(data):
    equilibrium = data['equilibrium']
    model, inputs = equilibrium['model'], data['inputs']
    radius = model['gas_radius_m']
    rho, sigma, gravity = (model[k] for k in
                          ('density_kg_m3', 'tension_N_m', 'gravity_m_s2'))
    np.testing.assert_allclose(4*rho*gravity*radius**2/sigma, 1., rtol=1e-12)
    np.testing.assert_allclose(gravity*inputs['viscosity_Pa_s']**4/(rho*sigma**3),
                               inputs['morton'], rtol=1e-12)
    assert inputs == physical_inputs(model)
    rows = data['frames']
    times = np.array([row['seconds'] for row in rows])
    distances = np.array([row['distance_m'] for row in rows])
    np.testing.assert_allclose(times, np.arange(len(rows))/data['fps'], atol=1e-14)
    assert np.all(np.diff(distances) < 0) and distances[-1] > 2.5*radius
    for row in rows:
        centers = np.asarray(row['centers_xy_m'])
        np.testing.assert_allclose(centers.sum(axis=0), 0., atol=1e-15)
        np.testing.assert_allclose(np.linalg.norm(centers[1]-centers[0]), row['distance_m'])
        speed = -migration_rate(row['distance_m'], model, inputs)/2
        np.testing.assert_allclose(speed, row['single_bubble_speed_mps'], rtol=1e-12)
        np.testing.assert_allclose(rho*speed*2*radius/inputs['viscosity_Pa_s'],
                                   row['reynolds_diameter'], rtol=1e-12)
        assert 0 < row['reynolds_diameter'] < 1
    # A distinct midpoint time grid checks both the saved clock and RK4 path.
    halfway = trajectory(model, inputs, substeps=8, seconds=times[-1], fps=2*data['fps'])
    np.testing.assert_allclose([r['distance_m'] for r in halfway[::2]], distances,
                               rtol=0, atol=1e-9)
    try:
        migration_rate(2.49*radius, model, inputs)
    except ValueError:
        pass
    else:
        raise AssertionError('Excluded near-contact regime was allowed')
    saved_audit = audit(equilibrium)
    refined = solve(radius=radius, steps=2048, initial=equilibrium['parameters_log'])
    extended = solve(radius=radius, steps=2048, far_lengths=16., initial=refined['parameters_log'])
    audits = [saved_audit, audit(refined), audit(extended)]
    keys = ('rim_radius_m', 'rim_height_m', 'cap_curvature_radius_m', 'cavity_bottom_z_m')
    differences = {key: abs(refined['model'][key]-model[key]) for key in keys}
    boundary = {key: abs(extended['model'][key]-refined['model'][key]) for key in keys}
    assert max(differences.values()) < 1e-8
    assert max(boundary.values()) < 1e-8
    assert audits[1]['independent_volume_relative_error'] != 0
    assert abs(audits[1]['independent_volume_relative_error']) < abs(audits[0]['independent_volume_relative_error'])
    return dict(equilibrium_audits=audits, refinement_difference_m=differences,
                far_boundary_difference_m=boundary, frames_checked=len(rows),
                midpoint_grid_maximum_difference_m=float(np.max(np.abs(
                    np.array([r['distance_m'] for r in halfway[::2]])-distances))),
                physical_accuracy_accepted=False, visual_accuracy_accepted=False,
                scope='Reference-condition reduced-model consistency, not coupled pair pressure balance, ordinary water, drainage or rupture.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--migration', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = check(json.loads(args.migration.read_text()))
    args.output.write_text(json.dumps(result, indent=2))
    print('PAIR_PHYSICS_TESTS', json.dumps(result), flush=True)
