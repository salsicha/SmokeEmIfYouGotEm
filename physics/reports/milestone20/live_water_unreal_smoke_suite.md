# Milestone 20 Live-Water Unreal Smoke Suite

Decision: `blocked`

Passed: `False`

Unreal editor execution status: `passed_in_unreal_editor`.

## Unreal Editor Automation

Evidence: `physics/reports/milestone20/unreal_editor_automation_result.json`

Executed at: `2026.07.04-07.46.36` on `MacEditor`.

Result: 2 succeeded, 0 succeeded with warnings, 0 failed, 0 not run.

## Checks

- `accepted_report_set_lock`: FAIL - Accepted Milestone 16 report-set lock is present, passing, and hash-addressed.
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

- This report keeps the Milestone 20 live-water Unreal smoke gate blocked.
- The suite is anchored to the current C++ report-set lock and must be regenerated if that lock changes.
- UE 5.8 MacEditor headless automation executed successfully; physical desktop, VR, and handheld captures remain platform sign-off evidence.
