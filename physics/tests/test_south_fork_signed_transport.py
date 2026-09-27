import numpy as np
import pytest
import json
import sys
import copy
import shutil

from analyze_south_fork_discharge_bed_cook import main, signed_transport, station_map_source, file_sha


EAST = [[0, 0, 0, 0, 1], [10, 10, 0, 0, 1]]


def test_forward_reverse_and_cross_flow_are_not_all_downstream():
    result = signed_transport([1, 2, 3], [2, 2, 2], [3, -3, 0], [0, 0, 3], EAST)
    np.testing.assert_array_equal(result, [6, -6, 0])
    assert result.sum() == 0  # speed-magnitude transport would incorrectly total18


def test_native_north_not_unreal_reflected_y():
    north = [[0, 0, 0, -1, 0], [10, 0, 10, -1, 0]]
    np.testing.assert_array_equal(signed_transport([3, 4], [2, 2], [0, 0], [3, -3], north), [6, -6])


def test_endpoint_context_and_dry_cell():
    np.testing.assert_array_equal(signed_transport([-1, 20, 5], [2, 2, 0], [3, 3, 7], [0, 0, 8], EAST), [6, 6, 0])


def test_interpolated_tangent_is_unit_length():
    curve = [[0, 0, 0, 0, 1], [10, 5, 5, -1, 0]]
    np.testing.assert_allclose(signed_transport([5], [2], [1], [1], curve), [2*np.sqrt(2)])


@pytest.mark.parametrize('route', [EAST[:1], [EAST[0], EAST[0]], [[0, 0, 0, 0, 2], EAST[1]],
                                  [[0, 0, 0, 0, 1], [10, 0, 0, 0, -1]]])
def test_invalid_or_undefined_route_rejected(route):
    with pytest.raises(ValueError):
        signed_transport([5], [1], [1], [0], route)


@pytest.mark.parametrize('depth,u,v', [([-1], [1], [0]), ([1], [float('nan')], [0]), ([1], [1, 2], [0])])
def test_bad_samples_rejected(depth, u, v):
    with pytest.raises(ValueError):
        signed_transport([5], depth, u, v, EAST)


@pytest.fixture
def counterflow_snapshot(tmp_path, monkeypatch):
    prep = tmp_path/'prep'
    package = prep/'core_0000'
    package.mkdir(parents=True)
    cook = tmp_path/'cook'
    frame = cook/'frame_000001'
    frame.mkdir(parents=True)
    (prep/'manifest.json').write_text(json.dumps(dict(packages=['core_0000'], section=dict(name='fixture', core_range_m=[0, 5]))))
    (package/'scenario.json').write_text(json.dumps(dict(grid=dict(nx=80, ny=80, dx=1., dy=1.))))
    bed = np.zeros((80, 80))
    np.save(package/'bed.npy', bed)
    mask = np.zeros((1, 80, 80), dtype=bool)
    mask[0, 0, :6] = True
    np.savez(prep/'station_map.npz', water=mask, surface=np.ones_like(mask, dtype=float)*2,
             station=np.ones_like(mask, dtype=float)*2.5)
    h = bed.copy(); h[0, :6] = 1
    u = bed.copy(); u[0, :6] = [3, -3, 0, 3, -3, 0]
    v = bed.copy(); v[0, :6] = [0, 0, 3, 0, 0, 3]
    for name, values in dict(h=h, u=u, v=v).items():
        np.save(frame/f'{name}.npy', values)
    (frame/'complete.json').write_text(json.dumps(dict(step=1, snapshot=True, exterior_fluxes=[0],
        time_seconds=1, volume_m3=6, maximum_depth_m=1, maximum_speed_mps=3)))
    route = tmp_path/'route.json'
    route.write_text(json.dumps(dict(horizontal_crs='EPSG:32610', points=EAST)))
    output = tmp_path/'analysis'
    command = ['analysis', str(output), '--cook', str(prep), str(cook), '1', '--route', str(route), '--discharge', '3.6']
    monkeypatch.setattr(sys, 'argv', command)
    return output, command, frame, package


def test_full_analysis_reports_signed_and_legacy_magnitude_without_acceptance(counterflow_snapshot):
    output, _, _, _ = counterflow_snapshot
    main()
    report = json.loads((output/'report.json').read_text())
    assert report['schema'].endswith('.v2')
    assert report['settling_accepted'] is False and report['normal_map_integrated'] is False
    assert report['bins']['signed_transport_proxy_m3s'][0] == 0
    assert report['bins']['unsigned_transport_proxy_m3s'][0] == 3.6
    with np.load(output/'bias.npz') as bias:
        assert bias['raw_bias'][0] == -1
        assert bias['used'][0] and not bias['settling_accepted']


