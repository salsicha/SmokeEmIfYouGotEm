"""Summarize existing evidence without promoting candidates to production."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09'
REVIEW=ROOT/'docs/reconstruction-review-2026-09-06'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else None


def main():
    manifest=read(BASE/'reconstruction_manifest.json')
    atlas=read(BASE/'sources/rapid_atlas/index.json')
    windows=read(BASE/'rapid_windows/index.json')
    full=read(BASE/'full_reach/manifest.json')
    progress={'scope':'South Fork only; Colorado, Pacuare and Futaleufu remain queued',
        'production_scene_replaced':False,'all_rapids_accepted':False,'photorealism_accepted':False,
        'captured_sources':{'dem_tiles':full['source_tile_count'],
            'full_reach_valid_fraction':full['corridor_valid_fraction'],
            'dated_rapid_reference_count':len(atlas['entries']),
            'half_metre_rapid_search_windows':len(windows['windows']),
            'rapid_search_windows_with_full_coverage':sum(w['valid_fraction']==1 for w in windows['windows']),
            'verified_rapid_count':sum(w['rapid_identity_verified'] for w in windows['windows'])},
        'aligned_channel_candidate':read(BASE/'full_reach/channel_alignment_report.json'),
        'troublemaker':{'geometry':read(BASE/'troublemaker/geometry_candidate/manifest.json'),
            'mean_flow_1m':read(REVIEW/'troublemaker_survey_flow_1m-mixed-inlet-conservative-edge.json'),
            'numerical_flux_1m':read(REVIEW/'troublemaker_numerical_boundary_flux-conservative-edge.json'),
            'mean_flow_half_metre':read(REVIEW/'troublemaker_survey_flow_0.5m-mixed-inlet-refined.json'),
            'half_metre_stability':read(REVIEW/'half_metre_stability.json'),
            'extended_half_metre_stability':read(ROOT/'docs/reconstruction-review-2026-09-07/extended_stability.json'),
            'captured_ground_engine_tests':read(ROOT/'docs/reconstruction-review-2026-09-07/engine-tests-final/index.json'),
            'registered_review_runtime':read(ROOT/'docs/reconstruction-review-2026-09-07/runtime_registration.json'),
            'latest_clean_review_performance':read(ROOT/'docs/reconstruction-review-2026-09-07/survey_performance_depth_limited.json') or read(ROOT/'docs/reconstruction-review-2026-09-07/survey_performance_triangle_fields.json') or read(ROOT/'docs/reconstruction-review-2026-09-07/survey_performance_one_foam_carrier.json') or read(ROOT/'docs/reconstruction-review-2026-09-07/survey_performance_shared_breaking.json') or read(ROOT/'docs/reconstruction-review-2026-09-07/survey_performance_gap_integrated.json') or read(ROOT/'docs/reconstruction-review-2026-09-07/survey_performance_surface_lit.json') or read(ROOT/'docs/reconstruction-review-2026-09-07/survey_performance_face_cache.json') or read(ROOT/'docs/reconstruction-review-2026-09-07/survey_performance_final.json'),
            'face_reuse_solver_equivalence':read(ROOT/'docs/reconstruction-review-2026-09-07/face-cache-comparison/report.json'),
            'face_reuse_review_performance':read(ROOT/'docs/reconstruction-review-2026-09-07/survey_performance_face_cache.json'),
            'face_reuse_engine_tests':read(ROOT/'docs/reconstruction-review-2026-09-07/engine-tests-face-cache/index.json'),
            'natural_drift_initial_engine_test':read(ROOT/'docs/reconstruction-review-2026-09-07/engine-natural-drift-initial/index.json'),
            'enclosed_rock_gap_candidate':read(ROOT/'docs/reconstruction-review-2026-09-07/rock-gap-candidate.json'),
            'single_carrier_lighting_experiment':read(ROOT/'docs/reconstruction-review-2026-09-07/surface-lighting-setup.json'),
            'single_carrier_lighting_engine_tests':read(ROOT/'docs/reconstruction-review-2026-09-07/engine-tests-surface-lit/index.json'),
            'gap_candidate_engine_integration':read(ROOT/'docs/reconstruction-review-2026-09-07/gap-engine-integration.json'),
            'gap_candidate_engine_tests':read(ROOT/'docs/reconstruction-review-2026-09-07/engine-tests-gap-integrated/index.json'),
            'guided_candidate_traversal':read(ROOT/'docs/reconstruction-review-2026-09-07/guided-review.json'),
            'opt_in_shared_breaking_tests':read(ROOT/'docs/reconstruction-review-2026-09-07/engine-shared-breaking-fresh-map/index.json'),
            'opt_in_shared_breaking_performance':read(ROOT/'docs/reconstruction-review-2026-09-07/survey_performance_shared_breaking.json'),
            'single_foam_carrier_material_audit':read(ROOT/'docs/reconstruction-review-2026-09-07/survey-material-audit.json'),
            'single_foam_carrier_tests':read(ROOT/'docs/reconstruction-review-2026-09-07/engine-one-foam-carrier/index.json'),
            'single_foam_carrier_performance':read(ROOT/'docs/reconstruction-review-2026-09-07/survey_performance_one_foam_carrier.json'),
            'gap_half_metre_resolution_comparison':read(ROOT/'docs/reconstruction-review-2026-09-07/gap-resolution-comparison.json'),
            'gap_half_metre_mean_flow':read(REVIEW/'troublemaker_survey_flow_0.5m-mixed-inlet-enclosed-rock-gaps-refined-20260907.json'),
            'gap_half_metre_numerical_flux':read(REVIEW/'troublemaker_numerical_boundary_flux-0.5m-enclosed-rock-gaps-refined-20260907.json'),
            'gap_continuation_comparison':read(ROOT/'docs/reconstruction-review-2026-09-07/gap-settled-resolution-comparison.json'),
            'gap_continuation_regional_hotspots':read(ROOT/'docs/reconstruction-review-2026-09-07/gap-continuation-hotspots.json'),
            'gap_continuation_mean_flow':read(REVIEW/'troublemaker_survey_flow_0.5m-mixed-inlet-enclosed-rock-gaps-settling-20260907.json'),
            'gap_continuation_numerical_flux':read(REVIEW/'troublemaker_numerical_boundary_flux-0.5m-enclosed-rock-gaps-settling-20260907.json'),
            'dated_atlas_discharge_context':read(ROOT/'docs/reconstruction-review-2026-09-07/naip-date-discharge-context.json'),
            'rock_pocket_source_review':read(ROOT/'docs/reconstruction-review-2026-09-07/rock-pocket-source-review.json'),
            'interior_collision_sampling_audit':read(ROOT/'docs/reconstruction-review-2026-09-07/engine-interior-mesh-audit.json'),
            'triangle_cook_mean_flow':read(REVIEW/'troublemaker_survey_flow_1m-mixed-inlet-mesh-triangles-20260907.json'),
            'triangle_cook_numerical_flux':read(REVIEW/'troublemaker_numerical_boundary_flux-mesh-triangles-20260907.json'),
            'triangle_cook_regional':read(ROOT/'docs/reconstruction-review-2026-09-07/triangle-cook-regional.json'),
            'triangle_candidate_staging':read(ROOT/'docs/reconstruction-review-2026-09-07/triangle-engine-integration.json'),
            'triangle_candidate_engine_tests':read(ROOT/'docs/reconstruction-review-2026-09-07/engine-triangle-fields/index.json'),
            'triangle_candidate_performance':read(ROOT/'docs/reconstruction-review-2026-09-07/survey_performance_triangle_fields.json'),
            'triangle_subgrid_geometry':read(ROOT/'docs/reconstruction-review-2026-09-07/triangle-subgrid-geometry.json'),
            'bank_spike_experiments':read(ROOT/'docs/reconstruction-review-2026-09-07/bank-spike-experiments.json'),
            'depth_limited_mean_flow':read(REVIEW/'troublemaker_survey_flow_1m-mixed-inlet-depth-limited-hydrostatic-20260907.json'),
            'depth_limited_flux':read(REVIEW/'troublemaker_numerical_boundary_flux-depth-limited-hydrostatic-20260907.json'),
            'depth_limited_regional':read(ROOT/'docs/reconstruction-review-2026-09-07/depth-limited-regional.json'),
            'depth_limited_refined_comparison':read(ROOT/'docs/reconstruction-review-2026-09-07/depth-limited-resolution-comparison.json'),
            'depth_limited_refined_regional':read(ROOT/'docs/reconstruction-review-2026-09-07/depth-limited-refined-regional.json'),
            'depth_limited_refined_mean_flow':read(REVIEW/'troublemaker_survey_flow_0.5m-mixed-inlet-depth-limited-refined-20260907.json'),
            'depth_limited_refined_flux':read(REVIEW/'troublemaker_numerical_boundary_flux-0.5m-depth-limited-refined-20260907.json'),
            'depth_limited_staging':read(ROOT/'docs/reconstruction-review-2026-09-07/depth-limited-engine-integration.json'),
            'depth_limited_engine_tests':read(ROOT/'docs/reconstruction-review-2026-09-07/engine-depth-limited/index.json'),
            'depth_limited_guided_engine_tests':read(ROOT/'docs/reconstruction-review-2026-09-07/engine-depth-limited-guided/index.json'),
            'attainable_guidance_combined_engine_tests':read(ROOT/'docs/reconstruction-review-2026-09-07/engine-attainable-steering-combined/index.json'),
            'depth_limited_performance':read(ROOT/'docs/reconstruction-review-2026-09-07/survey_performance_depth_limited.json'),
            'triangle_half_metre_rejected_comparison':read(ROOT/'docs/reconstruction-review-2026-09-07/triangle-resolution-comparison.json'),
            'cdfw_upper_reach_reference':read(BASE/'sources/cdfw_chili_bar_2018_survey_2020_memo.provenance.json'),
            'geometry_collision_samples':read(REVIEW/'engine/collision_and_capture_report.json'),
            'playable_setup':read(REVIEW/'engine/playable_setup.json'),
            'registered_runtime_tests':read(REVIEW/'engine/runtime_tests_final/index.json'),
            'review_performance':read(REVIEW/'engine/survey_performance_optimized.json'),
            'offline_optimization':read(REVIEW/'dry_culling_benchmark.json')},
        'repair':read(REVIEW/'engine/boot_spill_repair.json'),
        'saved_world_isolation':read(REVIEW/'engine/saved_world_isolation.json'),
        'remaining_acceptance':[
            'Verify each rapid identity and exposed rock layout against registered imagery and footage',
            'Calibrate explicitly inferred submerged geometry and source water stage/discharge',
            'Resolve hydraulic resolution sensitivity; no half-metre result accepted merely because it ran',
            'Migrate production route, terrain, collision, hydraulic tiles and starts together',
            'Validate actual boat-height animation, single wet surface, boulder collisions and boat drift',
            'Measure playable frame times and complete full-reach visual review before promotion']}
    (REVIEW/'south_fork_progress.json').write_text(json.dumps(progress,indent=2),encoding='utf-8')
    manifest['implementation_progress_report']=(REVIEW/'south_fork_progress.json').relative_to(ROOT).as_posix()
    manifest['source_acquisition_complete_for_candidate_corridor']=True
    manifest['separate_troublemaker_review_level_created']=progress['troublemaker']['playable_setup'] is not None
    manifest['production_scene_replaced']=False
    # Existing game_geometry_updated/hydraulics_recooked mean production, not
    # existence of a diagnostic package. Preserve their honest false values.
    (BASE/'reconstruction_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(progress['captured_sources'],indent=2))


if __name__=='__main__':main()
