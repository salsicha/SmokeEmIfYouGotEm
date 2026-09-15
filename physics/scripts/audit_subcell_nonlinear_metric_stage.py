"""Original-source nonlinear rate versus independent full continuum bracket."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

from finite_depth_pressure_reference import LENGTHS, WEIGHTS
from south_fork_registered_mesh import RegisteredMeshSampler
from subcell_geometry_patch import SubcellGeometryPatch
from subcell_wet_pool_partition import WetPoolPartition
from subcell_wet_pool_pressure import WetPoolPressureSystem
from subcell_wet_pool_pressure_rate import dual_direction
from subcell_wet_pool_primal_energy import evaluate
from subcell_wet_pool_transport import rates as base_rates
from subcell_nonlinear_metric_stage import stage
from subcell_source_face_section import stage_difference


def fixture(seed, n, *, preconditioner='auto'):
    length, dx = 16., 16/n
    phase = np.random.default_rng(seed).uniform(0, 2*np.pi, 6)
    bed = lambda x, y: .35*np.sin(x+phase[0])*np.cos(y+phase[1])+.2*np.cos(2*x-y+phase[2])
    east, north = np.arange(n+1)*dx, length-np.arange(n+1)*dx
    x, y = np.meshgrid(east, north)
    z = bed(2*np.pi*x/length, 2*np.pi*y/length)
    z[:, -1] = z[:, 0]; z[-1, :] = z[0, :]  # Exact periodic represented seam.
    roots = (np.arange((n+1)**2).reshape(n+1, n+1)[:-1, :-1]).ravel()
    source = RegisteredMeshSampler(dict(east_m=x, north_m=y, z_m=z,
        nominal_east_axis_m=east, nominal_north_axis_m=north,
        triangles=np.concatenate((np.stack((roots, roots+1, roots+n+1), 1),
                                  np.stack((roots+1, roots+n+2, roots+n+1), 1)))))
    yc, xc = np.meshgrid(2*np.pi*(np.arange(n)+.5)/n, 2*np.pi*(np.arange(n)+.5)/n, indexing='ij')
    eta = 1.5+.4*bed(xc, yc)+.12*np.sin(xc-yc+phase[3])
    u = np.stack((.7+.3*np.sin(xc+yc+phase[3])+.1*np.cos(2*yc+phase[4]),
                  .2+.2*np.cos(xc-yc+phase[4])+.1*np.sin(2*xc+phase[5])), axis=-1)
    origin = [dx/2, dx/2]
    patch = SubcellGeometryPatch(source, origin, (n, n), (dx, dx), (True, True),
                                relative_stages=True, exact_sources=True)
    v, p = patch.state_from_stages(eta, u)
    pools = WetPoolPartition(patch, source, origin, v, p, pressure_preconditioner=preconditioner)
    if any(len(owners) != 1 for owners in pools.parent_pools):
        raise ValueError('Independent continuum profile requires one positive region per cell')
    return pools, p.reshape(n*n, 1, 2)


def potential_control(partition, p):
    shape = partition.patch.shape
    dx = partition.patch.spacing[0]
    area = float(np.prod(partition.patch.spacing))
    volume = np.array([pool['volume'] for pool in partition.pools])
    h = volume.reshape(shape)/area
    eta = np.array([stage_difference(0., 0., pool['form']['stage_offset'], pool['form']['datum'])
                    for pool in partition.pools]).reshape(shape)
    bed = eta-h  # Cell average only in this independent continuum sampler.
    central = lambda value, j: (np.roll(value, -1, 1-j)-np.roll(value, 1, 1-j))/(2*dx)
    canonical = evaluate(partition, p)['canonical_velocity']
    v = canonical.reshape(*shape, 2)
    root = np.sqrt(volume)[:, None, None]
    q = root*canonical
    normalized = (1-float(np.sum(WEIGHTS)))*q
    phi = .5*(1-float(np.sum(WEIGHTS)))*np.sum(v*v, axis=-1)+9.81*eta
    residuals = []
    for length, weight in zip(LENGTHS, WEIGHTS):
        system = WetPoolPressureSystem(partition, float(length))
        z, info = system.solve(q)
        residuals.append(info['relative_residual'])
        normalized += weight*z
        w = (z/root).reshape(*shape, 2)
        divergence = sum(central(w[..., j], j) for j in range(2))
        bottom = sum(central(bed, j)*w[..., j] for j in range(2))
        phi += weight*(np.sum(v*w, axis=-1)-.5*np.sum(w*w, axis=-1)-1.5*length*(h*divergence-bottom)**2)
    roundtrip = float(np.max(abs(root*normalized-p)))
    if roundtrip > 1e-10*max(1., float(np.max(abs(p)))) or max(residuals) > 2e-5:
        raise ValueError(f'Original-source continuum control round-trip failed: {roundtrip}')
    u = (normalized/root).reshape(*shape, 2)
    omega = central(v[..., 1], 0)-central(v[..., 0], 1)
    vt = -np.stack([central(phi, j) for j in range(2)], axis=-1)
    vt -= omega[..., None]*np.stack((-u[..., 1], u[..., 0]), axis=-1)
    base = base_rates(partition, p[:, 0], full_metric=False)
    converted = dual_direction(partition, canonical, base['volume_rate'][:, None], vt.reshape(p.shape))
    return dict(physical_momentum_rate=converted['physical_momentum_rate'],
                maximum_roundtrip_error=roundtrip, canonical_vorticity_rms=float(np.sqrt(np.mean(omega**2))))


def compare(seed, n, *, preconditioner='auto'):
    part, p = fixture(seed, n, preconditioner=preconditioner)
    full, omitted = stage(part, p), stage(part, p, include_curvature=False)
    reference = potential_control(part, p)
    area = float(np.prod(part.patch.spacing))
    rms = lambda value: float(np.sqrt(np.mean(value**2)))/area
    return dict(seed=seed, resolution=n, domain_m=[16., 16.], preconditioner=preconditioner,
        full_vs_continuum_rms=rms(full['physical_momentum_rate']-reference['physical_momentum_rate']),
        omitted_curvature_vs_continuum_rms=rms(omitted['physical_momentum_rate']-reference['physical_momentum_rate']),
        curvature_contribution_rms=rms(omitted['physical_momentum_rate']-full['physical_momentum_rate']),
        energy_rate=full['energy_rate'], omitted_curvature_energy_rate=omitted['energy_rate'],
        local_momentum_ledger_error=full['local_momentum_ledger_error'],
        metric_time_ledger_error=full['metric_time_ledger_error'], skew_ledger_error=full['skew_ledger_error'],
        maximum_solve_residual=full['maximum_solve_residual'],
        maximum_roundtrip_error=reference['maximum_roundtrip_error'],
        canonical_vorticity_rms=reference['canonical_vorticity_rms'], curvature_scope=full['curvature_scope'],
        full_continuum_or_topology_or_time_or_native_or_gameplay_accepted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--resolutions', type=int, nargs='+', default=[8, 16, 32])
    parser.add_argument('--seeds', type=int, nargs='+', default=[2843, 2845])
    parser.add_argument('--preconditioner', choices=['auto', 'spectral-frozen-depth'], default='auto')
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    paths = sorted(Path(__file__).parent.glob('*.py'))
    hashes = lambda: {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    original = hashes()
    records = []
    failed = False
    for seed in args.seeds:
        for n in args.resolutions:
            try:
                row = compare(seed, n, preconditioner=args.preconditioner)
            except ValueError as exc:
                row = dict(seed=seed, resolution=n, preconditioner=args.preconditioner,
                           failure=str(exc),
                           full_continuum_or_topology_or_time_or_native_or_gameplay_accepted=False)
                failed = True
            records.append(row)
            print(json.dumps(row), flush=True)
            if failed:
                break
        if failed:
            break
    if hashes() != original:
        raise RuntimeError('Implementation changed during source-model comparison')
    with args.report.open('x') as stream:
        json.dump(dict(records=records, implementation_hashes=original,
                       full_continuum_or_topology_or_time_or_native_or_gameplay_accepted=False),
                  stream, indent=2, allow_nan=False)
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
