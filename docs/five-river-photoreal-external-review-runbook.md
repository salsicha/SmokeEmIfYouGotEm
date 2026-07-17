# Five-River Photoreal External Review Runbook

Generated: 2026-07-17

This runbook is a human-readable export of the fail-closed external action queue. It organizes the remaining manual review, source, asset, physics, platform, and final Definition of Done evidence without granting promotion by itself.

## Source Artifacts

- External action queue: `physics/data/real_world/five_river_photoreal_external_action_queue.json`
- Queue status: `five_river_external_action_queue_ready_pending_external_evidence`
- Source handoff packet: `physics/data/real_world/five_river_photoreal_evidence_handoff_packet.json`
- Source blocker matrix: `physics/data/real_world/five_river_photoreal_blocker_closure_matrix.json`

## Summary

- Action count: 13
- Evidence package count: 6
- Repo-ready action count: 13
- Tracked parent gate count: 15
- Blocked parent gate count: 15
- Readiness blocker count: 141
- Follow-up acceptance blocker count: 34
- Referenced artifact count: 132
- Referenced command count: 77
- Missing referenced path count: 0
- First action id: `01-A1-source-mile-access-decision`
- May mark execution plan complete: False

## Execution Rules

1. Complete actions in priority order unless an independent package has all prerequisites green.
2. Fill reviewed sidecars from source evidence; do not edit generated readiness or queue outputs by hand.
3. Regenerate each package validator after evidence is filled, then regenerate the aggregate queue.
4. Keep every parent gate closed until its own readiness report, follow-up acceptance gate, and required human review are green.
5. Treat the final Definition of Done evidence sidecar as a final audit only; it cannot bypass A/B/C/D/E gates.

## Package Queue

### A-route-stationing-flow-review

- First priority: 1
- Action count: 5
- Parent gates: `A1`, `A2`, `A3`, `A4`, `A5`
- Readiness blockers: 51
- Follow-up acceptance blockers: 34
- Repo ready for external work: True
- May mark any parent gate complete: False

### B-photoreal-asset-promotion

- First priority: 6
- Action count: 1
- Parent gates: `B2-south-fork`, `B2-colorado`, `B2-pacuare`, `B2-futaleufu`, `B2-chilko`
- Readiness blockers: 55
- Follow-up acceptance blockers: 0
- Repo ready for external work: True
- May mark any parent gate complete: False

### D-flexible-raft-external-validation

- First priority: 7
- Action count: 1
- Parent gates: `D6`
- Readiness blockers: 7
- Follow-up acceptance blockers: 0
- Repo ready for external work: True
- May mark any parent gate complete: False

### C-named-rapid-behavior-review

- First priority: 8
- Action count: 4
- Parent gates: `C2`, `C3`, `C4`, `C5`
- Readiness blockers: 28
- Follow-up acceptance blockers: 0
- Repo ready for external work: True
- May mark any parent gate complete: False

### E-platform-release-evidence

- First priority: 12
- Action count: 1
- Parent gates: `C5`
- Readiness blockers: 7
- Follow-up acceptance blockers: 0
- Repo ready for external work: True
- May mark any parent gate complete: False

### F-final-definition-of-done-evidence

- First priority: 13
- Action count: 1
- Parent gates: `A1`, `A2`, `A3`, `A4`, `A5`, `B2-south-fork`, `B2-colorado`, `B2-pacuare`, `B2-futaleufu`, `B2-chilko`, `D6`, `C2`, `C3`, `C4`, `C5`
- Readiness blockers: 141
- Follow-up acceptance blockers: 34
- Repo ready for external work: True
- May mark any parent gate complete: False


## Actions

### 01-A1-source-mile-access-decision

- Row id: `A1-source-mile-access-decision`
- Package: `A-route-stationing-flow-review`
- Evidence class: `human_and_domain_review`
- Parent gates: `A1`
- Parent gate count: 1
- Readiness blockers: 11
- Follow-up acceptance blockers: 9
- Status: `waiting_on_external_or_manual_evidence`
- Repo ready for external work: True
- May mark parent gate complete from action: False

**Owner Roles**

- owner
- South Fork guide or oarsman
- geospatial reviewer
- rights/publication reviewer

**Next Actions**

1. Use the non-authoritative recommendation packet to start review with split published-mile conventions, reviewed simulation stationing, and official_access_50927 as the endpoint candidate.
2. Use the reviewer briefing to compare source-mile/access options, evidence sources, required fields, and downstream regeneration commands.
3. Use the Markdown review form to collect the owner, guide/oarsman, geospatial, and rights/publication decision before copying accepted values into the JSON result.
4. Fill the source-mile/access decision result with the selected endpoint and station-axis policy.
5. Run the validator and regenerate the action packet only after all reviewer signoffs are present.
6. Regenerate downstream route, stationing, corridor windows, and solver-window actions from the accepted result.
7. Record post-decision acceptance evidence for regenerated outputs before asking A1 readiness to clear.

**Acceptance Requirements**

1. Reviewer decisions cite the briefing source artifacts and answer the endpoint, station-axis, publication-policy, and regeneration-scope questions.
2. The filled decision record is traceable to the Markdown review form or an equivalent signed review packet.
3. The decision validation report is green.
4. Regeneration actions are non-empty for every selected downstream scope.
5. The post-decision acceptance validation report is green for route/station-axis, corridor windows, rapid stationing, solver windows, flow windows, Unreal import, and final guide/geospatial/rights/owner acceptance.
6. The A1 readiness report no longer lists source-mile/access or post-decision regeneration blockers.

**Promotion Guardrails**

- Do not promote the current NHD-derived source-mile axis directly.
- Do not bind Meat Grinder or Troublemaker solver windows before regenerated exact geometry exists.

**Required Artifacts**

