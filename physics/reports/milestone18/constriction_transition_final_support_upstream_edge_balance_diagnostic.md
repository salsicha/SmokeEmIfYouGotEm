# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `reports/milestone18/constriction_transition_final_support_face_state_width_depth_diagnostic.json`
Face/source audit report: `reports/milestone18/constriction_transition_final_support_face_source_audit_diagnostic.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `12`
- Source-balance blockers: `11`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `1`
- Max abs volume-flux delta: `1.88858` m3/s
- Max abs balance delta: `16.5518` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 0 | `1-2` | `2.04571/1` | `0.157133/1` | -1.88858 | -16.5518 | `width=0, bank=0, face_h=-0.448783, column_h=-0.441029` | `2.30985/1` | 0.264138 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 0 | `8-9` | `-2.00767/-1` | `-0.480015/-1` | 1.52766 | -3.66397 | `width=0, bank=0, face_h=-0.0508607, column_h=-0.441029` | `-3.27533/-1` | -1.26766 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.22797/1` | -1.23499 | -11.5814 | `width=0, bank=0, face_h=-0.328098, column_h=-0.0832645` | `1.39772/1` | -0.0652368 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `-0.810663/-1` | 1.10061 | 2.40896 | `width=0, bank=0, face_h=0.438379, column_h=-0.0707909` | `-3.81531/-1` | -1.90403 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-0.719153/-1` | 0.950378 | 3.59674 | `width=1, bank=0, face_h=0.423963, column_h=-0.226598` | `-3.62941/-1` | -1.95988 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-0.54922/-1` | 0.819098 | 5.78139 | `width=0, bank=0, face_h=0.59616, column_h=0.256625` | `-3.55111/-1` | -2.18279 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-0.685144/-1` | 0.68313 | 4.09105 | `width=0, bank=0, face_h=0.431432, column_h=-0.0708053` | `-3.71355/-1` | -2.34527 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-0.615072/-1` | 0.667651 | 4.76738 | `width=0, bank=0, face_h=0.45754, column_h=-0.0832645` | `-3.57547/-1` | -2.29274 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-0.569115/-1` | 0.662599 | 4.47997 | `width=0, bank=0, face_h=0.432695, column_h=-0.0782361` | `-3.57586/-1` | -2.34414 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.6905/1` | 0.628984 | 12.3576 | `width=0, bank=0, face_h=0.467861, column_h=0.256625` | `0.629889/1` | 0.568373 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | `0.695852/1` | 0.621542 | 13.8114 | `width=0, bank=0, face_h=0.520209, column_h=-0.00653789` | `0.699677/1` | 0.625367 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `-0.674025/-1` | 1.6246 | -0.686194 | `width=0, bank=0, face_h=0.343195, column_h=-0.151382` | `-3.60461/-1` | -1.30599 | `upstream_edge_width_depth_mapping` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 7 | `1->-1` | `-1->-1` | `True` | `False` | `False` |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 6 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 4 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.
- GeoClaw lower/upper edge opposition is still missing from C++ upstream edge states.

## Next Levers

- Start with `lower_edge_face` column 0 rows 1-2; q delta is -1.88858 m3/s, balance delta is -16.5518 m3/s2, native post-source delta is 0.264138 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Preserve GeoClaw's lower-positive/upper-negative edge opposition across upstream wet-band columns.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
