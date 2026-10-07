"""Read a reopened continuous candidate's serialized native rapid registration.

Run in an isolated editor with RAFTSIM_CONTINUOUS_MAP_CONTRACT and a fresh
RAFTSIM_CONTINUOUS_MAP_REPORT under tmp. Does not save or modify any asset.
This validates serialization/identity, not terrain, boat motion or performance.
"""
import hashlib
import json
import math
import os
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]


def main():
    contract_path = (ROOT / os.environ['RAFTSIM_CONTINUOUS_MAP_CONTRACT']).resolve()
    report_path = (ROOT / os.environ['RAFTSIM_CONTINUOUS_MAP_REPORT']).resolve()
    contract_path.relative_to(ROOT)
    report_path.relative_to(ROOT / 'tmp')
    assert not report_path.exists(), 'Fresh receipt required'
    contract = json.loads(contract_path.read_text(encoding='utf-8'))
    assert contract['schema'] == 'raftsim.colorado_continuous_map_import.v1'
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name().split('.')[0] == contract['map_package'], 'Wrong opened map'
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    configs = [a for a in actors if isinstance(a, unreal.RaftSimRiverWaterConfig)]
    assert len(configs) == 1, 'Expected one persistent water state holder'
    config = configs[0]
    coordinate = config.get_editor_property('coordinate_map_path')
    assert coordinate == contract['coordinate_map'], 'Changed serialized coordinate path'
    chart_path = (ROOT / coordinate).resolve()
    chart_path.relative_to(ROOT)
    chart_bytes = chart_path.read_bytes()
    assert hashlib.sha256(chart_bytes).hexdigest() == contract['files_sha256'][coordinate]
    fingerprint = config.get_editor_property('registered_rapid_chart_fingerprint')
    assert fingerprint.lower() == hashlib.sha1(chart_bytes.decode('utf-8-sig').encode('utf-8')).hexdigest()
    counts = {'L_Colorado_BadgerCreek': 17, 'L_Colorado_HouseRock': 11, 'L_Hance': 40}
    sources = [s['map'] for s in contract['rapid_profile_sources']]
    assert len(sources) == len(set(sources)), 'Duplicate profile source'
    expected = sum(counts[s] for s in sources)
    features = config.get_editor_property('registered_rapid_features')
    assert len(features) == expected, 'Lost serialized rapid features'
    stations = []
    for feature in features:
        # Native serialized members deliberately are not editor-editable.
        # Export their actual reflected values; do not make gameplay fields
        # public/editable merely to support this read-only verification.
        serialized = feature.export_text()
        assert serialized.startswith('(') and serialized.endswith(')')
        fields = [item.split('=', 1) for item in serialized[1:-1].split(',')]
        assert len(fields) == 6 and all(len(item) == 2 for item in fields)
        values = {key.strip().lower(): float(value) for key, value in fields}
        assert set(values) == {'station', 'lateral', 'angledegrees', 'height', 'length', 'spill'}
        assert all(math.isfinite(v) for v in values.values()), 'Nonfinite saved feature'
        assert 0 < values['height'] <= 1.2 and 2 <= values['length'] <= 7
        assert 0 <= values['spill'] <= 1
        stations.append(values['station'])
    result = dict(schema='raftsim.continuous_saved_registration.v1', passed=True,
                  map_package=contract['map_package'],
                  contract_sha256=hashlib.sha256(contract_path.read_bytes()).hexdigest(),
                  coordinate_sha256=hashlib.sha256(chart_bytes).hexdigest(),
                  chart_fingerprint=fingerprint, feature_count=len(features),
                  source_profiles=sources, feature_station_range_m=[min(stations), max(stations)],
                  saved_packages=False, gameplay_acceptance=False, rendered_fps=None)
    with report_path.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    unreal.log('Continuous saved registration verified: ' + str(report_path))


if __name__ == '__main__':
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