- `physics/data/real_world/south_fork_american_chili_bar/review/full_reach_source_mile_access_review_briefing.json`
- `docs/south-fork-a1-source-mile-access-review-form.md`
- `physics/data/real_world/south_fork_american_chili_bar/review/full_reach_source_mile_access_recommendation.json`
- `physics/data/real_world/south_fork_american_chili_bar/review/full_reach_source_mile_access_decision_result_template.json`
- `physics/data/real_world/south_fork_american_chili_bar/review/full_reach_source_mile_access_decision_validation_report.json`
- `physics/data/real_world/south_fork_american_chili_bar/review/full_reach_source_mile_access_regeneration_action_packet.json`
- `physics/data/real_world/south_fork_american_chili_bar/review/full_reach_post_decision_acceptance_sidecar_template.json`
- `physics/data/real_world/south_fork_american_chili_bar/review/full_reach_post_decision_acceptance_validation_report.json`
- `physics/data/real_world/south_fork_american_chili_bar/review/a1_completion_readiness_report.json`

**Command Paths**

- `physics/src/raftsim/examples/generate_south_fork_a1_source_mile_access_review_briefing.py`
- `physics/src/raftsim/examples/generate_south_fork_a1_source_mile_access_review_form.py`
- `physics/src/raftsim/examples/generate_south_fork_a1_source_mile_access_recommendation.py`
- `physics/src/raftsim/examples/validate_south_fork_a1_source_mile_access_decision_result.py`
- `physics/src/raftsim/examples/generate_south_fork_a1_source_mile_access_regeneration_actions.py`
- `physics/src/raftsim/examples/validate_south_fork_a1_post_decision_acceptance.py`
- `physics/src/raftsim/examples/generate_south_fork_a1_readiness.py`

### 02-A2-centerline-rapid-mile-source-window-review

- Row id: `A2-centerline-rapid-mile-source-window-review`
- Package: `A-route-stationing-flow-review`
- Evidence class: `human_and_domain_review`
- Parent gates: `A2`
- Parent gate count: 1
- Readiness blockers: 13
- Follow-up acceptance blockers: 7
- Status: `waiting_on_external_or_manual_evidence`
- Repo ready for external work: True
- May mark parent gate complete from action: False

**Owner Roles**

- owner
- Grand Canyon oarsman
- geospatial reviewer
- NPS/USGS source reviewer
- rights/publication reviewer

**Next Actions**

1. Use the non-authoritative recommendation packet to start A2 review with official hydrography plus NPS/GCMRC river-mile calibration while keeping Pearce Ferry, CRS, source bboxes, and rapid miles reviewer-owned.
2. Use the reviewer briefing to answer the full-reach centerline, endpoint, CRS/station-axis, rapid-mile, bbox, publication, and regeneration-scope questions in one packet.
3. Use the Markdown review form to collect centerline/CRS, rapid-mile cross-check, source-window bbox, and publication decisions before copying accepted values into JSON review payloads.
4. Fill the centerline/CRS decision and rapid-mile cross-check sidecars from reviewed sources.
5. Fill and validate all 23 source-window bboxes before generating source-pull work orders.
6. Regenerate A2 readiness only after reviewed source decisions and source-pull status are updated.
7. Record post-review acceptance evidence for regenerated centerline, windows, stitched validation, rapid stationing, water windows, Unreal import, and final acceptance before asking A2 readiness to clear.

**Acceptance Requirements**

1. Reviewer decisions cite the A2 briefing source artifacts and answer the centerline, endpoint, station-axis, rapid-mile, bbox, publication, and regeneration-scope questions.
2. The filled centerline, rapid-mile, and bbox records are traceable to the Markdown review form or equivalent signed review packets.
3. Centerline/CRS, rapid-mile, and source-window bbox validators are green.
4. All 46 official source-pull rows have hash-locked outputs before source-window promotion.
5. The post-review acceptance validation report is green for full-reach centerline, window manifests, stitched validation, rapid stationing, rapid water windows, Unreal import, and oarsman/geospatial/rights/owner acceptance.
6. The A2 readiness report no longer blocks full-run centerline, bbox, rapid stationing, or source-pull promotion.

**Promotion Guardrails**

- Do not use the 4.7 km editor-binding limit as full Grand Canyon coverage.
- Do not download or import corridor sources from unreviewed bbox rows.

**Required Artifacts**

- `physics/data/real_world/colorado_river_grand_canyon_rowing/review/full_reach_review_briefing.json`
- `docs/colorado-a2-full-reach-review-form.md`
- `physics/data/real_world/colorado_river_grand_canyon_rowing/review/full_reach_review_recommendation.json`
- `physics/data/real_world/colorado_river_grand_canyon_rowing/review/full_reach_centerline_decision_template.json`
- `physics/data/real_world/colorado_river_grand_canyon_rowing/review/full_reach_centerline_decision_validation_report.json`
- `physics/data/real_world/colorado_river_grand_canyon_rowing/review/full_reach_rapid_mile_crosscheck_template.json`
- `physics/data/real_world/colorado_river_grand_canyon_rowing/review/full_reach_rapid_mile_crosscheck_validation_report.json`
- `physics/data/real_world/colorado_river_grand_canyon_rowing/production_corridor/full_reach_source_window_bbox_template.json`
- `physics/data/real_world/colorado_river_grand_canyon_rowing/production_corridor/full_reach_source_window_bbox_validation_report.json`
- `physics/data/real_world/colorado_river_grand_canyon_rowing/review/full_reach_regeneration_action_packet.json`
- `physics/data/real_world/colorado_river_grand_canyon_rowing/production_corridor/full_reach_window_source_pull_work_order.json`
- `physics/data/real_world/colorado_river_grand_canyon_rowing/production_corridor/full_reach_window_source_pull_status.json`
- `physics/data/real_world/colorado_river_grand_canyon_rowing/review/full_reach_post_review_acceptance_sidecar_template.json`
- `physics/data/real_world/colorado_river_grand_canyon_rowing/review/full_reach_post_review_acceptance_validation_report.json`
- `physics/data/real_world/colorado_river_grand_canyon_rowing/review/a2_completion_readiness_report.json`

**Command Paths**

- `physics/src/raftsim/examples/generate_colorado_a2_review_briefing.py`
- `physics/src/raftsim/examples/generate_colorado_a2_review_form.py`
- `physics/src/raftsim/examples/generate_colorado_a2_review_recommendation.py`
- `physics/src/raftsim/examples/validate_colorado_a2_centerline_decision.py`
- `physics/src/raftsim/examples/validate_colorado_a2_rapid_mile_crosscheck.py`
- `physics/src/raftsim/examples/validate_colorado_a2_source_window_bboxes.py`
- `physics/src/raftsim/examples/generate_colorado_a2_source_pull_work_order.py`
- `physics/src/raftsim/examples/generate_colorado_a2_source_pull_status.py`
- `physics/src/raftsim/examples/validate_colorado_a2_post_review_acceptance.py`
- `physics/src/raftsim/examples/generate_colorado_a2_readiness.py`

