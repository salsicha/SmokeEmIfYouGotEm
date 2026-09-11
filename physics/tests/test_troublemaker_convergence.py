from copy import deepcopy
from pathlib import Path
import runpy


def helper():
    return runpy.run_path(str(Path(__file__).resolve().parents[1] /
        'scripts/assess_troublemaker_convergence.py'))['assess']


def fixture():
    return {'experimental_prescribed_discharge_m3s': 45., 'snapshots': [
        {'nominal_cumulative_seconds': t, 'volume_m3': 20000.,
         'sections': [{'station_m': x, 'discharge_m3s': 45.} for x in (8348., 8362., 8400.)],
         'regions': [{'station_range_m': [8360, 8380], 'stage_p10_p50_p90_m': [-.8, -.6, -.4]}]}
        for t in (0., 9.6, 19.2, 28.8)]}


def test_mean_flow_screen_does_not_accept_underfeeding_storage_or_stage_drift():
    assess = helper()
    stable = fixture()
    result = assess(stable)
    assert result['mean_flow_screen_passed']
    assert result['photorealism_accepted'] is False and result['production_promoted'] is False
    underfed = deepcopy(stable)
    for row in underfed['snapshots']:
        for section in row['sections']:
            section['discharge_m3s'] = 32.
    storage = deepcopy(stable)
    for i, row in enumerate(storage['snapshots']):
        row['volume_m3'] += i*50.
    stage = deepcopy(stable)
    stage['snapshots'][-1]['regions'][0]['stage_p10_p50_p90_m'][1] += .04
    assert not assess(underfed)['mean_flow_screen_passed']
    assert not assess(storage)['mean_flow_screen_passed']
    assert not assess(stage)['mean_flow_screen_passed']


def test_invalid_convergence_inputs_cannot_pass():
    assess = helper()
    invalid = []
    for key, value in [('experimental_prescribed_discharge_m3s', float('nan')),
                       ('experimental_prescribed_discharge_m3s', 0.)]:
        data = fixture(); data[key] = value; invalid.append(data)
    data = fixture(); data['snapshots'][1]['nominal_cumulative_seconds'] = 0.; invalid.append(data)
    data = fixture(); data['snapshots'][0]['volume_m3'] = float('nan'); invalid.append(data)
    data = fixture(); data['snapshots'].pop(); invalid.append(data)
    data = fixture(); data['snapshots'][0]['sections'][0]['station_m'] += 1.; invalid.append(data)
    data = fixture(); data['snapshots'][0]['regions'][0]['stage_p10_p50_p90_m'] = []; invalid.append(data)
    for data in invalid:
        try:
            assess(data)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid convergence evidence accepted')
