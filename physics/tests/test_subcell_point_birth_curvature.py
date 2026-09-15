from fractions import Fraction as F
import numpy as np
import pytest

from subcell_point_birth_curvature import point_curvature_limit
from subcell_source_birth_pressure import SourceBirthPressure
from subcell_source_birth_geometry import SourceBirthGeometry
from subcell_source_curvature import SourceCurvatureTensor
from subcell_wet_pool_pressure import WetPoolPressureSystem
from subcell_wet_pool_primal_energy import evaluate
from subcell_geometry_patch import SubcellGeometryPatch
from subcell_wet_pool_partition import WetPoolPartition
from test_triangle_face_section import sampler
from test_subcell_source_birth_pressure import fixture as planar
from test_subcell_simultaneous_birth_pressure import requests_for, positive_probes


def crease(axis=0):
    source = sampler((lambda x, y: x+2*y+.5*abs(x)) if axis == 0
                     else (lambda x, y: 2*x+y+.5*abs(y)))
    shape, origin = ((1, 2), [-.25, .25]) if axis == 0 else ((2, 1), [.25, -.25])
    patch = SubcellGeometryPatch(source, origin, shape, [.5, .5], relative_stages=True, exact_sources=True)
    volume, momentum = patch.state_from_stages(np.array([1.17, -5.]).reshape(shape), (.8, .25))
    return WetPoolPartition(patch, source, origin, volume, momentum)


def original_force(part, requests, path, velocity):
    candidate = positive_probes(part, requests, path, velocity)
    momentum = np.array([p['momentum'] for p in candidate.pools])[:, None]
    volume = np.array([p['volume'] for p in candidate.pools])[:, None, None]
    root = np.sqrt(volume)
    primal = evaluate(candidate, momentum)
    u, result = momentum/volume, np.zeros_like(momentum)
    for pole in primal['poles']:
        s = WetPoolPressureSystem(candidate, pole['beta'])
        curvature = SourceCurvatureTensor(s)
        w = pole['normalized_auxiliary_velocity']/root
        nu = curvature.action(w, u)
        solution, stats = s.solve(nu/root)
        assert stats['relative_residual'] < 2e-5
        result += pole['alpha']*(root*solution-curvature.action(w, w))
    return result[:, 0], candidate


@pytest.mark.parametrize('axis', [0, 1])
@pytest.mark.parametrize('velocity', [(0., 0.), (.27, -.13)])
def test_guarded_common_trace_has_independent_nonzero_point_singularity(axis, velocity):
    part = crease(axis)
    requests = requests_for(part, (.7, 1.6))
    result = point_curvature_limit(SourceBirthPressure(part), requests, velocity)
    assert result['edges'] and all(not e['internal'] for e in result['edges'])
    expected = np.vstack((result['old_force_path_squared_limit'], result['newborn_force_path_squared_limit']))
    assert np.max(abs(expected)) > 1e-7
    errors = []
    for path in (1e-3, 2.5e-4, 6.25e-5, 1.5625e-5, 3.90625e-6):
        force, _ = original_force(part, requests, path, velocity)
        errors.append(np.max(abs(path**2*force-expected)))
    assert errors[-1] < errors[0]/8
    np.testing.assert_allclose(path**2*force, expected, rtol=.005, atol=2e-7)
    assert not result['common_trace_front_or_complete_force_or_time_or_native_or_gameplay_accepted']


def test_zero_crease_does_not_invent_a_singular_curvature_force():
    part, _, _ = planar()
    result = point_curvature_limit(SourceBirthPressure(part), requests_for(part))
    assert not result['edges']
    np.testing.assert_array_equal(result['old_force_path_squared_limit'], 0.)
    np.testing.assert_array_equal(result['newborn_force_path_squared_limit'], 0.)


def test_original_stage_still_rejects_the_unqualified_curvature_front():
    from subcell_nonlinear_metric_stage import stage
    part = crease()
    _, candidate = original_force(part, requests_for(part), 1e-3, (0., 0.))
    with pytest.raises(ValueError, match='One-sided or unequal wet support'):
        stage(candidate)


def test_invalid_bounded_newborn_velocity_rejects():
    part = crease()
    for velocity in ((float('nan'), 0.), np.zeros((3, 2))):
        with pytest.raises(ValueError, match='bounded physical newborn'):
            point_curvature_limit(SourceBirthPressure(part), requests_for(part), velocity)


