# Chilko A5 Stationing/08MA Flow Review Form

Generated: 2026-07-17

Use this form to collect reviewed Chilko endpoint, route-axis, GPS/aerial rapid point/span, guide, 08MA002 route translation, 08MA001 downstream context, flow-window, unsafe/washout, land/publication, and regeneration decisions before copying accepted values into the JSON review templates.

This form is not an approval by itself and cannot mark A5 complete.

## Source Records

- Reviewer briefing: `physics/data/real_world/chilko_river_bc/review/a5_review_briefing.json`
- Stationing digitizing template: `physics/data/real_world/chilko_river_bc/review/a5_stationing_digitizing_result_template.json`
- 08MA flow-source template: `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json`

Additional source artifacts:
- `digitizing_action_packet`: `physics/data/real_world/chilko_river_bc/review/a5_stationing_digitizing_action_packet.json`
- `digitizing_result_template`: `physics/data/real_world/chilko_river_bc/review/a5_stationing_digitizing_result_template.json`
- `digitizing_validation_report`: `physics/data/real_world/chilko_river_bc/review/a5_stationing_digitizing_validation_report.json`
- `flow_source_review_packet`: `physics/data/real_world/chilko_river_bc/review/a5_flow_source_review_packet.json`
- `flow_source_result_template`: `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json`
- `flow_source_validation_report`: `physics/data/real_world/chilko_river_bc/review/a5_flow_source_validation_report.json`
- `regeneration_action_packet`: `physics/data/real_world/chilko_river_bc/review/a5_regeneration_action_packet.json`
- `a5_completion_readiness_report`: `physics/data/real_world/chilko_river_bc/review/a5_completion_readiness_report.json`
- `review_recommendation`: `physics/data/real_world/chilko_river_bc/review/a5_review_recommendation.json`

## Current Gate State

- Status: `chilko_a5_review_briefing_ready_pending_human_decisions`
- Recommended stationing workflow id: `reviewed_endpoint_route_axis_plus_gps_or_aerial_rapid_digitizing`
- Recommended flow workflow id: `08ma002_daily_window_routing_with_08ma001_context_before_numeric_tuning`
- Rapid count: 5
- Critical rapid count: 3
- Passing rapid count: 0
- Stationing validation error count: 95
- Stationing reviewer role count: 5
- Flow window count: 4
- Passing flow window count: 0
- Flow validation error count: 123
- Flow reviewer role count: 6
- Manual regeneration action count: 0
- A5 readiness blocker count: 10
- Unsafe or washout playable: False
- May enable numeric flow: False
- May tune water visuals: False
- May tune feature forcing: False
- May bind solver windows: False
- May mark A5 complete: False

## Non-Authoritative Recommendation

- Recommended stationing workflow id: `reviewed_endpoint_route_axis_plus_gps_or_aerial_rapid_digitizing`
- Recommended flow workflow id: `08ma002_daily_window_routing_with_08ma001_context_before_numeric_tuning`
- Unsafe or washout playable: False
- Recommendation is not a decision: True
- Source artifact: `physics/data/real_world/chilko_river_bc/review/a5_review_recommendation.json`

## Decision Questions

Choose the reviewed Chilko put-in/take-out and route station axis, GPS or aerial rapid point/span geometry, guide confirmation, 08MA002-to-put-in flow-window routing, 08MA001 downstream context checks, unsafe/washout policy, land/publication limits, and post-review regeneration scope.

Blocked reason: The FWA route is source-scale technical evidence, but every priority rapid remains order-interpolated, exact endpoint geometry is not approved, and 08MA002/08MA001 flow windows are still review-only until routing, guide, land, and safety acceptance pass.

### reviewed_route_and_endpoint_axis

Which guide/geospatial-reviewed put-in, take-out, and route station axis replaces the source-scale FWA scaffold?

Record in: `reviewed_route_source`

Decision notes:


### gps_or_aerial_rapid_geometry

For each of the five priority rapids, what reviewed Point or LineString geometry, route station, confidence, and evidence is accepted?

Record in: `stationing_result_records`

Decision notes:


### guide_and_outfitter_confirmation

