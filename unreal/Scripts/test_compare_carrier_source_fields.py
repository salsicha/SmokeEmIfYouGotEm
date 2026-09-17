from copy import deepcopy
import numpy as np
import pytest
from compare_carrier_source_fields import compare


def fixture(sign=-1):
    meta = dict(schema='raftsim.submitted_carrier_shape.v2', source_nx=3, source_ny=3,
                world_y_sign=sign, game_frame=155, world_seconds=11., detail_sequence=150)
    xy = np.array([[x, y] for y in range(3) for x in range(3)], dtype=float)
    source = np.column_stack((np.arange(9), xy, np.ones(9), xy[:, 0]+2*xy[:, 1],
                              np.ones(9), np.zeros((9, 2))))
    points = np.array([[.25, .25, 0], [.75, .25, 0], [.25, .75, 0]])
    points[:, 1] *= sign
    rays = dict(game_frame=155, world_seconds=11., detail_sequence=150,
        probes=[dict(pixel=[640, 650], hit=dict(triangle=4, vertices_world_m=points.tolist(), slope_degrees=70.))])
    return meta, source, rays


@pytest.mark.parametrize('sign', [-1, 1])
def test_same_xy_affine_stages_and_distinct_epochs(sign):
    a, source, rays = fixture(sign)
    b, candidate = dict(a, game_frame=99, world_seconds=12., detail_sequence=80), source.copy()
    candidate[:, 4] = 3+4*candidate[:, 1]+5*candidate[:, 2]
    result = compare(a, source, rays, b, candidate)
    row = result['probes'][0]
    assert row['comparison_available'] and not result['accepted']
    np.testing.assert_allclose(row['reference']['gradient_world_xy'], [1, 2*sign], rtol=0, atol=1e-14)
    np.testing.assert_allclose(row['candidate']['gradient_world_xy'], [4, 5*sign], rtol=0, atol=1e-14)
    assert result['candidate_epoch']['game_frame'] == 99


def test_missing_dry_and_outside_are_preserved_not_compared():
    a, source, rays = fixture()
    rays['probes'].append(dict(pixel=[0, 0], hit=None))
    for mode in ('dry', 'outside'):
        candidate = source.copy()
        if mode == 'dry': candidate[0, 3] = 0
        else: candidate[:, 1] += 100
        result = compare(a, source, rays, a, candidate)
        assert len(result['probes']) == 2 and result['comparable_probes'] == 0
        assert 'candidate_minus_reference_stage_m' not in result['probes'][0]


def test_different_window_origin_and_resolution_still_use_world_coordinates():
    a, source, rays = fixture()
    b = dict(a, source_nx=5, source_ny=5)
    xy = np.array([[x, y] for y in np.arange(-.5, 2., .5) for x in np.arange(-.5, 2., .5)])
    candidate = np.column_stack((np.arange(25), xy, np.ones(25), xy[:, 0]+2*xy[:, 1],
                                 np.ones(25), np.zeros((25, 2))))
    row = compare(a, source, rays, b, candidate)['probes'][0]
    assert row['comparison_available']
    np.testing.assert_array_equal(row['candidate_minus_reference_stage_m'], np.zeros(3))


def test_nonplanar_quad_preserves_original_shoreline_diagonal():
    a, source, rays = fixture(sign=1)
    source[:, 4] = 0
    source[4, 4] = 1  # D corner of the first cell; other corners are zero.
    row = compare(a, source, rays, a, source)['probes'][0]
    np.testing.assert_array_equal(row['reference']['stage_m'], [.25, .25, .25])
    np.testing.assert_array_equal(row['candidate_minus_reference_stage_m'], np.zeros(3))


@pytest.mark.parametrize('kind', ['order', 'nonfinite', 'wet', 'depth', 'nonuniform', 'row_xy'])
def test_invalid_source_rejected(kind):
    a, source, rays = fixture()
    candidate = source.copy()
    if kind == 'order': candidate[0, 0] = 1
    if kind == 'nonfinite': candidate[0, 4] = np.nan
    if kind == 'wet': candidate[0, 3] = .5
    if kind == 'depth': candidate[0, 5] = -1
    if kind == 'nonuniform': candidate[2::3, 1] += .1
    if kind == 'row_xy': candidate[3, 1] += .1
    with pytest.raises(ValueError): compare(a, source, rays, a, candidate)


def test_unrelated_epoch_and_axis_convention_rejected():
    a, source, rays = fixture()
    for key in ('game_frame', 'world_seconds', 'detail_sequence'):
        altered = deepcopy(rays); altered[key] += 1
        with pytest.raises(ValueError, match='epoch'): compare(a, source, altered, a, source)
    with pytest.raises(ValueError, match='conventions'):
        compare(a, source, rays, dict(a, world_y_sign=1), source)