### 03-A3-pacuare-stationing-flow-review

- Row id: `A3-pacuare-stationing-flow-review`
- Package: `A-route-stationing-flow-review`
- Evidence class: `human_and_domain_review`
- Parent gates: `A3`
- Parent gate count: 1
- Readiness blockers: 8
- Follow-up acceptance blockers: 5
- Status: `waiting_on_external_or_manual_evidence`
- Repo ready for external work: True
- May mark parent gate complete from action: False

**Owner Roles**

- owner
- Pacuare guide
- geospatial reviewer
- hydrology/source reviewer
- rights/publication reviewer

**Next Actions**

1. Use the non-authoritative recommendation packet to start A3 review with reviewed-route/aerial digitizing for stationing and source-class flow evidence before numeric tuning.
2. Use the reviewer briefing to answer the Pacuare route authority, aerial source, rapid geometry, guide confirmation, flow-source, flash-response, publication, and regeneration-scope questions.
3. Replace provisional rapid order with reviewed GPS/aerial/guide stationing.
4. Attach reviewed source-class flow-band evidence and acceptance signoffs.
5. Regenerate stationing, editor markers, water-window inputs, and readiness from the accepted records.
6. Record post-review acceptance evidence for regenerated stationing, editor markers, flow source classes, water windows, solver validation, Unreal import, and final guide/geospatial/rights/hazard/owner acceptance.

**Acceptance Requirements**

1. Reviewer decisions cite the A3 briefing source artifacts and answer the route, aerial, rapid-geometry, guide, flow, flash-response, publication, and regeneration-scope questions.
2. Stationing and flow validators are green.
3. The regeneration action packet authorizes all required downstream Pacuare outputs.
4. The post-review acceptance validation report is green for regenerated stationing, catalog/editor outputs, source-class flow presets, rapid water windows, C++ solver validation, Unreal import, and final acceptance.
5. A3 readiness no longer lists provisional-order, flow-source, or post-review blockers.

**Promotion Guardrails**

- Do not promote downstream-order interpolation as exact geometry.
- Do not generate C3 water windows from unreviewed Pacuare stationing.

**Required Artifacts**

- `physics/data/real_world/pacuare_river_costa_rica/review/a3_review_briefing.json`
- `physics/data/real_world/pacuare_river_costa_rica/review/a3_review_recommendation.json`
- `physics/data/real_world/pacuare_river_costa_rica/review/a3_stationing_digitizing_result_template.json`
- `physics/data/real_world/pacuare_river_costa_rica/review/a3_stationing_digitizing_validation_report.json`
- `physics/data/real_world/pacuare_river_costa_rica/review/a3_flow_source_result_template.json`
- `physics/data/real_world/pacuare_river_costa_rica/review/a3_flow_source_validation_report.json`
- `physics/data/real_world/pacuare_river_costa_rica/review/a3_regeneration_action_packet.json`
- `physics/data/real_world/pacuare_river_costa_rica/review/a3_post_review_acceptance_sidecar_template.json`
- `physics/data/real_world/pacuare_river_costa_rica/review/a3_post_review_acceptance_validation_report.json`
- `physics/data/real_world/pacuare_river_costa_rica/review/a3_completion_readiness_report.json`

**Command Paths**

- `physics/src/raftsim/examples/generate_pacuare_a3_review_briefing.py`
- `physics/src/raftsim/examples/generate_pacuare_a3_review_recommendation.py`
- `physics/src/raftsim/examples/validate_pacuare_a3_digitizing_result.py`
- `physics/src/raftsim/examples/validate_pacuare_a3_flow_source_result.py`
- `physics/src/raftsim/examples/generate_pacuare_a3_regeneration_actions.py`
- `physics/src/raftsim/examples/validate_pacuare_a3_post_review_acceptance.py`
- `physics/src/raftsim/examples/generate_pacuare_a3_readiness.py`

### 04-A4-futaleufu-stationing-flow-review

- Row id: `A4-futaleufu-stationing-flow-review`
- Package: `A-route-stationing-flow-review`
- Evidence class: `human_and_domain_review`
- Parent gates: `A4`
- Parent gate count: 1
- Readiness blockers: 9
- Follow-up acceptance blockers: 6
- Status: `waiting_on_external_or_manual_evidence`
- Repo ready for external work: True
- May mark parent gate complete from action: False

**Owner Roles**

- owner
- Futaleufu guide
- geospatial reviewer
- DGA/hydrology source reviewer
- rights/publication reviewer

**Next Actions**

1. Use the non-authoritative recommendation packet to start A4 review with a reviewed route station axis, GPS/aerial rapid geometry, and DGA time-series route translation before numeric tuning.
2. Use the reviewer briefing to answer the Futaleufu route-axis, GPS/aerial rapid geometry, DGA route-translation, unsafe-high-water, publication, and regeneration-scope questions.
3. Replace provisional Futaleufu rapid stationing with reviewed point/span geometry.
4. Attach reviewed DGA flow-band evidence and signoffs.
5. Regenerate route outputs, editor markers, water-window inputs, and readiness after validation.
6. Record post-review acceptance evidence for regenerated stationing, editor markers, DGA source classes, water windows, unsafe high-water safety, solver validation, Unreal import, and final guide/geospatial/rights/hazard/owner acceptance.

**Acceptance Requirements**

1. Reviewer decisions cite the A4 briefing source artifacts and answer the route-axis, rapid-geometry, guide, DGA, unsafe-high-water, publication, and regeneration-scope questions.
2. Stationing and flow validators are green.
3. The action packet authorizes all required downstream Futaleufu outputs.
4. The post-review acceptance validation report is green for regenerated stationing, catalog/editor outputs, DGA source-class presets, rapid water windows, unsafe high-water safety, C++ solver validation, Unreal import, and final acceptance.
5. A4 readiness no longer lists provisional-order, DGA-flow, or regeneration blockers.

