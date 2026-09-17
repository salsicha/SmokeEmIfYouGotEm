import numpy as np
import pytest

from audit_froth_characteristics import FrozenCurrent, error_summary, analyze


def field(velocity):
    y, x = np.indices((65, 65))
    flow = np.zeros((65, 65, 4)); flow[..., 0] = 2
    flow[..., 1], flow[..., 2] = velocity(x*.5-16, y*.5-16)
    return FrozenCurrent(flow, (-16, -16), .5)


@pytest.mark.parametrize('order', [1, 2, 4])
def test_uniform_current_and_source_unchanged(order):
    f = field(lambda x, y: (x*0+1.25, y*0-.75))
    original = f.flow.copy(); points = np.array([[1., 3.], [-5., -4.]])
    out, ok = f.depart(points, .75, 8, order)
    assert ok.all()
    np.testing.assert_allclose(out, points-.75*np.array([1.25, -.75]), atol=1e-12)
    assert np.array_equal(f.flow, original)


def test_shear_bending_missed_by_straight_backtrace():
    f = field(lambda x, y: (.8*y+1, y*0+2))
    p = np.array([[0., 0.], [2., 1.]])
    t = .75
    exact = p-np.stack(((.8*p[:, 1]+1)*t-.8*t*t, np.full(2, 2*t)), axis=1)
    straight, ok = f.depart(p, t, 1, 1)
    mid, valid = f.depart(p, t, 2, 2)
    assert ok.all() and valid.all()
    np.testing.assert_allclose(mid, exact, atol=1e-12)
    assert np.linalg.norm(straight-exact, axis=1).min() > .4


def test_rotation_converges_to_independent_analytic_solution():
    f = field(lambda x, y: (-.7*y, .7*x))
    p = np.array([[2., 1.], [-3., 4.]])
    t = .75; a = -.7*t
    rotation = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    exact = p@rotation.T
    errors = []
    for steps in (2, 4, 8, 16):
        out, valid = f.depart(p, t, steps, 2)
        assert valid.all()
        errors.append(np.linalg.norm(out-exact))
    assert all(a/b > 3.8 for a, b in zip(errors, errors[1:]))
    out, valid = f.depart(p, t, 128, 4)
    assert valid.all()
    np.testing.assert_allclose(out, exact, atol=1e-10)


def test_missing_and_dry_are_not_zero_flow_or_clamped():
    f = field(lambda x, y: (x*0+2, y*0))
    p = np.array([[-15.8, 0.], [20., 0.], [np.nan, 0.]])
    out, valid = f.depart(p, .75, 4, 2)
    assert not valid.any() and np.isnan(out).all()
    f.flow[30:35, 30:35, 0] = 0
    out, valid = f.depart(np.array([[0., 0.]]), .5, 4, 2)
    assert not valid.any() and np.isnan(out).all()


@pytest.mark.parametrize('seconds,steps,order', [(-1, 2, 2), (float('nan'), 2, 2),
                                              (.5, 0, 2), (.5, 1.5, 2), (.5, 2, 3)])
def test_invalid_integrators_reject(seconds, steps, order):
    with pytest.raises(ValueError):
        field(lambda x, y: (x*0, y*0)).depart(np.zeros((1, 2)), seconds, steps, order)


def test_empty_summary_is_unavailable_not_zero_error():
    assert error_summary(np.array([])) == dict(count=0, rms_m=None, p95_m=None, maximum_m=None)


def snapshot(tmp_path):
    import json
    prefix = tmp_path/'source'
    metadata = dict(schema='raftsim.detail.snapshot.v2',arrays_complete=True,
                    dtype='little-endian float32',shape=[25,25,4],origin_m=[-6,-6],
                    cell_m=.5,simulation_s=12)
    (tmp_path/'source.json').write_text(json.dumps(metadata))
    flow = np.zeros((25,25,4),dtype='<f4');flow[...,0]=2;flow[...,1]=1.25;flow[...,2]=-.75
    surface = np.zeros_like(flow);surface[...,3]=.5
    flow.tofile(tmp_path/'source.flow.f32');surface.tofile(tmp_path/'source.surface.f32')
    return prefix, metadata


def test_complete_source_rows_and_common_cohorts(tmp_path):
    prefix, _ = snapshot(tmp_path)
    report = analyze(prefix)
    assert report['original_wet_interior_cells'] == 81
    assert len(report['input_sha256']) == 3
    assert not report['visual_accepted'] and not report['physical_accepted']
    for record in report['records']:
        assert len(record['rows']) == 81 and record['common_supported_rows'] == 81
        for method in record['methods'].values():
            assert method['common_foamy']['count'] == 81
            assert method['common_foamy']['maximum_m'] < 1e-12


@pytest.mark.parametrize('change', [dict(arrays_complete='true'),dict(simulation_s=float('nan')),
                                  dict(shape=[25,25,3]),dict(cell_m=0)])
def test_invalid_original_snapshot_rejected(tmp_path,change):
    import json
    prefix, metadata = snapshot(tmp_path)
    metadata.update(change)
    (tmp_path/'source.json').write_text(json.dumps(metadata))
    with pytest.raises(ValueError):
        analyze(prefix)