@pytest.mark.parametrize('reverse', [False, True])
def test_oblique_same_cell_original_edge_and_owner_reversal(reverse):
    source = sampler(lambda x, y: x+2*y+.5*abs(x-y))
    patch = SubcellGeometryPatch(source, [.25, .25], (1, 1), [.5, .5], relative_stages=True, exact_sources=True)
    v, p = patch.state_from_stages([[.5]], (.8, .25))
    base = WetPoolPartition(patch, source, [.25, .25], v, p)
    ids = sorted(map(int, patch.cells[0].source_triangle_indices), reverse=reverse)
    assert len(ids) == 2
    birth = SourceBirthGeometry(patch.cells[0].subset_sources([ids[0]]))
    volume = float(birth.moments(F(.5))[1])
    part = base.with_regions([dict(parent=0, source_triangle_indices=[ids[0]], volume=volume,
                                  momentum=volume*np.array([.8, .25]))])
    requests = [(0, ids[1], 1.3)]
    result = point_curvature_limit(SourceBirthPressure(part), requests)
    assert result['edges'] and all(e['internal'] for e in result['edges'])
    expected = np.vstack((result['old_force_path_squared_limit'], result['newborn_force_path_squared_limit']))
    if reverse:
        assert np.max(abs(expected)) > 1e-7
    else:
        # This orientation has zero leading newborn divergence: the source
        # slope is tangent to the pressure-coupling normal. Retain the zero
        # leading coefficient, not a manufactured nonzero force.
        np.testing.assert_array_equal(expected, 0.)
    errors = []
    for path in (1e-4, 2.5e-5, 6.25e-6):
        actual, _ = original_force(part, requests, path, (0., 0.))
        errors.append(np.max(abs(path**2*actual-expected)))
    assert errors[-1] < errors[0]/8
    np.testing.assert_allclose(path**2*actual, expected, rtol=.005, atol=2e-7)


def test_path_reparameterization_zero_motion_and_original_state_preservation():
    part = crease()
    requests = requests_for(part, (.7, 1.6))
    context = SourceBirthPressure(part)
    first = point_curvature_limit(context, requests, (.27, -.13))
    second = point_curvature_limit(context, [(p, s, 3*k) for p, s, k in requests], (.27, -.13))
    for key in ('old_force_path_squared_limit', 'newborn_force_path_squared_limit'):
        np.testing.assert_allclose(second[key], first[key]/9, atol=1e-11)
    assert context.state_signature() == context.original_state
    scope = first['front_edge_scope']
    assert scope['original_old_new_faces'] == sum(scope[k] for k in scope if k != 'original_old_new_faces')
    for pool in part.pools:
        pool['momentum'][:] = 0.
    zero = point_curvature_limit(SourceBirthPressure(part), requests)
    np.testing.assert_array_equal(zero['old_force_path_squared_limit'], 0.)
    np.testing.assert_array_equal(zero['newborn_force_path_squared_limit'], 0.)


def test_original_pullback_residual_gate_and_independent_probe(monkeypatch):
    import subcell_point_birth_curvature as curvature
    from audit_south_fork_simultaneous_birth import curvature_probe
    part = crease()
    requests = requests_for(part, (.7, 1.6))
    expected = point_curvature_limit(SourceBirthPressure(part), requests)
    candidate = positive_probes(part, requests, 1e-5, (0., 0.))
    report = curvature_probe(part, candidate, 1e-5, expected)
    assert report['maximum_relative_coefficient_error'] < .001
    assert not report['common_trace_front_or_full_model_accepted']
    expected['newborn_force_path_squared_limit'] += 1.
    wrong = curvature_probe(part, candidate, 1e-5, expected)
    assert wrong['maximum_relative_coefficient_error'] > .9
    original = curvature.range_cg
    def bad_residual(*args, **kwargs):
        value, stats = original(*args, **kwargs)
        return value, dict(stats, relative_residual=3e-5)
    monkeypatch.setattr(curvature, 'range_cg', bad_residual)
    with pytest.raises(ValueError, match='curvature pullback residual gate'):
        point_curvature_limit(SourceBirthPressure(part), requests)
