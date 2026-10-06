"""Retain guided review failures alongside bounded passing evidence."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / 'docs/reconstruction-review-2026-09-07'
RUNS = (
    ('initial', 'SurveyGuidedTraversalInitial', 'engine-guided-traversal-initial'),
    ('flow_compensated_early_criterion', 'SurveyGuidedTraversalFlowAware', 'engine-guided-traversal-flow-aware'),
    ('instrumented_strict_criterion', 'SurveyGuidedTraversalInstrumented', 'engine-guided-traversal-instrumented'),
    ('crew_pivot', 'SurveyGuidedTraversalCrewPivot', 'engine-guided-traversal-crew-pivot'),
    ('nearest_track_feedback', 'SurveyGuidedTraversalTrackFeedback', 'engine-guided-traversal-track-feedback'),
    ('two_second_pursuit', 'SurveyGuidedTraversalTwoSecondPursuit', 'engine-guided-traversal-two-second-pursuit'),
    ('shared_breaking_initial', 'SurveyGuidedTraversalSharedBreaking', 'engine-guided-traversal-shared-breaking'),
    ('shared_breaking_final', 'SurveySharedBreakingFinalTests', 'engine-shared-breaking-final'),
    ('shared_breaking_fresh_map', 'SurveySharedBreakingFreshMapTests', 'engine-shared-breaking-fresh-map'),
    ('single_foam_carrier', 'SurveyOneFoamCarrierTests', 'engine-one-foam-carrier'),
    ('triangle_fields', 'SurveyTriangleFieldTests', 'engine-triangle-fields'),
    ('depth_limited_fields', 'SurveyDepthLimitedTests', 'engine-depth-limited'),
    ('depth_limited_quoted_route', 'SurveyDepthLimitedGuidedQuoted', 'engine-depth-limited-guided'),
    ('coordinated_steering', 'SurveyCoordinatedSteering', 'engine-coordinated-steering'),
    ('attainable_steering', 'SurveyAttainableSteering', 'engine-attainable-steering'),
    ('attainable_steering_combined', 'SurveyAttainableSteeringCombined', 'engine-attainable-steering-combined'),
    ('muscl_scratch_reuse', 'SurveyMusclScratchTests', 'engine-muscl-scratch'),
    ('station_captures_baseline', 'SurveyStationWaterBaseline', 'engine-station-water-baseline'),
    ('station_captures_normal_isolation', 'SurveyStationWaterNormalIsolation', 'engine-station-water-normal-isolation'),
    ('runtime_texture_bindings', 'SurveyWaterTextureBindings', 'engine-water-texture-bindings'),
    ('current_normal_v1', 'SurveyStationWaterCurrentNormal', 'engine-station-water-current-normal'),
    ('current_normal_v2', 'SurveyStationWaterCurrentNormalV2', 'engine-station-water-current-normal-v2'),
    ('native_primitives_stale_default', 'NativePrimitivesTests', 'engine-native-primitives'),
    ('native_primitives_matching_default', 'GuidedDefaultRouteTests', 'engine-guided-default-route'),
    ('coordinated_attainable_default', 'GuidedCoordinatedDefaultTests', 'engine-guided-coordinated-default'),
    ('registered_rock_guided', 'RegisteredRockGuidedTests', 'engine-registered-rock-guided',
     'RaftSim.Survey.SouthForkRegisteredRockGuidedTraversal'),
)


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def meets_bounded_criteria(report):
    """Do not inherit a pass from the early test that omitted route error."""
    return bool(report['finite'] and report['reached_outlet'] and
        report['missing_ground_queries'] == 0 and report['duration_s'] <= 120.2 and
        report['minimum_tube_clearance_cm'] >= -.1 and
        report['maximum_route_error_m'] <= 5.)


def main():
    runs = []
    for entry in RUNS:
        name, log_name, directory = entry[:3]
        test_path = entry[3] if len(entry) == 4 else 'RaftSim.Survey.SouthForkGuidedTraversal'
        log_path = ROOT / 'unreal/Saved/Logs' / (log_name + '.log')
        log = log_path.read_text(encoding='utf-8-sig', errors='replace')
        match = re.search(r'SouthForkGuidedTraversal_\d{8}_\d{6}\.json', log)
        index = read(REVIEW / directory / 'index.json')
        test = next(t for t in index['tests'] if t['fullTestPath'] == test_path)
        if not match:
            if test['state'] != 'Fail':
                raise ValueError(f'Missing completed report in {log_path}')
            runs.append(dict(name=name, report=None, engine_test_path=test_path,
                engine_report=f'docs/reconstruction-review-2026-09-07/{directory}/index.json',
                engine_state=test['state'],meets_current_bounded_criteria=False,
                metrics=None,scope='Engine failure before a completed traversal report; not a physical traversal pass'))
            continue
        path = ROOT / 'unreal/Saved/Automation' / match[0]
        report = read(path)
        runs.append(dict(name=name, report=path.relative_to(ROOT).as_posix(), engine_test_path=test_path,
            engine_report=f'docs/reconstruction-review-2026-09-07/{directory}/index.json',
            engine_state=test['state'], meets_current_bounded_criteria=meets_bounded_criteria(report),
            metrics={k: v for k, v in report.items() if k != 'samples'}))
    result = dict(schema='raftsim.survey.guided_review.v1', runs=runs,
        baseline_has_one_bounded_pass=any(r['name'] == 'two_second_pursuit' and
            r['meets_current_bounded_criteria'] and r['engine_state'] == 'Success' for r in runs),
        repeated_robust_navigation_accepted=False, real_river_navigation_line=False,
        production_accepted=False, visual_accepted=False,
        note='Normal crew/guide inputs only. Six tube probes are sampled, not a continuous swept-hull proof. '
             'The early outlet-only success is retrospectively rejected by the route-error criterion. '
             'No test result verifies rapid identity, inferred bathymetry, or photorealism.')
    (REVIEW / 'guided-review.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    for run in runs:
        print(run['name'], run['engine_state'], run['meets_current_bounded_criteria'])


if __name__ == '__main__':
    main()
