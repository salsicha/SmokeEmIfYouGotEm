# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `reports/milestone18/constriction_wet_band_profile_relaxation_face_state_width_depth_diagnostic.json`
Face/source audit report: `reports/milestone18/constriction_wet_band_profile_relaxation_face_source_audit_diagnostic.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `12`
- Source-balance blockers: `12`
- Native post-source sign mismatches: `2`
- Paired-edge opposition mismatches: `6`
- Max abs volume-flux delta: `2.00177` m3/s
- Max abs balance delta: `16.0182` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `0.07975/1` | 1.44807 | 5.29476 | `width=0, bank=0, face_h=0.576697, column_h=0.231145` | `0.0953778/1` | 1.4637 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `0.0616748/0` | 1.73121 | 3.74831 | `width=0, bank=1, face_h=0.454463, column_h=-0.111817` | `-0.645428/-1` | 1.0241 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `0.00943565/0` | 1.29216 | 4.93337 | `width=-1, bank=1, face_h=0.483808, column_h=0.0342827` | `-1.30034/-1` | -0.0176215 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 7 | `7-8` | `-1.25704/-1` | `-0.0117578/0` | 1.24528 | -1.61576 | `width=-2, bank=2, face_h=-0.0424642, column_h=0.160624` | `-0.103189/-1` | 1.15385 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-0.0485485/0` | 1.18317 | 4.43419 | `width=-1, bank=1, face_h=0.443385, column_h=0.031839` | `-1.9279/-1` | -0.696184 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 6 | `1-2` | `0.728892/1` | `0.213499/1` | -0.515393 | -15.1008 | `width=0, bank=1, face_h=-0.477406, column_h=-0.111817` | `-0.424937/-1` | -1.15383 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `-0.296846/-1` | 2.00177 | -0.826241 | `width=-2, bank=1, face_h=0.35242, column_h=0.0204464` | `-2.7075/-1` | -0.408883 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 0 | `1-2` | `2.04571/1` | `0.209216/1` | -1.83649 | -16.0182 | `width=-2, bank=1, face_h=-0.429955, column_h=-0.272718` | `2.03229/1` | -0.0134229 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 0 | `8-9` | `-2.00767/-1` | `-0.227734/-1` | 1.77994 | -3.40583 | `width=-2, bank=1, face_h=-0.0162352, column_h=-0.272718` | `-2.55705/-1` | -0.549383 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 1 | `1-2` | `1.97499/1` | `0.20008/1` | -1.77491 | -7.60459 | `width=-2, bank=1, face_h=-0.128189, column_h=0.0204464` | `1.87975/1` | -0.0952365 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `-0.352882/-1` | 1.55839 | 2.08869 | `width=-1, bank=1, face_h=0.44099, column_h=0.0102546` | `-2.81488/-1` | -0.903599 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-0.150314/-1` | 1.21796 | 3.89035 | `width=-1, bank=1, face_h=0.437733, column_h=0.0339943` | `-2.57482/-1` | -1.20654 | `upstream_edge_width_depth_flux_balance` |

## Paired Edge Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 6 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 8 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 9 | `1->1` | `-1->1` | `True` | `False` | `False` |
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

- Start with `upper_edge_face` column 9 rows 7-8; q delta is 1.44807 m3/s, balance delta is 5.29476 m3/s2, native post-source delta is 1.4637 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Preserve GeoClaw's lower-positive/upper-negative edge opposition across upstream wet-band columns.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
