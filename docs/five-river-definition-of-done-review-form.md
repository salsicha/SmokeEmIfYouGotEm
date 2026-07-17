# Five-River Definition of Done Review Form

> **FROZEN July 17, 2026 — superseded by `docs/release-1.0-plan.md`.** The release plan's phase exit gates are the definition of done for 1.0.

Generated: 2026-07-17

Use this form only after the A/B/C/D/E source, asset, water, raft, platform, capture, test, commit, and push gates are green. Record hash-locked evidence and all reviewer signoffs in the JSON sidecar, then run the validator before starting the separate owner completion review.

This form is not approval. It cannot make a blocked source criterion complete, bypass any upstream gate, mark a river or the execution plan complete, or support lifelike, playable, photoreal, or release-ready claims by itself.

## Source Records

- Execution plan: `docs/five-river-photoreal-execution-plan.md`
- Definition of Done matrix: `physics/data/real_world/five_river_definition_of_done_matrix.json`
- Evidence sidecar: `physics/data/real_world/five_river_definition_of_done_evidence_sidecar_template.json`
- Validation report: `physics/data/real_world/five_river_definition_of_done_evidence_validation_report.json`

Additional source artifacts:
- `river_portfolio_plan`: `physics/data/real_world/river_portfolio_plan.json`
- `execution_plan_readiness_report`: `physics/data/real_world/five_river_photoreal_execution_plan_readiness_report.json`
- `external_action_queue`: `physics/data/real_world/five_river_photoreal_external_action_queue.json`
- `e1_platform_matrix_validation`: `physics/data/real_world/e1_platform_matrix_decision_validation_report.json`
- `e2_profile_parity_validation`: `physics/data/real_world/e2_scalability_profile_parity_validation_report.json`
- `e3_packaged_runtime_validation`: `physics/data/real_world/e3_packaged_runtime_validation_report.json`

## Current Gate State

- Matrix status: `five_river_definition_of_done_blocked_pending_external_evidence`
- River count: 5
- Definition of Done criteria per river: 6
- Total Definition of Done criterion count: 30
- Complete source-matrix criterion count: 0
- Blocked source-matrix criterion count: 30
- Complete river count: 0
- Blocked river count: 5
- Sidecar complete-reviewed criterion count: 0
- Evidence validation error count: 420
- May start manual completion review: False
- May mark any river complete from sidecar alone: False
- May mark five-river Definition of Done complete from sidecar alone: False
- May mark execution plan complete from sidecar alone: False
- May claim five-river photoreal ready: False
- May claim playable release ready: False

## River Summary

| Order | River | Put-in | Take-out | Parent gates | Complete criteria | Blocked criteria | River complete |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `american_south_fork` / South Fork American River | Chili Bar | Folsom Reservoir | `A1`, `B2-south-fork`, `C2`, `C3`, `C4`, `C5`, `D6` | 0 | 6 | False |
| 2 | `colorado_river_grand_canyon_rowing` / Colorado River through Grand Canyon | Lees Ferry | Pearce Ferry | `A2`, `B2-colorado`, `C2`, `C3`, `C4`, `C5`, `D6` | 0 | 6 | False |
| 3 | `pacuare_river_costa_rica` / Pacuare River | Tres Equis | Siquirres | `A3`, `B2-pacuare`, `C2`, `C3`, `C4`, `C5`, `D6` | 0 | 6 | False |
| 4 | `futaleufu_river_chile` / Futaleufu River | Rio Azul Swinging Bridge | The Pasarela | `A4`, `B2-futaleufu`, `C2`, `C3`, `C4`, `C5`, `D6` | 0 | 6 | False |
| 5 | `chilko_river_lava_canyon` / Chilko River | Chilko River Lodge | Chilko-Taseko Junction | `A5`, `B2-chilko`, `C2`, `C3`, `C4`, `C5`, `D6` | 0 | 6 | False |

## Required Sidecar Fields

- `river_id`
- `linked_parent_gate_ids`
- `criteria[].criterion_id`
- `criteria[].definition_of_done_item`
- `criteria[].linked_parent_gate_ids`
- `criteria[].required_external_action_ids`
- `criteria[].criterion_status = complete_reviewed`
- `criteria[].evidence_artifact_paths`
- `criteria[].evidence_sha256s`
- `criteria[].test_commands`
- `criteria[].commit_ids`
- `criteria[].push_records`
- `criteria[].plan_checkbox_marked_complete = false`
- `criteria[].notes`
- `criteria[].reviewer_signoff.river_guide_or_oarsman_reviewer`
- `criteria[].reviewer_signoff.geospatial_reviewer`
- `criteria[].reviewer_signoff.hydrology_or_physics_reviewer`
- `criteria[].reviewer_signoff.technical_art_reviewer`
- `criteria[].reviewer_signoff.hazard_rescue_readability_reviewer`
- `criteria[].reviewer_signoff.rights_publication_reviewer`
- `criteria[].reviewer_signoff.platform_performance_reviewer`
- `criteria[].reviewer_signoff.owner`

