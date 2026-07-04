# Milestone 19 Chaos Automation Fixture Export

Decision: `automation_fixture_export_complete_not_authority_evidence`

Exported 6 Chaos fixtures with 39 expanded parameter cases and 6 replay summaries.

These files are automation-ready fixtures, not Chaos authority evidence. Unreal still needs to execute the generated fixtures and replace placeholder telemetry frames with measured Chaos results before Chaos can be ranked against Jolt.

## Fixtures

- `raft_rock_angle_sweep`: 9 parameter cases, 960 fixed steps, replay `physics/reports/milestone19/chaos/replays/raft_rock_angle_sweep.replay_summary.json`.
- `shallow_shelf_grounding`: 9 parameter cases, 960 fixed steps, replay `physics/reports/milestone19/chaos/replays/shallow_shelf_grounding.replay_summary.json`.
- `pin_release_wrap_proxy`: 9 parameter cases, 960 fixed steps, replay `physics/reports/milestone19/chaos/replays/pin_release_wrap_proxy.replay_summary.json`.
- `crew_ejection_swimmer_transition`: 9 parameter cases, 960 fixed steps, replay `physics/reports/milestone19/chaos/replays/crew_ejection_swimmer_transition.replay_summary.json`.
- `fixed_step_replay_determinism`: 1 parameter cases, 1000 fixed steps, replay `physics/reports/milestone19/chaos/replays/fixed_step_replay_determinism.replay_summary.json`.
- `runtime_cost_crowded_scene`: 2 parameter cases, 3600 fixed steps, replay `physics/reports/milestone19/chaos/replays/runtime_cost_crowded_scene.replay_summary.json`.

## Notes

- This artifact completes the Chaos automation fixture export, not the Chaos authority decision.
- Unreal must execute the generated fixture map/tests and replace schema placeholder telemetry before Chaos can be ranked against Jolt.
- The custom C++ water solver remains authoritative water; Chaos consumes water snapshots and may not mutate water state.
