"""Compare a small prescribed-boundary window against a padded periodic control.

Manufactured right-going small-amplitude pulse, not measured river motion.
This measures window-boundary contamination without calling it reflection-free
or a physical wave validation. Both paths use the same nonlinear PDE reference.
The larger control must be checked for boundary/wrap influence separately.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from total_depth_bank_replay import advance


def channel_boundary(stage, rest_depth):
    """Rest-state exterior at x ends, reflecting sidewalls at y ends.

    Mirror the CURRENT stage's depth/tangential momentum across sidewalls.
    The zero normal face velocity/derivative is prescribed by the wall, not
    obtained by treating a sampled ghost-centre velocity as a face velocity.
    """
    ny, nx = stage.shape[:2]
    exterior = np.zeros((2*(ny+nx), 4)); exterior[:, 0] = rest_depth
    exterior[2*ny:2*ny+nx, :3] = stage[0, :, :3]*[1, 1, -1]
    exterior[2*ny+nx:, :3] = stage[-1, :, :3]*[1, 1, -1]
    return exterior, np.zeros(len(exterior)), np.zeros((len(exterior), 2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=16.)
    parser.add_argument('--padding-m', type=float, default=80.)
    args = parser.parse_args()
    if args.report.exists(): raise FileExistsError(args.report)
    if not 0 < args.seconds <= 20 or args.padding_m < 80 or args.padding_m % .5:
        raise ValueError('Explicit bounded time and full-cell padding required')
    dx, width, h0, amplitude, sigma, centre, gravity = .5, 40., 1., .001, 1.5, 12., 9.81
    states = {}; statistics = {}; histories = {}
    implementation_hashes = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in ('audit_prescribed_boundary_wave.py', 'total_depth_bank_replay.py', 'total_depth_nonlinear_pressure.py')}
    kwargs = dict(second_order=True, dispersive=True, pressure_model='rational_sgn',
        pressure_interpolation='depth_weighted', pressure_formulation='kinematic', pressure_bed_slope='geometry')
    for name, pad in (('prescribed_window', 0.), ('padded_periodic_control', args.padding_m)):
        nx = int((width+2*pad)/dx); x = -pad+(np.arange(nx)+.5)*dx
        eta = amplitude*np.exp(-.5*((x-centre)/sigma)**2)
        # Linear shallow-water right-going initialization is not an exact
        # nonlinear/dispersive travelling-wave solution. Same pulse in both runs.
        initial = np.stack((h0+eta, np.sqrt(gravity*h0)*eta, eta*0), axis=-1)[None]
        bed = np.zeros((1, nx)); history = []
        def boundary(time, stage): return channel_boundary(stage, h0)
        def checkpoint(value, status):
            start = int(pad/dx); history.append((value[:, start:start+int(width/dx)].copy(), status))
            print(json.dumps(dict(run=name, **status), allow_nan=False), flush=True)
        state, stats = advance(initial, bed, dx, args.seconds, max_trials=10000,
            periodic=pad > 0, boundary_at_time=boundary if pad == 0 else None,
            progress_every_seconds=4., on_checkpoint=checkpoint, **kwargs)
        states[name] = state; statistics[name] = stats; histories[name] = history
    x = (np.arange(int(width/dx))+.5)*dx
    initial_eta = amplitude*np.exp(-.5*((x-centre)/sigma)**2)
    initial_energy = float(gravity*np.sum(initial_eta**2)*dx)
    comparisons = []
    for (window, a), (control, b) in zip(histories['prescribed_window'], histories['padded_periodic_control']):
        if a['elapsed_s'] != b['elapsed_s']: raise ValueError('Mismatched comparison times')
        delta = window-control
        error_energy = float(np.sum(.5*gravity*delta[..., 0]**2+.5*delta[..., 1]**2/h0)*dx)
        comparisons.append(dict(elapsed_s=a['elapsed_s'], depth_difference_max_m=float(abs(delta[..., 0]).max()),
            linearized_difference_energy_over_initial=error_energy/initial_energy,
            scope='Boundary-window difference, not a separated reflected-wave coefficient'))
    control = states['padded_periodic_control']
    edge = np.concatenate((control[:, :10], control[:, -10:]), axis=1)
    result = dict(schema='raftsim.prescribed_boundary_wave.v2', scope=__doc__, scene_accepted=False,
        sidewalls='Current-stage mirrored depth/tangential momentum; zero normal face velocity and derivative',
        boundary_qualified=False, source='manufactured Gaussian pulse', amplitude_m=amplitude,
        sigma_m=sigma, centre_m=centre, cell_m=dx, window_width_m=width, padding_m=args.padding_m,
        duration_s=args.seconds, statistics=statistics, comparisons=comparisons,
        control_outer_5m_max_depth_perturbation_m=float(abs(edge[..., 0]-h0).max()),
        control_outer_5m_max_momentum=float(abs(edge[..., 1]).max()),
        implementation_hashes=implementation_hashes)
    with args.report.open('x') as output: json.dump(result, output, indent=2, allow_nan=False)
    print(json.dumps(result, indent=2, allow_nan=False), flush=True)


if __name__ == '__main__': main()
