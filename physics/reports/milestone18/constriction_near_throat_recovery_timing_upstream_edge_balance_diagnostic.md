# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `reports/milestone18/constriction_near_throat_recovery_timing_face_state_width_depth_diagnostic.json`
Face/source audit report: `reports/milestone18/constriction_near_throat_recovery_timing_face_source_audit_diagnostic.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `12`
- Source-balance blockers: `11`
- Native post-source sign mismatches: `0`
- Paired-edge opposition mismatches: `1`
- Max abs volume-flux delta: `1.67728` m3/s
- Max abs balance delta: `13.8828` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `lower_edge_face` | 0 | `1-2` | `2.04571/1` | `0.368434/1` | -1.67728 | -13.8783 | `width=0, bank=0, face_h=-0.355975, column_h=-0.326816` | `2.31835/1` | 0.272639 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 0 | `8-9` | `-2.00767/-1` | `-0.341566/-1` | 1.66611 | -1.79146 | `width=0, bank=0, face_h=0.108283, column_h=-0.326816` | `-3.25035/-1` | -1.24268 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 5 | `1-2` | `1.46296/1` | `0.228478/1` | -1.23448 | -11.3126 | `width=0, bank=0, face_h=-0.318712, column_h=-0.0692991` | `1.37583/1` | -0.0871309 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `-0.83235/-1` | 1.07893 | 3.17953 | `width=0, bank=0, face_h=0.489747, column_h=-0.0355915` | `-3.87081/-1` | -1.95953 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-0.730708/-1` | 0.938822 | 3.71712 | `width=1, bank=0, face_h=0.431133, column_h=-0.220996` | `-3.6485/-1` | -1.97897 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-0.539319/-1` | 0.829 | 5.66609 | `width=0, bank=0, face_h=0.589091, column_h=0.250493` | `-3.53288/-1` | -2.16456 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-0.70016/-1` | 0.668114 | 4.55214 | `width=0, bank=0, face_h=0.461621, column_h=-0.0484417` | `-3.7496/-1` | -2.38133 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-0.628339/-1` | 0.654384 | 5.06105 | `width=0, bank=0, face_h=0.476037, column_h=-0.0692991` | `-3.60659/-1` | -2.32387 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-0.580805/-1` | 0.650909 | 4.86968 | `width=0, bank=0, face_h=0.457876, column_h=-0.0594594` | `-3.60848/-1` | -2.37677 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.689205/1` | 0.627689 | 12.2504 | `width=0, bank=0, face_h=0.463926, column_h=0.250493` | `0.642457/1` | 0.580941 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | `0.697907/1` | 0.623597 | 13.8828 | `width=0, bank=0, face_h=0.522692, column_h=-0.0022464` | `0.694286/1` | 0.619976 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `-0.653223/-1` | 1.6454 | 0.263018 | `width=0, bank=0, face_h=0.414004, column_h=-0.103311` | `-3.63636/-1` | -1.33774 | `upstream_edge_width_depth_mapping` |

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

- Start with `lower_edge_face` column 0 rows 1-2; q delta is -1.67728 m3/s, balance delta is -13.8783 m3/s2, native post-source delta is 0.272639 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Preserve GeoClaw's lower-positive/upper-negative edge opposition across upstream wet-band columns.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
