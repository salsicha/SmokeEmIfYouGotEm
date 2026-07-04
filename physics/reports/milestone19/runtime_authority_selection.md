# Milestone 19 Runtime Authority Selection

Decision: `custom_reduced_runtime_fallback_selected_for_vertical_slice`

Selected runtime: `CustomReducedRigidBody`

Chaos and Jolt fixture exports exist, but the comparison report blocks authority selection because measured runtime telemetry has not replaced schema placeholder frames.

## Runtime Status

- Chaos: visual_and_non_authoritative_only_pending_measured_fixture_results.
- Jolt: candidate_pending_measured_jolt_sdk_fixture_results.
- Custom reduced: selected_fallback_until_chaos_or_jolt_passes_measured_fixture_suite.
- Chrono: high_fidelity_reference_and_research_only.

## Replacement Conditions

- Run measured Unreal Chaos automation fixtures over the shared contract.
- Run measured native Jolt SDK/plugin fixtures over the shared contract.
- Regenerate the Chaos-vs-Jolt comparison with non-placeholder telemetry.
- Select Chaos or Jolt only if the comparison report allows scoring-critical authority.
