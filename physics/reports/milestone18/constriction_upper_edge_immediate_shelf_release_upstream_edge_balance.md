# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_upper_edge_immediate_shelf_release_face_state_width_depth.json`
Face/source audit report: `physics/reports/milestone18/constriction_upper_edge_immediate_shelf_release_face_source_audit.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `9`
- Source-balance blockers: `12`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `0`
- Max abs volume-flux delta: `0.777682` m3/s
- Max abs balance delta: `14.1035` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.685275/1` | -0.777682 | -9.85657 | `width=0, bank=0, face_h=-0.283247, column_h=-0.0903834` | `1.64387/1` | 0.180913 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | `0.70411/1` | 0.6298 | 14.1035 | `width=0, bank=0, face_h=0.530364, column_h=0.0104754` | `0.468921/1` | 0.394611 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-1.08978/-1` | 0.579755 | 2.4889 | `width=1, bank=0, face_h=0.31793, column_h=-0.252554` | `-3.77641/-1` | -2.10687 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.637393/1` | 0.575876 | 11.8114 | `width=0, bank=0, face_h=0.450725, column_h=0.22896` | `0.469017/1` | 0.407501 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-0.972352/-1` | 0.310371 | 3.99201 | `width=0, bank=0, face_h=0.379591, column_h=-0.0903834` | `-3.74297/-1` | -2.46024 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-1.13146/-1` | 0.236812 | 4.43989 | `width=0, bank=0, face_h=0.418404, column_h=-0.0214668` | `-3.98015/-1` | -2.61188 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-1.1667/-1` | 0.201618 | 5.49793 | `width=0, bank=0, face_h=0.530826, column_h=0.22896` | `-3.98015/-1` | -2.61183 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-1.03319/-1` | 0.198528 | 4.13908 | `width=0, bank=0, face_h=0.375582, column_h=-0.0614418` | `-3.86997/-1` | -2.63826 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.553822/1` | -0.17507 | -13.9786 | `width=1, bank=0, face_h=-0.447928, column_h=-0.252554` | `1.28158/1` | 0.552687 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 4 | `1-2` | `0.236126/1` | `0.877416/1` | 0.641289 | -4.97515 | `width=0, bank=0, face_h=-0.190748, column_h=-0.0614418` | `1.96298/1` | 1.72685 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `-1.68926/-1` | 0.60936 | -0.967639 | `width=0, bank=0, face_h=0.158391, column_h=-0.0347551` | `-3.71027/-1` | -1.41165 | `upstream_edge_y_face_flux_source_balance` |
| `upper_edge_face` | 0 | `8-9` | `-2.00767/-1` | `-1.48272/-1` | 0.524953 | -2.30834 | `width=0, bank=0, face_h=-0.0811384, column_h=-0.205261` | `-3.45255/-1` | -1.44487 | `upstream_edge_y_face_flux_source_balance` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 4 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 6 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 7 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.

## Next Levers

- Start with `lower_edge_face` column 5 rows 1-2; q delta is -0.777682 m3/s, balance delta is -9.85657 m3/s2, native post-source delta is 0.180913 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
