import json

import numpy as np
import pytest

from audit_cartesian_storage_regions import compare_storage, digest, partition, run


def grid(x=0):
    return dict(nx=2, ny=2, dx=1., dy=1., origin_x=x, origin_y=0.)


def test_partition_covers_every_cell_once_in_native_east_north():
    points = [[0, 0, 0], [1, 1, 0], [2, 2, 0], [3, 3, 0]]
    labels, shape, area = partition([grid(), grid(2)], points, 2.)
    assert shape == (4, 2) and area == 1
    np.testing.assert_array_equal(labels, [0, 0, 0, 0, 1, 1, 1, 1])


def test_storage_closes_with_wetting_drying_and_empty_region():
    result = compare_storage([2., 1., 0.], [1., 0., 3.], np.array([0, 0, 2]), 2., 4.)
    assert result['storage_change_m3'] == 2
    assert result['storage_rate_m3s'] == .5
    assert sum(r['cells'] for r in result['regions']) == 3
    assert result['regions'][1]['common_wet_stage_change_m'] is None
    assert result['regions'][0]['common_wet_stage_change_m']['median'] == -1


@pytest.mark.parametrize('after', [[float('nan')], [-1.]])
def test_reject_invalid_depth(after):
    with pytest.raises(ValueError):
        compare_storage([1.], after, np.array([0]), 1., 1.)


@pytest.mark.parametrize('seconds', [0., -1., float('nan')])
def test_reject_invalid_interval(seconds):
    with pytest.raises(ValueError):
        compare_storage([1.], [2.], np.array([0]), 1., seconds)


def test_reject_duplicate_tile_and_invalid_station_order():
    with pytest.raises(ValueError, match='duplicate'):
        partition([grid(), grid()], [[0, 0, 0], [1, 1, 0]], 1.)
    with pytest.raises(ValueError, match='increasing'):
        partition([grid()], [[0, 0, 0], [0, 1, 0]], 1.)


def test_north_coordinate_is_not_reflected():
    labels, _, _ = partition([grid()], [[0, 0, 0], [2, 0, 1]], 1.)
    np.testing.assert_array_equal(labels, [0, 0, 2, 2])


def test_grid_origin_is_first_cell_center_not_lower_corner():
    labels, _, _ = partition([grid()], [[0, 0, 0], [1, .6, 0]], 1.)
    np.testing.assert_array_equal(labels, [0, 1, 0, 1])


@pytest.fixture
def synthetic_cook(tmp_path):
    package = tmp_path/'tile'
    package.mkdir()
    (package/'scenario.json').write_text(json.dumps({'grid': grid()}))
    np.save(package/'bed.npy', np.zeros((2, 2)))
    manifest = dict(dt_seconds=1., packages=['tile'], boundary_probes=[], inputs=[dict(
        name='tile', files={name: digest(package/name) for name in ('scenario.json', 'bed.npy')})])
    original = tmp_path/'manifest.json'
    original.write_text(json.dumps(manifest))
    cook = tmp_path/'cook'
    cook.mkdir()
    (cook/'input_manifest.json').write_bytes(original.read_bytes())
    (cook/'input_manifest_path.txt').write_text(str(original))
    for step, depth, volume in ((0, 1., 4.), (1, .5, 2.)):
        frame = cook/f'frame_{step:06d}'
        frame.mkdir()
        np.save(frame/'h.npy', np.full((2, 2), depth))
        (frame/'complete.json').write_text(json.dumps(dict(
            step=step, snapshot=True, time_seconds=step, volume_m3=volume,
            boundary_volume_m3=volume-4.)))
    route = tmp_path/'route.json'
    route.write_text(json.dumps(dict(horizontal_crs='EPSG:32610', points=[[0, 0, 0], [1, 1, 0]])))
    return cook, route


def test_completed_snapshot_storage_and_exterior_flux_close(synthetic_cook):
    result = run(*synthetic_cook, [0, 1], 1.)
    assert result['cells'] == 4 and result['passed'] and not result['settling_accepted']
    assert result['comparisons'][0]['storage_rate_m3s'] == -2.
    assert result['comparisons'][0]['exterior_closure_error_m3'] == 0.


@pytest.mark.parametrize('corruption', ['bed', 'manifest', 'volume', 'flux', 'incomplete', 'clock'])
def test_reject_corrupt_cook(synthetic_cook, corruption):
    cook, route = synthetic_cook
    if corruption == 'bed':
        np.save(cook.parent/'tile/bed.npy', np.ones((2, 2)))
    elif corruption == 'manifest':
        (cook/'input_manifest.json').write_text('{}')
    else:
        marker = cook/'frame_000001/complete.json'
        record = json.loads(marker.read_text())
        key, value = dict(volume=('volume_m3', 7.), flux=('boundary_volume_m3', 0.),
                          incomplete=('snapshot', False), clock=('time_seconds', 0.))[corruption]
        record[key] = value
        marker.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        run(cook, route, [0, 1], 1.)
