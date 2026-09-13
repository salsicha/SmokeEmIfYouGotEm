"""Use the current-flow planned line, retaining the superseded route evidence."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    folder = ROOT/'docs/reconstruction-review-2026-09-07'
    source = folder/'guided-route-inferred-flanks-20260912.json'
    target = folder/'guided-route-playable.json'
    backup = ROOT/'tmp/troublemaker-playable-before-inferred-flanks-20260912/guided-route-before-current-flow-replan.json'
    assert not backup.exists()
    new, old = json.loads(source.read_text()), json.loads(target.read_text())
    fields = ROOT/old['cooked_fields_dir']
    manifest = json.loads((fields/'manifest.json').read_text())
    assert new['source_geometry_sha256'] == old['source_geometry_sha256'] == manifest['review']['source_geometry_sha256']
    assert new['depth_sha256'] == old['depth_sha256'] == manifest['bands'][0]['arrays']['h']['sha256']
    for array in manifest['bands'][0]['arrays'].values():
        assert sha(fields/array['file']) == array['sha256']
    for key in ('required_depth_m','planning_footprint_length_m','planning_footprint_width_m','paddling_speed_limit_mps','method'):
        assert new[key] == old[key]
    assert new['station_lateral_m'][0] == old['station_lateral_m'][0]
    assert new['station_lateral_m'][-1] == old['station_lateral_m'][-1]
    assert new['minimum_route_footprint_depth_m'] >= new['required_depth_m']
    shutil.copy2(target, backup)
    new.update(cooked_fields_dir=old['cooked_fields_dir'], parent_route_sha256=sha(backup),
        source_route_sha256=sha(source), guidance_points_unchanged=False,
        route_recomputed_for_current_flow=True, revised_geometry_traversal_validated=False,
        planning_criteria_unchanged=True, steering_strength_and_route_gate_unchanged=True)
    target.write_text(json.dumps(new, indent=2)+'\n')
    differences = [(a,b) for a,b in zip(old['station_lateral_m'],new['station_lateral_m']) if a != b]
    print(json.dumps(dict(changed_points=len(differences), first_changes=differences[:8],
        previous_route_sha256=sha(backup), new_route_sha256=sha(target)), indent=2))


def restore_previous_after_failed_traversal():
    """Retain the failed replan and restore only this script's earlier line."""
    target = ROOT/'docs/reconstruction-review-2026-09-07/guided-route-playable.json'
    folder = ROOT/'tmp/troublemaker-playable-before-inferred-flanks-20260912'
    previous = folder/'guided-route-before-current-flow-replan.json'
    failed = folder/'guided-route-failed-current-flow-replan.json'
    assert sha(target) == '0a6ecd118d6c7aa4a3c7e26f5585a5afccc2a98d35342bfaa45d9656867f7d3f'
    assert sha(previous) == '2f25fc896776fb323abad3bcba2a3f4b42a145a227b4be7e55c8d8a5cae62e78'
    assert not failed.exists()
    report = json.loads((ROOT/'unreal/Saved/RaftSimValidation/troublemaker-inferred-flanks-replanned-traversal-20260912/index.json').read_text(encoding='utf-8-sig'))
    assert any(test['state'] == 'Fail' for test in report['tests'])
    shutil.copy2(target, failed)
    shutil.copy2(previous, target)
    assert sha(target) == sha(previous)
    print('Restored prior route only; failed replan retained at', failed)


if __name__ == '__main__':
    main()