**Promotion Guardrails**

- Do not promote generated corridor geometry before exact stationing is reviewed.
- Do not substitute visual canopy work for accepted hydrology and rapid geometry.

**Required Artifacts**

- `physics/data/real_world/futaleufu_river_chile/review/a4_review_briefing.json`
- `physics/data/real_world/futaleufu_river_chile/review/a4_review_recommendation.json`
- `physics/data/real_world/futaleufu_river_chile/review/a4_stationing_digitizing_result_template.json`
- `physics/data/real_world/futaleufu_river_chile/review/a4_stationing_digitizing_validation_report.json`
- `physics/data/real_world/futaleufu_river_chile/review/a4_flow_source_result_template.json`
- `physics/data/real_world/futaleufu_river_chile/review/a4_flow_source_validation_report.json`
- `physics/data/real_world/futaleufu_river_chile/review/a4_regeneration_action_packet.json`
- `physics/data/real_world/futaleufu_river_chile/review/a4_post_review_acceptance_sidecar_template.json`
- `physics/data/real_world/futaleufu_river_chile/review/a4_post_review_acceptance_validation_report.json`
- `physics/data/real_world/futaleufu_river_chile/review/a4_completion_readiness_report.json`

**Command Paths**

- `physics/src/raftsim/examples/generate_futaleufu_a4_review_briefing.py`
- `physics/src/raftsim/examples/generate_futaleufu_a4_review_recommendation.py`
- `physics/src/raftsim/examples/validate_futaleufu_a4_digitizing_result.py`
- `physics/src/raftsim/examples/validate_futaleufu_a4_flow_source_result.py`
- `physics/src/raftsim/examples/generate_futaleufu_a4_regeneration_actions.py`
- `physics/src/raftsim/examples/validate_futaleufu_a4_post_review_acceptance.py`
- `physics/src/raftsim/examples/generate_futaleufu_a4_readiness.py`

### 05-A5-chilko-stationing-flow-review

- Row id: `A5-chilko-stationing-flow-review`
- Package: `A-route-stationing-flow-review`
- Evidence class: `human_and_domain_review`
- Parent gates: `A5`
- Parent gate count: 1
- Readiness blockers: 10
- Follow-up acceptance blockers: 7
- Status: `waiting_on_external_or_manual_evidence`
- Repo ready for external work: True
- May mark parent gate complete from action: False

**Owner Roles**

- owner
- Chilko guide
- geospatial reviewer
- Water Survey of Canada source reviewer
- rights/publication reviewer

**Next Actions**

1. Use the non-authoritative recommendation packet to start A5 review with exact endpoint geometry, a reviewed route station axis, GPS/aerial rapid geometry, and 08MA002 daily-window routing with 08MA001 context before numeric tuning.
2. Use the reviewer briefing to answer the Chilko route/endpoint, rapid geometry, guide, 08MA002 routing, 08MA001 context, unsafe/washout, land/publication, and regeneration-scope questions.
3. Approve exact put-in/take-out geometry and priority rapid stationing.
4. Attach reviewed 08MA002 flow-window routing evidence and signoffs.
5. Regenerate route, source-window, editor, and water-window inputs after validation.
6. Record post-review acceptance evidence for regenerated stationing, endpoint/land publication, editor markers, 08MA source classes, water windows, unsafe/washout safety, solver validation, Unreal import, and final guide/geospatial/rights/land/hazard/owner acceptance.

**Acceptance Requirements**

1. Reviewer decisions cite the A5 briefing source artifacts and answer the route/endpoint, rapid-geometry, guide, 08MA002/08MA001, unsafe/washout, land/publication, and regeneration-scope questions.
2. Stationing and flow validators are green.
3. Regeneration actions cover the Chilko corridor and all priority rapid outputs.
4. The post-review acceptance validation report is green for regenerated stationing, endpoint/land-publication approval, catalog/editor outputs, 08MA flow source classes, rapid water windows, unsafe/washout safety, C++ solver validation, Unreal import, and final acceptance.
5. A5 readiness no longer lists exact-geometry, flow-source, or regeneration blockers.

**Promotion Guardrails**

- Do not promote provisional downstream-order stationing.
- Do not capture Chilko flow variants before exact stationing and gauge routing pass.

**Required Artifacts**

- `physics/data/real_world/chilko_river_bc/review/a5_review_briefing.json`
- `physics/data/real_world/chilko_river_bc/review/a5_review_recommendation.json`
- `physics/data/real_world/chilko_river_bc/review/a5_stationing_digitizing_result_template.json`
- `physics/data/real_world/chilko_river_bc/review/a5_stationing_digitizing_validation_report.json`
- `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json`
- `physics/data/real_world/chilko_river_bc/review/a5_flow_source_validation_report.json`
- `physics/data/real_world/chilko_river_bc/review/a5_regeneration_action_packet.json`
- `physics/data/real_world/chilko_river_bc/review/a5_post_review_acceptance_sidecar_template.json`
- `physics/data/real_world/chilko_river_bc/review/a5_post_review_acceptance_validation_report.json`
- `physics/data/real_world/chilko_river_bc/review/a5_completion_readiness_report.json`

**Command Paths**

- `physics/src/raftsim/examples/generate_chilko_a5_review_briefing.py`
- `physics/src/raftsim/examples/generate_chilko_a5_review_recommendation.py`
- `physics/src/raftsim/examples/validate_chilko_a5_digitizing_result.py`
- `physics/src/raftsim/examples/validate_chilko_a5_flow_source_result.py`
- `physics/src/raftsim/examples/generate_chilko_a5_regeneration_actions.py`
- `physics/src/raftsim/examples/validate_chilko_a5_post_review_acceptance.py`
- `physics/src/raftsim/examples/generate_chilko_a5_readiness.py`

### 06-B2-five-river-asset-source-import-review

- Row id: `B2-five-river-asset-source-import-review`
- Package: `B-photoreal-asset-promotion`
- Evidence class: `source_hash_import_capture_review`
- Parent gates: `B2-south-fork`, `B2-colorado`, `B2-pacuare`, `B2-futaleufu`, `B2-chilko`
- Parent gate count: 5
- Readiness blockers: 55
- Follow-up acceptance blockers: 0
- Status: `waiting_on_external_or_manual_evidence`
- Repo ready for external work: True
- May mark parent gate complete from action: False

