# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `reports/milestone18/constriction_upper_edge_flux_magnitude_balance_face_state_width_depth_diagnostic.json`
Face/source audit report: `reports/milestone18/constriction_upper_edge_flux_magnitude_balance_face_source_audit_diagnostic.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `12`
- Source-balance blockers: `11`
- Native post-source sign mismatches: `4`
- Paired-edge opposition mismatches: `4`
- Max abs volume-flux delta: `2.02418` m3/s
- Max abs balance delta: `16.4093` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 0 | `1-2` | `2.04571/1` | `0.0215295/0` | -2.02418 | -16.4093 | `width=-1, bank=1, face_h=-0.442309, column_h=-0.372017` | `1.90721/1` | -0.138502 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.120256/1` | -1.3427 | -11.3272 | `width=0, bank=0, face_h=-0.317802, column_h=-0.0819643` | `-0.0117574/0` | -1.47471 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.0719975/1` | -0.656894 | -14.4601 | `width=1, bank=0, face_h=-0.453549, column_h=-0.227515` | `-0.823012/-1` | -1.5519 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.579583/1` | 0.518067 | 12.1586 | `width=0, bank=0, face_h=0.46702, column_h=0.255238` | `-0.938307/-1` | -0.999823 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | `0.580364/1` | 0.506054 | 13.6054 | `width=0, bank=0, face_h=0.518957, column_h=-0.0085921` | `-0.594169/-1` | -0.668479 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 0 | `8-9` | `-2.00767/-1` | `-0.639133/-1` | 1.36854 | -3.47045 | `width=-1, bank=1, face_h=-0.0470244, column_h=-0.372017` | `-2.91908/-1` | -0.911408 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `-1.08316/-1` | 0.828115 | 2.83805 | `width=0, bank=0, face_h=0.444199, column_h=-0.0670011` | `-3.47536/-1` | -1.56408 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-0.933852/-1` | 0.735679 | 3.74787 | `width=1, bank=0, face_h=0.419085, column_h=-0.227515` | `-1.5503/-1` | 0.11923 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-0.828022/-1` | 0.540297 | 6.00033 | `width=0, bank=0, face_h=0.594572, column_h=0.255238` | `-1.9247/-1` | -0.556378 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-0.850393/-1` | 0.432329 | 4.97292 | `width=0, bank=0, face_h=0.45658, column_h=-0.0819643` | `-2.07748/-1` | -0.794762 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-0.955591/-1` | 0.412683 | 4.42207 | `width=0, bank=0, face_h=0.434085, column_h=-0.0680202` | `-3.29714/-1` | -1.92886 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `-0.905281/-1` | 1.39334 | -0.429149 | `width=0, bank=0, face_h=0.342638, column_h=-0.153993` | `-3.25714/-1` | -0.958516 | `upstream_edge_width_depth_mapping` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 1 | `1->-1` | `-1->-1` | `True` | `False` | `False` |
| 0 | `1->0` | `-1->-1` | `True` | `False` | `False` |
| 2 | `1->-1` | `-1->-1` | `True` | `False` | `False` |
| 7 | `1->-1` | `-1->-1` | `True` | `False` | `False` |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 6 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 4 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- C++ final-frame upstream edge volume-flux signs still disagree with GeoClaw.
- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Native C++ post-source y-face flux signs still disagree with GeoClaw.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.
- GeoClaw lower/upper edge opposition is still missing from C++ upstream edge states.

## Next Levers

- Start with `lower_edge_face` column 0 rows 1-2; q delta is -2.02418 m3/s, balance delta is -16.4093 m3/s2, native post-source delta is -0.138502 m3/s, wet-width delta is -1 cells, and bank-row delta is 1 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Preserve GeoClaw's lower-positive/upper-negative edge opposition across upstream wet-band columns.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
