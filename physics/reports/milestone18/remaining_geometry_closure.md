# Milestone 18 Remaining Geometry Closure

Schema: `raftsim.milestone18.remaining_geometry_closure.v0`

Decision: **BLOCKED**

Geometry report: `reports/milestone16/geometry_validation.json`
Focused reports: `reports/milestone18/constriction_transition_final_support_upstream_edge_balance_diagnostic.json, reports/milestone18/constriction_transition_final_support_face_state_width_depth_diagnostic.json, reports/milestone18/constriction_transition_final_support_face_source_audit_diagnostic.json, reports/milestone18/constriction_transition_final_support_retune.json, reports/milestone18/constriction_upper_edge_flux_magnitude_balance_upstream_edge_balance_diagnostic.json, reports/milestone18/constriction_upper_edge_flux_magnitude_balance_face_state_width_depth_diagnostic.json, reports/milestone18/constriction_upper_edge_flux_magnitude_balance_face_source_audit_diagnostic.json, reports/milestone18/constriction_upper_edge_flux_magnitude_balance_retune.json, reports/milestone18/constriction_upper_outside_shelf_support_upstream_edge_balance_diagnostic.json, reports/milestone18/constriction_upper_outside_shelf_support_face_state_width_depth_diagnostic.json, reports/milestone18/constriction_upper_outside_shelf_support_face_source_audit_diagnostic.json, reports/milestone18/constriction_upper_outside_shelf_support_retune.json, reports/milestone18/constriction_upper_edge_final_balance_upstream_edge_balance_diagnostic.json, reports/milestone18/constriction_upper_edge_final_balance_face_state_width_depth_diagnostic.json, reports/milestone18/constriction_upper_edge_final_balance_face_source_audit_diagnostic.json, reports/milestone18/constriction_upper_edge_final_balance_retune.json, reports/milestone18/constriction_transition_edge_balance_upstream_edge_balance_diagnostic.json, reports/milestone18/constriction_transition_edge_balance_face_state_width_depth_diagnostic.json, reports/milestone18/constriction_transition_edge_balance_face_source_audit_diagnostic.json, reports/milestone18/constriction_transition_edge_balance_retune.json, reports/milestone18/constriction_wet_band_profile_upstream_edge_balance_diagnostic.json, reports/milestone18/constriction_wet_band_profile_face_state_width_depth_diagnostic.json, reports/milestone18/constriction_wet_band_profile_face_source_audit_diagnostic.json, reports/milestone18/constriction_wet_band_profile_retune.json, reports/milestone18/constriction_lower_edge_width_depth_balance_upstream_edge_balance_diagnostic.json, reports/milestone18/constriction_lower_edge_width_depth_balance_face_state_width_depth_diagnostic.json, reports/milestone18/constriction_lower_edge_width_depth_balance_face_source_audit_diagnostic.json, reports/milestone18/constriction_lower_edge_width_depth_balance_retune.json, reports/milestone18/drop_ledge_hydraulic_control_diagnostic.json, reports/milestone18/drop_ledge_parity_retune.json`

## Summary

- Blocker count: `2`
- Promotion-ready count: `4`
- Next case: `constriction`

## Closure Queue

