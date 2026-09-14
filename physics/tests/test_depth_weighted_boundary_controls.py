"""Run ORIGINAL boundary assertions against the proposed scalar derivative.

No assertions are translated, weakened, skipped or marked expected-failure.
The old face-matrix identity describes a different discretization and is kept
as an explicit incompatibility check, not silently removed from this audit.
"""
import importlib.util
from pathlib import Path
import pytest
from depth_weighted_scalar_gradient import DepthWeightedSourceBoundary
from connected_depth_weighted_scalar_gradient import ConnectedDepthWeightedSourceBoundary


spec = importlib.util.spec_from_file_location('original_boundary_controls',
    Path(__file__).with_name('test_source_supported_scalar_boundary.py'))
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)

CASES = [
    ('test_affine_derivatives_exact_including_all_edges_and_corners', (n,))
    for n in (8, 16, 32)
] + [
    (name, ()) for name in (
        'test_smooth_boundary_error_refines_second_order',
        'test_current_interior_wins_and_source_inputs_are_untouched',
        'test_affine_velocity_ghost_divergence_uses_independent_face_trace',
        'test_pressure_force_and_work_unchanged_and_dry_columns_not_repaired',
        'test_missing_halo_and_unregistered_current_depth_are_rejected',
        'test_scalar_action_matches_independent_explicit_face_matrix',
        'test_partial_time_face_trace_is_not_lost_in_material_identity',
    )
] + [('test_actual_entering_ray_keeps_zero_state_and_nonzero_velocity_limit', (flat,))
     for flat in (True, False)]


@pytest.mark.parametrize('name,args', CASES, ids=[name+str(args) for name,args in CASES])
@pytest.mark.parametrize('implementation', [DepthWeightedSourceBoundary, ConnectedDepthWeightedSourceBoundary])
def test_original_boundary_assertion(monkeypatch, name, args, implementation):
    monkeypatch.setattr(original, 'SourceSupportedScalarBoundary', implementation)
    getattr(original, name)(*args)
