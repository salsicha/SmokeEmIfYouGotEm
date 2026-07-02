# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_throat_entry_final_depth_balance_face_state_width_depth.json`
Face/source audit report: `physics/reports/milestone18/constriction_throat_entry_final_depth_balance_face_source_audit.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `9`
- Source-balance blockers: `10`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `0`
- Max abs volume-flux delta: `1.00669` m3/s
- Max abs balance delta: `14.1035` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | `0.70411/1` | 0.6298 | 14.1035 | `width=0, bank=0, face_h=0.530364, column_h=0.010476` | `0.46892/1` | 0.39461 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.637392/1` | 0.575876 | 11.8114 | `width=0, bank=0, face_h=0.450724, column_h=0.228958` | `0.469018/1` | 0.407502 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.942069/1` | -0.520888 | -9.14867 | `width=0, bank=0, face_h=-0.273519, column_h=-0.0925023` | `1.70198/1` | 0.239026 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-1.22034/-1` | 0.449193 | 2.44804 | `width=1, bank=0, face_h=0.299945, column_h=-0.253683` | `-3.89626/-1` | -2.22673 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-1.58812/-1` | -0.219845 | 4.42006 | `width=0, bank=0, face_h=0.354694, column_h=-0.0255571` | `-3.98015/-1` | -2.61188 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-1.1667/-1` | 0.201619 | 5.49791 | `width=0, bank=0, face_h=0.530824, column_h=0.228958` | `-3.98015/-1` | -2.61183 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-1.38294/-1` | -0.151231 | 4.05534 | `width=0, bank=0, face_h=0.327114, column_h=-0.0645374` | `-3.98015/-1` | -2.74844 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-1.21678/-1` | 0.0659378 | 0 | `width=0, bank=0, face_h=0.346364, column_h=-0.0925023` | `-3.97252/-1` | -2.68979 | `upstream_edge_width_depth_mapping` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.695129/1` | -0.0337629 | 0 | `width=1, bank=0, face_h=-0.442458, column_h=-0.253683` | `1.31821/1` | 0.589314 | `upstream_edge_width_depth_mapping` |
| `lower_edge_face` | 4 | `1-2` | `0.236126/1` | `1.24282/1` | 1.00669 | -3.7828 | `width=0, bank=0, face_h=-0.176613, column_h=-0.0645374` | `2.03779/1` | 1.80166 | `upstream_edge_y_face_flux_source_balance` |
| `lower_edge_face` | 2 | `1-2` | `1.31687/1` | `1.87765/1` | 0.560778 | 3.90476 | `width=0, bank=0, face_h=0.0797869, column_h=0.00747285` | `2.90326/1` | 1.58639 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `-2.18419/-1` | -0.272917 | 2.24008 | `width=0, bank=0, face_h=0.160619, column_h=0.00747285` | `-3.98015/-1` | -2.06887 | `upstream_edge_y_face_flux_source_balance` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 4 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 6 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 7 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.

## Next Levers

- Start with `lower_edge_face` column 8 rows 2-3; q delta is 0.6298 m3/s, balance delta is 14.1035 m3/s2, native post-source delta is 0.39461 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
