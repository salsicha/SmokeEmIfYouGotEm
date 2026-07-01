# Milestone 18 Remaining Geometry Closure

Schema: `raftsim.milestone18.remaining_geometry_closure.v0`

Decision: **BLOCKED**

Geometry report: `reports/milestone16/geometry_validation.json`
Focused reports: `reports/milestone18/constriction_lateral_face_flux_diagnostic.json, reports/milestone18/constriction_face_source_audit_diagnostic.json, reports/milestone18/constriction_hydrostatic_source_decision.json, reports/milestone18/drop_ledge_hydraulic_control_diagnostic.json`

## Summary

- Blocker count: `2`
- Promotion-ready count: `4`
- Next case: `constriction`

## Closure Queue

| Priority | Case | Status | Failing checks | Focused evidence | Next lever |
| ---: | --- | --- | --- | --- | --- |
| 1 | `constriction` | BLOCKED | cross_section_linf=2, energy_change_delta=1, feature_location_delta=2, feature_strength_delta=2, field_linf=2, froude_delta=2, mass_drift_delta=1, probe_linf=2, slope_linf=2, wet_mismatch_fraction=1 | reports/milestone18/constriction_lateral_face_flux_diagnostic.json, reports/milestone18/constriction_face_source_audit_diagnostic.json, reports/milestone18/constriction_hydrostatic_source_decision.json | Start with `upper_edge_face` column 6 rows 8-9; the GeoClaw/C++ lateral flux proxy differs by 2.72825 m3/s. |
| 2 | `drops_ledges_tailwater` | BLOCKED | cross_section_linf=7, energy_change_delta=7, feature_location_delta=6, feature_strength_delta=6, field_linf=8, froude_delta=8, mass_drift_delta=4, probe_linf=8, slope_linf=8, wet_mismatch_fraction=3 | reports/milestone18/drop_ledge_hydraulic_control_diagnostic.json | Start with `field`/`u` at `final` cell 0,10; it is 3.32137x the diagnostic threshold. |
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
- Start with `upper_edge_face` column 6 rows 8-9; the GeoClaw/C++ lateral flux proxy differs by 2.72825 m3/s.
- Instrument or reconstruct the actual finite-volume lateral face flux/source balance before adding another post-step velocity or depth transport.
- Preserve GeoClaw's opposite-signed lower/upper upstream edge behavior; a single-sign lateral transport will keep damaging Froude shape.
- Start with `upper_edge_face` column 6 rows 8-9; reconstructed q delta is 2.72633 m3/s and balance delta is 8.87096 m3/s2.
- Export or inspect internal C++ y-face Riemann fluxes and hydrostatic bed-source terms at this face to verify the reconstructed final-frame audit.
- Move the upstream shallow-fast edge behavior into finite-volume face/source treatment rather than final velocity, depth, or gameplay forcing.
- Use the exported C++ internal audit at `upper_edge_face` column 6 rows 8-9; post-source q delta is 2.61144 m3/s.
- Preserve GeoClaw's lower-positive/upper-negative upstream edge opposition while keeping mass and energy gates visible.
- Do not promote the current constriction y-face source split by itself; it is manifest-recorded and audited on 32 faces but still leaves 65 post-source sign mismatches.
- Move the next constriction attempt to geometry-aware face-state reconstruction or width/depth mapping instead of increasing source-split strength.
- Keep the split bounded and feature forcing off unless a future geometry/state reconstruction report proves it helps without regressing conservation, Froude, or sampled fields.
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
