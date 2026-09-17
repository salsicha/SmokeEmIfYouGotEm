"""Updated source contracts must still reject concrete runtime regressions.

These are source-wiring checks, not substitutes for native behavior, hydraulic
validation or visual acceptance. No repository source is changed by a mutation.
"""
from pathlib import Path

import pytest

import test_troublemaker_challenge_launch as launch
import test_full_reach_water_presentation as terrain
import test_south_fork_water_performance_and_banding as water


SURFACE = water.RUNTIME_SOURCE
CLASSIFIER = SURFACE.with_name('RaftSimTerrainProbeSources.h')
SMOOTHING = water.WATER_SURFACE_HEADER.with_name('RaftSimWaterSmoothing.h')
CLOCK = water.PHYSICS_BRIDGE_SOURCE.parents[1] / 'Public/RaftSimFixedStepClock.h'


CASES = [
    ('obsolete-route', launch.FRONTEND_SOURCE, '33280.0f', '48900.0f', launch.test_troublemaker_is_not_a_standalone_scenario),
    ('section-endpoint', launch.FRONTEND_SOURCE, '120.0f, 9012.3264f', '120.0f, 9013.3264f', launch.test_troublemaker_is_not_a_standalone_scenario),
    ('rapid-menu-scenario', launch.FRONTEND_SOURCE, 'TEXT("hance_challenge")', 'TEXT("troublemaker_challenge")', launch.test_troublemaker_is_not_a_standalone_scenario),
    ('inflated-ray-budget', SURFACE, 'Attempt < 4 && RemainingRayBudget > 0', 'Attempt < 8 && RemainingRayBudget > 0', terrain.test_bank_terrain_probes_skip_blockers_without_expanding_the_ray_budget),
    ('free-ray-attempt', SURFACE, '--RemainingRayBudget;', '++RemainingRayBudget;', terrain.test_bank_terrain_probes_skip_blockers_without_expanding_the_ray_budget),
    ('lost-component-ground', CLASSIFIER, 'Component->ComponentHasTag(TEXT("RaftSimPhysicalGround"))', 'Component->ComponentHasTag(TEXT("WrongGround"))', terrain.test_bank_terrain_probes_skip_blockers_without_expanding_the_ray_budget),
    ('lost-legacy-ground', CLASSIFIER, 'Actor->ActorHasTag(TEXT("RaftSimFullReachTerrain")) ||', 'false ||', terrain.test_bank_terrain_probes_skip_blockers_without_expanding_the_ray_budget),
    ('expanded-tick-budget', water.PHYSICS_BRIDGE_SOURCE, 'double(WaterStepSeconds),4,', 'double(WaterStepSeconds),5,', water.test_live_solver_cannot_enter_a_render_frame_catch_up_spiral),
    ('discarded-frame-debt', water.PHYSICS_BRIDGE_SOURCE, 'LastOutput.FixedTicksThisFrame=Completed;', 'LastOutput.FixedTicksThisFrame=Completed; FixedClock.BacklogSeconds=FMath::Fmod(FixedClock.BacklogSeconds,WaterStepSeconds);', water.test_live_solver_cannot_enter_a_render_frame_catch_up_spiral),
    ('committed-failed-tick', CLOCK, 'if(!RunTick())return false;', 'RunTick();', water.test_live_solver_cannot_enter_a_render_frame_catch_up_spiral),
    ('coupled-order-reduction', water.LIVE_WINDOW_SOURCE,
     'Config.spatial_order = 2;\n        Config.boundary_mode = "scenario";\n        Scenario.roughness = Manning;\n        Scenario.boundaries.clear();',
     'Config.spatial_order = 1;\n        Config.boundary_mode = "scenario";\n        Scenario.roughness = Manning;\n        Scenario.boundaries.clear();',
     water.test_live_solver_cannot_enter_a_render_frame_catch_up_spiral),
    ('shared-bank-jump-rejected', SURFACE,
     '(bSingleLiveWaterSurfaceEnabled || bSharedBreakingReliefEnabled) ? 0.55f : 0.999f',
     'bSingleLiveWaterSurfaceEnabled ? 0.55f : 0.999f', water.test_single_surface_accepts_real_near_bank_hydraulic_jumps),
    ('bank-threshold-changed', SURFACE,
     '(bSingleLiveWaterSurfaceEnabled || bSharedBreakingReliefEnabled) ? 0.55f : 0.999f',
     '(bSingleLiveWaterSurfaceEnabled || bSharedBreakingReliefEnabled) ? 0.999f : 0.999f', water.test_single_surface_accepts_real_near_bank_hydraulic_jumps),
    ('clearance-reduced', SURFACE, 'FMath::Max(ResolvedVertexSpacingMeters, 3.0f)', 'FMath::Max(ResolvedVertexSpacingMeters, 1.0f)', water.test_single_surface_accepts_real_near_bank_hydraulic_jumps),
    ('hydraulic-pass-reduction', SURFACE, 'const int32 HydraulicPassCount = bSingleLiveWaterSurfaceEnabled ? 4 : 1', 'const int32 HydraulicPassCount = bSingleLiveWaterSurfaceEnabled ? 3 : 1', water.test_optical_smoothing_review_keeps_hydraulic_sources_and_other_rivers_fixed),
    ('wrong-hydraulic-snapshot', SMOOTHING, 'if (Pass+1==HydraulicPasses) Hydraulic=Surface;', 'if (Pass+2==HydraulicPasses) Hydraulic=Surface;', water.test_optical_smoothing_review_keeps_hydraulic_sources_and_other_rivers_fixed),
    ('dry-hole-smoothed', SMOOTHING, 'if (!Wet[I] || !Wet[U] || !Wet[D] || !Wet[R] || !Wet[L]) continue;', 'if (!Wet[I]) continue;', water.test_optical_smoothing_review_keeps_hydraulic_sources_and_other_rivers_fixed),
    ('other-river-optics-elided', SMOOTHING, 'return bNativeMean && !bNeedsOptical ? 0 : Configured;', 'return !bNeedsOptical ? 0 : Configured;', water.test_optical_smoothing_review_keeps_hydraulic_sources_and_other_rivers_fixed),
]


@pytest.mark.parametrize('name,target,before,after,check', CASES, ids=[case[0] for case in CASES])
def test_current_contract_rejects_regression(monkeypatch, name, target, before, after, check):
    original_read = Path.read_text
    text = original_read(target)
    assert before in text, f'{name}: mutation must reach current source'
    mutated = text.replace(before, after, 1)
    assert mutated != text
    reads = []

    def read(path, *args, **kwargs):
        if path.resolve() == target.resolve():
            reads.append(path)
            return mutated
        return original_read(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'read_text', read)
    with pytest.raises(AssertionError):
        check()
    assert reads, f'{name}: mutated source was not inspected'
