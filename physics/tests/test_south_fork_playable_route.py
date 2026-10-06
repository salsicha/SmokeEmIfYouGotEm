"""Full-river geography must not rescale/straighten the captured rapid."""
import importlib.util
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('playable_route', ROOT/'physics/scripts/build_south_fork_playable_route.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_densification_preserves_corners_length_and_runtime_edge_guard():
    xy = np.array([[100., 200.], [130., 200.], [130., 212.], [125., 217.]])
    points = MODULE.coordinate_points(xy)
    assert np.all(np.diff(points[:, 0]) > 0)
    assert abs(points[-1, 0] - (42 + np.sqrt(50))) < 1e-10
    assert np.allclose(np.linalg.norm(points[:, 3:5], axis=1), 1)
    for vertex in xy:
        assert np.min(np.linalg.norm(points[:, 1:3] - (vertex-xy[0]), axis=1)) < 1e-10
    for sign in (-1, 1):
        assert np.max(np.linalg.norm(np.diff(points[:, 1:3] + sign*256*points[:, 3:5], axis=0), axis=1)) < 16


def test_rigid_embedding_preserves_metric_geometry_and_datum():
    rapid_origin, river_origin = np.array([683805., 4296673.]), np.array([689269., 4293133.])
    offset = MODULE.engine_translation_cm(rapid_origin, river_origin, 220., 120.)
    local = np.array([[1., 2., 3.], [-8., 25., 30.], [20., -13., 8.]])
    world_rapid = local * [100., -100., 100.]
    world_river = world_rapid + offset
    recovered = world_river/[100., -100., 100.] + np.r_[river_origin, 120.]
    assert np.allclose(recovered, local + np.r_[rapid_origin, 220.], atol=1e-8, rtol=0)
    assert np.allclose(np.linalg.norm(np.diff(world_river, axis=0), axis=1),
                       100*np.linalg.norm(np.diff(local, axis=0), axis=1))


def test_river_chainage_is_not_local_rigid_station():
    points = MODULE.coordinate_points(np.array([[0., 0.], [30., 0.], [30., 20.]]))
    station, distance = MODULE.nearest_station(points, np.array([33., 10.]))
    assert abs(station-40.) < 1e-10 and abs(distance-3.) < 1e-10


def test_invalid_axes_are_rejected():
    for xy in ([[0., 0.]], [[0., 0.], [0., 0.]], [[0., 0.], [1., 0.], [0., 0.]], [[0., 0.], [float('nan'), 1.]]):
        try:
            MODULE.coordinate_points(xy)
        except ValueError:
            continue
        raise AssertionError('Invalid axis accepted')


def test_generated_route_profile_and_placement_share_one_frame():
    import json
    base = MODULE.OUT
    report = json.loads((base/'integration.json').read_text())
    coordinates = json.loads((base/'coordinate_map.json').read_text())
    placement = json.loads((base/'troublemaker_placement.json').read_text())
    points = np.asarray(coordinates['points'])
    assert report['coordinate_map.json']['sha256'] == MODULE.sha(base/'coordinate_map.json')
    assert report['troublemaker_placement.json']['sha256'] == MODULE.sha(base/'troublemaker_placement.json')
    assert report['route_source_profile']['sha256'] == MODULE.sha(base/'route_source_profile.npz')
    with np.load(base/'route_source_profile.npz') as profile:
        assert np.array_equal(profile['station_m'], points[:, 0])
        assert np.allclose(profile['utm_easting_m'], points[:, 1]+coordinates['origin_utm_m'][0])
        assert np.allclose(profile['utm_northing_m'], points[:, 2]+coordinates['origin_utm_m'][1])
        assert profile['within_survey_water'].all()
    rapid = json.loads((ROOT/placement['source_coordinate_map']).read_text())
    expected = MODULE.engine_translation_cm(rapid['origin_utm_m'], coordinates['origin_utm_m'],
        rapid['vertical_datum_m'], coordinates['vertical_datum_m'])
    assert np.array_equal(expected, placement['translation_from_existing_rapid_world_cm'])
    assert placement['scale'] == [1, 1, 1] and placement['rotation_degrees'] == [0, 0, 0]
    assert placement['parent_scenario_id'] == 'south_fork_full_descent'
    assert not placement['separate_menu_scenario']
    assert not report['normal_map_integrated'] and not report['full_reconstruction_accepted']
    embedded = json.loads((base/'troublemaker_hydraulic_coordinate_map.json').read_text())
    original_points, embedded_points = np.asarray(rapid['points']), np.asarray(embedded['points'])
    assert np.array_equal(original_points[:, 0], embedded_points[:, 0])
    assert np.array_equal(original_points[:, 3:5], embedded_points[:, 3:5])
    assert np.allclose(embedded_points[:, 1:3] - original_points[:, 1:3],
                       np.asarray(rapid['origin_utm_m']) - coordinates['origin_utm_m'], rtol=0, atol=1e-9)