Which Chilko guide or outfitter evidence confirms rapid locations, flow-sensitive behavior, cold-water hazards, and limited recovery zones?

Record in: `guide_reviewer / guide_evidence`

Decision notes:


### 08ma002_route_translation

How are 08MA002 daily or event-window records translated to the Chilko River Lodge put-in, including lag and tributary assumptions?

Record in: `route_translation_method / lag_or_travel_time_assumption`

Decision notes:


### 08ma001_downstream_context

How is 08MA001 downstream context used without confusing Taseko confluence influence for reach-local Chilko behavior?

Record in: `downstream_context_check`

Decision notes:


### flow_source_classes

Which ECCC time-series, route translation, downstream context, guide review, or unsafe/washout source class supports each flow window?

Record in: `flow_window_records`

Decision notes:


### unsafe_or_washout_policy

Should the unsafe or washout window remain review-only, and what safety/rescue readability evidence is required before gameplay use?

Record in: `safety_status`

Decision notes:


### land_and_publication_policy

What route, rapid, source, land, guide, and hazard details may appear in public tools, screenshots, captures, or docs?

Record in: `rights_publication_status / land_publication_status / rights_terms_status`

Decision notes:


### regeneration_scope

Which catalog, editor, 08MA flow-window, rapid-water-window, and solver-review outputs must be regenerated after validation?

Record in: `a5_regeneration_action_packet`

Decision notes:



## Key Measurements

- `catalog_run_length_m`: 55845.696
- `route_stationing_length_m`: 55845.696
- `route_is_source_scale_candidate`: True
- `exact_endpoint_geometry_approved`: False
- `rapid_count`: 5
- `flow_window_count`: 4
- `primary_flow_station`: 08MA002
- `downstream_context_station`: 08MA001
- `numeric_flow_bands_promoted`: False

## Stationing Digitizing

- Allowed geometry types: `Point`, `LineString`
- Allowed stationing kinds: `exact_gps_point`, `aerial_interpreted_point`, `aerial_interpreted_span`, `guide_reviewed_point`, `guide_reviewed_span`
- Allowed flow context classes: `08ma002_daily_window_routing_pending`, `08ma002_to_put_in_route_translation_reviewed`, `08ma001_downstream_context_reviewed`, `guide_reviewed_flow_band`, `hypothesis_pending_guide_review`
- Required review roles: `owner_or_producer_acceptance`, `chilko_guide_or_outfitter_reviewer`, `geospatial_reviewer`, `rights_publication_reviewer`, `hydrology_or_flow_reviewer`
- Record in: `physics/data/real_world/chilko_river_bc/review/a5_stationing_digitizing_result_template.json`