## Criterion Evidence Intake

Record each evidence artifact path and its lowercase 64-character SHA-256 in the JSON sidecar. Every criterion also needs non-empty test commands, commit IDs, and push records.

| River | Item | Criterion id | Source status | Parent gates | External actions | Evidence paths + hashes | Tests | Commits | Pushes | Criterion status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `american_south_fork` | 1 | `full_corridor_stationing_flow_bands` | `blocked_pending_reviewed_evidence` | `A1` | `01-A1-source-mile-access-decision`, `13-F-five-river-definition-of-done-evidence` |  |  |  |  |  |  |
| `american_south_fork` | 2 | `catalog_rapid_stationing_feature_inventory_and_runs` | `blocked_pending_reviewed_evidence` | `A1`, `C2`, `C3`, `C4` | `01-A1-source-mile-access-decision`, `13-F-five-river-definition-of-done-evidence`, `08-C1-C2-reviewed-subfeatures-editor-pins`, `09-C3-water-window-bindings`, `10-C4-simulator-output-behavior-review` |  |  |  |  |  |  |
| `american_south_fork` | 3 | `photoreal_assets_nanite_lumen_vsm_e2_performance` | `blocked_pending_reviewed_evidence` | `B2-south-fork` | `06-B2-five-river-asset-source-import-review`, `13-F-five-river-definition-of-done-evidence`, `12-E2-E3-platform-release-evidence` |  |  |  |  |  |  |
| `american_south_fork` | 4 | `flexible_raft_mechanics_and_reapproved_outcomes` | `blocked_pending_reviewed_evidence` | `D6`, `C5` | `07-D6-external-physics-measurements`, `13-F-five-river-definition-of-done-evidence`, `11-C5-flexible-raft-named-rapid-reruns`, `12-E2-E3-platform-release-evidence` |  |  |  |  |  |  |
| `american_south_fork` | 5 | `lifelike_low_reference_high_captures_and_review` | `blocked_pending_reviewed_evidence` | `A1`, `B2-south-fork`, `C4`, `C5` | `01-A1-source-mile-access-decision`, `13-F-five-river-definition-of-done-evidence`, `06-B2-five-river-asset-source-import-review`, `10-C4-simulator-output-behavior-review`, `11-C5-flexible-raft-named-rapid-reruns`, `12-E2-E3-platform-release-evidence` |  |  |  |  |  |  |
| `american_south_fork` | 6 | `hash_locked_evidence_green_tests_commit_push` | `blocked_pending_reviewed_evidence` | `A1`, `B2-south-fork`, `C2`, `C3`, `C4`, `C5`, `D6` | `01-A1-source-mile-access-decision`, `13-F-five-river-definition-of-done-evidence`, `06-B2-five-river-asset-source-import-review`, `08-C1-C2-reviewed-subfeatures-editor-pins`, `09-C3-water-window-bindings`, `10-C4-simulator-output-behavior-review`, `11-C5-flexible-raft-named-rapid-reruns`, `12-E2-E3-platform-release-evidence`, `07-D6-external-physics-measurements` |  |  |  |  |  |  |
| `colorado_river_grand_canyon_rowing` | 1 | `full_corridor_stationing_flow_bands` | `blocked_pending_reviewed_evidence` | `A2` | `02-A2-centerline-rapid-mile-source-window-review`, `13-F-five-river-definition-of-done-evidence` |  |  |  |  |  |  |
| `colorado_river_grand_canyon_rowing` | 2 | `catalog_rapid_stationing_feature_inventory_and_runs` | `blocked_pending_reviewed_evidence` | `A2`, `C2`, `C3`, `C4` | `02-A2-centerline-rapid-mile-source-window-review`, `13-F-five-river-definition-of-done-evidence`, `08-C1-C2-reviewed-subfeatures-editor-pins`, `09-C3-water-window-bindings`, `10-C4-simulator-output-behavior-review` |  |  |  |  |  |  |
| `colorado_river_grand_canyon_rowing` | 3 | `photoreal_assets_nanite_lumen_vsm_e2_performance` | `blocked_pending_reviewed_evidence` | `B2-colorado` | `06-B2-five-river-asset-source-import-review`, `13-F-five-river-definition-of-done-evidence`, `12-E2-E3-platform-release-evidence` |  |  |  |  |  |  |
| `colorado_river_grand_canyon_rowing` | 4 | `flexible_raft_mechanics_and_reapproved_outcomes` | `blocked_pending_reviewed_evidence` | `D6`, `C5` | `07-D6-external-physics-measurements`, `13-F-five-river-definition-of-done-evidence`, `11-C5-flexible-raft-named-rapid-reruns`, `12-E2-E3-platform-release-evidence` |  |  |  |  |  |  |
| `colorado_river_grand_canyon_rowing` | 5 | `lifelike_low_reference_high_captures_and_review` | `blocked_pending_reviewed_evidence` | `A2`, `B2-colorado`, `C4`, `C5` | `02-A2-centerline-rapid-mile-source-window-review`, `13-F-five-river-definition-of-done-evidence`, `06-B2-five-river-asset-source-import-review`, `10-C4-simulator-output-behavior-review`, `11-C5-flexible-raft-named-rapid-reruns`, `12-E2-E3-platform-release-evidence` |  |  |  |  |  |  |
| `colorado_river_grand_canyon_rowing` | 6 | `hash_locked_evidence_green_tests_commit_push` | `blocked_pending_reviewed_evidence` | `A2`, `B2-colorado`, `C2`, `C3`, `C4`, `C5`, `D6` | `02-A2-centerline-rapid-mile-source-window-review`, `13-F-five-river-definition-of-done-evidence`, `06-B2-five-river-asset-source-import-review`, `08-C1-C2-reviewed-subfeatures-editor-pins`, `09-C3-water-window-bindings`, `10-C4-simulator-output-behavior-review`, `11-C5-flexible-raft-named-rapid-reruns`, `12-E2-E3-platform-release-evidence`, `07-D6-external-physics-measurements` |  |  |  |  |  |  |
| `pacuare_river_costa_rica` | 1 | `full_corridor_stationing_flow_bands` | `blocked_pending_reviewed_evidence` | `A3` | `03-A3-pacuare-stationing-flow-review`, `13-F-five-river-definition-of-done-evidence` |  |  |  |  |  |  |
| `pacuare_river_costa_rica` | 2 | `catalog_rapid_stationing_feature_inventory_and_runs` | `blocked_pending_reviewed_evidence` | `A3`, `C2`, `C3`, `C4` | `03-A3-pacuare-stationing-flow-review`, `13-F-five-river-definition-of-done-evidence`, `08-C1-C2-reviewed-subfeatures-editor-pins`, `09-C3-water-window-bindings`, `10-C4-simulator-output-behavior-review` |  |  |  |  |  |  |
| `pacuare_river_costa_rica` | 3 | `photoreal_assets_nanite_lumen_vsm_e2_performance` | `blocked_pending_reviewed_evidence` | `B2-pacuare` | `06-B2-five-river-asset-source-import-review`, `13-F-five-river-definition-of-done-evidence`, `12-E2-E3-platform-release-evidence` |  |  |  |  |  |  |
| `pacuare_river_costa_rica` | 4 | `flexible_raft_mechanics_and_reapproved_outcomes` | `blocked_pending_reviewed_evidence` | `D6`, `C5` | `07-D6-external-physics-measurements`, `13-F-five-river-definition-of-done-evidence`, `11-C5-flexible-raft-named-rapid-reruns`, `12-E2-E3-platform-release-evidence` |  |  |  |  |  |  |
| `pacuare_river_costa_rica` | 5 | `lifelike_low_reference_high_captures_and_review` | `blocked_pending_reviewed_evidence` | `A3`, `B2-pacuare`, `C4`, `C5` | `03-A3-pacuare-stationing-flow-review`, `13-F-five-river-definition-of-done-evidence`, `06-B2-five-river-asset-source-import-review`, `10-C4-simulator-output-behavior-review`, `11-C5-flexible-raft-named-rapid-reruns`, `12-E2-E3-platform-release-evidence` |  |  |  |  |  |  |
| `pacuare_river_costa_rica` | 6 | `hash_locked_evidence_green_tests_commit_push` | `blocked_pending_reviewed_evidence` | `A3`, `B2-pacuare`, `C2`, `C3`, `C4`, `C5`, `D6` | `03-A3-pacuare-stationing-flow-review`, `13-F-five-river-definition-of-done-evidence`, `06-B2-five-river-asset-source-import-review`, `08-C1-C2-reviewed-subfeatures-editor-pins`, `09-C3-water-window-bindings`, `10-C4-simulator-output-behavior-review`, `11-C5-flexible-raft-named-rapid-reruns`, `12-E2-E3-platform-release-evidence`, `07-D6-external-physics-measurements` |  |  |  |  |  |  |
| `futaleufu_river_chile` | 1 | `full_corridor_stationing_flow_bands` | `blocked_pending_reviewed_evidence` | `A4` | `04-A4-futaleufu-stationing-flow-review`, `13-F-five-river-definition-of-done-evidence` |  |  |  |  |  |  |
| `futaleufu_river_chile` | 2 | `catalog_rapid_stationing_feature_inventory_and_runs` | `blocked_pending_reviewed_evidence` | `A4`, `C2`, `C3`, `C4` | `04-A4-futaleufu-stationing-flow-review`, `13-F-five-river-definition-of-done-evidence`, `08-C1-C2-reviewed-subfeatures-editor-pins`, `09-C3-water-window-bindings`, `10-C4-simulator-output-behavior-review` |  |  |  |  |  |  |
| `futaleufu_river_chile` | 3 | `photoreal_assets_nanite_lumen_vsm_e2_performance` | `blocked_pending_reviewed_evidence` | `B2-futaleufu` | `06-B2-five-river-asset-source-import-review`, `13-F-five-river-definition-of-done-evidence`, `12-E2-E3-platform-release-evidence` |  |  |  |  |  |  |
| `futaleufu_river_chile` | 4 | `flexible_raft_mechanics_and_reapproved_outcomes` | `blocked_pending_reviewed_evidence` | `D6`, `C5` | `07-D6-external-physics-measurements`, `13-F-five-river-definition-of-done-evidence`, `11-C5-flexible-raft-named-rapid-reruns`, `12-E2-E3-platform-release-evidence` |  |  |  |  |  |  |
| `futaleufu_river_chile` | 5 | `lifelike_low_reference_high_captures_and_review` | `blocked_pending_reviewed_evidence` | `A4`, `B2-futaleufu`, `C4`, `C5` | `04-A4-futaleufu-stationing-flow-review`, `13-F-five-river-definition-of-done-evidence`, `06-B2-five-river-asset-source-import-review`, `10-C4-simulator-output-behavior-review`, `11-C5-flexible-raft-named-rapid-reruns`, `12-E2-E3-platform-release-evidence` |  |  |  |  |  |  |
| `futaleufu_river_chile` | 6 | `hash_locked_evidence_green_tests_commit_push` | `blocked_pending_reviewed_evidence` | `A4`, `B2-futaleufu`, `C2`, `C3`, `C4`, `C5`, `D6` | `04-A4-futaleufu-stationing-flow-review`, `13-F-five-river-definition-of-done-evidence`, `06-B2-five-river-asset-source-import-review`, `08-C1-C2-reviewed-subfeatures-editor-pins`, `09-C3-water-window-bindings`, `10-C4-simulator-output-behavior-review`, `11-C5-flexible-raft-named-rapid-reruns`, `12-E2-E3-platform-release-evidence`, `07-D6-external-physics-measurements` |  |  |  |  |  |  |
| `chilko_river_lava_canyon` | 1 | `full_corridor_stationing_flow_bands` | `blocked_pending_reviewed_evidence` | `A5` | `05-A5-chilko-stationing-flow-review`, `13-F-five-river-definition-of-done-evidence` |  |  |  |  |  |  |
| `chilko_river_lava_canyon` | 2 | `catalog_rapid_stationing_feature_inventory_and_runs` | `blocked_pending_reviewed_evidence` | `A5`, `C2`, `C3`, `C4` | `05-A5-chilko-stationing-flow-review`, `13-F-five-river-definition-of-done-evidence`, `08-C1-C2-reviewed-subfeatures-editor-pins`, `09-C3-water-window-bindings`, `10-C4-simulator-output-behavior-review` |  |  |  |  |  |  |
| `chilko_river_lava_canyon` | 3 | `photoreal_assets_nanite_lumen_vsm_e2_performance` | `blocked_pending_reviewed_evidence` | `B2-chilko` | `06-B2-five-river-asset-source-import-review`, `13-F-five-river-definition-of-done-evidence`, `12-E2-E3-platform-release-evidence` |  |  |  |  |  |  |
| `chilko_river_lava_canyon` | 4 | `flexible_raft_mechanics_and_reapproved_outcomes` | `blocked_pending_reviewed_evidence` | `D6`, `C5` | `07-D6-external-physics-measurements`, `13-F-five-river-definition-of-done-evidence`, `11-C5-flexible-raft-named-rapid-reruns`, `12-E2-E3-platform-release-evidence` |  |  |  |  |  |  |
| `chilko_river_lava_canyon` | 5 | `lifelike_low_reference_high_captures_and_review` | `blocked_pending_reviewed_evidence` | `A5`, `B2-chilko`, `C4`, `C5` | `05-A5-chilko-stationing-flow-review`, `13-F-five-river-definition-of-done-evidence`, `06-B2-five-river-asset-source-import-review`, `10-C4-simulator-output-behavior-review`, `11-C5-flexible-raft-named-rapid-reruns`, `12-E2-E3-platform-release-evidence` |  |  |  |  |  |  |
| `chilko_river_lava_canyon` | 6 | `hash_locked_evidence_green_tests_commit_push` | `blocked_pending_reviewed_evidence` | `A5`, `B2-chilko`, `C2`, `C3`, `C4`, `C5`, `D6` | `05-A5-chilko-stationing-flow-review`, `13-F-five-river-definition-of-done-evidence`, `06-B2-five-river-asset-source-import-review`, `08-C1-C2-reviewed-subfeatures-editor-pins`, `09-C3-water-window-bindings`, `10-C4-simulator-output-behavior-review`, `11-C5-flexible-raft-named-rapid-reruns`, `12-E2-E3-platform-release-evidence`, `07-D6-external-physics-measurements` |  |  |  |  |  |  |

