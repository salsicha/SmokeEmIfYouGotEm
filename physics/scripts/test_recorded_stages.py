import numpy as np
import pytest
import audit_recorded_stages as audit


def metadata():
    return dict(schema='raftsim.recorded_nonlinear_stages.v1', trials=[dict(byte_offset=0)])


def test_stage_layout_does_not_alias_final_clock_or_flags():
    data = bytearray(audit.RECORD_BYTES)
    for stage in range(2):
        offset = stage*audit.STAGE_BYTES
        np.frombuffer(data, '<f4', audit.N*4, offset)[:] = stage+1
        np.frombuffer(data, '<u4', audit.N, offset+audit.N*40)[:] = 3
        np.frombuffer(data, '<f4', audit.N*2, offset+audit.N*48)[:] = stage+4
    np.frombuffer(data, '<f4', audit.N*4, audit.N*112)[:] = 9
    np.frombuffer(data, '<f4', 4, audit.N*128)[:] = [10, .125, 0, 0]
    np.frombuffer(data, '<u4', 4, audit.N*128+32)[:] = [0, 0, 0, 1]
    _, stages, final, clock, info, flags = next(audit.read_records(metadata(), data))
    assert (stages[0]['state'] == 1).all() and (stages[1]['state'] == 2).all()
    assert (stages[0]['pairs'] == 3).all() and (stages[1]['force'] == 5).all()
    assert (final == 9).all() and clock.tolist() == [10, .125, 0, 0]
    assert flags.tolist() == [0, 0, 0, 1]


@pytest.mark.parametrize('size', [audit.RECORD_BYTES-1, audit.RECORD_BYTES+1])
def test_truncated_or_trailing_trace_rejected(size):
    with pytest.raises(ValueError): list(audit.read_records(metadata(), bytearray(size)))


def test_unexpected_offset_rejected():
    record = metadata(); record['trials'][0]['byte_offset'] = 16
    with pytest.raises(ValueError): list(audit.read_records(record, bytearray(audit.RECORD_BYTES)))


def test_polynomial_layout_keeps_both_stages_and_final_clock_separate():
    record = metadata(); record['schema'] = 'raftsim.recorded_nonlinear_stages.v2'
    data = bytearray(audit.POLYNOMIAL_RECORD_BYTES)
    for stage in range(2):
        offset = stage*audit.N*120
        np.frombuffer(data, '<f4', audit.N*4, offset)[:] = stage+1
        for k in range(4):
            np.frombuffer(data, '<f4', audit.N*4, offset+audit.N*(56+16*k))[:] = 10*stage+k+3
    np.frombuffer(data, '<f4', audit.N*4, audit.N*240)[:] = 20
    np.frombuffer(data, '<f4', 4, audit.N*256)[:] = [2, .125, 0, 0]
    _, stages, final, clock, _, _ = next(audit.read_records(record, data))
    for stage in range(2):
        assert (stages[stage]['state'] == stage+1).all()
        for k, name in enumerate(('raw_x', 'raw_y', 'slope_x', 'slope_y')):
            assert (stages[stage][name] == 10*stage+k+3).all()
    assert (final == 20).all() and clock.tolist() == [2, .125, 0, 0]


def test_polynomial_layout_rejects_old_size_and_excess_records():
    record = metadata(); record['schema'] = 'raftsim.recorded_nonlinear_stages.v2'
    with pytest.raises(ValueError, match='binary'):
        list(audit.read_records(record, bytearray(audit.RECORD_BYTES)))
    record['trials'] *= 65
    with pytest.raises(ValueError, match='count'):
        list(audit.read_records(record, b''))


@pytest.mark.parametrize('interval', [-1, 1, 1.5])
def test_operator_rejects_out_of_range_or_fractional_interval(interval):
    record = metadata(); record['trials'][0]['interval'] = interval
    with pytest.raises(ValueError, match='outside observed'):
        audit.operators(record, bytearray(audit.RECORD_BYTES), dict(observations=[{}, {}]))


@pytest.mark.parametrize('limiter,mode', [('binary', 1), ('continuous', 3), ('unscaled', 5)])
def test_operator_uses_captured_model_at_both_stages(monkeypatch, limiter, mode):
    scalar = np.zeros((128, 128)); vector = np.zeros((128, 128, 2))
    state = np.zeros((128, 128, 4)); state[..., 0] = 1
    stage = dict(state=state, rate=np.zeros_like(state), force=vector,
        fraction=scalar, pairs=scalar.astype(np.uint32))
    trial = dict(interval=0, trial=0, begin=0., attempted_dt=.001)
    monkeypatch.setattr(audit, 'read_records', lambda *_: iter([(trial, [stage, stage], state, None, None, None)]))
    endpoint = dict(bed=scalar, native_seconds=0.)
    monkeypatch.setattr(audit.temporal, 'observations', lambda *_: (endpoint, endpoint))
    monkeypatch.setattr(audit.temporal, 'boundary_provider', lambda *_: (None, lambda *_: (None, None, None)))
    calls = []
    def rate(*args, **kwargs):
        calls.append(kwargs['shoreline_limiter'])
        audit.temporal.bank.nonlinear_pressure_force(state[..., 0], scalar, vector, vector,
            [scalar.astype(bool), scalar.astype(bool)], .5, dispersion_fraction=scalar, bed_slope=vector)
        return np.zeros((128, 128, 3)), .001
    monkeypatch.setattr(audit.temporal.bank, 'rate', rate)
    monkeypatch.setattr(audit, 'nonlinear_pressure_force', lambda *_args, **_kwargs: (vector, []))
    report = audit.operators(dict(shoreline_limiter=limiter, trials=[trial]), b'',
        dict(shoreline_limiter=limiter, summary=[1, 1, 1, mode], observations=[{}, {}]))
    assert calls == [limiter, limiter]
    assert report['shoreline_limiter'] == limiter and report['maximum_hydro_error'] == 0


def test_operator_rejects_mismatched_model_before_arithmetic():
    with pytest.raises(ValueError, match='mode'):
        audit.operators(dict(shoreline_limiter='unscaled'), b'',
            dict(shoreline_limiter='unscaled', summary=[1, 1, 2, 3]))
