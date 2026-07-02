# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_lower_edge_transition_source_depth_face_state_width_depth_diagnostic.json`
Face/source audit report: `physics/reports/milestone18/constriction_lower_edge_transition_source_depth_face_source_audit_diagnostic.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `11`
- Source-balance blockers: `9`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `1`
- Max abs volume-flux delta: `0.86887` m3/s
- Max abs balance delta: `14.1467` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `-1.42975/-1` | 0.86887 | 2.07857 | `width=0, bank=0, face_h=0.465742, column_h=-0.0171191` | `-3.98015/-1` | -1.68153 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.612155/1` | -0.850802 | -9.87212 | `width=0, bank=0, face_h=-0.280354, column_h=-0.0864117` | `1.5738/1` | 0.11084 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | `0.663679/1` | 0.589369 | 14.1467 | `width=0, bank=0, face_h=0.534233, column_h=0.0168779` | `0.333705/1` | 0.259395 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.598253/1` | 0.536736 | 11.8727 | `width=0, bank=0, face_h=0.455332, column_h=0.236767` | `0.333362/1` | 0.271845 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-1.18374/-1` | 0.485786 | 2.72242 | `width=1, bank=0, face_h=0.324323, column_h=-0.247561` | `-3.88703/-1` | -2.2175 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `-1.53096/-1` | 0.380314 | 4.28668 | `width=0, bank=0, face_h=0.492138, column_h=0.0168665` | `-3.98015/-1` | -2.06887 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-1.02797/-1` | 0.254749 | 4.13894 | `width=0, bank=0, face_h=0.384691, column_h=-0.0864117` | `-3.80598/-1` | -2.52325 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.474318/1` | -0.254574 | -13.9538 | `width=1, bank=0, face_h=-0.444042, column_h=-0.247561` | `1.1896/1` | 0.460708 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-1.09459/-1` | 0.137126 | 0 | `width=0, bank=0, face_h=0.379211, column_h=-0.0585241` | `-3.93537/-1` | -2.70366 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-1.25572/-1` | 0.112558 | 0 | `width=0, bank=0, face_h=0.420281, column_h=-0.0202816` | `-3.98015/-1` | -2.61188 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-1.3264/-1` | 0.0419223 | 0 | `width=0, bank=0, face_h=0.539763, column_h=0.236767` | `-3.98015/-1` | -2.61183 | `upstream_edge_width_depth_mapping` |
| `lower_edge_face` | 7 | `2-3` | `0.351794/1` | `0.0289766/0` | -0.322818 | -3.17803 | `width=0, bank=0, face_h=-0.10146, column_h=-0.0988227` | `0.551713/1` | 0.199919 | `upstream_edge_y_face_flux_source_balance` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 7 | `1->0` | `-1->-1` | `True` | `False` | `False` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
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

- Start with `upper_edge_face` column 1 rows 8-9; q delta is 0.86887 m3/s, balance delta is 2.07857 m3/s2, native post-source delta is -1.68153 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Preserve GeoClaw's lower-positive/upper-negative edge opposition across upstream wet-band columns.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
