from types import SimpleNamespace
import numpy as np
import pytest

from test_subcell_wet_pool_pressure import partition
from triangle_cell_storage import TriangleCellStorage
from triangle_face_section import TriangleFaceSection
from subcell_source_region_faces import clipped_edge
from subcell_energy_flux import face_flux_normal
from subcell_wet_pool_pressure import WetPoolPressureSystem
from subcell_wet_pool_pressure_rate import WetPoolPressureRate
from subcell_wet_pool_primal_energy import evaluate, kinetic_volume_gradient
from subcell_wet_pool_transport import rates
from finite_depth_pressure_reference import LENGTHS


def regions(height=lambda x, y: .2*x-.13*y, spacing=(1., 1.), origin=(.11, .07)):
    base, _, _, _ = partition(height, .713, (1, 1), spacing, origin)
    cell = base.patch.cells[0]
    states = []
    for source in sorted(set(cell.source_triangle_indices)):
        mask = cell.source_triangle_indices == source
        storage = TriangleCellStorage(cell.triangles[mask], cell.source_triangle_indices[mask])
        volume = storage.volume_and_wet_area(.713)[0]
        states.append(dict(parent=0, source_triangle_indices=[int(source)], volume=volume,
                           momentum=volume*np.array([.4, -.2])))
    return base, base.with_regions(states), states


def test_exact_internal_edge_clip_excludes_point_box_and_vertical_contacts():
    source = SimpleNamespace(xyz=np.array([[-1., -1., 0.], [1., 1., 2.],
                                          [-.5, -.5, 0.], [-.5, .5, 0.], [0., 0., 0.], [0., 0., 1.]]))
    xyz, length = clipped_edge(source, (0, 1), [0., 0.], [1., 1.])
    np.testing.assert_allclose(xyz, [[-.5, -.5, .5], [.5, .5, 1.5]], atol=0.)
    np.testing.assert_allclose(length, np.sqrt(2), atol=0.)
    assert clipped_edge(source, (2, 3), [0., 0.], [1., 1.]) is None
    assert clipped_edge(source, (4, 5), [0., 0.], [1., 1.]) is None
    assert clipped_edge(source, (0, 1), [1.5, -.5], [1., 1.]) is None


@pytest.mark.parametrize('dissipative', [False, True])
def test_oblique_flux_rotation_and_owner_reversal(dissipative):
    section = TriangleFaceSection([[[0., -.2], [1., .3]]], [0., 1.])
    left, right, normal = np.array([.7, -.2]), np.array([-.3, .9]), np.array([.6, .8])
    f, info = face_flux_normal(section, .73, left, .51, right, normal, dissipative=dissipative)
    angle = .61
    rot = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    g, other = face_flux_normal(section, .73, rot@left, .51, rot@right, rot@normal, dissipative=dissipative)
    np.testing.assert_allclose(g, np.r_[f[0], rot@f[1:]], atol=1e-14)
    np.testing.assert_allclose(other['expected_energy_work'], info['expected_energy_work'], atol=1e-14)
    reversed_flux, _ = face_flux_normal(section, .51, right, .73, left, -normal, dissipative=dissipative)
    np.testing.assert_allclose(reversed_flux, -f, atol=1e-14)
    with pytest.raises(ValueError, match='unit'):
        face_flux_normal(section, .73, left, .51, right, normal*2)


def test_explicit_source_regions_preserve_geometry_without_forcing_shared_state():
    base, divided, states = regions()
    assert len(divided.pools) > 1
    assert divided.internal_faces
    np.testing.assert_allclose(divided.reassembled_volumes, base.reassembled_volumes, atol=1e-14)
    np.testing.assert_allclose(divided.reassembled_momenta, base.reassembled_momenta, atol=1e-14)
    assert divided.maximum_volume_error is None
    assert base.parent_pools == [[0]]
    assert any(np.all(abs(face['normal']) > .1) for face in divided.internal_faces)
    for face in divided.internal_faces:
        assert face['left'] != face['right']
        np.testing.assert_allclose(np.linalg.norm(face['normal']), 1., atol=1e-15)
        assert len(face['edge_vertex_ids']) == 2
    with pytest.raises(ValueError, match='Disjoint'):
        base.with_regions(states+[states[0]])
    with pytest.raises(ValueError, match='Disjoint'):
        base.with_regions([dict(states[0], source_triangle_indices=[1000000])])


@pytest.mark.parametrize('dissipative', [False, True])
def test_internal_source_faces_close_bed_geometry_mass_momentum_and_base_work(dissipative):
    _, divided, _ = regions()
    volume = np.array([p['volume'] for p in divided.pools])
    p = volume[:, None]*np.random.default_rng(2701).normal(size=(len(volume), 2))
    r = rates(divided, p, dissipative=dissipative)
    assert r['complete_fixed_topology_base_rates']
    assert r['internal_active_source_edges'] > 0
    assert r['maximum_hydrostatic_geometry_closure_error'] < 1e-12
    assert r['momentum_boundary_bed_error'] < 1e-12
    assert abs(r['net_mass_rate']) < 1e-12
    assert r['base_energy_identity_error'] < 1e-11
    lake = rates(divided, np.zeros_like(p))
    np.testing.assert_allclose(lake['momentum_rate'], 0., atol=1e-12)
    np.testing.assert_allclose(lake['volume_rate'], 0., atol=1e-12)