**Owner Roles**

- asset acquisition owner
- technical artist
- ecology or guide reviewer
- rights reviewer
- performance reviewer
- owner

**Next Actions**

1. Use the non-authoritative recommendation packet to start B2 review with a local-only hash-report workflow, first-party iteration assets, and per-river promotion blocked until source hashes, Unreal captures, domain reviews, and performance evidence pass.
2. Use the B2 reviewer briefing to answer storage policy, exact source selection, acquisition evidence, hashes, import/capture evidence, per-river promotion, corridor-substitution, post-review, and release-limit questions.
3. Approve storage/download policy before acquiring local-only or large binary sources.
4. Record source acquisition selections, source hashes, Unreal import reports, isolated captures, and reviews.
5. Merge only validated source-hash, import/capture, and promotion-decision sidecars.

**Acceptance Requirements**

1. Reviewer decisions cite the B2 briefing source artifacts and answer the storage/source/acquisition/hash/import/promotion/substitution/post-review questions.
2. All selected source assets have reviewed provenance and hash records.
3. Every imported asset has an Unreal import report and hash-locked capture evidence.
4. Per-river B2 completion readiness reports allow promotion for the intended river.

**Promotion Guardrails**

- Do not commit local-only licensed binaries.
- Do not substitute shared corridor assets without explicit corridor-substitution approval.
- Do not mark any B2 river complete from missing source or capture evidence.

**Required Artifacts**

- `physics/data/real_world/photoreal_b2_review_briefing.json`
- `physics/data/real_world/photoreal_b2_review_recommendation.json`
- `physics/data/real_world/photoreal_b2_source_storage_decision_result_template.json`
- `physics/data/real_world/photoreal_b2_source_storage_decision_validation_report.json`
- `physics/data/real_world/photoreal_b2_source_acquisition_work_order.json`
- `physics/data/real_world/photoreal_b2_source_acquisition_selection_sidecar_template.json`
- `physics/data/real_world/photoreal_b2_source_acquisition_selection_validation_report.json`
- `physics/data/real_world/photoreal_b2_source_acquisition_result_sidecar_template.json`
- `physics/data/real_world/photoreal_b2_source_acquisition_result_validation_report.json`
- `physics/data/real_world/photoreal_b2_source_hash_report_template.json`
- `physics/data/real_world/photoreal_b2_source_hash_sidecar_template.json`
- `physics/data/real_world/photoreal_b2_source_hash_sidecar_merge_report.json`
- `physics/data/real_world/photoreal_b2_source_hash_validation_report.json`
- `physics/data/real_world/photoreal_b2_import_capture_review_sidecar_template.json`
- `physics/data/real_world/photoreal_b2_import_capture_review_sidecar_merge_report.json`
- `physics/data/real_world/photoreal_b2_import_capture_review_validation_report.json`
- `physics/data/real_world/photoreal_b2_asset_promotion_decision_sidecar_template.json`
- `physics/data/real_world/photoreal_b2_asset_promotion_decision_sidecar_merge_report.json`
- `physics/data/real_world/photoreal_b2_asset_promotion_decision_validation_report.json`
- `physics/data/real_world/photoreal_b2_corridor_substitution_work_order.json`
- `physics/data/real_world/photoreal_b2_corridor_substitution_result_sidecar_template.json`
- `physics/data/real_world/photoreal_b2_corridor_substitution_review_validation_report.json`
- `physics/data/real_world/photoreal_b2_asset_promotion_readiness_report.json`
- `physics/data/real_world/south_fork_american_chili_bar/asset_intake/south_fork_b2_completion_readiness_report.json`
- `physics/data/real_world/colorado_river_grand_canyon_rowing/asset_intake/colorado_b2_completion_readiness_report.json`
- `physics/data/real_world/pacuare_river_costa_rica/asset_intake/pacuare_b2_completion_readiness_report.json`
- `physics/data/real_world/futaleufu_river_chile/asset_intake/futaleufu_b2_completion_readiness_report.json`
- `physics/data/real_world/chilko_river_lava_canyon/asset_intake/chilko_b2_completion_readiness_report.json`

**Command Paths**

- `physics/src/raftsim/examples/generate_photoreal_b2_review_briefing.py`
- `physics/src/raftsim/examples/generate_photoreal_b2_review_recommendation.py`
- `physics/src/raftsim/examples/validate_photoreal_b2_source_storage_decision_result.py`
- `physics/src/raftsim/examples/validate_photoreal_b2_source_acquisition_selection.py`
- `physics/src/raftsim/examples/validate_photoreal_b2_source_acquisition_result.py`
- `physics/src/raftsim/examples/merge_photoreal_b2_source_hash_sidecar.py`
- `physics/src/raftsim/examples/merge_photoreal_b2_import_capture_review_sidecar.py`
- `physics/src/raftsim/examples/merge_photoreal_b2_asset_promotion_decision_sidecar.py`
- `physics/src/raftsim/examples/generate_photoreal_b2_asset_promotion_readiness.py`

### 07-D6-external-physics-measurements

- Row id: `D6-external-physics-measurements`
- Package: `D-flexible-raft-external-validation`
- Evidence class: `external_engine_measurements`
- Parent gates: `D6`
- Parent gate count: 1
- Readiness blockers: 7
- Follow-up acceptance blockers: 0
- Status: `waiting_on_external_or_manual_evidence`
- Repo ready for external work: True
- May mark parent gate complete from action: False

**Owner Roles**

- Project Chrono or compliant-reference implementer
- Unreal Chaos implementer
- physics reviewer
- replay reviewer
- guide/safety reviewer
- owner

**Next Actions**

1. Use the non-authoritative recommendation packet to run D6 as preflight, seven compliant-reference measurements, seven Chaos measurements, sidecar merges, regenerated comparison, and physics/Unreal/replay/guide-safety review before runtime authority.
2. Run the D6 measurement preflight before attempting sidecar merges or comparison regeneration.
3. Run the seven fixture inputs in both the compliant reference and Unreal Chaos.
4. Use the committed compliant-reference runner sidecar and summary paths as the Project Chrono/reviewed-model output handoff.
5. Use the committed Chaos runner sidecar and summary paths as the Unreal automation output handoff.
6. Record source reports, engine versions, 64-hex telemetry hashes, and required metric paths.
7. Merge both target sidecars and regenerate the D6 comparison and readiness reports.

