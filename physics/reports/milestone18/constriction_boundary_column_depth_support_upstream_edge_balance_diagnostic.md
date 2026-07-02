# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_boundary_column_depth_support_face_state_width_depth_diagnostic.json`
Face/source audit report: `physics/reports/milestone18/constriction_boundary_column_depth_support_face_source_audit_diagnostic.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `11`
- Source-balance blockers: `9`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `1`
- Max abs volume-flux delta: `1.1376` m3/s
- Max abs balance delta: `14.9694` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `-1.16102/-1` | 1.1376 | 1.63225 | `width=0, bank=0, face_h=0.466912, column_h=-0.0165296` | `-3.98015/-1` | -1.68153 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.349127/1` | -1.11383 | -11.2555 | `width=0, bank=0, face_h=-0.319343, column_h=-0.0920849` | `1.35027/1` | -0.112689 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `-1.22729/-1` | 0.683985 | 3.54541 | `width=0, bank=0, face_h=0.478424, column_h=0.00739147` | `-3.98015/-1` | -2.06887 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | `0.658536/1` | 0.584226 | 14.0878 | `width=0, bank=0, face_h=0.532383, column_h=0.0137888` | `0.331446/1` | 0.257136 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.595155/1` | 0.533638 | 11.7971 | `width=0, bank=0, face_h=0.45268, column_h=0.232225` | `0.338097/1` | 0.276581 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.268478/1` | -0.460414 | -14.9694 | `width=1, bank=0, face_h=-0.473818, column_h=-0.250682` | `0.997434/1` | 0.268542 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-1.29274/-1` | 0.376787 | 3.154 | `width=1, bank=0, face_h=0.342317, column_h=-0.250682` | `-3.98015/-1` | -2.31062 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-1.20876/-1` | 0.159518 | 4.34232 | `width=0, bank=0, face_h=0.402868, column_h=-0.035892` | `-3.98015/-1` | -2.61188 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-1.16465/-1` | 0.118077 | 0 | `width=0, bank=0, face_h=0.404966, column_h=-0.0920849` | `-3.98015/-1` | -2.69743 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-1.15469/-1` | 0.0770227 | 0 | `width=0, bank=0, face_h=0.387737, column_h=-0.0682888` | `-3.98015/-1` | -2.74844 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-1.32576/-1` | 0.0425631 | 0 | `width=0, bank=0, face_h=0.534581, column_h=0.232225` | `-3.98015/-1` | -2.61183 | `upstream_edge_width_depth_mapping` |
| `lower_edge_face` | 7 | `2-3` | `0.351794/1` | `-0.0477789/0` | -0.399573 | -3.36962 | `width=0, bank=0, face_h=-0.107953, column_h=-0.102779` | `0.487694/1` | 0.1359 | `upstream_edge_y_face_flux_source_balance` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 7 | `1->0` | `-1->-1` | `True` | `False` | `False` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 6 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 4 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- C++ final-frame upstream edge volume-flux signs still disagree with GeoClaw.
- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.
- GeoClaw lower/upper edge opposition is still missing from C++ upstream edge states.

## Next Levers

- Start with `upper_edge_face` column 1 rows 8-9; q delta is 1.1376 m3/s, balance delta is 1.63225 m3/s2, native post-source delta is -1.68153 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Preserve GeoClaw's lower-positive/upper-negative edge opposition across upstream wet-band columns.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
