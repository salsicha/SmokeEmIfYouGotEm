# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `reports/milestone18/constriction_upstream_boundary_interior_relax_face_state_width_depth_diagnostic.json`
Face/source audit report: `reports/milestone18/constriction_upstream_boundary_interior_relax_face_source_audit_diagnostic.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `12`
- Source-balance blockers: `11`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `1`
- Max abs volume-flux delta: `1.67734` m3/s
- Max abs balance delta: `14.0552` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 0 | `1-2` | `2.04571/1` | `0.368368/1` | -1.67734 | -14.0552 | `width=0, bank=0, face_h=-0.362368, column_h=-0.335967` | `2.32766/1` | 0.281947 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 0 | `8-9` | `-2.00767/-1` | `-0.333483/-1` | 1.67419 | -1.97333 | `width=0, bank=0, face_h=0.0947014, column_h=-0.335967` | `-3.23334/-1` | -1.22567 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.228253/1` | -1.2347 | -11.4141 | `width=0, bank=0, face_h=-0.322251, column_h=-0.0747016` | `1.38405/1` | -0.0789025 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `-0.819787/-1` | 1.09149 | 2.968 | `width=0, bank=0, face_h=0.476308, column_h=-0.0448694` | `-3.85043/-1` | -1.93916 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-0.726253/-1` | 0.943277 | 3.61019 | `width=1, bank=0, face_h=0.424417, column_h=-0.22614` | `-3.63722/-1` | -1.96769 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-0.535559/-1` | 0.83276 | 5.48395 | `width=0, bank=0, face_h=0.577316, column_h=0.240184` | `-3.51846/-1` | -2.15014 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-0.691311/-1` | 0.676962 | 4.39992 | `width=0, bank=0, face_h=0.451958, column_h=-0.0557118` | `-3.73455/-1` | -2.36628 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-0.623406/-1` | 0.659317 | 4.94852 | `width=0, bank=0, face_h=0.468968, column_h=-0.0747016` | `-3.59516/-1` | -2.31244 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-0.574555/-1` | 0.657159 | 4.74367 | `width=0, bank=0, face_h=0.449899, column_h=-0.065524` | `-3.59583/-1` | -2.36412 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.683849/1` | 0.622333 | 12.0783 | `width=0, bank=0, face_h=0.457815, column_h=0.240184` | `0.655811/1` | 0.594295 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | `0.694289/1` | 0.619979 | 13.7414 | `width=0, bank=0, face_h=0.517744, column_h=-0.0104916` | `0.705854/1` | 0.631544 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `-0.640357/-1` | 1.65826 | 0.0246303 | `width=0, bank=0, face_h=0.397762, column_h=-0.114483` | `-3.61289/-1` | -1.31427 | `upstream_edge_width_depth_mapping` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 7 | `1->-1` | `-1->-1` | `True` | `False` | `False` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
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

- Start with `lower_edge_face` column 0 rows 1-2; q delta is -1.67734 m3/s, balance delta is -14.0552 m3/s2, native post-source delta is 0.281947 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Preserve GeoClaw's lower-positive/upper-negative edge opposition across upstream wet-band columns.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
