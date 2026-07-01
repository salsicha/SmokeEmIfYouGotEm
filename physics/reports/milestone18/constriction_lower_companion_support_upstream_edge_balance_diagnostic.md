# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `reports/milestone18/constriction_lower_companion_support_face_state_width_depth_diagnostic.json`
Face/source audit report: `reports/milestone18/constriction_lower_companion_support_face_source_audit_diagnostic.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `12`
- Source-balance blockers: `12`
- Native post-source sign mismatches: `6`
- Paired-edge opposition mismatches: `8`
- Max abs volume-flux delta: `4.54348` m3/s
- Max abs balance delta: `12.7446` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `-3.08053/-1` | -4.54348 | 1.01423 | `width=-1, bank=1, face_h=-0.207799, column_h=0.346015` | `-0.470514/-1` | -1.93347 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `-2.38264/-1` | -3.11153 | -4.66712 | `width=1, bank=0, face_h=-0.29771, column_h=0.0719138` | `-0.897889/-1` | -1.62678 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `1.09176/1` | 2.7613 | 11.8491 | `width=1, bank=0, face_h=0.875537, column_h=0.0719138` | `0.178557/1` | 1.84809 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 7 | `7-8` | `-1.25704/-1` | `1.1537/1` | 2.41074 | 8.19067 | `width=-1, bank=1, face_h=0.418162, column_h=0.323402` | `1.00161/1` | 2.25865 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 8 | `7-8` | `-1.40735/-1` | `0.727947/1` | 2.13529 | 4.90341 | `width=0, bank=0, face_h=0.292348, column_h=0.382114` | `0.728007/1` | 2.13535 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `0.4326/1` | 1.80092 | 12.5911 | `width=0, bank=0, face_h=0.992194, column_h=0.590115` | `0.432732/1` | 1.80105 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `0.0669915/0` | 2.36561 | 0.61637 | `width=-1, bank=1, face_h=0.458534, column_h=-0.0180205` | `-2.51549/-1` | -0.216866 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `0.917725/1` | 2.20045 | 12.7446 | `width=-1, bank=1, face_h=0.901838, column_h=0.346015` | `-0.713288/-1` | 0.569435 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 0 | `8-9` | `-2.00767/-1` | `0.0218877/0` | 2.02956 | -1.64405 | `width=-2, bank=1, face_h=0.125839, column_h=-0.182715` | `-2.46578/-1` | -0.458106 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `0.109022/1` | 2.0203 | 3.90964 | `width=0, bank=0, face_h=0.565623, column_h=-0.0123918` | `-2.55959/-1` | -0.648318 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `0.627976/1` | 1.85969 | 10.2003 | `width=-1, bank=1, face_h=0.772915, column_h=0.265474` | `-1.595/-1` | -0.363287 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `0.368995/1` | 1.73727 | 7.29556 | `width=-1, bank=1, face_h=0.646995, column_h=0.16597` | `-2.34779/-1` | -0.979513 | `upstream_edge_width_depth_flux_balance` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 7 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 1 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 8 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 0 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 2 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 4 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 9 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 3 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 5 | `1->-1` | `-1->1` | `True` | `True` | `True` |
| 6 | `1->-1` | `-1->1` | `True` | `True` | `True` |

## Blocked Reasons

- C++ final-frame upstream edge volume-flux signs still disagree with GeoClaw.
- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Native C++ post-source y-face flux signs still disagree with GeoClaw.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.
- GeoClaw lower/upper edge opposition is still missing from C++ upstream edge states.

## Next Levers

- Start with `lower_edge_face` column 5 rows 1-2; q delta is -4.54348 m3/s, balance delta is 1.01423 m3/s2, native post-source delta is -1.93347 m3/s, wet-width delta is -1 cells, and bank-row delta is 1 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Preserve GeoClaw's lower-positive/upper-negative edge opposition across upstream wet-band columns.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