| Priority | Case | Status | Failing checks | Focused evidence | Next lever |
| ---: | --- | --- | --- | --- | --- |
| 1 | `constriction` | BLOCKED | cross_section_linf=2, energy_change_delta=1, feature_location_delta=2, feature_strength_delta=2, field_linf=2, froude_delta=2, mass_drift_delta=1, probe_linf=2, slope_linf=2, wet_mismatch_fraction=1 | reports/milestone18/constriction_transition_final_support_upstream_edge_balance_diagnostic.json, reports/milestone18/constriction_transition_final_support_face_state_width_depth_diagnostic.json, reports/milestone18/constriction_transition_final_support_face_source_audit_diagnostic.json, reports/milestone18/constriction_transition_final_support_retune.json, reports/milestone18/constriction_upper_edge_flux_magnitude_balance_upstream_edge_balance_diagnostic.json, reports/milestone18/constriction_upper_edge_flux_magnitude_balance_face_state_width_depth_diagnostic.json, reports/milestone18/constriction_upper_edge_flux_magnitude_balance_face_source_audit_diagnostic.json, reports/milestone18/constriction_upper_edge_flux_magnitude_balance_retune.json, reports/milestone18/constriction_upper_outside_shelf_support_upstream_edge_balance_diagnostic.json, reports/milestone18/constriction_upper_outside_shelf_support_face_state_width_depth_diagnostic.json, reports/milestone18/constriction_upper_outside_shelf_support_face_source_audit_diagnostic.json, reports/milestone18/constriction_upper_outside_shelf_support_retune.json, reports/milestone18/constriction_upper_edge_final_balance_upstream_edge_balance_diagnostic.json, reports/milestone18/constriction_upper_edge_final_balance_face_state_width_depth_diagnostic.json, reports/milestone18/constriction_upper_edge_final_balance_face_source_audit_diagnostic.json, reports/milestone18/constriction_upper_edge_final_balance_retune.json, reports/milestone18/constriction_lower_edge_width_depth_balance_upstream_edge_balance_diagnostic.json, reports/milestone18/constriction_lower_edge_width_depth_balance_face_state_width_depth_diagnostic.json, reports/milestone18/constriction_lower_edge_width_depth_balance_face_source_audit_diagnostic.json, reports/milestone18/constriction_lower_edge_width_depth_balance_retune.json | Start with `lower_edge_face` column 0 rows 1-2; q delta is -1.88858 m3/s, balance delta is -16.5518 m3/s2, native post-source delta is 0.264138 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells. |
| 2 | `drops_ledges_tailwater` | BLOCKED | cross_section_linf=7, energy_change_delta=7, feature_location_delta=6, feature_strength_delta=6, field_linf=8, froude_delta=8, mass_drift_delta=4, probe_linf=8, slope_linf=8, wet_mismatch_fraction=3 | reports/milestone18/drop_ledge_hydraulic_control_diagnostic.json, reports/milestone18/drop_ledge_parity_retune.json | Start with `field`/`u` at `final` cell 0,10; it is 3.32137x the diagnostic threshold. |
| 3 | `stitched_reach_drop_handoffs` | PASS | none | none | Preserve this geometry family as a guardrail while retuning active blockers. |
| 10 | `wet_dry_shoreline` | PASS | none | none | Preserve this geometry family as a guardrail while retuning active blockers. |
| 11 | `bed_step` | PASS | none | none | Preserve this geometry family as a guardrail while retuning active blockers. |
| 12 | `hydrostatic_sloping_balance` | PASS | none | none | Preserve this geometry family as a guardrail while retuning active blockers. |

## Active Blockers

### Constrictions

- Case ID: `constriction`
- Scenarios: `constriction`
- Failing checks: `cross_section_linf=2, energy_change_delta=1, feature_location_delta=2, feature_strength_delta=2, field_linf=2, froude_delta=2, mass_drift_delta=1, probe_linf=2, slope_linf=2, wet_mismatch_fraction=1`
- Threshold failures remain in: constriction.