@pytest.mark.parametrize('length', LENGTHS)
def test_internal_pressure_symmetry_derivative_and_reverse_gradient(length):
    _, divided, _ = regions()
    system = WetPoolPressureSystem(divided, float(length))
    assert any(face.get('internal_source_edge') for face in system.connections)
    assert system.source_blocks
    volume = system.h[:, 0]
    rng = np.random.default_rng(2702)
    q, r = rng.normal(size=(2, len(volume), 1, 2))
    matrix = np.column_stack([system.apply(e.reshape(q.shape)).ravel() for e in np.eye(q.size)])
    for indices, cholesky in system.source_blocks:
        dofs = np.array([[2*i, 2*i+1] for i in indices]).ravel()
        np.testing.assert_allclose(cholesky@cholesky.T, matrix[np.ix_(dofs, dofs)], atol=1e-11)
        actual = system.precondition(q, 'source-block')[indices].ravel()
        np.testing.assert_allclose(actual, np.linalg.solve(matrix[np.ix_(dofs, dofs)], q[indices].ravel()), atol=1e-11)
    pq, pr = system.precondition(q, 'source-block'), system.precondition(r, 'source-block')
    assert float(np.sum(q*pq)) > 0
    np.testing.assert_allclose(np.sum(q*pr), np.sum(r*pq), atol=1e-12)
    vd = volume*rng.uniform(-.1, .1, len(volume))
    np.testing.assert_allclose(np.sum(q*system.apply(r)), np.sum(r*system.apply(q)), atol=1e-11)
    tangent = WetPoolPressureRate(system, vd[:, None])
    step = 1e-5
    low = WetPoolPressureSystem(divided.volume_probe(volume-step*vd), float(length))
    high = WetPoolPressureSystem(divided.volume_probe(volume+step*vd), float(length))
    np.testing.assert_allclose(tangent.apply(q), (high.apply(q)-low.apply(q))/(2*step), rtol=1e-7, atol=2e-7)
    reverse = kinetic_volume_gradient(system, q)['value']@vd
    np.testing.assert_allclose(reverse, .5*np.sum(q*tangent.apply(q))/length, atol=1e-11)
    p = volume[:, None, None]*q
    energy = evaluate(divided, p)
    before, after = evaluate(low.partition, p), evaluate(high.partition, p)
    np.testing.assert_allclose(energy['volume_gradient']@vd, (after['total']-before['total'])/(2*step), atol=1e-8, rtol=1e-7)


def test_original_disconnected_pool_graph_keeps_unchanged_local_preconditioning():
    base, _, _, _ = partition(lambda x, y: 1-abs(x), .37)
    system = WetPoolPressureSystem(base, float(LENGTHS[0]))
    assert not system.source_blocks
    q = np.ones((len(base.pools), 1, 2))
    np.testing.assert_array_equal(system.precondition(q, 'block'), system.precondition(q, 'source-block'))
    assert system.solve(q)[1]['preconditioner'] == 'block'


def test_missing_internal_source_region_requires_activation_not_a_false_wall():
    base, divided, states = regions(lambda x, y: 0*x, (2., 2.), (0., 0.))
    omitted = next(state for state in states if np.all(abs(base.sampler.xyz[base.sampler.faces[state['source_triangle_indices'][0]], :2]) < 1))
    candidate = base.with_regions([s for s in states if s is not omitted])
    result = rates(candidate)
    pending = [f for f in result['unresolved_activation_faces'] if f['axis'] is None]
    assert len(pending) == 3
    assert all(f['left_parent'] == f['right_parent'] == 0 for f in pending)
    assert result['volume_rate'] is None and result['momentum_rate'] is None


def test_thin_region_uses_local_datum_for_topology_not_rounded_absolute_stage():
    base, _, _, _ = partition(lambda x, y: np.clip(x+.5, 0., 1.), 1.713, (1, 1), (2., 2.), (0., 0.))
    cell = base.patch.cells[0]
    source = next(int(i) for i in set(cell.source_triangle_indices)
                  if np.all(cell.triangles[cell.source_triangle_indices == i, :, 2] == 1.))
    for volume in (1e-20, 1e-50, 1e-150):
        state = dict(parent=0, source_triangle_indices=[source], volume=volume,
                     momentum=np.array([.4, -.2])*volume)
        candidate = base.with_regions([state])
        form = candidate.pools[0]['form']
        assert form['stage_offset'] > 0
        assert form['stage_offset']+form['datum'] == form['datum']
        assert candidate.volume_probe(np.array([2*volume])).pools[0]['volume'] == 2*volume