| Rapid | Order | Priority | Class | Current station m | Route focus m | Current kind | Required geometry | Required stationing kinds | Required flow context classes | Passing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Bidwell Rapids | 1 | critical | IV (guide-published, all reviewed levels) | 9307.616 | 9307.616 | `provisional_downstream_order_interpolation` | `Point`, `LineString` | `exact_gps_point`, `aerial_interpreted_point`, `aerial_interpreted_span`, `guide_reviewed_point`, `guide_reviewed_span` | `reviewed_fwa_route_centerline`, `accepted_aerial_or_orthomosaic`, `rapid_feature_digitizer`, `chilko_guide_or_outfitter_confirmation`, `rights_land_and_publication_review`, `08ma002_flow_window_context` | False |
| Lava Canyon | 2 | critical | III-V (flow-dependent reach, exact feature scope pending) | 18615.232 | 18615.232 | `provisional_downstream_order_interpolation` | `Point`, `LineString` | `exact_gps_point`, `aerial_interpreted_point`, `aerial_interpreted_span`, `guide_reviewed_point`, `guide_reviewed_span` | `reviewed_fwa_route_centerline`, `accepted_aerial_or_orthomosaic`, `rapid_feature_digitizer`, `chilko_guide_or_outfitter_confirmation`, `rights_land_and_publication_review`, `08ma002_flow_window_context` | False |
| White Mile | 3 | critical | IV-V (flow-dependent) | 27922.848 | 27922.848 | `provisional_downstream_order_interpolation` | `Point`, `LineString` | `exact_gps_point`, `aerial_interpreted_point`, `aerial_interpreted_span`, `guide_reviewed_point`, `guide_reviewed_span` | `reviewed_fwa_route_centerline`, `accepted_aerial_or_orthomosaic`, `rapid_feature_digitizer`, `chilko_guide_or_outfitter_confirmation`, `rights_land_and_publication_review`, `08ma002_flow_window_context` | False |
| Green Mile | 4 | high | guide review required | 37230.464 | 37230.464 | `provisional_downstream_order_interpolation` | `Point`, `LineString` | `exact_gps_point`, `aerial_interpreted_point`, `aerial_interpreted_span`, `guide_reviewed_point`, `guide_reviewed_span` | `reviewed_fwa_route_centerline`, `accepted_aerial_or_orthomosaic`, `rapid_feature_digitizer`, `chilko_guide_or_outfitter_confirmation`, `rights_land_and_publication_review`, `08ma002_flow_window_context` | False |
| Miracle Canyon | 5 | high | guide review required | 46538.08 | 46538.08 | `provisional_downstream_order_interpolation` | `Point`, `LineString` | `exact_gps_point`, `aerial_interpreted_point`, `aerial_interpreted_span`, `guide_reviewed_point`, `guide_reviewed_span` | `reviewed_fwa_route_centerline`, `accepted_aerial_or_orthomosaic`, `rapid_feature_digitizer`, `chilko_guide_or_outfitter_confirmation`, `rights_land_and_publication_review`, `08ma002_flow_window_context` | False |

## Stationing Record Checklist

| Field | Required | Currently missing or invalid | Record in |
| --- | --- | --- | --- |
| `geometry_type` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_stationing_digitizing_result_template.json` |
| `geometry_coordinates_wgs84` | True | False | `physics/data/real_world/chilko_river_bc/review/a5_stationing_digitizing_result_template.json` |
| `route_station_m` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_stationing_digitizing_result_template.json` |
| `stationing_kind` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_stationing_digitizing_result_template.json` |
| `reviewed_route_source` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_stationing_digitizing_result_template.json` |
| `gps_or_aerial_source` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_stationing_digitizing_result_template.json` |
| `digitized_by` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_stationing_digitizing_result_template.json` |
| `digitized_on` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_stationing_digitizing_result_template.json` |
| `confidence_m` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_stationing_digitizing_result_template.json` |
| `guide_reviewer` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_stationing_digitizing_result_template.json` |
| `guide_reviewed_on` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_stationing_digitizing_result_template.json` |
| `rights_publication_status` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_stationing_digitizing_result_template.json` |
| `land_publication_status` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_stationing_digitizing_result_template.json` |
| `flow_context_class` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_stationing_digitizing_result_template.json` |
| `flow_context_source` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_stationing_digitizing_result_template.json` |
| `source_evidence` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_stationing_digitizing_result_template.json` |
| `guide_evidence` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_stationing_digitizing_result_template.json` |

## Stationing Reviewer Signoff

| Role | Missing or unapproved | Name or role | Review date | Approved | Evidence paths or hashes | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `owner_or_producer_acceptance` | True |  |  | false |  |  |
| `chilko_guide_or_outfitter_reviewer` | True |  |  | false |  |  |
| `geospatial_reviewer` | True |  |  | false |  |  |
| `rights_publication_reviewer` | True |  |  | false |  |  |
| `hydrology_or_flow_reviewer` | True |  |  | false |  |  |

## 08MA Flow-Window Records

- Allowed source classes: `eccc_08ma002_daily_time_series`, `eccc_08ma002_to_put_in_route_translation`, `eccc_08ma001_downstream_context_check`, `guide_reviewed_flow_band`, `unsafe_high_water_or_washout_review`, `hypothesis_pending_guide_review`
- Required review roles: `owner_or_producer_acceptance`, `hydrology_or_flow_reviewer`, `chilko_guide_or_outfitter_reviewer`, `geospatial_route_translation_reviewer`, `rights_land_publication_reviewer`, `gameplay_safety_reviewer`
- Numeric values allowed now: False
- Water visual tuning allowed now: False
- Feature forcing tuning allowed now: False
- Rapid water windows allowed now: False
- Solver windows allowed now: False
- Record in: `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json`

