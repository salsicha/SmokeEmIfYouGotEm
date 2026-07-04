# Milestone 19 Jolt Smoke Harness Export

Decision: `native_jolt_smoke_harness_export_complete_not_authority_evidence`

Exported 6 Jolt fixtures with 39 expanded parameter cases and 6 replay summaries.

These files are automation-ready fixtures, not authority evidence. The runtime still needs to execute the generated fixtures and replace placeholder telemetry frames with measured results before it can be ranked against the other candidate.

## Fixtures

- `raft_rock_angle_sweep`: 9 parameter cases, 960 fixed steps, replay `physics/reports/milestone19/jolt/replays/raft_rock_angle_sweep.replay_summary.json`.
- `shallow_shelf_grounding`: 9 parameter cases, 960 fixed steps, replay `physics/reports/milestone19/jolt/replays/shallow_shelf_grounding.replay_summary.json`.
- `pin_release_wrap_proxy`: 9 parameter cases, 960 fixed steps, replay `physics/reports/milestone19/jolt/replays/pin_release_wrap_proxy.replay_summary.json`.
- `crew_ejection_swimmer_transition`: 9 parameter cases, 960 fixed steps, replay `physics/reports/milestone19/jolt/replays/crew_ejection_swimmer_transition.replay_summary.json`.
- `fixed_step_replay_determinism`: 1 parameter cases, 1000 fixed steps, replay `physics/reports/milestone19/jolt/replays/fixed_step_replay_determinism.replay_summary.json`.
- `runtime_cost_crowded_scene`: 2 parameter cases, 3600 fixed steps, replay `physics/reports/milestone19/jolt/replays/runtime_cost_crowded_scene.replay_summary.json`.

## Notes

- This artifact completes the native Jolt smoke harness export, not the Jolt authority decision.
- The harness target is buildable without vendoring Jolt and validates contract/schema plumbing first.
- Measured Jolt physics telemetry must replace placeholder frames before Jolt can be ranked against Chaos.