@pytest.mark.parametrize('flag', ['--transport-screen-only', '--settled-only'])
def test_counterflow_cannot_qualify_for_bias_by_speed_magnitude(counterflow_snapshot, flag):
    output, command, _, _ = counterflow_snapshot
    command.append(flag)
    with pytest.raises(ValueError, match='No eligible bias'):
        main()
    assert not output.exists()


@pytest.mark.parametrize('corruption', ['incomplete', 'grid', 'discharge'])
def test_invalid_snapshot_grid_or_target_rejected(counterflow_snapshot, corruption):
    output, command, frame, package = counterflow_snapshot
    if corruption == 'discharge':
        command[-1] = 'nan'
    elif corruption == 'grid':
        (package/'scenario.json').write_text(json.dumps(dict(grid=dict(nx=80, ny=80, dx=2., dy=1.))))
    else:
        marker = frame/'complete.json'
        record = json.loads(marker.read_text()); record['snapshot'] = False
        marker.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        main()
    assert not output.exists()


def test_fit_preserves_numerics_but_labels_simulated_not_measured_bathymetry(tmp_path, monkeypatch):
    from fit_south_fork_discharge_bed_correction import main as fit
    analysis = tmp_path/'analysis'; analysis.mkdir()
    bed = tmp_path/'bed'; bed.mkdir()
    np.savez(analysis/'bias.npz', station=[2.5, 7.5], raw_bias=[.1, 0.], used=[True, True])
    (bed/'design.json').write_text(json.dumps(dict(station_center_m=[2.5, 7.5],
        centerline_depth_m=[1., 2.], pool_weight=[0., 1.], normal_depth_m=[1., 2.])))
    output = tmp_path/'fit.npz'
    monkeypatch.setattr(sys, 'argv', ['fit', str(output), '--pair', str(analysis), str(bed), '--design-bed', str(bed)])
    fit()
    kernel = np.exp(-.5*(np.arange(-9, 10)/3.)**2); kernel /= kernel.sum()
    with np.load(output, allow_pickle=False) as result:
        np.testing.assert_array_equal(result['bias'], np.convolve(np.pad([.1, 0.], 9, mode='edge'), kernel, mode='valid'))
        np.testing.assert_array_equal(result['measured'], result['simulated_samples'])
        assert result['fractional_factor'] == .1
        assert not result['settling_accepted']
        assert 'not measured bathymetry' in str(result['provenance'])


@pytest.fixture
def restart_snapshot(counterflow_snapshot):
    from prepare_cartesian_snapshot_restart import make_restart_manifest
    output, command, frame, package = counterflow_snapshot
    original = package.parent
    scenario_path = package/'scenario.json'
    scenario = json.loads(scenario_path.read_text())
    scenario.update(metadata=dict(scenario_id=package.name, generator='fixture',
                                 description='fixture', provenance={}),
                    roughness=.035, boundaries=[])
    scenario_path.write_text(json.dumps(scenario))
    for name in ('features.json', 'probes.json'):
        (package/name).write_text('{}')
    manifest = json.loads((original/'manifest.json').read_text())
    manifest.update(dt_seconds=.05, geometry_manifest='same-geometry.json',
                    geometry_manifest_sha256='same-geometry-hash',
                    inputs=[dict(name=package.name, files={name: file_sha(package/name)
                        for name in ('scenario.json', 'bed.npy', 'features.json', 'probes.json')})])
    (original/'manifest.json').write_text(json.dumps(manifest))
    restart = original.parent/'restart'
    shutil.copytree(original, restart, ignore=shutil.ignore_patterns('station_map.npz'))
    current = make_restart_manifest(manifest, 1.)
    current.update(packages=copy.deepcopy(manifest['packages']), inputs=copy.deepcopy(manifest['inputs']),
                   restart=dict(source_manifest=str(original/'manifest.json'),
                                source_manifest_sha256=file_sha(original/'manifest.json'),
                                added_context_count=0, added_initial_water_volume_m3=0))
    (restart/'manifest.json').write_text(json.dumps(current))
    command[3] = str(restart)
    return output, command, original, restart, current


