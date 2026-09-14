"""Audit actual GPU inputs before a finite-amplitude solver migration.

No captured values are clipped or rewritten. A local nonlinear characteristic
estimate is not a measured phase speed, GPU CFL proof, or scene acceptance.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from audit_detail_wave_regime import read_snapshot
from detail_nonlinear_flux import G, mean_strain_source, simple_wave, advance_periodic


def analyze(flow, state, cell_m):
    if (flow.shape != state.shape or flow.ndim != 3 or flow.shape[-1] != 4
            or not np.all(np.isfinite(flow)) or not np.all(np.isfinite(state))
            or np.any(flow[..., 0] < 0) or np.any(state[..., 3] < 0)
            or not np.isfinite(cell_m) or cell_m <= 0):
        raise ValueError("Invalid captured arrays/spacing")
    wet = flow[..., 0] > .01
    if not np.any(wet):
        raise ValueError("No wet captured cells")
    h0, eta, q = flow[..., 0][wet].astype(float), state[..., 0][wet].astype(float), state[..., 1:3][wet].astype(float)
    h = h0 + eta
    result = dict(wet_cells=int(wet.sum()), nonpositive_total_depth_cells=int(np.sum(h <= 0)),
        minimum_total_depth_m=float(h.min()), maximum_relative_elevation=float(np.max(abs(eta) / h0)),
        elevation_rms_m=float(np.sqrt(np.mean(eta**2))), maximum_abs_elevation_m=float(np.max(abs(eta))))
    if np.any(h <= 0):
        result['nonlinear_migration_admissible'] = False
        return result
    velocity = flow[..., 1:3][wet].astype(float)
    relative_velocity = q / h[:, None]
    signal = np.sum(abs(velocity + relative_velocity), axis=-1) + 2*np.sqrt(G*h)
    baseline_signal = np.sum(abs(velocity), axis=-1) + 2*np.sqrt(G*h0)
    result.update(nonlinear_migration_admissible=None,
        maximum_relative_velocity_mps=float(np.max(np.linalg.norm(relative_velocity, axis=1))),
        maximum_background_signal_mps=float(baseline_signal.max()), maximum_nonlinear_signal_mps=float(signal.max()),
        instantaneous_nonlinear_cfl_at_120hz=float(signal.max()/120/cell_m),
        # The old caller bounds only the prescribed mean. This diagnostic is
        # one instant, not the maximum across later states/RK reconstructed faces.
        cfl_verified_for_future_stages=False)
    interior = wet.copy()
    gradient = np.zeros((*wet.shape, 2, 2))
    for axis in (0, 1):
        grid_axis = 1-axis
        interior &= np.roll(wet, -1, grid_axis) & np.roll(wet, 1, grid_axis)
        gradient[..., :, axis] = (np.roll(flow[..., 1:3], -1, grid_axis)-np.roll(flow[..., 1:3], 1, grid_axis))/(2*cell_m)
    interior[[0, -1], :] = False
    interior[:, [0, -1]] = False
    strain = mean_strain_source(state[..., :3][interior], gradient[interior])
    norms = np.linalg.norm(strain, axis=-1)
    result.update(interior_gradient_cells=int(interior.sum()),
        maximum_mean_strain_source_m2s2=float(norms.max()) if norms.size else None,
        rms_mean_strain_source_m2s2=float(np.sqrt(np.mean(norms**2))) if norms.size else None)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshots', nargs='+', type=Path)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--mean-strain-integrated', action='store_true',
                        help='Caller declaration for this captured build, not inferred from arrays')
    args = parser.parse_args()
    report = dict(schema='raftsim.nonlinear_detail_input_audit.v3', scene_accepted=False,
        nonlinear_transport_integrated=False, reference_video_viewed=False,
        mean_strain_integrated_caller_declaration=args.mean_strain_integrated,
        scope='Actual captured flow/state applicability and independent constant-background analytic verification; not variable-river, dispersive, post-breaking or foam acceptance. v2 accounts for the mean owning its acceleration/bed balance: relative source is -(q dot grad)U, not -((U eta+q) dot grad)U.', snapshots=[], simple_wave=[])
    for path in args.snapshots:
        metadata, arrays, hashes = read_snapshot(path)
        report['snapshots'].append(dict(path=str(path.resolve()), metadata=metadata, hashes=hashes,
            analysis=analyze(arrays['flow'], arrays['state'], metadata['cell_m'])))
    for count in (200, 400):
        dx = 40/count
        x = (np.arange(count)+.5)*dx
        initial = simple_wave(x, 0)
        actual, stats = advance_periodic(initial, 1.5, [.4, 0], dx, 1.2)
        exact = simple_wave(x, 1.2)
        stats.update(cells=count, explicitly_authored_probe=True, depth_m=1.5, amplitude_m=.45,
            wavelength_m=40, current_mps=.4, mean_abs_height_error_m=float(np.mean(abs(actual[:, 0]-exact[:, 0]))),
            maximum_conserved_sum_error=float(np.max(abs(actual.sum(axis=0)-initial.sum(axis=0)))),
            analytic_max_slope_initial=float(np.max(abs(np.gradient(initial[:, 0], dx)))),
            analytic_max_slope_final=float(np.max(abs(np.gradient(exact[:, 0], dx)))))
        report['simple_wave'].append(stats)
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