**Acceptance Requirements**

1. All 14 target/fixture measured-result rows pass provenance validation.
2. The compliant-reference runner sidecar has real measured rows instead of the committed not_measured placeholders.
3. The Chaos runner sidecar has real measured rows instead of the committed not_measured placeholders.
4. The regenerated comparison report has no missing target pairs and passes numeric gates.
5. Physics, Unreal, replay, and guide/safety reviewers approve the D6 result.

**Promotion Guardrails**

- Do not satisfy D6 with Python-only fixture replay.
- Do not enable scoring-critical flexible-raft behavior before D6 and named-rapid review pass.

**Required Artifacts**

- `physics/data/calibration/flexible_raft_d6_measurement_recommendation.json`
- `physics/data/calibration/flexible_raft_d6_measurement_work_order.json`
- `physics/data/calibration/flexible_raft_d6_measurement_preflight.json`
- `physics/data/calibration/flexible_raft_d6_fixture_input_package.json`
- `physics/data/calibration/flexible_raft_d6_chaos_measured_results_sidecar_template.json`
- `physics/reports/d6/compliant/flexible_raft_d6_compliant_measured_results.json`
- `physics/reports/d6/compliant/summary.json`
- `physics/reports/d6/chaos/flexible_raft_d6_chaos_measured_results.json`
- `physics/reports/d6/chaos/summary.json`
- `physics/data/calibration/flexible_raft_d6_chaos_measured_results_merge_report.json`
- `physics/data/calibration/flexible_raft_d6_compliant_measured_results_sidecar_template.json`
- `physics/data/calibration/flexible_raft_d6_compliant_measured_results_merge_report.json`
- `physics/data/calibration/flexible_raft_d6_measured_results_template.json`
- `physics/data/calibration/flexible_raft_d6_comparison_report.json`
- `physics/data/calibration/flexible_raft_d6_completion_readiness_report.json`

**Command Paths**

- `physics/src/raftsim/examples/generate_flexible_raft_d6_measurement_recommendation.py`
- `physics/src/raftsim/examples/generate_flexible_raft_d6_measurement_preflight.py`
- `physics/src/raftsim/examples/generate_flexible_raft_d6_compliant_runner_export.py`
- `physics/src/raftsim/examples/generate_flexible_raft_d6_chaos_runner_export.py`
- `physics/src/raftsim/examples/merge_flexible_raft_d6_chaos_measured_results.py`
- `physics/src/raftsim/examples/merge_flexible_raft_d6_compliant_measured_results.py`
- `physics/src/raftsim/examples/generate_flexible_raft_d6_comparison_report.py`
- `physics/src/raftsim/examples/generate_flexible_raft_d6_readiness.py`

### 08-C1-C2-reviewed-subfeatures-editor-pins

- Row id: `C1-C2-reviewed-subfeatures-editor-pins`
- Package: `C-named-rapid-behavior-review`
- Evidence class: `named_rapid_water_and_behavior_evidence`
- Parent gates: `C2`
- Parent gate count: 1
- Readiness blockers: 7
- Follow-up acceptance blockers: 0
- Status: `waiting_on_external_or_manual_evidence`
- Repo ready for external work: True
- May mark parent gate complete from action: False

**Owner Roles**

- rapid research owner
- guide reviewer
- geospatial reviewer
- technical artist
- rights reviewer
- owner

**Next Actions**

1. Use the non-authoritative recommendation packet to start C2 review with South Fork Meat Grinder and Troublemaker first, keep Zambezi passive until Batoka source evidence exists, and preserve the C1/C2/C3/C4 gate boundaries.
2. Fill the reviewed subfeature inventory for each named rapid.
3. Generate editor pin packets from accepted C1 inventory only.
4. Record exact pin placements, captures, and required signoffs before regenerating the Unreal overlay.

**Acceptance Requirements**

1. The C1 sidecar merge report is green.
2. Exact placement sidecar is mergeable with capture and signoff evidence.
3. The Unreal subfeature overlay is regenerated from accepted placements and C2 readiness is green.

**Promotion Guardrails**

- Do not replace parent rapid markers from unreviewed subfeature rows.
- Do not bind C3 water windows from unreviewed editor pins.

**Required Artifacts**

- `physics/data/real_world/named_rapid_editor_pin_recommendation.json`
- `physics/data/real_world/named_rapid_feature_inventory_sidecar_template.json`
- `physics/data/real_world/named_rapid_feature_inventory_sidecar_merge_report.json`
- `physics/data/real_world/named_rapid_editor_pin_packet.json`
- `physics/data/real_world/named_rapid_editor_pin_placement_sidecar_template.json`
- `physics/data/real_world/named_rapid_editor_pin_placement_merge_report.json`
- `unreal/Content/RaftSim/River/named_rapid_subfeature_editor_pins.json`
- `physics/data/real_world/named_rapid_editor_pin_completion_readiness_report.json`

**Command Paths**

- `physics/src/raftsim/examples/generate_named_rapid_editor_pin_recommendation.py`
- `physics/src/raftsim/examples/merge_named_rapid_feature_inventory_sidecar.py`
- `physics/src/raftsim/examples/generate_named_rapid_editor_pin_packet.py`
- `physics/src/raftsim/examples/generate_named_rapid_editor_pin_placement.py`
- `physics/src/raftsim/examples/generate_named_rapid_subfeature_editor_pin_layer.py`
- `physics/src/raftsim/examples/generate_named_rapid_editor_pin_readiness.py`

### 09-C3-water-window-bindings

- Row id: `C3-water-window-bindings`
- Package: `C-named-rapid-behavior-review`
- Evidence class: `named_rapid_water_and_behavior_evidence`
- Parent gates: `C3`
- Parent gate count: 1
- Readiness blockers: 7
- Follow-up acceptance blockers: 0
- Status: `waiting_on_external_or_manual_evidence`
- Repo ready for external work: True
- May mark parent gate complete from action: False

**Owner Roles**