Next levers:
- Start with `lower_edge_face` column 0 rows 1-2; q delta is -1.88858 m3/s, balance delta is -16.5518 m3/s2, native post-source delta is 0.264138 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Preserve GeoClaw's lower-positive/upper-negative edge opposition across upstream wet-band columns.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
- Start with `lower_edge_face` column 7 rows 2-3; q delta is -0.460782 m3/s, face mean-depth delta is -0.0955201 m, wet-width delta is 0 cells, and max bank-row delta is 0 cells.
- Build a geometry-aware face-state reconstruction before y-face flux evaluation; the source split alone did not restore the GeoClaw edge signs.
- Use the authored initial -> GeoClaw final -> C++ final column profiles to retune constriction width/depth mapping before accepting any face-state change.
- Preserve GeoClaw's lower/upper edge opposition in the upstream wet band; a single-sign lateral state remains a blocker.
- Keep feature forcing and stronger source-split tuning off, then rerun the face/source audit, mask/throat diagnostics, threshold report, and Milestone 17 guardrail.
- Start with `lower_edge_face` column 7 rows 2-3; reconstructed q delta is -0.460782 m3/s and balance delta is -2.99048 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `lower_edge_face` column 7 rows 2-3; post-source q delta is 0.224797 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
- Start with `lower_edge_face` column 0 rows 1-2; q delta is -2.02418 m3/s, balance delta is -16.4093 m3/s2, native post-source delta is -0.138502 m3/s, wet-width delta is -1 cells, and bank-row delta is 1 cells.
- Start with `lower_edge_face` column 1 rows 1-2; q delta is -2.05596 m3/s, face mean-depth delta is -0.132276 m, wet-width delta is 0 cells, and max bank-row delta is 0 cells.
- Start with `lower_edge_face` column 1 rows 1-2; reconstructed q delta is -2.05596 m3/s and balance delta is -7.75814 m3/s2.
- Use the exported C++ internal audit at `lower_edge_face` column 1 rows 1-2; post-source q delta is -0.31461 m3/s.
- Start with `upper_edge_face` column 4 rows 8-9; q delta is 1.17248 m3/s, balance delta is 4.32016 m3/s2, native post-source delta is -0.699634 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Start with `upper_edge_face` column 4 rows 8-9; q delta is 1.17248 m3/s, face mean-depth delta is 0.435841 m, wet-width delta is 0 cells, and max bank-row delta is 0 cells.
- Start with `upper_edge_face` column 4 rows 8-9; reconstructed q delta is 1.17248 m3/s and balance delta is 4.32016 m3/s2.
- Use the exported C++ internal audit at `upper_edge_face` column 4 rows 8-9; post-source q delta is -0.699634 m3/s.
- Start with `upper_edge_face` column 4 rows 8-9; q delta is 1.17713 m3/s, balance delta is 4.40553 m3/s2, native post-source delta is -0.699467 m3/s, wet-width delta is -1 cells, and bank-row delta is 1 cells.
- Start with `upper_edge_face` column 4 rows 8-9; q delta is 1.17713 m3/s, face mean-depth delta is 0.441478 m, wet-width delta is -1 cells, and max bank-row delta is 1 cells.
- Start with `upper_edge_face` column 4 rows 8-9; reconstructed q delta is 1.17713 m3/s and balance delta is 4.40553 m3/s2.
- Use the exported C++ internal audit at `upper_edge_face` column 4 rows 8-9; post-source q delta is -0.699467 m3/s.
- Start with `upper_edge_face` column 6 rows 8-9; q delta is 2.97684 m3/s, balance delta is 11.7197 m3/s2, native post-source delta is 2.05363 m3/s, wet-width delta is 1 cells, and bank-row delta is 0 cells.
- Start with `upper_edge_face` column 6 rows 8-9; q delta is 2.97684 m3/s, face mean-depth delta is 0.855736 m, wet-width delta is 1 cells, and max bank-row delta is 0 cells.
- Start with `upper_edge_face` column 6 rows 8-9; reconstructed q delta is 2.97684 m3/s and balance delta is 11.7197 m3/s2.
- Use the exported C++ internal audit at `upper_edge_face` column 6 rows 8-9; post-source q delta is 2.05363 m3/s.
- Close constriction field, slope, probe, cross-section, and wet-mask parity before treating raft coupling as actionable.
- Preserve or restore conservation and energy checks before accepting any visual/gameplay forcing.

### Drops, Ledges, And Tailwater

- Case ID: `drops_ledges_tailwater`
- Scenarios: `drop_ledge, south_fork_cascading_low_runnable, south_fork_cascading_median_runnable, south_fork_cascading_high_runnable`
- Failing checks: `cross_section_linf=7, energy_change_delta=7, feature_location_delta=6, feature_strength_delta=6, field_linf=8, froude_delta=8, mass_drift_delta=4, probe_linf=8, slope_linf=8, wet_mismatch_fraction=3`
- Threshold failures remain in: drop_ledge, south_fork_cascading_high_runnable, south_fork_cascading_low_runnable, south_fork_cascading_median_runnable.
- Cascading reach/drop handoff checks pass separately; these failures are whole-window water-field parity blockers: south_fork_cascading_high_runnable, south_fork_cascading_low_runnable, south_fork_cascading_median_runnable.

Next levers:
- Start with `field`/`u` at `final` cell 0,10; it is 3.32137x the diagnostic threshold.
- Retune the ledge hydraulic-control free-surface/depth reconstruction and downstream recovery shape before adding gameplay feature forcing.
- Preserve the passing conservation, energy, and Froude checks; this is a water-shape blocker, not permission to hide errors with forcing.
- Inspect depth, stage, and streamwise momentum across the ledge lip and first tailwater recovery columns.
- Use the raw probe/cross-section coordinates as the acceptance surface for the next corrected-reference parity run.
- Keep `feature_strength_scale=0` and rerun the Milestone 17 analytic guardrail after the solver change.
- Retune the single drop/ledge hydraulic-control lane before folding the fix into cascading South Fork flows.
- Use stitched whole-window cascading comparisons for acceptance; reach-local seams already pass and cannot hide water-field errors.
- Preserve or restore conservation and energy checks before accepting any visual/gameplay forcing.
