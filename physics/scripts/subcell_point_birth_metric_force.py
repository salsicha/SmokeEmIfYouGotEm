"""Original metric-time force coefficients at coupled point-source births.

For V_new=c*k^3*e^3, old volumes and all physical velocities fixed, this
evaluates lim M_e*u on old pools and lim (M_e*u)_new/e. It is one required
term of the nonlinear equation, NOT the full front force or a time update.
No positive-water state, inverse dry mass, energy remainder or fitted force
is constructed. The two original pressure poles and 40-CG gates remain.
"""
import numpy as np

from subcell_simultaneous_birth_pressure import point_limits
from subcell_wet_pool_pressure import WetPoolPressureSystem


def point_metric_force(context, requests):
    """Matrix-free leading physical inertial-metric derivative M_e*u.

    Write A=I+beta*Q_old, C=I+beta*D_new, and let sqrt(e)*B be
    the original normalized old/new Q block. With z=A^-1*R_old*u,
    x=C^-1*B.T*z, the Schur derivative gives
        old: -alpha*beta*R_old*A^-1*B*x,
        new/e: 2*alpha*sqrt(c*k^3)*x.
    B*x is formed through original positive factors and their transpose;
    solving a dense inverse or redistributing scalar work would not give
    the independently required local force vector.
    """
    limit = point_limits(context, requests)  # Also validates unchanged state.
    part = context.partition
    volume = np.array([p['volume'] for p in part.pools])
    velocity = np.array([p['momentum'] for p in part.pools])/volume[:, None]
    roots = np.sqrt(limit['volume_path_coefficients'])
    columns = limit['old_divergence_column_sqrt_path_coefficient']
    old_force = np.zeros((len(volume), 2))
    new_force = np.zeros((len(roots), 2))
    poles = []
    for record in limit['poles']:
        system = WetPoolPressureSystem(part, record['beta'])
        x = record['coupled_response']
        divergence_column = columns@x.ravel()
        factors = [p['form']['factor'][:, 0]*value
                   for p, value in zip(part.pools, divergence_column)]
        rhs = system.factor_transpose(factors)
        pulled, stats = system.solve(rhs)
        if stats['relative_residual'] > 2e-5:
            raise ValueError('Original 40-CG point metric force residual gate failed')
        old = -record['alpha']*record['beta']*system.root[:, None]*pulled[:, 0]
        new = 2*record['alpha']*roots[:, None]*x
        work = .5*float(np.sum(velocity*old))
        error = abs(work-record['energy_path_slope'])
        if not np.isfinite(old).all() or not np.isfinite(new).all():
            raise ValueError('Point metric force exceeds represented range')
        if error > 1e-10:
            raise ValueError('Original point metric force work identity failed')
        old_force += old
        new_force += new
        poles.append(dict(alpha=record['alpha'], beta=record['beta'],
                          old_force=old, newborn_force_over_path_limit=new,
                          old_pullback_solve=stats, work_identity_error=error))
    work = .5*float(np.sum(velocity*old_force))
    error = abs(work-limit['fixed_old_state_energy_path_slope'])
    if error > 1e-10:
        raise ValueError('Original combined point metric force work identity failed')
    return dict(limit=limit, old_force_limit=old_force,
                newborn_force_over_path_limit=new_force,
                metric_energy_path_work_limit=work, work_identity_error=error,
                poles=poles,
                full_front_force_or_impulse_or_time_or_native_or_gameplay_accepted=False)
