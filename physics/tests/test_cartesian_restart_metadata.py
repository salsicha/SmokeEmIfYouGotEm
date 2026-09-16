import copy

import pytest

from prepare_cartesian_snapshot_restart import make_restart_manifest


def test_checkpoint_replaces_initialization_claims_without_changing_physical_inputs():
    original = dict(initialization_is_fresh_not_restart=True, initial_time_seconds=0.,
        maximum_initial_depth_m=2., maximum_initial_speed_mps=4.,
        initial_velocity_method='cold warm start', packages=['core'], inputs=[{'name': 'core'}],
        restart={'source_time_seconds': 10.}, settled_hydraulics=True, normal_map_integrated=True,
        geometry_manifest_sha256='geometry', terrain_union={'cap': 'source'},
        dt_seconds=.05, boundary_probes=[{'edge': 'west'}], measured_bathymetry=False)
    saved = copy.deepcopy(original)
    result = make_restart_manifest(original, 50.)
    assert original == saved
    assert result['initial_time_seconds'] == 50.
    assert result['initialization_is_fresh_not_restart'] is False
    assert not result['settled_hydraulics'] and not result['normal_map_integrated']
    assert result['packages'] == result['inputs'] == []
    assert all(key not in result for key in ('maximum_initial_depth_m', 'maximum_initial_speed_mps', 'restart'))
    for key in ('geometry_manifest_sha256', 'terrain_union', 'dt_seconds', 'boundary_probes', 'measured_bathymetry'):
        assert result[key] == original[key]
    result['terrain_union']['cap'] = 'changed'
    assert original == saved


@pytest.mark.parametrize('time', [True, -1., float('nan'), float('inf'), '50'])
def test_invalid_checkpoint_clock_is_not_relabelled(time):
    with pytest.raises(ValueError):
        make_restart_manifest({}, time)
