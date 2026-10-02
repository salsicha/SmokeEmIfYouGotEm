"""Check real all-map receipts; never substitute enablement for visual/FPS proof."""
import argparse
import hashlib
import json
import math
from pathlib import Path

MAPS = {'L_SouthForkAmerican_FullReach', 'L_SouthFork_Troublemaker',
        'L_Hance', 'L_LavaCanyon', 'L_Terminator', 'L_UpperHuacas',
        'L_Zambezi', 'L_ZambeziUpperGorge'}
ROOT = Path(__file__).resolve().parents[2]


def finite(value):
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(finite(item) for item in value.values())
    if isinstance(value, list):
        return all(finite(item) for item in value)
    return True


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--index', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    output = args.report.resolve()
    if not output.is_relative_to(ROOT / 'tmp') or output.exists():
        raise RuntimeError('Fresh repository-local report required')
    index = read(args.index)
    stage = Path(index['packaged_root'])
    binary = stage / 'SmokeEmIfYouGotEm/Binaries/Win64/SmokeEmIfYouGotEm.exe'
    with binary.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    rows = []
    for item in index['maps']:
        feature, foam = read(item['feature_receipt']), read(item['foam_transport_receipt'])
        launch = read(ROOT / 'tmp' / item['label'] / 'launch.json')
        assert item['map'] in MAPS and feature['map'] == item['map']
        assert launch['exit_code'] == 0 and launch['binary_sha256'] == digest
        assert feature['feature_kinematics_enabled'] and feature['wet_probes'] > 0
        assert feature['dry_became_wet'] == 0 and feature['maximum_shared_surface_error_mps'] <= 1e-5
        assert len(feature['actual_boat_motion']) > 1 and finite(feature) and finite(foam)
        cartesian = 'maximum_source_transport_error_mps' in foam
        error = foam['maximum_source_transport_error_mps' if cartesian else 'maximum_submitted_transport_error_mps']
        assert error <= 1e-5
        if cartesian:
            assert foam['feature_kinematics_enabled'] and foam['audited_source_anchors'] > 0
        else:
            assert foam['feature_current_enabled'] and foam['shape_valid'] and foam['non_finite_vertices'] == 0
            assert foam['moving_transport_vertices'] > 0
        if 'maximum_bulk_channel_error_mps' in foam:
            assert foam['maximum_bulk_channel_error_mps'] <= 1e-5
        if 'material_clock_error_seconds' in foam:
            assert foam['material_clock_present'] and foam['material_clock_error_seconds'] <= 1e-5
        rows.append(dict(map=item['map'], native_exit_code=0,
                         feature_current_enabled=True, finite_motion=True,
                         shared_surface_error_mps=feature['maximum_shared_surface_error_mps'],
                         foam_transport_error_mps=error, changed_probes=feature['changed_probes'],
                         physical_eddy_owners=feature['active_physical_eddy_owners']))
    found = {row['map'] for row in rows}
    assert len(found) == len(rows), 'Duplicate map receipt'
    report = dict(schema='raftsim.packaged_shared_water_rollout_audit.v1',
                  binary_sha256=digest, maps=rows, maps_checked=len(rows),
                  all_eight_maps_checked=found == MAPS, missing_maps=sorted(MAPS-found),
                  retained_receipts_passed=True,
                  scope='Actual default shared-current/foam wiring and finite production-raft timer states. Not every obstacle trajectory, dense contact, pixel, normal-menu or 20 FPS acceptance.',
                  visual_accepted=False, fps_accepted=False)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
