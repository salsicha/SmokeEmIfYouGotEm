# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `physics/reports/milestone18/constriction_y_face_state_reconstruction_face_state_width_depth_diagnostic.json`
Face/source audit report: `physics/reports/milestone18/constriction_y_face_state_reconstruction_face_source_audit_diagnostic.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `12`
- Source-balance blockers: `12`
- Native post-source sign mismatches: `5`
- Paired-edge opposition mismatches: `10`
- Max abs volume-flux delta: `2.31188` m3/s
- Max abs balance delta: `15.4598` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 0 | `1-2` | `2.04571/1` | `0.0156733/0` | -2.03004 | -15.4598 | `width=-2, bank=1, face_h=-0.407394, column_h=-0.180283` | `-0.526633/-1` | -2.57234 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 1 | `1-2` | `1.97499/1` | `0.0249939/0` | -1.94999 | -7.47588 | `width=-1, bank=1, face_h=-0.121934, column_h=-0.0170277` | `-0.627916/-1` | -2.6029 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 7 | `7-8` | `-1.25704/-1` | `0.587196/1` | 1.84423 | 3.7595 | `width=-2, bank=2, face_h=0.23036, column_h=0.36115` | `0.480288/1` | 1.73733 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `0.106/1` | 1.47432 | 9.39791 | `width=0, bank=0, face_h=0.824915, column_h=0.446733` | `0.106047/1` | 1.47437 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.034192/0` | -0.0273243 | 14.7079 | `width=0, bank=0, face_h=0.57317, column_h=0.446733` | `-3.7397/-1` | -3.80121 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `0.013262/0` | 2.31188 | 0.664542 | `width=-1, bank=1, face_h=0.462006, column_h=-0.0170277` | `-1.76216/-1` | 0.536457 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `0.571263/1` | 2.24079 | 8.44944 | `width=1, bank=0, face_h=0.719577, column_h=-0.0384993` | `-0.0605623/-1` | 1.60897 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 0 | `8-9` | `-2.00767/-1` | `-0.000811807/0` | 2.00686 | -1.57089 | `width=-2, bank=1, face_h=0.131317, column_h=-0.180283` | `-1.68807/-1` | 0.319598 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `0.0258384/0` | 1.93712 | 3.74314 | `width=0, bank=0, face_h=0.555515, column_h=-0.0205582` | `-1.82068/-1` | 0.0905988 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `0.363212/1` | 1.64594 | 9.76692 | `width=0, bank=0, face_h=0.763868, column_h=0.114192` | `-0.757489/-1` | 0.525234 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `0.080096/0` | 1.44837 | 6.37694 | `width=0, bank=0, face_h=0.596607, column_h=0.0166863` | `-1.78397/-1` | -0.415699 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `0.187296/1` | 1.41901 | 8.20501 | `width=0, bank=0, face_h=0.672553, column_h=0.0703835` | `-1.33391/-1` | -0.102195 | `upstream_edge_width_depth_flux_balance` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 1 | `1->0` | `-1->0` | `True` | `False` | `False` |
| 6 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 0 | `1->0` | `-1->0` | `True` | `False` | `False` |
| 2 | `1->0` | `-1->0` | `True` | `False` | `False` |
| 7 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 8 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 5 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 9 | `1->0` | `-1->1` | `True` | `False` | `False` |
| 3 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 4 | `1->1` | `-1->1` | `True` | `False` | `False` |

## Blocked Reasons

- C++ final-frame upstream edge volume-flux signs still disagree with GeoClaw.
- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Native C++ post-source y-face flux signs still disagree with GeoClaw.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.
- GeoClaw lower/upper edge opposition is still missing from C++ upstream edge states.

## Next Levers

- Start with `lower_edge_face` column 0 rows 1-2; q delta is -2.03004 m3/s, balance delta is -15.4598 m3/s2, native post-source delta is -2.57234 m3/s, wet-width delta is -2 cells, and bank-row delta is 1 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Preserve GeoClaw's lower-positive/upper-negative edge opposition across upstream wet-band columns.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
