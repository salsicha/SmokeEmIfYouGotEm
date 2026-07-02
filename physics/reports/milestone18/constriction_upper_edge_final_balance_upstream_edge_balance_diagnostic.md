# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `reports/milestone18/constriction_upper_edge_final_balance_face_state_width_depth_diagnostic.json`
Face/source audit report: `reports/milestone18/constriction_upper_edge_final_balance_face_source_audit_diagnostic.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `12`
- Source-balance blockers: `12`
- Native post-source sign mismatches: `2`
- Paired-edge opposition mismatches: `1`
- Max abs volume-flux delta: `1.99953` m3/s
- Max abs balance delta: `15.9559` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-0.0545847/0` | 1.17713 | 4.40553 | `width=-1, bank=1, face_h=0.441478, column_h=0.0307705` | `-1.93118/-1` | -0.699467 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | `0.762303/1` | 0.687993 | 13.6503 | `width=0, bank=0, face_h=0.510141, column_h=-0.0231101` | `-0.18945/-1` | -0.26376 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.721048/1` | 0.659531 | 12.0918 | `width=0, bank=0, face_h=0.455826, column_h=0.236663` | `-0.58299/-1` | -0.644506 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `-0.299087/-1` | 1.99953 | -0.766169 | `width=-2, bank=1, face_h=0.356761, column_h=0.0240212` | `-2.71176/-1` | -0.413141 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 0 | `1-2` | `2.04571/1` | `0.208981/1` | -1.83673 | -15.9559 | `width=-2, bank=1, face_h=-0.42765, column_h=-0.268673` | `2.02816/1` | -0.0175494 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 0 | `8-9` | `-2.00767/-1` | `-0.229651/-1` | 1.77802 | -3.34632 | `width=-2, bank=1, face_h=-0.0113311, column_h=-0.268673` | `-2.56095/-1` | -0.553278 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 1 | `1-2` | `1.97499/1` | `0.199555/1` | -1.77543 | -7.54571 | `width=-2, bank=1, face_h=-0.12607, column_h=0.0240212` | `1.87546/1` | -0.0995263 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `-0.354976/-1` | 1.5563 | 2.13928 | `width=-1, bank=1, face_h=0.444394, column_h=0.0128134` | `-2.81849/-1` | -0.907211 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-0.190436/-1` | 1.47909 | 3.3568 | `width=0, bank=1, face_h=0.428141, column_h=-0.117384` | `-0.828621/-1` | 0.840909 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-0.151579/-1` | 1.21669 | 3.90633 | `width=-1, bank=1, face_h=0.438786, column_h=0.0348568` | `-2.57645/-1` | -1.20818 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-0.0940721/-1` | 1.18865 | 4.70741 | `width=-1, bank=1, face_h=0.468931, column_h=0.0302913` | `-1.36676/-1` | -0.0840391 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-0.19768/-1` | 1.17064 | 5.26413 | `width=0, bank=0, face_h=0.573318, column_h=0.236663` | `-1.31768/-1` | 0.0506416 | `upstream_edge_width_depth_flux_balance` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 4 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 6 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 7 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- C++ final-frame upstream edge volume-flux signs still disagree with GeoClaw.
- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Native C++ post-source y-face flux signs still disagree with GeoClaw.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.
- GeoClaw lower/upper edge opposition is still missing from C++ upstream edge states.

## Next Levers

- Start with `upper_edge_face` column 4 rows 8-9; q delta is 1.17713 m3/s, balance delta is 4.40553 m3/s2, native post-source delta is -0.699467 m3/s, wet-width delta is -1 cells, and bank-row delta is 1 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Preserve GeoClaw's lower-positive/upper-negative edge opposition across upstream wet-band columns.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
