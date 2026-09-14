"""Reject conservation-only two-pole candidates that change nonlinear dynamics.

This is a positive, flat, periodic 1-D research comparison, NOT river acceptance.
The independent continuum-potential control differentiates the stationary dual
kinetic density, rather than reusing either candidate's momentum stress. Original
pressure solves and physical-coordinate derivatives remain unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from audit_reconstructed_closed_energy import fixture
from conservative_rational_stress import stress_stage_physical
from finite_depth_pressure_reference import WEIGHTS
from rational_dual_energy_reference import evaluate as dual
from rational_metric_transport_stage import stage
from rational_physical_momentum_rate import physical_rate
from rational_primal_energy import evaluate as primal
from smooth_rational_velocity_stage import make


def potential_control(g, p):
    """Continuum v_t=-d_x(H_h), sampled with the original pressure geometry.

    Hkin = c*h*v^2/2 + sum_j weight_j * stationary[
        h*v*a_j - h*a_j^2/2 - length_j*h^3*(a_j,x)^2/2].
    The envelope derivative holds v and each stationary auxiliary a_j fixed.
    This is a consistency oracle, not an exactly conservative discrete stage.
    """
    if min(g.h.shape) != 1 or not np.all(g.bed == g.bed.flat[0]):
        raise ValueError('One-dimensional flat periodic control required')
    axis = 1 if g.h.shape[0] == 1 else 0
    component = 1-axis
    prepared = primal(g, p)
    v = prepared['canonical_velocity']
    r = dual(g, v, preconditioner='patch')
    u = r['layer_velocity']
    if np.max(np.abs(r['canonical_gradient_flux']-p)) > 1e-10*max(1., np.max(np.abs(p))):
        raise ValueError('Continuum control physical round-trip is unqualified')
    potential = .5*(1-float(np.sum(WEIGHTS)))*np.sum(v*v, axis=-1)+9.81*(g.h+g.bed)
    for pole in r['poles']:
        auxiliary = pole['normalized_auxiliary_velocity']/np.sqrt(g.h)[..., None]
        # Use a direct centered continuum derivative, independent of the
        # reconstructed D_h used by both candidate stress implementations.
        ax = (np.roll(auxiliary[..., component], -1, axis)
              - np.roll(auxiliary[..., component], 1, axis))/(2*g.dx)
        potential += pole['weight']*(np.sum(v*auxiliary, axis=-1)
            -.5*np.sum(auxiliary*auxiliary, axis=-1)
            -1.5*pole['length']*g.h*g.h*ax*ax)
    vt = np.zeros_like(v)
    vt[..., component] = -(np.roll(potential, -1, axis)-np.roll(potential, 1, axis))/(2*g.dx)
    mass_face = .5*(g.h+np.roll(g.h, -1, axis))*.5*(u[..., component]+np.roll(u[..., component], -1, axis))
    ht = -(mass_face-np.roll(mass_face, 1, axis))/g.dx
    converted = physical_rate(g, v, ht, vt, derivative_preconditioner='patch', primal_preconditioner='patch')
    return dict(depth_rate=ht, physical_momentum_rate=converted['momentum_rate'])


def compare(seed, resolution):
    source, bed = fixture(seed, 'smooth', resolution)
    g = make(source[..., 0], bed, 16/resolution)
    p = source[..., 1:]
    candidate = stage(g, p)
    independent = stage(g, p, auxiliary_transport='independent-modes')
    stress = stress_stage_physical(g, p, flux_scheme='paired-base')
    oracle = potential_control(g, p)
    # RMS of the longitudinal pointwise rate: no shrinking transverse-domain
    # factor, energy cancellation, or division by a vanishing reference rate.
    rms = lambda a, b: float(np.sqrt(np.mean((a['physical_momentum_rate'][..., 0]
                                           -b['physical_momentum_rate'][..., 0])**2)))
    return dict(seed=seed, resolution=resolution,
        source_state_sha256=hashlib.sha256(source.tobytes()).hexdigest(),
        energy_rate=candidate['energy_rate'],
        net_mass_rate=candidate['net_mass_rate'],
        total_momentum_rate=candidate['total_momentum_rate'].tolist(),
        maximum_solve_residual=candidate['maximum_solve_residual'],
        local_momentum_flux_error=candidate['local_momentum_flux_error'],
        metric_time_flux_error=candidate['metric_time_flux_error'],
        skew_flux_error=candidate['skew_flux_error'],
        local_flux_passed=bool(candidate['local_momentum_flux_error'] < 1e-10),
        conservation_passed=bool(abs(candidate['energy_rate']) < 1e-10
            and abs(candidate['net_mass_rate']) < 1e-10
            and np.max(abs(candidate['total_momentum_rate'])) < 1e-10),
        candidate_vs_stress_rms=rms(candidate, stress),
        candidate_vs_potential_rms=rms(candidate, oracle),
        independent_vs_potential_rms=rms(independent, oracle),
        stress_vs_potential_rms=rms(stress, oracle),
        candidate_vs_stress_mass_max=float(np.max(abs(candidate['depth_rate']-stress['depth_rate']))))


def summarize(records):
    controls = []
    for seed in (2200, 2202, 2204, 2206):
        rows = sorted((r for r in records if r['seed'] == seed), key=lambda r: r['resolution'])
        if [r['resolution'] for r in rows] != [32, 64, 128]:
            raise ValueError('Complete original three-grid profile required')
        ratios = lambda key: [rows[i][key]/rows[i+1][key] for i in (0, 1)]
        candidate_ratios = ratios('candidate_vs_potential_rms')
        baseline_ratios = ratios('stress_vs_potential_rms')
        independent_ratios = ratios('independent_vs_potential_rms')
        controls.append(dict(seed=seed, candidate_refinement_ratios=candidate_ratios,
            stress_refinement_ratios=baseline_ratios,
            independent_refinement_ratios=independent_ratios,
            # A necessary second-order trend check, not sufficient PDE proof.
            necessary_consistency_trend_passed=bool(all(r > 3 for r in candidate_ratios)),
            comparator_trend_passed=bool(all(r > 3 for r in baseline_ratios))))
    return dict(controls=controls,
        conservation_passed=all(r['conservation_passed'] for r in records),
        local_flux_passed=all(r['local_flux_passed'] for r in records),
        necessary_consistency_trend_passed=all(r['necessary_consistency_trend_passed'] for r in controls),
        comparator_trend_passed=all(r['comparator_trend_passed'] for r in controls),
        nonlinear_model_or_local_flux_or_dry_or_history_or_gameplay_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    # Lock all direct and indirect local script dependencies, not only the two
    # entry points: a changed fixture/solver must invalidate this comparison.
    paths = sorted(Path(__file__).parent.glob('*.py'))
    hashes = lambda: {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    initial = hashes()
    records = []
    for seed in (2200, 2202, 2204, 2206):
        for n in (32, 64, 128):
            record = compare(seed, n)
            records.append(record)
            print(json.dumps(record), flush=True)
    summary = summarize(records)
    if hashes() != initial:
        raise RuntimeError('Implementation changed during audit')
    with args.report.open('x') as stream:
        json.dump(dict(records=records, summary=summary, implementation_hashes=initial),
                  stream, indent=2, allow_nan=False)
    print(json.dumps(summary), flush=True)
    # Exit 0 means only the explicitly listed research controls passed; the
    # separate full-qualification flag stays false even when all of these pass.
    return 0 if (summary['conservation_passed'] and summary['necessary_consistency_trend_passed']
                 and summary['comparator_trend_passed'] and summary['local_flux_passed']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