- water-window author
- water-solver reviewer
- GeoClaw or analytic parity reviewer
- guide reviewer
- owner

**Next Actions**

1. Use the non-authoritative recommendation packet to start C3 review with South Fork Meat Grinder and Troublemaker first, keep Zambezi passive until Batoka source evidence exists, and keep feature forcing off unless bounded, manifest-recorded, compared, and not hiding conservation failures.
2. Bind exact rapid geometry and reviewed C2 subfeatures to reach-local water-window scenarios.
3. Attach stitched validation, C++/GeoClaw-or-analytic comparisons, conservation, raft-coupling, flow-source, and forcing manifests.
4. Regenerate the C3 validation and readiness reports after each accepted binding batch.

**Acceptance Requirements**

1. Every intended binding has exact geometry, reviewed pins, and stitched validation output.
2. C++ water evidence passes the required parity, conservation, and raft-coupling gates.
3. C3 readiness no longer blocks C4 review-run preparation.

**Promotion Guardrails**

- Do not hide physics failures with feature forcing.
- Do not prepare C4 simulator runs from invalid C3 bindings.

**Required Artifacts**

- `physics/data/real_world/named_rapid_water_window_recommendation.json`
- `physics/data/real_world/named_rapid_water_window_binding_template.json`
- `physics/data/real_world/named_rapid_water_window_binding_validation_report.json`
- `physics/data/real_world/named_rapid_water_window_completion_readiness_report.json`
- `unreal/Content/RaftSim/River/named_rapid_subfeature_editor_pins.json`

**Command Paths**

- `physics/src/raftsim/examples/generate_named_rapid_water_window_recommendation.py`
- `physics/src/raftsim/examples/generate_named_rapid_water_window_binding.py`
- `physics/src/raftsim/examples/generate_named_rapid_water_window_readiness.py`

### 10-C4-simulator-output-behavior-review

- Row id: `C4-simulator-output-behavior-review`
- Package: `C-named-rapid-behavior-review`
- Evidence class: `named_rapid_water_and_behavior_evidence`
- Parent gates: `C4`
- Parent gate count: 1
- Readiness blockers: 7
- Follow-up acceptance blockers: 0
- Status: `waiting_on_external_or_manual_evidence`
- Repo ready for external work: True
- May mark parent gate complete from action: False

**Owner Roles**

- simulator runner
- guide reviewer
- visual reviewer
- technical reviewer
- rights reviewer
- owner

**Next Actions**

1. Use the non-authoritative recommendation packet to start C4 review with South Fork Meat Grinder and Troublemaker first, keep Zambezi passive until Batoka source evidence exists, and require trajectory, raft/crew/swimmer/rescue telemetry, conservation overlay, guide-seat video, river-eye video, fixed frames, hashes, and reviewer signoff.
2. Generate deterministic run preparations from valid C3 water windows.
3. Run clean and consequence lines at required flows with raft, crew, swimmer, rescue, conservation, video, and frame evidence.
4. Fill the simulator output sidecar and regenerate C4 readiness after review.

**Acceptance Requirements**

1. All required trajectory, telemetry, overlay, video, fixed-frame, and review-decision hashes are present.
2. Guide, visual, technical, rights, and owner reviews pass.
3. C4 readiness no longer blocks C5 flexible-raft re-review.

**Promotion Guardrails**

- Do not mark behavior approved from preparation packets alone.
- Do not promote playable named rapids before accepted C4 outputs exist.

**Required Artifacts**

- `physics/data/real_world/named_rapid_simulator_review_recommendation.json`
- `physics/data/real_world/named_rapid_simulator_review_preparation_packet.json`
- `physics/data/real_world/named_rapid_simulator_review_output_sidecar_template.json`
- `physics/data/real_world/named_rapid_simulator_review_output_validation_report.json`
- `physics/data/real_world/named_rapid_simulator_review_completion_readiness_report.json`

**Command Paths**

- `physics/src/raftsim/examples/generate_named_rapid_simulator_review_recommendation.py`
- `physics/src/raftsim/examples/generate_named_rapid_simulator_review_preparation.py`
- `physics/src/raftsim/examples/generate_named_rapid_simulator_review_output.py`
- `physics/src/raftsim/examples/generate_named_rapid_simulator_review_readiness.py`

### 11-C5-flexible-raft-named-rapid-reruns

- Row id: `C5-flexible-raft-named-rapid-reruns`
- Package: `C-named-rapid-behavior-review`
- Evidence class: `named_rapid_water_and_behavior_evidence`
- Parent gates: `C5`
- Parent gate count: 1
- Readiness blockers: 7
- Follow-up acceptance blockers: 0
- Status: `waiting_on_external_or_manual_evidence`
- Repo ready for external work: True
- May mark parent gate complete from action: False

**Owner Roles**

- flexible-raft simulator runner
- guide/safety reviewer
- physics reviewer
- technical reviewer
- rights reviewer
- owner

**Next Actions**

1. Use the non-authoritative recommendation packet to start C5 review with South Fork Meat Grinder and Troublemaker first, keep Zambezi passive until Batoka source evidence exists, and require C4 decision hashes, D6 comparison hashes, flexible-raft replay, crew weight distribution, wrap/pin/flip/release, swimmer/rescue readability, captures, hashes, and reviewer signoff.
2. Rerun accepted C4 rapids with the D6-approved flexible raft.
3. Record crew weight distribution, wrap/pin/flip/release, swimmer/rescue readability, replay hashes, and captures.
4. Regenerate C5 readiness only after C4 and D6 gates are green.

**Acceptance Requirements**

1. C4 behavior review is accepted for the rapid and flow.
2. D6 external validation is complete.
3. C5 sidecar validation passes with guide/safety/physics/technical/rights/owner signoff.

**Promotion Guardrails**

- Do not enable scoring-critical flexible-raft outcomes from C5 sidecars unless D6 and platform gates are green.
- Do not substitute E2/E3 platform parity for missing flexible-raft rerun evidence.

**Required Artifacts**