## Criterion Reviewer Signoff

Every role must sign every criterion in the JSON sidecar. Names in this summary do not replace the per-criterion sidecar fields.

| River / criterion | `river_guide_or_oarsman_reviewer` | `geospatial_reviewer` | `hydrology_or_physics_reviewer` | `technical_art_reviewer` | `hazard_rescue_readability_reviewer` | `rights_publication_reviewer` | `platform_performance_reviewer` | `owner` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `american_south_fork` / `full_corridor_stationing_flow_bands` |  |  |  |  |  |  |  |  |
| `american_south_fork` / `catalog_rapid_stationing_feature_inventory_and_runs` |  |  |  |  |  |  |  |  |
| `american_south_fork` / `photoreal_assets_nanite_lumen_vsm_e2_performance` |  |  |  |  |  |  |  |  |
| `american_south_fork` / `flexible_raft_mechanics_and_reapproved_outcomes` |  |  |  |  |  |  |  |  |
| `american_south_fork` / `lifelike_low_reference_high_captures_and_review` |  |  |  |  |  |  |  |  |
| `american_south_fork` / `hash_locked_evidence_green_tests_commit_push` |  |  |  |  |  |  |  |  |
| `colorado_river_grand_canyon_rowing` / `full_corridor_stationing_flow_bands` |  |  |  |  |  |  |  |  |
| `colorado_river_grand_canyon_rowing` / `catalog_rapid_stationing_feature_inventory_and_runs` |  |  |  |  |  |  |  |  |
| `colorado_river_grand_canyon_rowing` / `photoreal_assets_nanite_lumen_vsm_e2_performance` |  |  |  |  |  |  |  |  |
| `colorado_river_grand_canyon_rowing` / `flexible_raft_mechanics_and_reapproved_outcomes` |  |  |  |  |  |  |  |  |
| `colorado_river_grand_canyon_rowing` / `lifelike_low_reference_high_captures_and_review` |  |  |  |  |  |  |  |  |
| `colorado_river_grand_canyon_rowing` / `hash_locked_evidence_green_tests_commit_push` |  |  |  |  |  |  |  |  |
| `pacuare_river_costa_rica` / `full_corridor_stationing_flow_bands` |  |  |  |  |  |  |  |  |
| `pacuare_river_costa_rica` / `catalog_rapid_stationing_feature_inventory_and_runs` |  |  |  |  |  |  |  |  |
| `pacuare_river_costa_rica` / `photoreal_assets_nanite_lumen_vsm_e2_performance` |  |  |  |  |  |  |  |  |
| `pacuare_river_costa_rica` / `flexible_raft_mechanics_and_reapproved_outcomes` |  |  |  |  |  |  |  |  |
| `pacuare_river_costa_rica` / `lifelike_low_reference_high_captures_and_review` |  |  |  |  |  |  |  |  |
| `pacuare_river_costa_rica` / `hash_locked_evidence_green_tests_commit_push` |  |  |  |  |  |  |  |  |
| `futaleufu_river_chile` / `full_corridor_stationing_flow_bands` |  |  |  |  |  |  |  |  |
| `futaleufu_river_chile` / `catalog_rapid_stationing_feature_inventory_and_runs` |  |  |  |  |  |  |  |  |
| `futaleufu_river_chile` / `photoreal_assets_nanite_lumen_vsm_e2_performance` |  |  |  |  |  |  |  |  |
| `futaleufu_river_chile` / `flexible_raft_mechanics_and_reapproved_outcomes` |  |  |  |  |  |  |  |  |
| `futaleufu_river_chile` / `lifelike_low_reference_high_captures_and_review` |  |  |  |  |  |  |  |  |
| `futaleufu_river_chile` / `hash_locked_evidence_green_tests_commit_push` |  |  |  |  |  |  |  |  |
| `chilko_river_lava_canyon` / `full_corridor_stationing_flow_bands` |  |  |  |  |  |  |  |  |
| `chilko_river_lava_canyon` / `catalog_rapid_stationing_feature_inventory_and_runs` |  |  |  |  |  |  |  |  |
| `chilko_river_lava_canyon` / `photoreal_assets_nanite_lumen_vsm_e2_performance` |  |  |  |  |  |  |  |  |
| `chilko_river_lava_canyon` / `flexible_raft_mechanics_and_reapproved_outcomes` |  |  |  |  |  |  |  |  |
| `chilko_river_lava_canyon` / `lifelike_low_reference_high_captures_and_review` |  |  |  |  |  |  |  |  |
| `chilko_river_lava_canyon` / `hash_locked_evidence_green_tests_commit_push` |  |  |  |  |  |  |  |  |

