"""Full-velocity flat periodic research controls, never scene acceptance."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from conservative_rational_stress import stress_stage_physical
from finite_depth_pressure_reference import WEIGHTS
from rational_dual_energy_reference import evaluate as dual
from rational_metric_transport_2d import stage
from rational_physical_momentum_rate import physical_rate
from rational_primal_energy import evaluate as primal
from rational_velocity_bracket_reference import gradient
from smooth_rational_velocity_stage import make


def fixture(seed, n):
    phase = np.random.default_rng(seed).uniform(0, 2*np.pi, 6)
    y, x = np.meshgrid(2*np.pi*(np.arange(n)+.5)/n,
                       2*np.pi*(np.arange(n)+.5)/n, indexing='ij')
    h = 1.5+.15*np.sin(x+phase[0])*np.cos(y+phase[1])+.1*np.cos(2*x-y+phase[2])
    u = np.stack((.7+.3*np.sin(x+y+phase[3])+.1*np.cos(2*y+phase[4]),
                  .2+.2*np.cos(x-y+phase[4])+.1*np.sin(2*x+phase[5])), axis=-1)
    return make(h, np.zeros_like(h), 16/n), h[..., None]*u


def potential_control(g, p):
    """Independent stationary-dual depth derivative plus canonical vorticity.

    The full continuum velocity bracket includes -curl(v)*J(u). Omitting it
    would test only potential flow and miss the actual 2-D turning-current term.
    """
    h = g.h
    v = primal(g, p, preconditioner='spectral-flat')['canonical_velocity']
    response = dual(g, v, preconditioner='spectral-flat')
    u = response['layer_velocity']
    roundtrip = float(np.max(abs(response['canonical_gradient_flux']-p)))
    if roundtrip > 1e-10*max(1., float(np.max(abs(p)))):
        raise ValueError('Independent control physical round-trip unqualified')
    potential = .5*(1-float(np.sum(WEIGHTS)))*np.sum(v*v, axis=-1)+9.81*(h+g.bed)
    for pole in response['poles']:
        auxiliary = pole['normalized_auxiliary_velocity']/np.sqrt(h)[..., None]
        d = gradient(auxiliary[..., 0], g.dx)[..., 0]+gradient(auxiliary[..., 1], g.dx)[..., 1]
        potential += pole['weight']*(np.sum(v*auxiliary, axis=-1)-.5*np.sum(auxiliary*auxiliary, axis=-1)
            -1.5*pole['length']*h*h*d*d)
    omega = gradient(v[..., 1], g.dx)[..., 0]-gradient(v[..., 0], g.dx)[..., 1]
    rotation = omega[..., None]*np.stack((-u[..., 1], u[..., 0]), axis=-1)
    vt = -gradient(potential, g.dx)-rotation
    faces = [.5*(h+np.roll(h, -1, axis))*.5*(u[..., j]+np.roll(u[..., j], -1, axis))
             for j, axis in enumerate((1, 0))]
    ht = -sum((f-np.roll(f, 1, axis))/g.dx for f, axis in zip(faces, (1, 0)))
    converted = physical_rate(g, v, ht, vt, derivative_preconditioner='spectral-flat', primal_preconditioner='spectral-flat')
    return dict(physical_momentum_rate=converted['momentum_rate'], depth_rate=ht,
        canonical_vorticity_rms=float(np.sqrt(np.mean(omega*omega))),
        maximum_roundtrip_error=roundtrip)


def compare(seed, n):
    g, p = fixture(seed, n)
    full = stage(g, p)
    incomplete = stage(g, p, tensor_coupling='longitudinal-only')
    original = stress_stage_physical(g, p, flux_scheme='paired-base', preconditioner='spectral-flat')
    reference = potential_control(g, p)
    rms = lambda r: float(np.sqrt(np.mean((r['physical_momentum_rate']-reference['physical_momentum_rate'])**2)))
    return dict(seed=seed, resolution=n, domain_m=[16., 16.],
        depth_sha256=hashlib.sha256(g.h.tobytes()).hexdigest(),
        momentum_sha256=hashlib.sha256(p.tobytes()).hexdigest(),
        full_vs_potential_rms=rms(full), incomplete_vs_potential_rms=rms(incomplete),
        stress_vs_potential_rms=rms(original), energy_rate=full['energy_rate'],
        net_mass_rate=full['net_mass_rate'], total_momentum_rate=full['total_momentum_rate'].tolist(),
        local_momentum_flux_error=full['local_momentum_flux_error'],
        maximum_solve_residual=full['maximum_solve_residual'],
        reconstructed_derivative_error=full['reconstructed_derivative_error'],
        canonical_vorticity_rms=reference['canonical_vorticity_rms'],
        maximum_roundtrip_error=reference['maximum_roundtrip_error'],
        conservation_passed=bool(abs(full['energy_rate']) < 1e-10 and abs(full['net_mass_rate']) < 1e-10
            and np.max(abs(full['total_momentum_rate'])) < 1e-10 and full['local_momentum_flux_error'] < 1e-10))


def summarize(records):
    controls = []
    for seed in (2310, 2312):
        rows = sorted((r for r in records if r['seed'] == seed), key=lambda r: r['resolution'])
        if [r['resolution'] for r in rows] != [16, 32, 64]:
            raise ValueError('Complete two-dimensional three-grid profile required')
        ratios = lambda key: [rows[i][key]/rows[i+1][key] for i in (0, 1)]
        full = ratios('full_vs_potential_rms')
        stress = ratios('stress_vs_potential_rms')
        controls.append(dict(seed=seed, full_refinement_ratios=full,
            stress_refinement_ratios=stress, incomplete_refinement_ratios=ratios('incomplete_vs_potential_rms'),
            necessary_consistency_trend_passed=all(r > 3 for r in full),
            comparator_trend_passed=all(r > 3 for r in stress)))
    return dict(controls=controls, conservation_passed=all(r['conservation_passed'] for r in records),
        necessary_consistency_trend_passed=all(r['necessary_consistency_trend_passed'] for r in controls),
        comparator_trend_passed=all(r['comparator_trend_passed'] for r in controls),
        nonlinear_model_or_terrain_or_dry_or_history_or_gameplay_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    paths = sorted(Path(__file__).parent.glob('*.py'))
    hashes = lambda: {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    original = hashes()
    records = []
    for seed in (2310, 2312):
        for n in (16, 32, 64):
            r = compare(seed, n)
            records.append(r)
            print(json.dumps(r), flush=True)
    summary = summarize(records)
    if hashes() != original:
        raise RuntimeError('Implementation changed during audit')
    with args.report.open('x') as stream:
        json.dump(dict(records=records, summary=summary, implementation_hashes=original), stream,
                  indent=2, allow_nan=False)
    print(json.dumps(summary), flush=True)
    return 0 if all(summary[k] for k in ('conservation_passed', 'necessary_consistency_trend_passed',
                                        'comparator_trend_passed')) else 1


if __name__ == '__main__':
    raise SystemExit(main())
