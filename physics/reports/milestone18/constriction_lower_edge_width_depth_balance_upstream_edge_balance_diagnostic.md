# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `reports/milestone18/constriction_lower_edge_width_depth_balance_face_state_width_depth_diagnostic.json`
Face/source audit report: `reports/milestone18/constriction_lower_edge_width_depth_balance_face_source_audit_diagnostic.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `12`
- Source-balance blockers: `12`
- Native post-source sign mismatches: `5`
- Paired-edge opposition mismatches: `10`
- Max abs volume-flux delta: `2.97684` m3/s
- Max abs balance delta: `15.7838` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `1.30731/1` | 2.97684 | 11.7197 | `width=1, bank=0, face_h=0.855736, column_h=0.0630603` | `0.384098/1` | 2.05363 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 7 | `7-8` | `-1.25704/-1` | `1.35527/1` | 2.61231 | 7.97982 | `width=-2, bank=2, face_h=0.398292, column_h=0.487092` | `1.20251/1` | 2.45954 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 8 | `7-8` | `-1.40735/-1` | `0.869809/1` | 2.27716 | 4.75684 | `width=0, bank=0, face_h=0.280214, column_h=0.371713` | `0.869809/1` | 2.27716 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `0.533395/1` | 1.90171 | 12.3448 | `width=0, bank=0, face_h=0.976824, column_h=0.57694` | `0.533507/1` | 1.90183 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `0.0659398/0` | 2.36456 | 0.405672 | `width=-1, bank=1, face_h=0.44412, column_h=-0.0285739` | `-2.50758/-1` | -0.208963 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `1.06589/1` | 2.34861 | 12.4438 | `width=0, bank=0, face_h=0.878728, column_h=0.201482` | `-0.567483/-1` | 0.71524 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 0 | `8-9` | `-2.00767/-1` | `0.0213771/0` | 2.02905 | -1.83037 | `width=-2, bank=1, face_h=0.111857, column_h=-0.194088` | `-2.45838/-1` | -0.450712 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `0.107149/1` | 2.01843 | 3.64949 | `width=0, bank=0, face_h=0.54912, column_h=-0.0234252` | `-2.55038/-1` | -0.639107 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `0.739692/1` | 1.97141 | 9.80709 | `width=0, bank=0, face_h=0.746853, column_h=0.129693` | `-1.48135/-1` | -0.249638 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `0.408781/1` | 1.77705 | 6.66777 | `width=0, bank=0, face_h=0.608444, column_h=0.0319355` | `-2.29128/-1` | -0.923003 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 7 | `2-3` | `0.351794/1` | `0.762363/1` | 0.410569 | 3.50142 | `width=-2, bank=2, face_h=0.100491, column_h=0.487092` | `-1.86821/-1` | -2.22 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 0 | `1-2` | `2.04571/1` | `0.0539762/1` | -1.99173 | -15.7838 | `width=-2, bank=1, face_h=-0.41938, column_h=-0.194088` | `1.80163/1` | -0.244076 | `upstream_edge_width_depth_flux_balance` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 6 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 7 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 1 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 5 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 8 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 0 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 2 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 4 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 9 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 3 | `1->1` | `-1->1` | `True` | `False` | `False` |

## Blocked Reasons

- C++ final-frame upstream edge volume-flux signs still disagree with GeoClaw.
- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Native C++ post-source y-face flux signs still disagree with GeoClaw.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.
- GeoClaw lower/upper edge opposition is still missing from C++ upstream edge states.

## Next Levers

- Start with `upper_edge_face` column 6 rows 8-9; q delta is 2.97684 m3/s, balance delta is 11.7197 m3/s2, native post-source delta is 2.05363 m3/s, wet-width delta is 1 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Preserve GeoClaw's lower-positive/upper-negative edge opposition across upstream wet-band columns.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
