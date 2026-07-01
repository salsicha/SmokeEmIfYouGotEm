# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `reports/milestone18/constriction_edge_face_convention_face_state_width_depth_diagnostic.json`
Face/source audit report: `reports/milestone18/constriction_edge_face_convention_face_source_audit_diagnostic.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `12`
- Source-balance blockers: `12`
- Native post-source sign mismatches: `6`
- Paired-edge opposition mismatches: `10`
- Max abs volume-flux delta: `2.33225` m3/s
- Max abs balance delta: `15.4882` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `0.642842/1` | 2.31237 | 8.60956 | `width=1, bank=0, face_h=0.725794, column_h=-0.0323006` | `0.00646466/0` | 1.676 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 0 | `1-2` | `2.04571/1` | `0.0220884/0` | -2.02362 | -15.4882 | `width=-2, bank=1, face_h=-0.408442, column_h=-0.181905` | `-0.0993244/-1` | -2.14503 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 1 | `1-2` | `1.97499/1` | `0.0365035/0` | -1.93848 | -7.51415 | `width=-1, bank=1, face_h=-0.12333, column_h=-0.0189808` | `-0.195658/-1` | -2.17064 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 7 | `7-8` | `-1.25704/-1` | `0.663418/1` | 1.92046 | 3.96959 | `width=-2, bank=2, face_h=0.238427, column_h=0.367199` | `0.555651/1` | 1.81269 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `0.143938/1` | 1.51226 | 9.53286 | `width=0, bank=0, face_h=0.832214, column_h=0.452989` | `0.144003/1` | 1.51232 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.0437077/0` | -0.0178087 | 14.8127 | `width=0, bank=0, face_h=0.576819, column_h=0.452989` | `-3.74375/-1` | -3.80526 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `0.0336336/0` | 2.33225 | 0.625433 | `width=-1, bank=1, face_h=0.459303, column_h=-0.0189808` | `-1.74243/-1` | 0.556185 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 0 | `8-9` | `-2.00767/-1` | `0.010435/0` | 2.01811 | -1.59833 | `width=-2, bank=1, face_h=0.129269, column_h=-0.181905` | `-1.67658/-1` | 0.33109 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `0.0542254/0` | 1.9655 | 3.69359 | `width=0, bank=0, face_h=0.552272, column_h=-0.0226275` | `-1.79387/-1` | 0.117407 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `0.438356/1` | 1.72108 | 9.88936 | `width=0, bank=0, face_h=0.768789, column_h=0.116583` | `-0.690307/-1` | 0.592416 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `0.134357/1` | 1.50263 | 6.34389 | `width=0, bank=0, face_h=0.594182, column_h=0.0131241` | `-1.73554/-1` | -0.367261 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `0.25631/1` | 1.48802 | 8.2582 | `width=0, bank=0, face_h=0.674612, column_h=0.0708009` | `-1.27367/-1` | -0.0419579 | `upstream_edge_width_depth_flux_balance` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 1 | `1->0` | `-1->0` | `True` | `False` | `False` |
| 6 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 0 | `1->0` | `-1->0` | `True` | `False` | `False` |
| 2 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 7 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 8 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 5 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 9 | `1->0` | `-1->1` | `True` | `False` | `False` |
| 3 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 4 | `1->1` | `-1->1` | `True` | `False` | `False` |

## Blocked Reasons

- C++ final-frame upstream edge volume-flux signs still disagree with GeoClaw.
- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Native C++ post-source y-face flux signs still disagree with GeoClaw.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.
- GeoClaw lower/upper edge opposition is still missing from C++ upstream edge states.

## Next Levers

- Start with `upper_edge_face` column 6 rows 8-9; q delta is 2.31237 m3/s, balance delta is 8.60956 m3/s2, native post-source delta is 1.676 m3/s, wet-width delta is 1 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Preserve GeoClaw's lower-positive/upper-negative edge opposition across upstream wet-band columns.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
