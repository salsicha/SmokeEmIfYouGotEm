"""Explicit boundary coupling checks; no transparent-wave or scene acceptance."""
import numpy as np
import pytest
import total_depth_bank_replay as bank
from total_depth_nonlinear_pressure import geometric_bed_slope
from export_total_depth_exterior_fixtures import fixtures, pack_edges
from test_prescribed_pressure_boundary import traces

KW = dict(second_order=True, dispersive=True, pressure_model='rational_sgn',
          pressure_interpolation='depth_weighted', pressure_formulation='kinematic', pressure_bed_slope='geometry')


def uniform(shape, velocity):
    h = np.ones(shape)
    state = np.stack((h, h*velocity[0], h*velocity[1]), axis=-1)
    es = np.zeros((2*sum(shape), 4)); es[:, :3] = state[0, 0]
    return state, (es, np.zeros(len(es))), traces(shape, velocity)


@pytest.mark.parametrize('shape', [(9, 13), (1, 17), (19, 1), (1, 1)])
@pytest.mark.parametrize('velocity', [(1., 0.), (-1., 0.), (0., 1.), (0., -1.)])
def test_uniform_exterior_transport_pressure_composition_is_stationary(shape, velocity):
    state, exterior, trace = uniform(shape, velocity); ledger = {}; stats = {}
    result, bound = bank.rate(state, state[..., 0]*0, .5, exterior=exterior,
        pressure_boundary=trace, pressure_diagnostics=stats, boundary_diagnostics=ledger, **KW)
    np.testing.assert_array_equal(result, 0)
    assert bound > 0 and stats['worst_relative_residual'] == 0
    assert ledger['outward_rate'][0] == 0


@pytest.mark.parametrize('shape', [(9, 13), (1, 17), (19, 1), (1, 1)])
def test_physical_bed_slope_uses_actual_ghost_centres_even_single_axis(shape):
    ny, nx = shape; y, x = np.indices((ny+2, nx+2))
    padded = .01*x*x+.03*y*y+.02*x*y
    before = padded.copy(); bed = padded[1:-1, 1:-1]; exterior = pack_edges(padded)
    expected = np.stack((padded[1:-1, 2:]-padded[1:-1, :-2],
                         padded[2:, 1:-1]-padded[:-2, 1:-1]), axis=-1)
    np.testing.assert_array_equal(geometric_bed_slope(bed, .5, exterior_bed=exterior), expected)
    np.testing.assert_array_equal(padded, before)


@pytest.mark.parametrize('bad', ['count', 'nan', 'periodic'])
def test_invalid_exterior_physical_bed_refused(bad):
    bed = np.zeros((3, 5)); ext = np.zeros(16)
    if bad == 'count': ext = ext[:-1]
    if bad == 'nan': ext[-1] = np.nan
    with pytest.raises(ValueError): geometric_bed_slope(bed, .5, bad == 'periodic', exterior_bed=ext)


@pytest.mark.parametrize('bad', ['no_exterior', 'periodic', 'hydro_only', 'linear', 'centered', 'expanded', 'weighted'])
def test_boundary_contract_cannot_be_ignored_or_silently_downgraded(bad):
    state, exterior, trace = uniform((3, 5), (1., 0.)); kw = dict(KW)
    if bad == 'no_exterior': exterior = None
    if bad == 'periodic': kw['periodic'] = True
    if bad == 'hydro_only': kw['dispersive'] = False
    if bad == 'linear': kw['pressure_model'] = 'linear'
    if bad == 'centered': kw['pressure_interpolation'] = 'centered'
    if bad == 'expanded': kw['pressure_formulation'] = 'expanded'
    if bad == 'weighted': kw['pressure_bed_slope'] = 'weighted'
    with pytest.raises(ValueError): bank.rate(state, np.zeros((3, 5)), .5, exterior=exterior, pressure_boundary=trace, **kw)


