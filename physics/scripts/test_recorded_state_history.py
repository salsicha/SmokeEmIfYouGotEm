import json
import numpy as np
import pytest
import audit_recorded_state_history as history
from audit_recorded_stages import RECORD_BYTES, N


def fixture(tmp_path):
    source = json.dumps(dict(observations=[dict(native_seconds=1., origin_x=2., origin_y=3.), {}])).encode()
    source_path = tmp_path/'source.json'; source_path.write_bytes(source)
    binary = bytearray(RECORD_BYTES)
    np.frombuffer(binary, '<f4', N*4)[:] = 2
    binary_path = tmp_path/'trace.bin'; binary_path.write_bytes(binary)
    metadata = dict(schema='raftsim.recorded_nonlinear_stages.v1', completed=True,
        final_state_exact_to_live=True, source=str(source_path), binary=str(binary_path),
        trials=[dict(byte_offset=0, interval=0, trial=0, begin=1.)])
    return source, metadata, tmp_path/'trace.json'


def test_exact_endpoint_and_duplicate_capture(tmp_path):
    source, metadata, path = fixture(tmp_path); path.write_text(json.dumps(metadata))
    values, provenance = history.recorded_endpoints([path, path], source)
    assert len(values) == 1 and len(provenance) == 2
    np.testing.assert_array_equal(values[(1., (2., 3.))], np.full((128, 128, 3), 2.))


@pytest.mark.parametrize('field,value', [('interval', -1), ('interval', 1), ('interval', 0.5),
    ('trial', -1), ('trial', 0.5), ('begin', 1.1), ('completed', False), ('final_state_exact_to_live', False)])
def test_unqualified_endpoint_rejected(tmp_path, field, value):
    source, metadata, path = fixture(tmp_path)
    target = metadata if field in ('completed', 'final_state_exact_to_live') else metadata['trials'][0]
    target[field] = value; path.write_text(json.dumps(metadata))
    with pytest.raises(ValueError): history.recorded_endpoints([path], source)


def test_other_source_history_rejected(tmp_path):
    source, metadata, path = fixture(tmp_path); path.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match='another live source'):
        history.recorded_endpoints([path], source+b' ')


def test_endpoint_model_must_match_its_captured_history(tmp_path):
    source, metadata, path = fixture(tmp_path)
    metadata['shoreline_limiter'] = 'continuous';path.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match='different shoreline model'):
        history.recorded_endpoints([path], source)
    record = json.loads(source);record['shoreline_limiter'] = 'continuous'
    source = json.dumps(record).encode()
    from pathlib import Path
    Path(metadata['source']).write_bytes(source)
    values, _ = history.recorded_endpoints([path], source)
    assert len(values) == 1
