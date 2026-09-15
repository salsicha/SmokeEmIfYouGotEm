"""Independent full canonical bracket versus nonlinear terrain metric candidate."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from finite_depth_pressure_reference import WEIGHTS
from rational_dual_energy_reference import evaluate as dual
from rational_physical_momentum_rate import physical_rate
from rational_primal_energy import evaluate as primal
from rational_terrain_metric_transport import central, stage
from smooth_rational_velocity_stage import make


def fixture(seed, n):
    phase = np.random.default_rng(seed).uniform(0, 2*np.pi, 6)
    y, x = np.meshgrid(2*np.pi*(np.arange(n)+.5)/n,
                       2*np.pi*(np.arange(n)+.5)/n, indexing='ij')
    bed = .35*np.sin(x+phase[0])*np.cos(y+phase[1])+.2*np.cos(2*x-y+phase[2])
    h = 1.5-.6*bed+.12*np.sin(x-y+phase[3])
    u = np.stack((.7+.3*np.sin(x+y+phase[3])+.1*np.cos(2*y+phase[4]),
                  .2+.2*np.cos(x-y+phase[4])+.1*np.sin(2*x+phase[5])), axis=-1)
    return make(h, bed, 16/n), h[..., None]*u


def potential_control(g, p, *, preconditioner='spectral-frozen-depth'):
    """Original dual poles, stationary depth potential and canonical curl.

    Continuum auxiliary term is -1.5 lambda (h div(w)-grad(b).w)^2.
    This does not reuse the candidate's N, J, skew force or metric derivative.
    Central derivatives sample the full continuum bracket independently.
    """
    h = g.h
    v = primal(g, p, preconditioner=preconditioner)['canonical_velocity']
    response = dual(g, v, preconditioner=preconditioner)
    u = response['layer_velocity']
    roundtrip = float(np.max(abs(response['canonical_gradient_flux']-p)))
    if roundtrip > 1e-10*max(1., float(np.max(abs(p)))):
        raise ValueError(f'Independent control physical round-trip unqualified: {roundtrip}')
    potential = .5*(1-float(np.sum(WEIGHTS)))*np.sum(v*v, axis=-1)+9.81*(h+g.bed)
    for pole in response['poles']:
        auxiliary = pole['normalized_auxiliary_velocity']/np.sqrt(h)[..., None]
        d = sum(central(auxiliary[..., j], j, g.dx) for j in range(2))
        e = sum(central(g.bed, j, g.dx)*auxiliary[..., j] for j in range(2))
        potential += pole['weight']*(np.sum(v*auxiliary, axis=-1)
            -.5*np.sum(auxiliary*auxiliary, axis=-1)-1.5*pole['length']*(h*d-e)**2)
    omega = central(v[..., 1], 0, g.dx)-central(v[..., 0], 1, g.dx)
    rotation = omega[..., None]*np.stack((-u[..., 1], u[..., 0]), axis=-1)
    vt = -np.stack([central(potential, j, g.dx) for j in range(2)], axis=-1)-rotation
    faces = [.5*(h+np.roll(h, -1, axis))*.5*(u[..., j]+np.roll(u[..., j], -1, axis))
             for j, axis in enumerate((1, 0))]
    ht = -sum((f-np.roll(f, 1, axis))/g.dx for f, axis in zip(faces, (1, 0)))
    converted = physical_rate(g, v, ht, vt, derivative_preconditioner=preconditioner, primal_preconditioner=preconditioner)
    return dict(physical_momentum_rate=converted['momentum_rate'], depth_rate=ht,
                canonical_vorticity_rms=float(np.sqrt(np.mean(omega*omega))),
                maximum_roundtrip_error=roundtrip)


def compare(seed, n):
    g, p = fixture(seed, n)
    reference = potential_control(g, p)
    variants = {name: stage(g, p, coupling=name) for name in ('full', 'no-commutator', 'no-hessian')}
    full = variants['full']
    rms = lambda value: float(np.sqrt(np.mean(value*value)))
    return dict(seed=seed, resolution=n, domain_m=[16., 16.],
        input_sha256={key: hashlib.sha256(value.tobytes()).hexdigest()
                      for key, value in (('depth', g.h), ('bed', g.bed), ('momentum', p))},
        potential_rms={key: rms(value['physical_momentum_rate']-reference['physical_momentum_rate'])
                       for key, value in variants.items()},
        omitted_term_rms={key: rms(value['physical_momentum_rate']-full['physical_momentum_rate'])
                          for key, value in variants.items() if key != 'full'},
        energy_rates={key: value['energy_rate'] for key, value in variants.items()},
        net_mass_rate=full['net_mass_rate'], gravity_mass_work_error=full['gravity_mass_work_error'],
        local_momentum_ledger_error=full['local_momentum_ledger_error'],
        metric_time_ledger_error=full['metric_time_ledger_error'], skew_ledger_error=full['skew_ledger_error'],
        total_momentum_rate=full['total_momentum_rate'].tolist(),
        total_bed_force=(full['physical_bed_force'].sum(axis=(0, 1))*g.dx**2).tolist(),
        skew_energy_work=full['skew_energy_work'], maximum_solve_residual=full['maximum_solve_residual'],
        maximum_roundtrip_error=reference['maximum_roundtrip_error'],
        canonical_vorticity_rms=reference['canonical_vorticity_rms'],
        local_physical_bed_force_ledger_accepted=False,
        nonlinear_model_or_dry_or_history_or_gameplay_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--resolutions', type=int, nargs='+', default=[16, 32, 64])
    parser.add_argument('--seeds', type=int, nargs='+', default=[2401, 2403])
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    hashes = lambda: {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in sorted(Path(__file__).parent.glob('*.py'))}
    original = hashes()
    records = []
    for seed in args.seeds:
        for n in args.resolutions:
            row = compare(seed, n)
            records.append(row)
            print(json.dumps(row), flush=True)
    if hashes() != original:
        raise RuntimeError('Implementation changed during audit')
    with args.report.open('x') as stream:
        json.dump(dict(records=records, implementation_hashes=original,
                       nonlinear_model_or_dry_or_history_or_gameplay_accepted=False),
                  stream, indent=2, allow_nan=False)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
