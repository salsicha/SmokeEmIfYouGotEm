# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `reports/milestone18/constriction_upstream_edge_support_face_state_width_depth_diagnostic.json`
Face/source audit report: `reports/milestone18/constriction_upstream_edge_support_face_source_audit_diagnostic.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `12`
- Source-balance blockers: `12`
- Native post-source sign mismatches: `6`
- Paired-edge opposition mismatches: `10`
- Max abs volume-flux delta: `2.33091` m3/s
- Max abs balance delta: `16.1293` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `0.661378/1` | 2.33091 | 10.4804 | `width=1, bank=0, face_h=0.824555, column_h=0.0393688` | `0.000312364/0` | 1.66984 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 0 | `1-2` | `2.04571/1` | `0.0329342/0` | -2.01278 | -16.1293 | `width=-2, bank=1, face_h=-0.431999, column_h=-0.215297` | `-0.0486263/0` | -2.09434 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 7 | `7-8` | `-1.25704/-1` | `0.693717/1` | 1.95075 | 6.47764 | `width=-2, bank=2, face_h=0.356975, column_h=0.456106` | `0.581104/1` | 1.83814 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 8 | `7-8` | `-1.40735/-1` | `0.379457/1` | 1.7868 | 3.61562 | `width=0, bank=0, face_h=0.238906, column_h=0.336307` | `0.379595/1` | 1.78694 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `0.168088/1` | 1.53641 | 11.4815 | `width=0, bank=0, face_h=0.938336, column_h=0.543951` | `0.168162/1` | 1.53648 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `0.002881/0` | 2.3015 | 0.131475 | `width=-1, bank=1, face_h=0.425348, column_h=-0.0423658` | `-1.74478/-1` | 0.553839 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 0 | `8-9` | `-2.00767/-1` | `-0.0141869/0` | 1.99348 | -2.1728 | `width=-2, bank=1, face_h=0.0857881, column_h=-0.215297` | `-1.66842/-1` | 0.339251 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `0.0187728/0` | 1.93005 | 3.50238 | `width=0, bank=0, face_h=0.540152, column_h=-0.0298204` | `-1.81469/-1` | 0.0965872 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `0.425212/1` | 1.70793 | 11.5134 | `width=0, bank=0, face_h=0.855466, column_h=0.179942` | `-0.738707/-1` | 0.544016 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `0.0902148/1` | 1.45849 | 6.60698 | `width=0, bank=0, face_h=0.610433, column_h=0.0271335` | `-1.78323/-1` | -0.414955 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `0.220163/1` | 1.45188 | 9.27381 | `width=0, bank=0, face_h=0.732251, column_h=0.112756` | `-1.33369/-1` | -0.101979 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 1 | `1-2` | `1.97499/1` | `0.0464699/1` | -1.92852 | -8.03971 | `width=-1, bank=1, face_h=-0.142193, column_h=-0.0423658` | `-0.151073/-1` | -2.12606 | `upstream_edge_width_depth_flux_balance` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 6 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 1 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 0 | `1->0` | `-1->0` | `True` | `False` | `False` |
| 7 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 2 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 8 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 5 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 9 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 3 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 4 | `1->1` | `-1->1` | `True` | `False` | `False` |

## Blocked Reasons

- C++ final-frame upstream edge volume-flux signs still disagree with GeoClaw.
- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Native C++ post-source y-face flux signs still disagree with GeoClaw.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.
- GeoClaw lower/upper edge opposition is still missing from C++ upstream edge states.

## Next Levers

- Start with `upper_edge_face` column 6 rows 8-9; q delta is 2.33091 m3/s, balance delta is 10.4804 m3/s2, native post-source delta is 1.66984 m3/s, wet-width delta is 1 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Preserve GeoClaw's lower-positive/upper-negative edge opposition across upstream wet-band columns.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
