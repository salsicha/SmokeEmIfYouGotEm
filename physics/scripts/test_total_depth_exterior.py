import numpy as np
import pytest
import json
from total_depth_bank_replay import rate
from export_total_depth_exterior_fixtures import fixtures, pack_edges
from export_total_depth_exterior_fixtures import recorded_fixtures


@pytest.mark.parametrize('complete,exact', [(False, True), (True, False), (False, False)])
def test_recorded_exterior_fixture_rejects_unqualified_trace(tmp_path, complete, exact):
    path = tmp_path/'trace.json'
    path.write_text(json.dumps(dict(completed=complete, final_state_exact_to_live=exact)))
    with pytest.raises(ValueError, match='exactly'):
        recorded_fixtures(path, 0)


@pytest.mark.parametrize('index', [-1, 1, 1.5])
def test_recorded_exterior_fixture_rejects_invalid_trial_index(tmp_path, index):
    path = tmp_path/'trace.json'
    path.write_text(json.dumps(dict(completed=True, final_state_exact_to_live=True, trials=[{}])))
    with pytest.raises(ValueError, match='index'):
        recorded_fixtures(path, index)


@pytest.mark.parametrize('c', fixtures(), ids=lambda c: c['name']+str(c['bed'].shape))
def test_exterior_flux_balance_and_positive_euler(c):
    s = c['state'].astype(float); before = s.copy(); ledger = {}
    r, dt = rate(s[..., :3], c['bed'].astype(float), c['dx'], second_order=c['second_order'],
                 foam=s[..., 3], exterior=c['exterior'], boundary_diagnostics=ledger)
    np.testing.assert_array_equal(s, before)
    for k in (0, 3):
        net = r[..., k].sum()*c['dx']**2+ledger['outward_rate'][k]
        magnitude = abs(r[..., k]).sum()*c['dx']**2+abs(ledger['flux'][:, k]).sum()*c['dx']
        assert abs(net) <= 2e-14*max(magnitude, 1e-30)
        if np.isfinite(dt): assert np.all(s[..., k]+dt*r[..., k] >= 0)
    if c['name'].split('_')[0] in ('east', 'west', 'north', 'south', 'lake', 'dry'):
        np.testing.assert_array_equal(r, 0)
    hydro, hcfl = rate(s[..., :3], c['bed'].astype(float), c['dx'],
        second_order=c['second_order'], exterior=c['exterior'])
    np.testing.assert_array_equal(hydro, r[..., :3]); assert hcfl == dt


@pytest.mark.parametrize('which', ['negative_h', 'negative_foam', 'dry_momentum', 'nan', 'inf_bed', 'count', 'overflow'])
def test_invalid_ghosts_rejected(which):
    s = np.zeros((3, 4, 3)); s[..., 0] = 1
    e = np.zeros((14, 4)); e[:, 0] = 1; b = np.zeros(14)
    if which == 'negative_h': e[0, 0] = -1
    if which == 'negative_foam': e[0, 3] = -1
    if which == 'dry_momentum': e[0, :2] = [0, 1]
    if which == 'nan': e[0, 1] = np.nan
    if which == 'inf_bed': b[-1] = np.inf
    if which == 'count': e = e[:-1]
    if which == 'overflow': e[0, :2] = [1e-310, 1]
    with pytest.raises(ValueError, match='exterior|Exterior'):
        rate(s, np.zeros((3, 4)), .5, exterior=(e, b))


def test_pressure_and_periodic_exterior_not_silently_combined():
    c = fixtures()[0]
    for mode in ('periodic', 'dispersive'):
        with pytest.raises(ValueError, match='Exterior transport'):
            rate(c['state'][..., :3], c['bed'], .5, exterior=c['exterior'], **{mode: True})


@pytest.mark.parametrize('second', [False, True])
def test_flat_bed_momentum_balance_includes_boundary_pressure(second):
    rng = np.random.default_rng(991)
    h = rng.uniform(.5, 2, (15, 19))
    s = np.stack((h, h*rng.uniform(-2, 2, h.shape), h*rng.uniform(-2, 2, h.shape), h*.2), axis=-1)
    ledger = {}
    r, _ = rate(s[1:-1, 1:-1, :3], np.zeros((13, 17)), .5, second_order=second,
        foam=s[1:-1, 1:-1, 3], exterior=(pack_edges(s), np.zeros(60)), boundary_diagnostics=ledger)
    for k in (1, 2):
        assert abs(r[..., k].sum()*.25+ledger['outward_rate'][k]) < 2e-12


@pytest.mark.parametrize('axis,sign', [(0, 1), (0, -1), (1, 1), (1, -1)])
def test_foam_pulse_leaves_throughflow_window_with_stage_flux_ledger(axis, sign):
    # Supplied uniform water remains steady. Only a passive foam pulse is
    # tested here; this is NOT a nonreflecting dispersive wave experiment.
    full = np.zeros((14, 18, 4)); full[..., 0] = 1; full[..., axis+1] = sign*2
    ext = pack_edges(full), np.zeros(2*(12+16))
    s = full[1:-1, 1:-1].copy(); s[4:8, 6:10, 3] = 1
    bed = np.zeros(s.shape[:2]); initial = s[..., 3].sum()*.25; outward = 0.
    for _ in range(400):
        d1 = {}; d2 = {}
        r1, b1 = rate(s[..., :3], bed, .5, foam=s[..., 3], exterior=ext, boundary_diagnostics=d1)
        dt = min(.02, b1)
        stage = s+dt*r1
        r2, b2 = rate(stage[..., :3], bed, .5, foam=stage[..., 3], exterior=ext, boundary_diagnostics=d2)
        assert dt <= b2
        s = .5*(s+stage+dt*r2)
        outward += .5*dt*(d1['outward_rate'][3]+d2['outward_rate'][3])
    np.testing.assert_array_equal(s[..., :3], full[1:-1, 1:-1, :3])
    assert np.all(s[..., 3] >= 0)
    assert s[..., 3].sum()*.25 < initial*.01
    assert abs(s[..., 3].sum()*.25+outward-initial) < 1e-12
