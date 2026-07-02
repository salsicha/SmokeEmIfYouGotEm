# Milestone 18 Constriction Upstream Edge Balance Diagnostic

Schema: `raftsim.milestone18.constriction_upstream_edge_balance.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Face-state width/depth report: `reports/milestone18/constriction_upper_outside_shelf_support_face_state_width_depth_diagnostic.json`
Face/source audit report: `reports/milestone18/constriction_upper_outside_shelf_support_face_source_audit_diagnostic.json`
Diagnostic scope: Joins constriction upstream edge face-state width/depth samples with reconstructed face/source balance and native C++ post-source audit rows before the next solver retune.

## Summary

- Target samples: `12`
- Blocked targets: `12`
- Width/depth coupled blockers: `12`
- Source-balance blockers: `12`
- Native post-source sign mismatches: `2`
- Paired-edge opposition mismatches: `1`
- Max abs volume-flux delta: `1.99982` m3/s
- Max abs balance delta: `16.1413` m3/s2

## Target Samples

| Face | Column | Rows | GeoClaw q/sign | C++ q/sign | q delta | Balance delta | Width/depth deltas | Native C++ post q/sign | Native delta | Lever |
| --- | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `upper_edge_face` | 4 | `8-9` | `-1.23171/-1` | `-0.059235/0` | 1.17248 | 4.32016 | `width=0, bank=0, face_h=0.435841, column_h=-0.0752411` | `-1.93135/-1` | -0.699634 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 8 | `2-3` | `0.0743101/1` | `0.764397/1` | 0.690087 | 13.7496 | `width=0, bank=0, face_h=0.513655, column_h=-0.01731` | `-0.2011/-1` | -0.27541 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 9 | `2-3` | `0.0615163/1` | `0.721736/1` | 0.660219 | 12.1268 | `width=0, bank=0, face_h=0.457099, column_h=0.238812` | `-0.587814/-1` | -0.64933 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 1 | `8-9` | `-2.29862/-1` | `-0.298798/-1` | 1.99982 | -0.966064 | `width=-1, bank=1, face_h=0.342036, column_h=-0.0770795` | `-2.69912/-1` | -0.400501 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 0 | `1-2` | `2.04571/1` | `0.203094/1` | -1.84262 | -16.1413 | `width=-1, bank=1, face_h=-0.434382, column_h=-0.360127` | `2.0353/1` | -0.0104072 | `upstream_edge_width_depth_flux_balance` |
| `lower_edge_face` | 1 | `1-2` | `1.97499/1` | `0.198647/1` | -1.77634 | -7.72757 | `width=-1, bank=1, face_h=-0.132575, column_h=-0.0770795` | `1.88669/1` | -0.0882922 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 0 | `8-9` | `-2.00767/-1` | `-0.23488/-1` | 1.77279 | -3.57754 | `width=-1, bank=1, face_h=-0.0309037, column_h=-0.360127` | `-2.54231/-1` | -0.534636 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 2 | `8-9` | `-1.91128/-1` | `-0.35546/-1` | 1.55582 | 1.99324 | `width=0, bank=0, face_h=0.434333, column_h=-0.0756038` | `-2.81268/-1` | -0.901405 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 6 | `8-9` | `-1.66953/-1` | `-0.194278/-1` | 1.47525 | 3.30752 | `width=1, bank=0, face_h=0.4249, column_h=-0.223965` | `-0.829232/-1` | 0.840299 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 3 | `8-9` | `-1.36827/-1` | `-0.155559/-1` | 1.21272 | 3.80133 | `width=0, bank=0, face_h=0.431688, column_h=-0.0704633` | `-2.57457/-1` | -1.20629 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 5 | `8-9` | `-1.28272/-1` | `-0.0987741/-1` | 1.18395 | 4.63663 | `width=0, bank=0, face_h=0.464316, column_h=-0.0769659` | `-1.36752/-1` | -0.0848014 | `upstream_edge_width_depth_flux_balance` |
| `upper_edge_face` | 9 | `7-8` | `-1.36832/-1` | `-0.199814/-1` | 1.1685 | 5.30216 | `width=0, bank=0, face_h=0.575773, column_h=0.238812` | `-1.32021/-1` | 0.0481122 | `upstream_edge_width_depth_flux_balance` |

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

- Start with `upper_edge_face` column 4 rows 8-9; q delta is 1.17248 m3/s, balance delta is 4.32016 m3/s2, native post-source delta is -0.699634 m3/s, wet-width delta is 0 cells, and bank-row delta is 0 cells.
- Revise upstream edge width/depth support before accepting another predictor-state reconstruction; the edge sign error is coupled to geometry support.
- Retune y-face flux/source balance at the same face after the geometry support is corrected, not as a standalone source-strength increase.
- Preserve GeoClaw's lower-positive/upper-negative edge opposition across upstream wet-band columns.
- Keep feature forcing off, rerun the face-state, face/source, threshold, and Milestone 17 guardrail reports after the next solver change.
