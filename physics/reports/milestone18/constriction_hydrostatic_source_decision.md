# Milestone 18 Constriction Hydrostatic Source Decision

Schema: `raftsim.milestone18.constriction_hydrostatic_source_decision.v0`

Decision: **REVISE_OR_REJECT**

Scenario: `constriction_seed_16`
Face/source audit: `reports/milestone18/constriction_face_source_audit_diagnostic.json`
Diagnostic scope: Decision artifact derived from the exported C++ internal constriction y-face audit; it does not change solver behavior by itself.

## Summary

- source_audit_decision: `BLOCKED`
- cpp_internal_audit_sample_count: `96`
- cpp_internal_post_source_sign_mismatch_count: `65`
- cpp_internal_hydrostatic_face_source_enabled_count: `32`
- cpp_internal_constriction_source_split_applied_count: `32`
- cpp_internal_source_applied_count: `16`
- cpp_internal_max_abs_post_source_delta_m3ps: `5.05494`
- target_post_source_delta_m3ps: `2.61144`

## Target Face

| Face | Column | Rows | Reference q | Base q | Post-source q | Post-source delta | Hydrostatic source enabled | Constriction source applied | Cell bed-source S/N |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `upper_edge_face` | 6 | 8-9 | -1.66953 | 1.05673 | 0.941911 | 2.61144 | `True` | `True` | -0 / -13.7887 |

## Rationale

- The C++ internal audit has 65 post-source sign mismatches across 96 constriction y-face samples.
- Hydrostatic y-face source terms are enabled on 32 of 96 audited samples, while constriction face sources are applied on 16 samples and constriction source splitting is applied on 32 samples.
- The selected target remains wrong after current source handling: `upper_edge_face` column 6 rows 8-9 has post-source q delta 2.61144 m3/s.

## Acceptance Constraints

- Keep feature/gameplay forcing disabled for this fixture; this is a finite-volume water-solver treatment test.
- Manifest-record the y-face source-split parameters, target face set, conservation deltas, and feature-forcing scale.
- Compare against the corrected GeoClaw `user`-boundary constriction reference and rerun the face/source audit.
- Preserve or improve visible mass, energy, Froude, wet-mask, field, slope, probe, and cross-section checks.
- Run Milestone 17 analytic guardrails before and after the solver attempt; reject the change if guardrails regress.

## Blocked Reasons

- Native C++ constriction y-face flux signs still disagree with GeoClaw after current source handling.
- A constriction y-face source split is present, but post-source face signs still disagree with GeoClaw.
- The next change must not be promoted until full geometry checks pass or improve without hiding conservation failures.

## Next Levers

- Do not promote the current constriction y-face source split by itself; it is manifest-recorded and audited on 32 faces but still leaves 65 post-source sign mismatches.
- Move the next constriction attempt to geometry-aware face-state reconstruction or width/depth mapping instead of increasing source-split strength.
- Keep the split bounded and feature forcing off unless a future geometry/state reconstruction report proves it helps without regressing conservation, Froude, or sampled fields.