def test_analysis_of_restart_uses_identical_map_and_state_statistics(restart_snapshot):
    output, command, original, restart, current = restart_snapshot
    command[3] = str(original)
    main()
    reference = json.loads((output/'report.json').read_text())
    command[3] = str(restart)
    command[1] = str(output.parent/'restart-analysis')
    main()
    result = json.loads((output.parent/'restart-analysis/report.json').read_text())
    assert result['summary'] == reference['summary']
    assert result['bins'] == reference['bins']
    assert result['mass_balance'] == reference['mass_balance']
    assert result['station_map_sources'][0] == dict(prep=str(restart),
        path=str(original/'station_map.npz'), sha256=file_sha(original/'station_map.npz'),
        inherited_from_restart=True)
    assert not result['settling_accepted'] and not result['normal_map_integrated']
    assert not (restart/'station_map.npz').exists()  # read-only inheritance


def test_station_map_can_cross_multiple_exact_restarts(restart_snapshot):
    _, _, original, restart, current = restart_snapshot
    next_dir = restart.parent/'next'
    shutil.copytree(restart, next_dir)
    next_manifest = copy.deepcopy(current)
    next_manifest['initial_time_seconds'] = 2.
    next_manifest['restart'].update(source_manifest=str(restart/'manifest.json'),
                                   source_manifest_sha256=file_sha(restart/'manifest.json'))
    assert station_map_source(next_dir, next_manifest) == original/'station_map.npz'


@pytest.mark.parametrize('change', ['hash', 'geometry', 'packages', 'context', 'volume',
                                  'clock_claim', 'new_physics', 'bed', 'features', 'probes',
                                  'grid', 'roughness', 'boundary', 'tampered_file'])
def test_restart_map_rejects_mismatched_ancestry(restart_snapshot, change):
    _, _, _, restart, current = restart_snapshot
    name = current['packages'][0]
    if change == 'hash':
        current['restart']['source_manifest_sha256'] = 'wrong'
    elif change == 'geometry':
        current['geometry_manifest_sha256'] = 'different'
    elif change == 'packages':
        current['packages'] = ['different']
    elif change == 'context':
        current['restart']['added_context_count'] = 1
    elif change == 'volume':
        current['restart']['added_initial_water_volume_m3'] = 1
    elif change == 'clock_claim':
        current['initialization_is_fresh_not_restart'] = True
    elif change == 'new_physics':
        current['new_solver_option'] = True
    else:
        filename = {'bed': 'bed.npy', 'features': 'features.json', 'probes': 'probes.json'}.get(change, 'scenario.json')
        path = restart/name/filename
        if change == 'bed':
            np.save(path, np.ones((80, 80)))
        elif change in ('features', 'probes'):
            path.write_text('{"changed":true}')
        else:
            scenario = json.loads(path.read_text())
            if change in ('grid', 'tampered_file'):
                scenario['grid']['dx'] = 2.
            elif change == 'roughness':
                scenario['roughness'] = .02
            else:
                scenario['boundaries'] = [dict(kind='outflow')]
            path.write_text(json.dumps(scenario))
        if change != 'tampered_file':
            current['inputs'][0]['files'][filename] = file_sha(path)
    with pytest.raises(ValueError):
        station_map_source(restart, current)


def test_missing_station_map_without_ancestry_is_rejected(tmp_path):
    with pytest.raises(ValueError, match='No station map'):
        station_map_source(tmp_path, {})


@pytest.mark.parametrize('bad_map', ['shape', 'nonfinite', 'numeric_mask'])
def test_analysis_rejects_invalid_station_map(counterflow_snapshot, bad_map):
    output, _, _, package = counterflow_snapshot
    path = package.parent/'station_map.npz'
    with np.load(path) as saved:
        fields = {key: saved[key] for key in saved.files}
    if bad_map == 'shape':
        fields['station'] = fields['station'][:, :-1]
    elif bad_map == 'nonfinite':
        fields['surface'][0, 0, 0] = np.nan
    else:
        fields['water'] = fields['water'].astype(float)
    np.savez(path, **fields)
    with pytest.raises(ValueError, match='Station map must match'):
        main()
    assert not output.exists()


def test_dry_unassigned_station_sentinel_is_not_a_water_sample(counterflow_snapshot):
    output, _, _, package = counterflow_snapshot
    path = package.parent/'station_map.npz'
    with np.load(path) as saved:
        fields = {key: saved[key] for key in saved.files}
    fields['station'][~fields['water']] = np.nan
    np.savez(path, **fields)
    main()
    report = json.loads((output/'report.json').read_text())
    assert report['summary']['cells'] == 6
    assert report['summary']['cook_wet_fraction_of_captured_mask'] == 1.
    assert report['bins']['signed_transport_proxy_m3s'][0] == 0
