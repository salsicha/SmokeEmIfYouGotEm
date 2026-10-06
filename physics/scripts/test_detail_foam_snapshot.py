import numpy as np
import pytest

from audit_detail_foam_snapshot import analyze, audit, smoothstep
from test_detail_mean_geometry import fixture


def data():
    flow = np.zeros((32, 32, 4), dtype='<f4'); flow[..., 0] = 1.; flow[..., 3] = .2
    state = np.zeros_like(flow); state[..., 3] = 2.
    y, x = np.indices(flow.shape[:2])
    weight = smoothstep(0., 4., np.minimum.reduce((x, y, 31-x, 31-y))*.5)
    surface = np.zeros_like(flow); surface[..., 3] = -np.expm1(-2.)*weight
    return flow, state, surface


def test_density_resolve_and_unattributed_advected_foam():
    flow, state, surface = data(); flow[..., 3] = 0.
    result = analyze(flow, state, surface, .5)
    assert result['resolve_equation_passed']
    assert result['nonzero_coverage_on_zero_weight'] == 0
    assert result['groups']['full_weight']['dense_foam_with_current_source_below_005'] == 256
    assert result['density_sum_cell_area'] == 512.


def test_paired_surface_mismatch_is_not_a_pass():
    flow, state, surface = data(); surface[16, 16, 3] -= .1
    assert not analyze(flow, state, surface, .5)['resolve_equation_passed']


@pytest.mark.parametrize('kind', ['nan', 'negative_density', 'negative_depth', 'source_range'])
def test_invalid_physical_inputs_refused(kind):
    flow, state, surface = data()
    if kind == 'nan': surface[0, 0, 0] = np.nan
    if kind == 'negative_density': state[0, 0, 3] = -1.
    if kind == 'negative_depth': flow[0, 0, 0] = -1.
    if kind == 'source_range': flow[0, 0, 3] = 1.1
    with pytest.raises(ValueError): analyze(flow, state, surface, .5)


def test_surface_is_length_checked_and_hash_bound(tmp_path):
    import json
    path, metadata = fixture(tmp_path); metadata['cell_m'] = .5
    path.write_text(json.dumps(metadata))
    surface_path = path.with_suffix('.surface.f32'); surface_path.write_bytes(b'bad')
    with pytest.raises(ValueError, match='surface'): audit(path)
    np.zeros((3, 4, 4), dtype='<f4').tofile(surface_path)
    result = audit(path)
    assert result['analysis']['resolve_equation_passed']
    assert str(surface_path) in result['sha256']
