# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `reports/milestone18/constriction_transition_edge_face_balance_face_state_width_depth_diagnostic.json`
Face/source audit report: `reports/milestone18/constriction_transition_edge_face_balance_face_source_audit_diagnostic.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `12`
- Source-balance blockers: `12`
- Native post-source sign mismatches: `1`
- Paired-edge opposition mismatches: `6`
- Max abs volume-flux delta: `2.00203` m3/s
- Max abs balance delta: `16.0255` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `0.0617202/0` | 1.73125 | 3.75159 | `width=0, bank=1, face_h=0.45467, column_h=-0.111648` | `-0.645444/-1` | 1.02409 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `0.32969/1` | 1.69801 | 5.34509 | `width=0, bank=0, face_h=0.575696, column_h=0.230276` | `-0.864055/-1` | 0.504263 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `0.00947995/0` | 1.2922 | 4.93365 | `width=-1, bank=1, face_h=0.483826, column_h=0.0342971` | `-1.30032/-1` | -0.017595 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 7 | `7-8` | `-1.25704/-1` | `-0.0147242/0` | 1.24231 | -1.59815 | `width=-2, bank=2, face_h=-0.0414753, column_h=0.161367` | `-0.106148/-1` | 1.15089 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-0.0484702/0` | 1.18324 | 4.43259 | `width=-1, bank=1, face_h=0.443281, column_h=0.031754` | `-1.92779/-1` | -0.696073 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.213534/1` | -0.515358 | -15.0977 | `width=0, bank=1, face_h=-0.477298, column_h=-0.111648` | `-0.425275/-1` | -1.15417 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `-0.296586/-1` | 2.00203 | -0.833275 | `width=-2, bank=1, face_h=0.351911, column_h=0.020027` | `-2.70701/-1` | -0.408387 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 0 | `1-2` | `2.04571/1` | `0.209244/1` | -1.83647 | -16.0255 | `width=-2, bank=1, face_h=-0.430222, column_h=-0.273186` | `2.03276/1` | -0.0129452 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 0 | `8-9` | `-2.00767/-1` | `-0.227514/-1` | 1.78016 | -3.41271 | `width=-2, bank=1, face_h=-0.0168034, column_h=-0.273186` | `-2.55661/-1` | -0.548936 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 1 | `1-2` | `1.97499/1` | `0.200141/1` | -1.77484 | -7.6115 | `width=-2, bank=1, face_h=-0.128437, column_h=0.020027` | `1.88025/1` | -0.0947341 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `-0.352631/-1` | 1.55865 | 2.08241 | `width=-1, bank=1, face_h=0.440567, column_h=0.0099371` | `-2.81443/-1` | -0.903156 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-0.150161/-1` | 1.21811 | 3.88733 | `width=-1, bank=1, face_h=0.437533, column_h=0.0338316` | `-2.57458/-1` | -1.20631 | `upstream_edge_width_depth_flux_balance` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 6 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 9 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 8 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 5 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 7 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 4 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- C++ final-frame upstream edge volume-flux signs still disagree with GeoClaw.
- Reconstructed face/source balance still blocks at one or more upstream edge faces.
- Native C++ post-source y-face flux signs still disagree with GeoClaw.
- Upstream edge face-state flux errors are coupled to wet-band width, bank-row, or depth support deltas.
- GeoClaw lower/upper edge opposition is still missing from C++ upstream edge states.

## Next Levers

- Start with `upper_edge_face` column 6 rows 8-9; q delta is 1.73125 m3/s, balance delta is 3.75159 m3/s2, native post-source delta is 1.02409 m3/s, wet-width delta is 0 cells, and bank-row delta is 1 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Preserve GeoClaw's lower-positive/upper-negative edge opposition across upstream wet-band columns.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