| Flow window | Display name | Priority | Reference months | Primary station | Downstream context | Expected behavior | Required fields | Passing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `low_technical_review` | Low technical review window | high | [10, 11, 12, 1, 2, 3, 4, 5] | 08MA002 | 08MA001 | shallower shelves, more exposed boulder contact, less sticky holes, and tighter rescue margins | `source_class`, `primary_station_number`, `downstream_context_station_number`, `provider`, `variables`, `units`, `time_zone`, `temporal_resolution`, `daily_window_selection`, `route_translation_method`, `lag_or_travel_time_assumption`, `tributary_adjustment_assumption`, `downstream_context_check`, `reach_relation`, `guide_reviewed_behavior`, `feature_behavior_notes`, `rights_terms_status` | False |
| `reference_summer_runnable_review` | Reference summer runnable review window | critical | [6, 7, 8, 9] | 08MA002 | 08MA001 | continuous cold big-water run with wave trains, laterals, strong eddy lines, and limited recovery | `source_class`, `primary_station_number`, `downstream_context_station_number`, `provider`, `variables`, `units`, `time_zone`, `temporal_resolution`, `daily_window_selection`, `route_translation_method`, `lag_or_travel_time_assumption`, `tributary_adjustment_assumption`, `downstream_context_check`, `reach_relation`, `guide_reviewed_behavior`, `feature_behavior_notes`, `rights_terms_status` | False |
| `high_big_water_review` | High big-water review window | critical | [6, 7, 8] | 08MA002 | 08MA001 | larger standing waves, stronger laterals, stickier holes at selected stages, and faster swimmer drift | `source_class`, `primary_station_number`, `downstream_context_station_number`, `provider`, `variables`, `units`, `time_zone`, `temporal_resolution`, `daily_window_selection`, `route_translation_method`, `lag_or_travel_time_assumption`, `tributary_adjustment_assumption`, `downstream_context_check`, `reach_relation`, `guide_reviewed_behavior`, `feature_behavior_notes`, `rights_terms_status` | False |
| `unsafe_or_washout_review_only` | Unsafe or washout review-only window | critical | [6, 7, 8] | 08MA002 | 08MA001 | some holes may wash out while hydraulics, pins, flips, swimmer separation, and recovery consequences intensify | `source_class`, `primary_station_number`, `downstream_context_station_number`, `provider`, `variables`, `units`, `time_zone`, `temporal_resolution`, `daily_window_selection`, `route_translation_method`, `lag_or_travel_time_assumption`, `tributary_adjustment_assumption`, `downstream_context_check`, `reach_relation`, `guide_reviewed_behavior`, `feature_behavior_notes`, `rights_terms_status`, `safety_status` | False |

## Flow Record Checklist

| Field | Required | Currently missing or invalid | Record in |
| --- | --- | --- | --- |
| `source_class` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `primary_station_number` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `downstream_context_station_number` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `provider` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `source_url_or_report` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `reviewed_on` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `variables` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `units` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `time_zone` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `temporal_resolution` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `record_start_end` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `daily_window_selection` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `route_translation_method` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `lag_or_travel_time_assumption` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `tributary_adjustment_assumption` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `downstream_context_check` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `reach_relation` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `date_or_season_window` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `band_threshold_description` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `guide_reviewed_behavior` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `feature_behavior_notes` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `guide_reviewer` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `guide_reviewed_on` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `rights_terms_status` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `source_evidence` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `guide_evidence` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |
| `safety_status` | True | True | `physics/data/real_world/chilko_river_bc/review/a5_flow_source_result_template.json` |

## Flow Reviewer Signoff

| Role | Missing or unapproved | Name or role | Review date | Approved | Evidence paths or hashes | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `owner_or_producer_acceptance` | True |  |  | false |  |  |
| `hydrology_or_flow_reviewer` | True |  |  | false |  |  |
| `chilko_guide_or_outfitter_reviewer` | True |  |  | false |  |  |
| `geospatial_route_translation_reviewer` | True |  |  | false |  |  |
| `rights_land_publication_reviewer` | True |  |  | false |  |  |
| `gameplay_safety_reviewer` | True |  |  | false |  |  |

