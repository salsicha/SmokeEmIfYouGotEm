"""Independent zero-flow pressure limit for the unqualified smooth stage.

Three periodic flat-bed cells [1,2,4] retain different donor heights on the
two sides of zero flow. The exact gravity-only oracle uses Fraction arithmetic
and explicit reconstructed heights, not the stage's pressure/transport code.
No model, source trajectory, or acceptance gate is changed by this audit.
"""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import numpy as np
from smooth_rational_velocity_stage import make, stage


def gravity_oracle(sign):
    h = [F(1), F(2), F(4)]
    # The three-cell continuous-envelope slopes are [0,3/2,0].
    # h_i+s_i/2 and h_(i+1)-s_(i+1)/2 respectively.
    retained = [F(1), F(11,4), F(4)] if sign >= 0 else [F(5,4), F(4), F(1)]
    gravity, dx = F(981,100), F(1,2)
    pieces = [retained[i]*(h[(i+1)%3]-h[i])/(h[i]+h[(i+1)%3])/dx for i in range(3)]
    rate = [-gravity*(pieces[i]+pieces[(i-1)%3]) for i in range(3)]
    momentum = sum(h[i]*rate[i] for i in range(3))*dx*dx
    return dict(retained=[float(x) for x in retained],
                velocity_rate=[float(x) for x in rate], momentum_rate=float(momentum))


def run(axis):
    if axis not in (0, 1):
        raise ValueError('A registered spatial axis is required')
    h = np.array([[1., 2., 4.]])
    if axis == 0:
        h = h.T
    component = 1-axis
    bed = np.zeros_like(h)
    geometry = make(h, bed, .5)
    probes = []
    for epsilon in (2.**-12, 2.**-20, 2.**-28):
        sides = []
        for sign in (-1, 1):
            v = np.zeros((*h.shape, 2)); v[..., component] = sign*epsilon
            r = stage(geometry, v)
            oracle = gravity_oracle(sign)
            rate = r['canonical_velocity_rate'][..., component].ravel()
            sides.append(dict(sign=sign, velocity_rate=rate.tolist(),
                mass_rate=r['depth_rate'].ravel().tolist(),
                physical_velocity_recovery_error=float(abs(r['layer_velocity']-v).max()),
                exact_gravity_limit_error=float(abs(rate-oracle['velocity_rate']).max()),
                momentum_rate=float(np.sum(h*r['canonical_velocity_rate'][..., component]
                    +r['depth_rate']*v[..., component])*.25),
                energy_rate=r['energy_rate']))
        mass_gap=float(abs(np.array(sides[1]['mass_rate'])-sides[0]['mass_rate']).max())
        force_gap=float(abs(np.array(sides[1]['velocity_rate'])-sides[0]['velocity_rate']).max())
        probes.append(dict(epsilon=epsilon, sides=sides, mass_rate_gap=mass_gap,
                           canonical_rate_gap=force_gap))
    zero = np.zeros((*h.shape, 2))
    original = stage(geometry, zero)['canonical_velocity_rate']
    mirrored_h = np.flip(h, axis).copy()
    mirrored = stage(make(mirrored_h, bed, .5), zero)['canonical_velocity_rate']
    expected = np.flip(original, axis).copy(); expected[..., component] *= -1
    return dict(axis=axis, depth_sha256=hashlib.sha256(h.tobytes()).hexdigest(),
        negative_oracle=gravity_oracle(-1), nonnegative_oracle=gravity_oracle(1),
        probes=probes, resting_reflection_error=float(abs(mirrored-expected).max()),
        mass_gap_shrink=probes[0]['mass_rate_gap']/probes[-1]['mass_rate_gap'],
        force_gap_shrink=probes[0]['canonical_rate_gap']/probes[-1]['canonical_rate_gap'],
        flow_reversal_continuity_passed=bool(probes[0]['canonical_rate_gap']>
                                           100*probes[-1]['canonical_rate_gap']),
        physical_model_or_gameplay_accepted=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True); args=parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    # Capture inputs before execution and verify them after, never silently
    # attribute an audit to a version that was edited while it was running.
    names=('audit_smooth_stage_reversal.py','smooth_rational_velocity_stage.py',
           'smooth_pressure_geometry.py','smooth_pressure_reverse.py',
           'reverse_rational_depth_gradient.py','continuous_extremum_transport.py',
           'extremum_preserving_transport.py','hydrostatic_energy_transport.py',
           'rational_dual_energy_reference.py')
    hashes=lambda: {name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                    for name in names}
    original=hashes(); records=[run(axis) for axis in (1,0)]
    if hashes()!=original:
        raise RuntimeError('Audit implementation changed during execution')
    report=dict(scope=__doc__,records=records,implementation_hashes=original)
    with args.report.open('x') as stream:
        json.dump(report,stream,indent=2,allow_nan=False)
    print(json.dumps(records),flush=True)


if __name__=='__main__':
    main()
