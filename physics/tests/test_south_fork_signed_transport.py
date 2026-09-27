import numpy as np
import pytest
import json
import sys

from analyze_south_fork_discharge_bed_cook import main, signed_transport


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
