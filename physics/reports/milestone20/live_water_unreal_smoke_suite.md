# Milestone 20 Live-Water Unreal Smoke Suite

Decision: `pass_text_first_unreal_smoke_gate`

Passed: `True`

Unreal editor execution status: `not_run_in_text_first_workspace`.

## Checks

- `accepted_report_set_lock`: PASS - Accepted Milestone 16 report-set lock is present, passing, and hash-addressed.
- `live_water_bridge_lock_match`: PASS - Live-water bridge references the accepted report-set lock hash.
- `regression_fixture_import_coverage`: PASS - Unreal automation import covers Milestone 16/17/18 accepted fixtures.
- `traceable_data_assets_stitched_outputs`: PASS - Traceable data assets include reach-local grids and stitched whole-window outputs.
- `debug_view_coverage`: PASS - Debug views expose every required water, raft, contact, and runtime-budget overlay.
- `target_profile_budgets`: PASS - Accepted runtime profile records pass desktop, VR, and handheld target budget profiles.
- `deterministic_replay_evidence`: PASS - Accepted deterministic replay groups match.

## Target Profiles

| Profile | Records | Passed | Max ms/tick | Budget ms/tick |
| --- | ---: | ---: | ---: | ---: |
| desktop | 80 | 80 | 1.270460 | 4.800000 |
| handheld | 80 | 80 | 1.270460 | 5.600000 |
| vr | 80 | 80 | 1.270460 | 2.400000 |

## Notes

- This report closes the text-first Milestone 20 gate in this repo workspace.
- A UE 5.8 workstation should execute the generated automation test and attach measured editor/runtime output before release or platform sign-off.
- The suite is anchored to the accepted C++ report-set lock and must be regenerated if that lock changes.
