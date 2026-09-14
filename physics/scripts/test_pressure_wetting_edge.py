import numpy as np
import pytest
from audit_pressure_wetting_edge import toggle_edge, bracket_transition
import audit_pressure_wetting_edge as audit


@pytest.mark.parametrize('component', [0, 1])
@pytest.mark.parametrize('opened', [False, True])
def test_counterfactual_changes_exactly_one_edge_without_mutating_source(component, opened):
    pairs = [np.full((4, 5), opened, dtype=bool) for _ in range(2)]
    depth = np.ones((4, 5)); depth[1, 2] = np.nextafter(0., 1.)
    changed, neighbor = toggle_edge(pairs, depth, (1, 1), component)
    assert neighbor == ((1, 2) if component == 0 else (2, 1))
    assert sum(np.count_nonzero(a != b) for a, b in zip(changed, pairs)) == 1
    assert not any(np.shares_memory(a, b) for a, b in zip(changed, pairs))
    assert all(np.all(p == opened) for p in pairs)


@pytest.mark.parametrize('point,component', [((3, 1), 1), ((1, 4), 0), ((-1, 1), 0), ((1, 1), 2)])
def test_wrapped_or_invalid_edge_rejected(point, component):
    with pytest.raises(ValueError, match='edge'):
        toggle_edge([np.ones((4, 5), dtype=bool) for _ in range(2)], np.ones((4, 5)), point, component)


def test_dry_neighbor_cannot_be_opened():
    depth = np.ones((4, 5)); depth[2, 1] = 0
    with pytest.raises(ValueError, match='positive-depth'):
        toggle_edge([np.ones((4, 5), dtype=bool) for _ in range(2)], depth, (1, 1), 1)


@pytest.mark.parametrize('bad', ['nan', 'negative', 'shape', 'fractional_graph'])
def test_invalid_depth_or_non_boolean_graph_rejected(bad):
    depth = np.ones((4, 5)); pairs = [np.ones((4, 5), dtype=bool) for _ in range(2)]
    if bad == 'nan': depth[0, 0] = np.nan
    elif bad == 'negative': depth[0, 0] = -1
    elif bad == 'shape': depth = depth[0]
    else: pairs[0] = pairs[0].astype(float)*.5
    with pytest.raises(ValueError, match='pressure'):
        toggle_edge(pairs, depth, (1, 1), 1)


def test_transition_bracket_converges_without_changing_sample_values():
    calls = []
    def sample(alpha):
        calls.append(alpha); return dict(value=alpha, opened=alpha > .3)
    low, high = bracket_transition(sample, lambda value: value['opened'])
    assert low[0] <= .3 < high[0] and high[0]-low[0] <= 2**-48
    assert low[1]['value'] == low[0] and high[1]['value'] == high[0]
    assert len(calls) == 50 and min(calls) == 0 and max(calls) == 1


@pytest.mark.parametrize('threshold', [-1., 2.])
def test_non_bracketing_endpoints_rejected(threshold):
    with pytest.raises(ValueError, match='bracket'):
        bracket_transition(lambda alpha: alpha, lambda alpha: alpha > threshold)


def small_state():
    y, x = np.indices((4, 5)); bed = .03*x+.02*y
    state = np.zeros((4, 5, 4)); state[..., 0] = 1-bed
    state[..., 1] = .1*np.sin(x)*state[..., 0]
    state[..., 2] = .1*np.cos(y)*state[..., 0]
    exterior = np.concatenate((state[:, 0], state[:, -1], state[0], state[-1]))
    exterior_bed = np.concatenate((bed[:, 0], bed[:, -1], bed[0], bed[-1]))
    trace = np.zeros((18, 2))
    for value in (state, bed, exterior, exterior_bed, trace): value.flags.writeable = False
    return state, dict(bed=bed, cell_meters=.5), lambda *_: (exterior, exterior_bed, trace)


def test_capture_and_pressure_decomposition_preserve_readonly_sources():
    state, endpoint, boundary = small_state()
    before = state.copy(); bed_before = endpoint['bed'].copy()
    cpu, faces = audit.capture_hydro(state, endpoint, boundary, 0., (1, 1), 1, 'unscaled')
    assert len(faces) == 1 and not np.shares_memory(cpu['state'], state)
    _, exterior_bed, trace = boundary(0., None)
    slope = audit.pressure.geometric_bed_slope(endpoint['bed'], .5, exterior_bed=exterior_bed)
    pairs = [(cpu['pairs'] & 1) != 0, (cpu['pairs'] & 2) != 0]
    force, report = audit.evaluate(cpu, endpoint['bed'], .5, trace, slope, pairs, [(1, 1), (2, 1)])
    assert np.isfinite(force).all()
    assert report['pressure_divergence_plus_traction_error'] < 1e-12
    assert all(value >= 0 for value in report['dispersive_matrix_quadratic_integral_per_pole'])
    for row in report['cells']:
        np.testing.assert_allclose(np.array(row['pressure_divergence'])+row['bottom_traction'], row['force'], atol=1e-12)
    np.testing.assert_array_equal(state, before)
    np.testing.assert_array_equal(endpoint['bed'], bed_before)


def test_failed_capture_restores_original_operators(monkeypatch):
    state, endpoint, boundary = small_state()
    faces, pressure = audit.temporal.bank.hydrostatic_faces, audit.temporal.bank.nonlinear_pressure_force
    def fail(*_args, **_kwargs): raise RuntimeError('intentional diagnostic failure')
    monkeypatch.setattr(audit.temporal.bank, 'rate', fail)
    with pytest.raises(RuntimeError, match='intentional'):
        audit.capture_hydro(state, endpoint, boundary, 0., (1, 1), 1, 'unscaled')
    assert audit.temporal.bank.hydrostatic_faces is faces
    assert audit.temporal.bank.nonlinear_pressure_force is pressure