## Post-Review Commands

Run these after the relevant review payloads are filled with evidence:

1. `python physics/src/raftsim/examples/validate_chilko_a5_digitizing_result.py --repo-root . --result <filled-stationing-result.json> --output <accepted-stationing-result.json> --report <stationing-validation-report.json>`
2. `python physics/src/raftsim/examples/validate_chilko_a5_flow_source_result.py --repo-root . --result <filled-08ma-flow-source-result.json> --output <accepted-08ma-flow-source-result.json> --report <08ma-flow-source-validation-report.json>`
3. `python physics/src/raftsim/examples/generate_chilko_a5_regeneration_actions.py --repo-root . --digitizing-result <accepted-stationing-result.json> --flow-source-result <accepted-08ma-flow-source-result.json> --output <accepted-regeneration-action-packet.json> --report <regeneration-action-report.json>`
4. `python physics/src/raftsim/examples/generate_chilko_a5_readiness.py --repo-root . --digitizing-result <accepted-stationing-result.json> --flow-source-result <accepted-08ma-flow-source-result.json> --output <a5-readiness-report.json>`

Manual actions unlocked only by valid reviewed inputs:

| Step | Required valid inputs | Currently allowed | Expected outputs |
| --- | --- | --- | --- |
| `a5_regenerate_named_rapid_catalog` | `stationing_digitizing` | False | `physics/data/real_world/chilko_river_bc/review/a5_reviewed_rapid_stationing.json`, `physics/data/real_world/chilko_river_bc/review/a5_named_rapid_catalog_regeneration_report.json` |
| `a5_regenerate_editor_markers` | `stationing_digitizing` | False | `unreal/Content/RaftSim/Tools/Reviewed/chilko_reviewed_markers.json`, `physics/data/real_world/chilko_river_bc/review/a5_editor_marker_regeneration_report.json` |
| `a5_update_08ma002_flow_window_source_classes` | `flow_source` | False | `physics/data/real_world/chilko_river_bc/hydrology/a5_reviewed_08ma002_flow_window_source_class_presets.json`, `physics/data/real_world/chilko_river_bc/review/a5_flow_window_source_class_update_report.json` |
| `a5_generate_rapid_water_window_inputs` | `stationing_digitizing`, `flow_source` | False | `physics/data/real_world/chilko_river_bc/water_windows/a5_rapid_water_window_input_manifest.json`, `physics/data/real_world/chilko_river_bc/water_windows/a5_rapid_water_window_review_queue.json` |
| `a5_prepare_solver_window_review_queue` | `stationing_digitizing`, `flow_source` | False | `physics/data/real_world/chilko_river_bc/water_windows/a5_solver_window_review_queue.json`, `physics/data/real_world/chilko_river_bc/review/a5_solver_window_gate_report.json` |

## Promotion Guardrails

- `can_select_route_from_briefing_alone`: False
- `can_replace_order_interpolation`: False
- `can_record_08ma_flow_classes_from_briefing_alone`: False
- `can_enable_numeric_discharge_values`: False
- `can_tune_water_visuals`: False
- `can_tune_feature_forcing`: False
- `can_make_unsafe_or_washout_playable`: False
- `can_generate_rapid_water_windows`: False
- `can_import_unreal_route`: False
- `can_bind_solver_windows`: False
- `can_mark_a5_complete`: False

## Completion Rule

1. all five priority rapid stationing records pass validation
2. all four 08MA002/08MA001 flow-window records pass validation
3. exact endpoint geometry and land/publication review are accepted
4. unsafe or washout windows remain review-only until safety acceptance is recorded
5. all requested regeneration actions produce reviewed catalog, editor, flow-source, and water-window input outputs
6. C++ water and solver-window validation pass on regenerated Chilko windows
7. guide, geospatial, rights, land, hazard, hydrology, and owner acceptance is recorded