- `physics/data/real_world/named_rapid_flexible_raft_rerun_recommendation.json`
- `physics/data/real_world/named_rapid_flexible_raft_rerun_sidecar_template.json`
- `physics/data/real_world/named_rapid_flexible_raft_rerun_validation_report.json`
- `physics/data/real_world/named_rapid_flexible_raft_rerun_completion_readiness_report.json`
- `physics/data/real_world/named_rapid_simulator_review_completion_readiness_report.json`
- `physics/data/calibration/flexible_raft_d6_completion_readiness_report.json`

**Command Paths**

- `physics/src/raftsim/examples/generate_named_rapid_flexible_raft_rerun_recommendation.py`
- `physics/src/raftsim/examples/generate_named_rapid_flexible_raft_rerun.py`
- `physics/src/raftsim/examples/generate_named_rapid_flexible_raft_rerun_readiness.py`

### 12-E2-E3-platform-release-evidence

- Row id: `E2-E3-platform-release-evidence`
- Package: `E-platform-release-evidence`
- Evidence class: `platform_and_release_evidence`
- Parent gates: `C5`
- Parent gate count: 1
- Readiness blockers: 7
- Follow-up acceptance blockers: 0
- Status: `waiting_on_external_or_manual_evidence`
- Repo ready for external work: True
- May mark parent gate complete from action: False

**Owner Roles**

- platform test owner
- performance reviewer
- hazard/readability reviewer
- release owner
- owner

**Next Actions**

1. Record the E1 platform-matrix owner decision before using E2/E3 evidence for release-candidate planning; keep console and handheld as evaluation or explicitly deferred targets until owner hardware/licensing decisions exist.
2. Use the non-authoritative recommendation packet to start E2/E3 release evidence with same-seed profile parity first, then packaged runtime rows for all five runnable rivers and six profiles, while keeping authoritative physics identical and named-rapid/flexible-raft gates separate.
3. Populate E2 profile-parity results from measured same-seed runs across all target profiles.
4. Populate E3 packaged-runtime rows with package manifests, artifact hashes, captures, traces, and reviews.
5. Use platform evidence only after named-rapid and flexible-raft gates are already valid.

**Acceptance Requirements**

1. E2 validation is green for every required profile-parity job.
2. E3 validation is green for every five-river/profile packaged runtime row.
3. Hazard/readability and release reviews approve the packaged runtime evidence.

**Promotion Guardrails**

- Do not change authoritative physics per profile to satisfy performance.
- Do not claim a playable release from packaged evidence while A/B/C/D gates remain blocked.

**Required Artifacts**

- `physics/data/real_world/e1_platform_matrix_decision_packet.json`
- `physics/data/real_world/e1_platform_matrix_decision_result_template.json`
- `physics/data/real_world/e1_platform_matrix_decision_validation_report.json`
- `physics/data/real_world/e2_e3_platform_release_recommendation.json`
- `physics/data/real_world/e2_scalability_profile_parity_contract.json`
- `physics/data/real_world/e2_scalability_profile_parity_result_sidecar_template.json`
- `physics/data/real_world/e2_scalability_profile_parity_validation_report.json`
- `physics/data/real_world/e3_release_candidate_packaging_matrix.json`
- `physics/data/real_world/e3_packaged_runtime_result_sidecar_template.json`
- `physics/data/real_world/e3_packaged_runtime_validation_report.json`

**Command Paths**

- `physics/src/raftsim/examples/validate_e1_platform_matrix_decision.py`
- `physics/src/raftsim/examples/generate_e2_e3_platform_release_recommendation.py`
- `physics/src/raftsim/examples/generate_e2_scalability_profile_parity_results.py`
- `physics/src/raftsim/examples/generate_e3_packaged_runtime_results.py`

### 13-F-five-river-definition-of-done-evidence

- Row id: `F-five-river-definition-of-done-evidence`
- Package: `F-final-definition-of-done-evidence`
- Evidence class: `final_definition_of_done_evidence`
- Parent gates: `A1`, `A2`, `A3`, `A4`, `A5`, `B2-south-fork`, `B2-colorado`, `B2-pacuare`, `B2-futaleufu`, `B2-chilko`, `D6`, `C2`, `C3`, `C4`, `C5`
- Parent gate count: 15
- Readiness blockers: 141
- Follow-up acceptance blockers: 34
- Status: `waiting_on_external_or_manual_evidence`
- Repo ready for external work: True
- May mark parent gate complete from action: False

**Owner Roles**

- river guide or oarsman reviewer
- geospatial reviewer
- hydrology or physics reviewer
- technical art reviewer
- hazard/rescue readability reviewer
- rights/publication reviewer
- platform/performance reviewer
- owner

**Next Actions**

1. Use the Definition of Done matrix only after A/B/C/D/E source, asset, water, raft, platform, capture, test, commit, and push gates are green.
2. Fill one final evidence row per river criterion with hash-locked artifacts, test commands, commit IDs, push records, and all reviewer signoffs.
3. Run the Definition of Done evidence validator and keep the manual completion review blocked until it is green.
4. After a green sidecar, perform the owner completion review and update plan checkboxes as a separate manual step.

**Acceptance Requirements**

1. The source Definition of Done matrix reports all 30 criteria complete before the sidecar can validate.
2. Every sidecar criterion row has evidence paths, SHA-256 hashes, test commands, commit IDs, push records, and required signoffs.
3. The Definition of Done evidence validation report is green.
4. The owner manually reviews the green matrix and sidecar before any parent gate or execution-plan completion checkbox is marked complete.

**Promotion Guardrails**

- Do not use final DoD evidence to bypass any A/B/C/D/E readiness gate.
- Do not mark the execution plan complete from the sidecar alone.
- Do not claim lifelike, playable, or release readiness while the source matrix remains blocked.

**Required Artifacts**

- `docs/five-river-photoreal-execution-plan.md`
- `physics/data/real_world/five_river_definition_of_done_matrix.json`
- `physics/data/real_world/five_river_definition_of_done_evidence_sidecar_template.json`
- `physics/data/real_world/five_river_definition_of_done_evidence_validation_report.json`

**Command Paths**

- `physics/src/raftsim/examples/generate_five_river_definition_of_done.py`
- `physics/src/raftsim/examples/validate_five_river_definition_of_done_evidence.py`

## Promotion Guardrail

This runbook cannot mark parent gates complete, claim photoreal readiness, claim playable readiness, or close the execution plan. It only exposes the evidence work that still has to be completed and reviewed.