def test_variable_composition_passes_same_stage_hydro_rate_graph_and_exterior_bed(monkeypatch):
    c = next(c for c in fixtures() if c['name'] == 'random_mc' and c['bed'].shape == (13, 17))
    state, bed = c['state'][..., :3].astype(float), c['bed'].astype(float)
    trace = traces(bed.shape, (.25, -.125), (.01, -.02)); captured = []
    original = bank.nonlinear_pressure_force
    def capture(*args, **kwargs):
        captured.append((args, kwargs))
        return np.zeros_like(args[2]), [dict(relative_residual=0., iterations=0)]
    monkeypatch.setattr(bank, 'nonlinear_pressure_force', capture)
    hydro, bound = bank.rate(state, bed, .5, exterior=c['exterior'], pressure_boundary=trace, **KW)
    args, kwargs = captured[0]
    np.testing.assert_array_equal(kwargs['bed_slope'], c['slope'])
    np.testing.assert_array_equal(kwargs['mass_rate'], hydro[..., 0])
    np.testing.assert_array_equal(kwargs['momentum_rate'], hydro[..., 1:])
    np.testing.assert_array_equal(kwargs['boundary_velocity'], trace)
    expected_force, stats = original(*args, **kwargs)
    monkeypatch.setattr(bank, 'nonlinear_pressure_force', original)
    result, actual_bound = bank.rate(state, bed, .5, exterior=c['exterior'], pressure_boundary=trace, **KW)
    np.testing.assert_array_equal(result[..., 0], hydro[..., 0])
    np.testing.assert_array_equal(result[..., 1:], hydro[..., 1:]+expected_force)
    assert actual_bound == bound and max(s['relative_residual'] for s in stats) <= 2e-5


def test_unqualified_pressure_residual_is_not_accepted(monkeypatch):
    state, exterior, trace = uniform((3, 5), (1., 0.))
    monkeypatch.setattr(bank, 'nonlinear_pressure_force', lambda *a, **kw:
        (np.zeros_like(a[2]), [dict(relative_residual=2.1e-5, iterations=40)]))
    with pytest.raises(ValueError, match='residual'):
        bank.rate(state, np.zeros((3, 5)), .5, exterior=exterior, pressure_boundary=trace, **KW)


def source(shape, time):
    # Independently prescribed analytic face trace AND ghost-centre fields.
    # No assumption that an arbitrary sampled centre value is a face value.
    h, ux, uy = 1+.02*time, .25+.1*time, -.125+.05*time
    es = np.zeros((2*sum(shape), 4)); es[:, :3] = (h, h*ux, h*uy)
    return es, np.zeros(len(es)), traces(shape, (ux, uy), (.1, .05))


def test_time_dependent_rk_uses_each_stage_time_and_balances_accepted_flux():
    shape = (3, 7); state, _, _ = uniform(shape, (.25, -.125)); bed = np.zeros(shape)
    times = []
    seen_stages = []
    def provider(time, stage):
        assert not stage.flags.writeable
        seen_stages.append(stage.copy()); times.append(time); return source(shape, time)
    actual, stats = bank.advance(state, bed, .5, .05, boundary_at_time=provider, **KW)
    current = state.copy(); elapsed = 0.; outward = 0.; expected_times = []
    while elapsed < .05:
        es, eb, trace = source(shape, elapsed); first_ledger = {}
        first, bound = bank.rate(current, bed, .5, exterior=(es, eb), pressure_boundary=trace,
            boundary_diagnostics=first_ledger, **KW)
        dt = min(1/120, .05-elapsed, bound); stage = current+dt*first
        es, eb, trace = source(shape, elapsed+dt); second_ledger = {}
        second, stage_bound = bank.rate(stage, bed, .5, exterior=(es, eb), pressure_boundary=trace,
            boundary_diagnostics=second_ledger, **KW)
        assert dt <= stage_bound
        expected_times.extend((elapsed, elapsed+dt))
        current = .5*(current+stage+dt*second)
        outward += .5*dt*(first_ledger['outward_rate'][0]+second_ledger['outward_rate'][0]); elapsed += dt
    np.testing.assert_array_equal(actual, current)
    assert times == expected_times and stats['rejected_trials'] == 0
    np.testing.assert_array_equal(seen_stages[0], state)
    assert not np.array_equal(seen_stages[1], state)
    assert stats['boundary_outward_volume_m3'] == outward and outward != 0
    assert abs(stats['mass_balance_error_m3']) < 2e-14


