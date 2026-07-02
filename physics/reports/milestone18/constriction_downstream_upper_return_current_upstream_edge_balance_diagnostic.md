# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_downstream_upper_return_current_face_state_width_depth_diagnostic.json`
Face/source audit report: `physics/reports/milestone18/constriction_downstream_upper_return_current_face_source_audit_diagnostic.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `12`
- Source-balance blockers: `9`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `1`
- Max abs volume-flux delta: `1.4773` m3/s
- Max abs balance delta: `15.0904` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 0 | `1-2` | `2.04571/1` | `0.568408/1` | -1.4773 | -11.9523 | `width=0, bank=0, face_h=-0.294602, column_h=-0.266457` | `2.26908/1` | 0.223368 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.273117/1` | -1.18984 | -11.5209 | `width=0, bank=0, face_h=-0.326841, column_h=-0.104442` | `1.28545/1` | -0.17751 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `-1.22934/-1` | 1.06928 | 0.750931 | `width=0, bank=0, face_h=0.394724, column_h=-0.0661109` | `-3.98015/-1` | -1.68153 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 0 | `8-9` | `-2.00767/-1` | `-0.96476/-1` | 1.04291 | -0.982721 | `width=0, bank=0, face_h=0.124282, column_h=-0.266457` | `-3.79134/-1` | -1.78367 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `-1.30855/-1` | 0.60273 | 2.90907 | `width=0, bank=0, face_h=0.423113, column_h=-0.0306414` | `-3.98015/-1` | -2.06887 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | `0.621356/1` | 0.547046 | 13.4199 | `width=0, bank=0, face_h=0.510111, column_h=-0.0230365` | `0.349966/1` | 0.275656 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.195206/1` | -0.533686 | -15.0904 | `width=1, bank=0, face_h=-0.476756, column_h=-0.256853` | `0.903376/1` | 0.174485 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.574834/1` | 0.513317 | 11.1602 | `width=0, bank=0, face_h=0.429913, column_h=0.193578` | `0.390393/1` | 0.328877 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-1.442/-1` | 0.22753 | 3.31962 | `width=1, bank=0, face_h=0.334509, column_h=-0.256853` | `-3.98015/-1` | -2.31062 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-1.29877/-1` | 0.0695501 | 0 | `width=0, bank=0, face_h=0.490149, column_h=0.193578` | `-3.98015/-1` | -2.61183 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-1.29949/-1` | 0.0687831 | 0 | `width=0, bank=0, face_h=0.36699, column_h=-0.0627775` | `-3.98015/-1` | -2.61188 | `upstream_edge_width_depth_mapping` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-1.25543/-1` | 0.0272882 | 0 | `width=0, bank=0, face_h=0.388783, column_h=-0.104442` | `-3.98015/-1` | -2.69743 | `upstream_edge_width_depth_mapping` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 7 | `1->-1` | `-1->-1` | `True` | `False` | `False` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 6 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 4 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.
- GeoClaw lower/upper edge opposition is still missing from C++ upstream edge states.

## Next Levers

- Start with `lower_edge_face` column 0 rows 1-2; q delta is -1.4773 m3/s, balance delta is -11.9523 m3/s2, native post-source delta is 0.223368 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Preserve GeoClaw's lower-positive/upper-negative edge opposition across upstream wet-band columns.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
