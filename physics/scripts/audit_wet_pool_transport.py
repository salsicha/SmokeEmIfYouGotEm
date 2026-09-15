"""Captured-pool physical energy, volume work and explicit base-flux support."""
import numpy as np

from finite_depth_pressure_reference import LENGTHS, WEIGHTS
from subcell_wet_pool_pressure import WetPoolPressureSystem, response
from subcell_wet_pool_pressure_rate import WetPoolPressureRate
from subcell_wet_pool_primal_energy import evaluate
from subcell_wet_pool_transport import rates


def audit_transport(pools):
    volume = np.array([p['volume'] for p in pools.pools])
    p = np.array([p['momentum'] for p in pools.pools])[:, None, :]
    energy = evaluate(pools, p)
    root = np.sqrt(volume)[:, None, None]
    dual = response(pools, root*energy['canonical_velocity'])
    recovered = root*dual['value']
    roundtrip = float(np.max(abs(recovered-p)/volume[:, None, None]))
    index = np.arange(len(volume))
    pattern = .1*np.sin(.53*index+.3)
    vd = volume*(pattern-np.sum(volume*pattern)/volume.sum())
    pd = volume[:, None, None]*.05*np.stack((np.cos(.31*index), np.sin(.47*index)), axis=-1)[:, None, :]
    # Independent forward directional assembly, not the reverse gradient loop.
    forward = float((energy['volume_gradient_terms']['momentum_normalization']
                     +energy['volume_gradient_terms']['potential'])@vd)
    pole_directions = []
    for pole in energy['poles']:
        s = WetPoolPressureSystem(pools, pole['beta'])
        z = pole['normalized_auxiliary_velocity']
        action = WetPoolPressureRate(s, vd[:, None]).apply(z)
        work = .5*pole['alpha']*float(np.sum(z*action))/pole['beta']
        reverse = pole['alpha']*float(pole['reverse_terms']['value']@vd)
        forward += work
        pole_directions.append(dict(beta=pole['beta'], alpha=pole['alpha'],
            iterations=pole['iterations'], relative_residual=pole['relative_residual'],
            forward_volume_work=work, reverse_volume_work=reverse,
            scaled_forward_reverse_error=abs(work-reverse)/max(1., abs(work))))
    reverse = float(energy['volume_gradient']@vd)
    gradient_error = abs(forward-reverse)/max(1., abs(forward))
    # Independent small dense Q from local Gram tensors and row maps, not CG's
    # factor actions; original S is then inverted directly as an audit oracle.
    if len(volume) > 1024:
        raise ValueError('Dense inverse-metric audit exceeds bounded patch scope')
    s = WetPoolPressureSystem(pools, float(LENGTHS[0]))
    qmatrix = np.zeros((p.size, p.size))
    for i, pool in enumerate(pools.pools):
        mapping = s.row_maps[i]
        cols = sorted(set(mapping) | {2*i, 2*i+1})
        jet = np.zeros((3, len(cols)))
        for j, col in enumerate(cols):
            jet[0, j] = mapping.get(col, 0.)/s.root[col//2]
            if col//2 == i:
                jet[1+col%2, j] = 1/s.root[i]
        qmatrix[np.ix_(cols, cols)] += jet.T@pool['form']['gram']@jet
    eye = np.eye(p.size)
    smatrix = (1-float(np.sum(WEIGHTS)))*eye
    for length, weight in zip(LENGTHS, WEIGHTS):
        smatrix += weight*np.linalg.solve(eye+length*qmatrix, eye)
    dense = np.linalg.solve(smatrix, (p/root).ravel()).reshape(p.shape)
    dense_canonical = dense/root
    canonical_error = float(np.max(abs(dense_canonical-energy['canonical_velocity'])/np.maximum(1., abs(dense_canonical))))
    dense_kinetic = .5*float(np.sum((p/root)*dense))
    energy_error = abs(dense_kinetic-energy['kinetic'])/max(1., abs(dense_kinetic))
    probes = []
    target = reverse+float(np.sum(energy['canonical_velocity']*pd))
    for step in (1e-4, 5e-5, 2.5e-5):
        low = evaluate(pools.volume_probe(volume-step*vd), p-step*pd)
        high = evaluate(pools.volume_probe(volume+step*vd), p+step*pd)
        observed = (high['total']-low['total'])/(2*step)
        probes.append(dict(step=step, analytic_total_work=target, finite_difference_total_work=observed,
                           scaled_error=abs(observed-target)/max(1., abs(target))))
    central = rates(pools, p[:, 0], dissipative=False)
    dissipative = rates(pools, p[:, 0], dissipative=True)
    def report_flux(value):
        result = {key: item.tolist() if isinstance(item, np.ndarray) else item
                  for key, item in value.items() if key != 'fluxes'}
        result['base_balance_controls_passed'] = (max(abs(value['net_mass_rate']),
            value['momentum_boundary_bed_error'], value['base_energy_identity_error'],
            value['maximum_hydrostatic_geometry_closure_error']) < 1e-10
            if value['complete_fixed_topology_base_rates'] else None)
        return result
    passed = (roundtrip < 1e-9 and gradient_error < 1e-10 and canonical_error < 1e-10
              and energy_error < 1e-10 and energy['positive_energy_contraction_error']/max(1., energy['kinetic']) < 1e-10
              and all(probe['scaled_error'] < 1e-6 for probe in probes)
              and all(pole['scaled_forward_reverse_error'] < 1e-10 for pole in pole_directions))
    return dict(physical_energy_controls_passed=passed, pool_count=len(volume),
        kinetic=energy['kinetic'], potential=energy['potential'], total=energy['total'],
        original_pole_momentum_roundtrip_error_per_volume=roundtrip,
        dense_original_inverse_canonical_error=canonical_error, dense_original_inverse_energy_error=energy_error,
        scaled_forward_reverse_volume_work_error=gradient_error,
        positive_energy_contraction_error=energy['positive_energy_contraction_error'],
        gradient_terms={key: val.tolist() for key, val in energy['volume_gradient_terms'].items()},
        inverse_factors=pole_directions, independent_energy_probes=probes,
        central_base=report_flux(central), dissipative_base=report_flux(dissipative),
        original_pole_roundtrip_solves=dual['poles'],
        nonlinear_or_wetting_or_time_or_gameplay_accepted=False)