## Current Blocker Summary

| River | Criterion id | Blocker count | Missing source artifact count | Source artifacts |
| --- | --- | --- | --- | --- |
| `american_south_fork` | `full_corridor_stationing_flow_bands` | 11 | 0 | `physics/data/real_world/south_fork_american_chili_bar/review/a1_completion_readiness_report.json` |
| `american_south_fork` | `catalog_rapid_stationing_feature_inventory_and_runs` | 26 | 0 | `physics/data/real_world/south_fork_american_chili_bar/review/a1_completion_readiness_report.json`, `physics/data/real_world/named_rapid_editor_pin_completion_readiness_report.json`, `physics/data/real_world/named_rapid_water_window_completion_readiness_report.json`, `physics/data/real_world/named_rapid_simulator_review_completion_readiness_report.json` |
| `american_south_fork` | `photoreal_assets_nanite_lumen_vsm_e2_performance` | 7 | 0 | `physics/data/real_world/south_fork_american_chili_bar/asset_intake/south_fork_b2_completion_readiness_report.json`, `physics/data/real_world/e1_platform_matrix_decision_validation_report.json`, `physics/data/real_world/e2_scalability_profile_parity_validation_report.json` |
| `american_south_fork` | `flexible_raft_mechanics_and_reapproved_outcomes` | 10 | 0 | `physics/data/calibration/flexible_raft_d6_completion_readiness_report.json`, `physics/data/real_world/named_rapid_flexible_raft_rerun_completion_readiness_report.json` |
| `american_south_fork` | `lifelike_low_reference_high_captures_and_review` | 31 | 0 | `physics/data/real_world/south_fork_american_chili_bar/review/a1_completion_readiness_report.json`, `physics/data/real_world/south_fork_american_chili_bar/asset_intake/south_fork_b2_completion_readiness_report.json`, `physics/data/real_world/named_rapid_simulator_review_completion_readiness_report.json`, `physics/data/real_world/named_rapid_flexible_raft_rerun_completion_readiness_report.json`, `physics/data/real_world/e3_packaged_runtime_validation_report.json` |
| `american_south_fork` | `hash_locked_evidence_green_tests_commit_push` | 46 | 0 | `physics/data/real_world/five_river_photoreal_execution_plan_readiness_report.json`, `physics/data/real_world/five_river_photoreal_external_action_queue.json`, `physics/data/real_world/e1_platform_matrix_decision_validation_report.json`, `physics/data/real_world/e2_scalability_profile_parity_validation_report.json`, `physics/data/real_world/e3_packaged_runtime_validation_report.json` |
| `colorado_river_grand_canyon_rowing` | `full_corridor_stationing_flow_bands` | 12 | 0 | `physics/data/real_world/colorado_river_grand_canyon_rowing/review/a2_completion_readiness_report.json` |
| `colorado_river_grand_canyon_rowing` | `catalog_rapid_stationing_feature_inventory_and_runs` | 27 | 0 | `physics/data/real_world/colorado_river_grand_canyon_rowing/review/a2_completion_readiness_report.json`, `physics/data/real_world/named_rapid_editor_pin_completion_readiness_report.json`, `physics/data/real_world/named_rapid_water_window_completion_readiness_report.json`, `physics/data/real_world/named_rapid_simulator_review_completion_readiness_report.json` |
| `colorado_river_grand_canyon_rowing` | `photoreal_assets_nanite_lumen_vsm_e2_performance` | 7 | 0 | `physics/data/real_world/colorado_river_grand_canyon_rowing/asset_intake/colorado_b2_completion_readiness_report.json`, `physics/data/real_world/e1_platform_matrix_decision_validation_report.json`, `physics/data/real_world/e2_scalability_profile_parity_validation_report.json` |
| `colorado_river_grand_canyon_rowing` | `flexible_raft_mechanics_and_reapproved_outcomes` | 10 | 0 | `physics/data/calibration/flexible_raft_d6_completion_readiness_report.json`, `physics/data/real_world/named_rapid_flexible_raft_rerun_completion_readiness_report.json` |
| `colorado_river_grand_canyon_rowing` | `lifelike_low_reference_high_captures_and_review` | 32 | 0 | `physics/data/real_world/colorado_river_grand_canyon_rowing/review/a2_completion_readiness_report.json`, `physics/data/real_world/colorado_river_grand_canyon_rowing/asset_intake/colorado_b2_completion_readiness_report.json`, `physics/data/real_world/named_rapid_simulator_review_completion_readiness_report.json`, `physics/data/real_world/named_rapid_flexible_raft_rerun_completion_readiness_report.json`, `physics/data/real_world/e3_packaged_runtime_validation_report.json` |
| `colorado_river_grand_canyon_rowing` | `hash_locked_evidence_green_tests_commit_push` | 47 | 0 | `physics/data/real_world/five_river_photoreal_execution_plan_readiness_report.json`, `physics/data/real_world/five_river_photoreal_external_action_queue.json`, `physics/data/real_world/e1_platform_matrix_decision_validation_report.json`, `physics/data/real_world/e2_scalability_profile_parity_validation_report.json`, `physics/data/real_world/e3_packaged_runtime_validation_report.json` |
| `pacuare_river_costa_rica` | `full_corridor_stationing_flow_bands` | 8 | 0 | `physics/data/real_world/pacuare_river_costa_rica/review/a3_completion_readiness_report.json` |
| `pacuare_river_costa_rica` | `catalog_rapid_stationing_feature_inventory_and_runs` | 23 | 0 | `physics/data/real_world/pacuare_river_costa_rica/review/a3_completion_readiness_report.json`, `physics/data/real_world/named_rapid_editor_pin_completion_readiness_report.json`, `physics/data/real_world/named_rapid_water_window_completion_readiness_report.json`, `physics/data/real_world/named_rapid_simulator_review_completion_readiness_report.json` |
| `pacuare_river_costa_rica` | `photoreal_assets_nanite_lumen_vsm_e2_performance` | 7 | 0 | `physics/data/real_world/pacuare_river_costa_rica/asset_intake/pacuare_b2_completion_readiness_report.json`, `physics/data/real_world/e1_platform_matrix_decision_validation_report.json`, `physics/data/real_world/e2_scalability_profile_parity_validation_report.json` |
| `pacuare_river_costa_rica` | `flexible_raft_mechanics_and_reapproved_outcomes` | 10 | 0 | `physics/data/calibration/flexible_raft_d6_completion_readiness_report.json`, `physics/data/real_world/named_rapid_flexible_raft_rerun_completion_readiness_report.json` |
| `pacuare_river_costa_rica` | `lifelike_low_reference_high_captures_and_review` | 28 | 0 | `physics/data/real_world/pacuare_river_costa_rica/review/a3_completion_readiness_report.json`, `physics/data/real_world/pacuare_river_costa_rica/asset_intake/pacuare_b2_completion_readiness_report.json`, `physics/data/real_world/named_rapid_simulator_review_completion_readiness_report.json`, `physics/data/real_world/named_rapid_flexible_raft_rerun_completion_readiness_report.json`, `physics/data/real_world/e3_packaged_runtime_validation_report.json` |
| `pacuare_river_costa_rica` | `hash_locked_evidence_green_tests_commit_push` | 43 | 0 | `physics/data/real_world/five_river_photoreal_execution_plan_readiness_report.json`, `physics/data/real_world/five_river_photoreal_external_action_queue.json`, `physics/data/real_world/e1_platform_matrix_decision_validation_report.json`, `physics/data/real_world/e2_scalability_profile_parity_validation_report.json`, `physics/data/real_world/e3_packaged_runtime_validation_report.json` |
| `futaleufu_river_chile` | `full_corridor_stationing_flow_bands` | 9 | 0 | `physics/data/real_world/futaleufu_river_chile/review/a4_completion_readiness_report.json` |
| `futaleufu_river_chile` | `catalog_rapid_stationing_feature_inventory_and_runs` | 24 | 0 | `physics/data/real_world/futaleufu_river_chile/review/a4_completion_readiness_report.json`, `physics/data/real_world/named_rapid_editor_pin_completion_readiness_report.json`, `physics/data/real_world/named_rapid_water_window_completion_readiness_report.json`, `physics/data/real_world/named_rapid_simulator_review_completion_readiness_report.json` |
| `futaleufu_river_chile` | `photoreal_assets_nanite_lumen_vsm_e2_performance` | 7 | 0 | `physics/data/real_world/futaleufu_river_chile/asset_intake/futaleufu_b2_completion_readiness_report.json`, `physics/data/real_world/e1_platform_matrix_decision_validation_report.json`, `physics/data/real_world/e2_scalability_profile_parity_validation_report.json` |
| `futaleufu_river_chile` | `flexible_raft_mechanics_and_reapproved_outcomes` | 10 | 0 | `physics/data/calibration/flexible_raft_d6_completion_readiness_report.json`, `physics/data/real_world/named_rapid_flexible_raft_rerun_completion_readiness_report.json` |
| `futaleufu_river_chile` | `lifelike_low_reference_high_captures_and_review` | 29 | 0 | `physics/data/real_world/futaleufu_river_chile/review/a4_completion_readiness_report.json`, `physics/data/real_world/futaleufu_river_chile/asset_intake/futaleufu_b2_completion_readiness_report.json`, `physics/data/real_world/named_rapid_simulator_review_completion_readiness_report.json`, `physics/data/real_world/named_rapid_flexible_raft_rerun_completion_readiness_report.json`, `physics/data/real_world/e3_packaged_runtime_validation_report.json` |
| `futaleufu_river_chile` | `hash_locked_evidence_green_tests_commit_push` | 44 | 0 | `physics/data/real_world/five_river_photoreal_execution_plan_readiness_report.json`, `physics/data/real_world/five_river_photoreal_external_action_queue.json`, `physics/data/real_world/e1_platform_matrix_decision_validation_report.json`, `physics/data/real_world/e2_scalability_profile_parity_validation_report.json`, `physics/data/real_world/e3_packaged_runtime_validation_report.json` |
| `chilko_river_lava_canyon` | `full_corridor_stationing_flow_bands` | 10 | 0 | `physics/data/real_world/chilko_river_bc/review/a5_completion_readiness_report.json` |
| `chilko_river_lava_canyon` | `catalog_rapid_stationing_feature_inventory_and_runs` | 25 | 0 | `physics/data/real_world/chilko_river_bc/review/a5_completion_readiness_report.json`, `physics/data/real_world/named_rapid_editor_pin_completion_readiness_report.json`, `physics/data/real_world/named_rapid_water_window_completion_readiness_report.json`, `physics/data/real_world/named_rapid_simulator_review_completion_readiness_report.json` |
| `chilko_river_lava_canyon` | `photoreal_assets_nanite_lumen_vsm_e2_performance` | 7 | 0 | `physics/data/real_world/chilko_river_lava_canyon/asset_intake/chilko_b2_completion_readiness_report.json`, `physics/data/real_world/e1_platform_matrix_decision_validation_report.json`, `physics/data/real_world/e2_scalability_profile_parity_validation_report.json` |
| `chilko_river_lava_canyon` | `flexible_raft_mechanics_and_reapproved_outcomes` | 10 | 0 | `physics/data/calibration/flexible_raft_d6_completion_readiness_report.json`, `physics/data/real_world/named_rapid_flexible_raft_rerun_completion_readiness_report.json` |
| `chilko_river_lava_canyon` | `lifelike_low_reference_high_captures_and_review` | 30 | 0 | `physics/data/real_world/chilko_river_bc/review/a5_completion_readiness_report.json`, `physics/data/real_world/chilko_river_lava_canyon/asset_intake/chilko_b2_completion_readiness_report.json`, `physics/data/real_world/named_rapid_simulator_review_completion_readiness_report.json`, `physics/data/real_world/named_rapid_flexible_raft_rerun_completion_readiness_report.json`, `physics/data/real_world/e3_packaged_runtime_validation_report.json` |
| `chilko_river_lava_canyon` | `hash_locked_evidence_green_tests_commit_push` | 45 | 0 | `physics/data/real_world/five_river_photoreal_execution_plan_readiness_report.json`, `physics/data/real_world/five_river_photoreal_external_action_queue.json`, `physics/data/real_world/e1_platform_matrix_decision_validation_report.json`, `physics/data/real_world/e2_scalability_profile_parity_validation_report.json`, `physics/data/real_world/e3_packaged_runtime_validation_report.json` |

