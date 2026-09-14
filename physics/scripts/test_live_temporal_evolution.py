"""Observation ownership, full interval evolution, and binary reference checks."""
import copy
import struct
import numpy as np
import pytest
import audit_live_temporal_evolution as audit


def record():
    a = dict(nx=3, ny=2, cell_meters=.5, origin_x=2., origin_y=-4., native_seconds=.125, revision=1,
             state=np.tile([1., .75, 0., 0.], (6, 1)).ravel().tolist(), bed=[0.]*6,
             exterior_state=np.tile([1., .75, 0., 0.], (10, 1)).ravel().tolist(), exterior_bed=[0.]*10,
             face_normal_velocity=[.75]*4+[0.]*6)
    b = copy.deepcopy(a); b.update(native_seconds=.15625, revision=2)
    return dict(schema='raftsim.live_temporal_boundary_inputs.v1', first=a, second=b)


@pytest.mark.parametrize('key,value', [('origin_x', 3.), ('origin_y', 0.), ('cell_meters', .25),
    ('native_seconds', .125), ('revision', 1), ('bed', [1.]*6), ('exterior_bed', [1.]*10),
    ('face_normal_velocity', [float('nan')]*10), ('nx', 513)])
def test_bad_pair_rejected(key, value):
    source = record(); source['second'][key] = value
    with pytest.raises(ValueError): audit.observations(source)


def test_nonzero_foam_cannot_be_dropped():
    source = record(); source['first']['state'][3] = .01
    with pytest.raises(ValueError, match='foam'): audit.observations(source)


def test_boundary_uses_actual_independent_face_observations():
    source = record(); source['second']['face_normal_velocity'] = [2.]*10
    a, b = audit.observations(source); duration, sample = audit.boundary_provider(a, b)
    for t in (0., duration*.25, duration):
        es, bed, trace = sample(t, None)
        np.testing.assert_array_equal(es, a['exterior_state'])
        np.testing.assert_array_equal(bed, a['exterior_bed'])
        np.testing.assert_array_equal(trace[:, 0], (1-t/duration)*a['face_normal_velocity']+t/duration*b['face_normal_velocity'])
        np.testing.assert_array_equal(trace[:, 1], (b['face_normal_velocity']-a['face_normal_velocity'])/duration)
    for t in (-1e-10, duration+1e-10, float('nan')):
        with pytest.raises(ValueError): sample(t, None)


def test_complete_interval_evolves_not_second_interior_reset(tmp_path):
    source = record(); source['second']['state'][0] = 1.5
    initial = copy.deepcopy(source)
    result, report = audit.replay(source)
    np.testing.assert_array_equal(result, np.asarray(source['first']['state']).reshape(2, 3, 4)[..., :3])
    assert source == initial
    assert report['completed'] and not report['integrated'] and not report['scene_accepted']
    assert report['statistics']['elapsed_s'] == .03125
    assert report['statistics']['steps'] == 4 and report['statistics']['rejected_trials'] == 0
    assert abs(report['statistics']['mass_balance_error_m3']) < 1e-14
    path = tmp_path/'fixture.bin'; audit.write_fixture(path, source, result)
    data = path.read_bytes()
    assert struct.unpack('<IIIIfdd', data[:36]) == (0x52535445, 1, 3, 2, .5, .125, .15625)
    assert len(data) == 36+4*(6*4+6+2*10*4+10+2*10+6*4)
    with pytest.raises(FileExistsError): audit.write_fixture(path, source, result)


def test_initial_failure_preserves_input(monkeypatch):
    def fail(*args, **kwargs): raise ValueError('pressure residual')
    monkeypatch.setattr(audit.bank, 'advance', fail)
    source = record(); state, report = audit.replay(source)
    assert not report['completed'] and report['failure']['elapsed_s'] == 0
    np.testing.assert_array_equal(state, np.asarray(source['first']['state']).reshape(2, 3, 4)[..., :3])


def test_hybrid_interval_keeps_constant_solution_and_declares_fixture_mode(tmp_path):
    source=record(); before=copy.deepcopy(source)
    expected,default=audit.replay(source)
    actual,report=audit.replay(source,breaking_model='hybrid_front')
    assert source==before and report['completed'] and report['breaking_model']=='hybrid_front'
    np.testing.assert_array_equal(actual,expected)
    old=tmp_path/'nonbreaking.bin'; new=tmp_path/'hybrid.bin'
    audit.write_fixture(old,source,expected)
    audit.write_fixture(new,source,actual,breaking_model='hybrid_front')
    a,b=old.read_bytes(),new.read_bytes()
    assert struct.unpack('<I',b[4:8])==(2,) and struct.unpack('<I',b[36:40])==(1,)
    assert a[36:]==b[40:]
    assert len(b)==len(a)+4
    with pytest.raises(ValueError):audit.replay(source,breaking_model='unknown')
    with pytest.raises(ValueError):audit.write_fixture(tmp_path/'bad.bin',source,actual,breaking_model='unknown')
