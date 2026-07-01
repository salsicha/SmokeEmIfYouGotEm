# Milestone 18 Constriction Hydrostatic Source Decision

Schema: `raftsim.milestone18.constriction_hydrostatic_source_decision.v0`

Decision: **TEST_REQUIRED**

Scenario: `constriction_seed_16`
Face/source audit: `reports/milestone18/constriction_face_source_audit_diagnostic.json`
Diagnostic scope: Decision artifact derived from the exported C++ internal constriction y-face audit; it does not change solver behavior by itself.

## Summary

- source_audit_decision: `BLOCKED`
- cpp_internal_audit_sample_count: `96`
- cpp_internal_post_source_sign_mismatch_count: `65`
- cpp_internal_hydrostatic_face_source_enabled_count: `0`
- cpp_internal_source_applied_count: `16`
- cpp_internal_max_abs_post_source_delta_m3ps: `5.0561`
- target_post_source_delta_m3ps: `2.6134`

## Target Face

| Face | Column | Rows | Reference q | Base q | Post-source q | Post-source delta | Hydrostatic source enabled | Constriction source applied | Cell bed-source S/N |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `upper_edge_face` | 6 | 8-9 | -1.66953 | 1.0586 | 0.943874 | 2.6134 | `False` | `True` | -0 / -13.7891 |

## Rationale

- The C++ internal audit has 65 post-source sign mismatches across 96 constriction y-face samples.
- Hydrostatic y-face source terms are enabled on 0 of 96 audited samples, while constriction face sources are applied on 16 samples.
- The selected target remains wrong after current source handling: `upper_edge_face` column 6 rows 8-9 has post-source q delta 2.6134 m3/s.

## Acceptance Constraints

- Keep feature/gameplay forcing disabled for this fixture; this is a finite-volume water-solver treatment test.
- Manifest-record the y-face source-split parameters, target face set, conservation deltas, and feature-forcing scale.
- Compare against the corrected GeoClaw `user`-boundary constriction reference and rerun the face/source audit.
- Preserve or improve visible mass, energy, Froude, wet-mask, field, slope, probe, and cross-section checks.
- Run Milestone 17 analytic guardrails before and after the solver attempt; reject the change if guardrails regress.

## Blocked Reasons

- Native C++ constriction y-face flux signs still disagree with GeoClaw after current source handling.
- Hydrostatic y-face source treatment is absent for the audited constriction faces.
- The next change must not be promoted until full geometry checks pass or improve without hiding conservation failures.

## Next Levers

- Implement a fixture-scoped constriction y-face hydrostatic/source-splitting experiment at the audited `upper_edge_face` column 6 rows 8-9 target first.
- Apply the treatment inside the finite-volume face/source update, not as final velocity/depth transport or gameplay forcing.
- Promote only if the face/source report, throat/shape/timing diagnostics, Milestone 17 guardrail, and threshold report all support the change.
- If the split worsens field, slope, wet-mask, probe, cross-section, Froude, mass, or energy checks, reject it and move to geometry width/depth mapping.