## Post-Review Commands

1. `python physics/src/raftsim/examples/generate_five_river_definition_of_done.py --repo-root .`
2. `python physics/src/raftsim/examples/validate_five_river_definition_of_done_evidence.py --repo-root . --sidecar <filled-five-river-dod-evidence-sidecar.json> --matrix <green-five-river-dod-matrix.json> --output <accepted-five-river-dod-evidence-sidecar.json> --report <five-river-dod-validation-report.json>`
3. `UV_CACHE_DIR=/private/tmp/raftsim-uv-cache PYTHONPATH=physics/src uv run pytest -q physics/tests`
4. `python physics/src/raftsim/examples/generate_five_river_photoreal_evidence_handoff.py --repo-root .`
5. `python physics/src/raftsim/examples/generate_five_river_photoreal_blocker_closure_matrix.py --repo-root .`
6. `python physics/src/raftsim/examples/generate_five_river_photoreal_external_action_queue.py --repo-root .`
7. `python physics/src/raftsim/examples/generate_five_river_photoreal_external_review_runbook.py --repo-root .`

## Promotion Guardrails

- `may_mark_any_river_complete_from_this_matrix_alone`: False
- `may_mark_execution_plan_complete_from_this_matrix_alone`: False
- `may_claim_photoreal_or_playable_release`: False
- `reason`: This matrix summarizes the explicit Definition of Done and links each river criterion to existing readiness, action, and platform gates. It does not replace reviewed sidecars, source assets, measured physics outputs, lifelike captures, human approvals, green tests, commits, or pushes.
- `can_start_manual_completion_review`: False
- `can_mark_any_river_complete_from_sidecar_alone`: False
- `can_mark_execution_plan_complete_from_sidecar_alone`: False
- `can_replace_source_data_review`: False
- `can_replace_physics_or_platform_validation`: False
- `can_replace_human_lifelike_review`: False
- `can_replace_tests_commits_or_pushes`: False

## Owner Completion Review

The owner completion review starts only after the source matrix and evidence sidecar are both green.

1. run the full physics and Unreal/editor validation suites referenced by the evidence
2. verify the recorded commit and push identifiers exist on the intended remotes
3. perform the manual owner completion review for each river
4. update plan checkboxes only after the reviewed source matrix and sidecar are both green

- Owner reviewer:
- Review date:
- Accepted river ids:
- Rejected or reopened river ids:
- Final matrix path + SHA-256:
- Final evidence sidecar path + SHA-256:
- Validation report path + SHA-256:
- Plan checkbox update commit id:
- Push record:
- Notes:

## Completion Rule

1. the source Definition of Done matrix reports all 30 criteria complete
2. every river/criterion row records complete_reviewed status
3. every criterion links hash-locked evidence artifacts
4. every required reviewer role signs each criterion
5. green test, commit, and push evidence is recorded for each river
6. the validation report is green before any manual plan checkbox update
