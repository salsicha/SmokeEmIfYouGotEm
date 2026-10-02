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


def feature_activation(feature):
    """Separate exercised native feature topology from quiet-window parity.

    Observed current branches are not a boat-exit or whole-river proof.
    Missing history is explicitly unavailable, never a passing activation.
    """
    history = feature.get('feature_activation_history')
    if history is None:
        return dict(available=False, hole_activation_observed=False,
                    eddy_activation_observed=False)
    if not isinstance(history, list) or not history or not finite(history):
        raise ValueError('Finite nonempty actual feature history required')
    times = [row['world_seconds'] for row in history]
    if any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError('Feature observation times must increase')
    hole_probes = returns = legs = circulations = eddy_topologies = 0
    max_holes = max_eddies = 0
    for row in history:
        for key in ('published_hole_owners', 'physical_eddy_owners'):
            if not isinstance(row[key], int) or row[key] < 0:
                raise ValueError('Nonnegative integer native owner counts required')
        max_holes = max(max_holes, row['published_hole_owners'])
        max_eddies = max(max_eddies, row['physical_eddy_owners'])
        holes = row['actual_wet_hole_depth_probes']
        eddies = row['actual_wet_eddy_owner_probes']
        if len(holes) > row['published_hole_owners'] or len(eddies) > row['physical_eddy_owners']:
            raise ValueError('Probe observations exceed actual owner counts')
        for hole in holes:
            if hole['depth_m'] <= .05 or hole['intensity'] <= 0 or hole['spilling_fraction'] <= 0:
                raise ValueError('Hole probe has no actual wet active owner')
            delta = hole['submerged_along_mps'] - hole['surface_along_mps']
            if abs(delta-hole['submerged_minus_surface_along_mps']) > 1e-5:
                raise ValueError('Hole depth-leg receipt is inconsistent')
            hole_probes += 1
            returns += hole['surface_along_mps'] < -.1
            legs += delta > 1e-5
            circulations += (hole['surface_along_mps'] < -.1 and
                            hole['submerged_along_mps'] > .1 and delta > 1e-5)
        for eddy in eddies:
            if not eddy['physical_source']:
                raise ValueError('Eddy topology requires an actual physical source')
            probes = eddy['actual_wet_hull_current_probes']
            by_position = {(p['local_x_radius'], p['local_y_radius']): p for p in probes}
            if len(by_position) != len(probes):
                raise ValueError('Duplicate eddy branch probe')
            back = by_position.get((4., .1))
            head = by_position.get((1.75, .6))
            exit_ = by_position.get((2.25, 1.25))
            eddy_topologies += bool(back and head and exit_ and
                back['actual_along_mps'] < -.1 and
                head['actual_across_mps'] > .05 and
                exit_['actual_along_mps'] > .1)
    return dict(available=True, observations=len(history),
                maximum_observation_gap_seconds=max((b-a for a, b in zip(times, times[1:])), default=0),
                maximum_published_hole_owners=max_holes,
                maximum_physical_eddy_owners=max_eddies,
                actual_wet_hole_depth_probes=hole_probes,
                hole_surface_return_probes=returns,
                hole_submerged_leg_probes=legs,
                complete_hole_circulation_probes=circulations,
                hole_activation_observed=circulations > 0,
                complete_eddy_current_topology_observations=eddy_topologies,
                eddy_activation_observed=eddy_topologies > 0,
                scope='Actual native wet owner/current samples across loaded windows. '
                      'Not complete river geometry coverage, boat washout, pixel or FPS acceptance.')


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--index', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--require-feature-coverage', action='store_true')
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
        activation = feature_activation(feature)
        if args.require_feature_coverage and not activation['available']:
            raise ValueError('Native time-resolved feature coverage missing')
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
                         physical_eddy_owners=feature['active_physical_eddy_owners'],
                         feature_activation=activation))
    found = {row['map'] for row in rows}
    assert len(found) == len(rows), 'Duplicate map receipt'
    report = dict(schema='raftsim.packaged_shared_water_rollout_audit.v1',
                  binary_sha256=digest, maps=rows, maps_checked=len(rows),
                  all_eight_maps_checked=found == MAPS, missing_maps=sorted(MAPS-found),
                  retained_receipts_passed=True,
                  all_maps_have_time_resolved_feature_coverage=all(row['feature_activation']['available'] for row in rows),
                  maps_without_observed_hole_activation=[row['map'] for row in rows if not row['feature_activation']['hole_activation_observed']],
                  maps_without_observed_eddy_activation=[row['map'] for row in rows if not row['feature_activation']['eddy_activation_observed']],
                  scope='Actual default shared-current/foam wiring and finite production-raft timer states. Not every obstacle trajectory, dense contact, pixel, normal-menu or 20 FPS acceptance.',
                  visual_accepted=False, fps_accepted=False)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