def test_rejected_stage_resamples_time_and_contributes_no_flux(monkeypatch):
    shape = (3, 7); state, _, _ = uniform(shape, (.25, -.125)); bed = np.zeros(shape)
    original = bank.rate; calls = 0; times = []; accepted = []
    def reject_once(*args, **kwargs):
        nonlocal calls
        calls += 1
        result, bound = original(*args, **kwargs)
        if calls == 2:
            # Pollute only the rejected diagnostic ledger. Its water must never
            # appear in accepted cumulative accounting.
            kwargs['boundary_diagnostics']['outward_rate'][0] = 1e9
            return result, 1/480
        return result, bound
    def provider(time, stage): times.append(time); return source(shape, time)
    monkeypatch.setattr(bank, 'rate', reject_once)
    result, stats = bank.advance(state, bed, .5, 1/120, boundary_at_time=provider,
        on_step=lambda a, b, d: accepted.append(d), **KW)
    assert stats['rejected_trials'] == 1 and len(accepted) == 2
    assert times[:3] == [0., 1/120, 1/240]
    assert abs(stats['mass_balance_error_m3']) < 2e-14
    assert abs(stats['boundary_outward_volume_m3']) < .01
    assert np.isfinite(result).all()


def test_boundary_callback_cannot_mutate_interior_stage():
    state, _, _ = uniform((3, 7), (.25, -.125)); before = state.copy()
    def bad_provider(time, stage): stage[0, 0, 0] = 100
    with pytest.raises(ValueError, match='read-only'):
        bank.advance(state, np.zeros((3, 7)), .5, .01, boundary_at_time=bad_provider, **KW)
    np.testing.assert_array_equal(state, before)


def test_reflecting_channel_sides_have_exactly_zero_water_flux():
    from audit_prescribed_boundary_wave import channel_boundary
    y, x = np.indices((3, 7)); h = 1+.1*np.sin(x+y)
    state = np.stack((h, h*.3, h*.2*np.cos(x)), axis=-1)
    es, eb, trace = channel_boundary(state, 1.)
    np.testing.assert_array_equal(es[6:13, :3], state[0]*[1, 1, -1])
    np.testing.assert_array_equal(es[13:, :3], state[-1]*[1, 1, -1])
    ledger = {}
    bank.rate(state, np.zeros_like(h), .5, exterior=(es, eb), pressure_boundary=trace,
        boundary_diagnostics=ledger, **KW)
    np.testing.assert_array_equal(ledger['flux'][6:, 0], 0)


@pytest.mark.parametrize('fault', ['first_stage_failure', 'trial_budget'])
def test_failure_preserves_accepted_open_boundary_inventory(monkeypatch, fault):
    shape = (3, 7); state, _, _ = uniform(shape, (.25, -.125)); bed = np.zeros(shape)
    original = bank.rate; calls = 0
    def evaluate(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 3 and fault == 'first_stage_failure': raise ValueError('Injected source failure')
        return original(*args, **kwargs)
    monkeypatch.setattr(bank, 'rate', evaluate)
    kind = bank.ReplayInvalidRate if fault == 'first_stage_failure' else bank.ReplayExhausted
    with pytest.raises(kind) as caught:
        bank.advance(state, bed, .5, .02, max_trials=1 if fault == 'trial_budget' else 100,
            boundary_at_time=lambda t, s: source(shape, t), **KW)
    error = caught.value; stats = error.diagnostics
    assert stats['steps'] == 1 and stats['elapsed_s'] == 1/120
    assert stats['boundary_outward_volume_m3'] != 0
    change = float(error.state[..., 0].sum()*.25-state[..., 0].sum()*.25)
    assert change == stats['volume_error_m3']
    assert stats['mass_balance_error_m3'] == change+stats['boundary_outward_volume_m3']
    assert abs(stats['mass_balance_error_m3']) < 2e-14
