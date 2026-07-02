# Milestone 18 Constriction Face-State Width/Depth Diagnostic

Schema: `raftsim.milestone18.constriction_face_state_width_depth.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_upper_edge_flux_magnitude_balance/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_upper_edge_flux_magnitude_balance/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Compares authored, GeoClaw final, and C++ final wet-band columns while checking GeoClaw/C++ upstream edge face states before the next constriction solver change.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Depth delta threshold: `0.25` m
Wet-width delta threshold: `1` cells
Bank-row delta threshold: `1` cells

## Summary

- Face-state blockers: `18`
- Face sign mismatches: `4`
- Width mapping blockers: `0`
- Bank alignment blockers: `0`
- Depth mapping blockers: `3`
- Edge opposition mismatches: `4`
- Max abs volume-flux delta: `2.05596` m3/s
- Max abs face mean-depth delta: `0.594572` m
- Max abs wet-width delta: `1` cells
- Max abs bank-row delta: `1` cells
- Recommended levers: `['geometry_aware_face_state_reconstruction', 'geometry_aware_face_state_reconstruction_with_width_depth_mapping_check', 'preserve_as_guardrail']`

## Worst Face-State Samples

| Face | Column | Rows | Zone | GeoClaw h/v/q/sign | C++ h/v/q/sign | q delta | Depth delta | Width/bank deltas | Blockers | Lever |
| --- | ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| `lower_edge_face` | 1 | `1-2` | `upstream_approach` | `0.978339/2.01871/1.97499/1` | `0.846062/-0.0957106/-0.0809771/-1` | -2.05596 | -0.132276 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `lower_edge_face` | 0 | `1-2` | `upstream_approach` | `1.198/1.70761/2.04571/1` | `0.755688/0.0284899/0.0215295/0` | -2.02418 | -0.442309 | `-1/1/0` | `face=True, width=False, bank=False, depth=True` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `lower_edge_face` | 2 | `1-2` | `upstream_approach` | `1.01111/1.30241/1.31687/1` | `0.90328/-0.169848/-0.153421/-1` | -1.47029 | -0.107827 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `lower_edge_face` | 7 | `2-3` | `upstream_approach` | `1.13495/0.309964/0.351794/1` | `1.03731/-0.299122/-0.310282/-1` | -0.662076 | -0.097643 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 1 | `8-9` | `upstream_approach` | `1.03834/-2.21375/-2.29862/-1` | `1.38097/-0.655538/-0.905281/-1` | 1.39334 | 0.342638 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 0 | `8-9` | `upstream_approach` | `1.23942/-1.61985/-2.00767/-1` | `1.1924/-0.536008/-0.639133/-1` | 1.36854 | -0.0470244 | `-1/1/0` | `face=True, width=False, bank=False, depth=True` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `lower_edge_face` | 5 | `1-2` | `upstream_approach` | `1.24635/1.17379/1.46296/1` | `0.928552/0.129509/0.120256/1` | -1.3427 | -0.317802 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 2 | `8-9` | `upstream_approach` | `1.0484/-1.82303/-1.91128/-1` | `1.4926/-0.725686/-1.08316/-1` | 0.828115 | 0.444199 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 6 | `8-9` | `upstream_approach` | `1.15452/-1.44608/-1.66953/-1` | `1.5736/-0.593448/-0.933852/-1` | 0.735679 | 0.419085 | `1/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `lower_edge_face` | 6 | `1-2` | `upstream_approach` | `1.39221/0.523551/0.728892/1` | `0.93866/0.0767025/0.0719975/1` | -0.656894 | -0.453549 | `1/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `lower_edge_face` | 3 | `1-2` | `upstream_approach` | `1.0627/0.775286/0.823895/1` | `0.913896/0.197398/0.180401/1` | -0.643494 | -0.148803 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 9 | `7-8` | `upstream_approach` | `0.983374/-1.39145/-1.36832/-1` | `1.57795/-0.524746/-0.828022/-1` | 0.540297 | 0.594572 | `0/0/0` | `face=True, width=False, bank=False, depth=True` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |

## Column Profiles

| Column | Zone | Authored width/banks/depth | GeoClaw width/banks/depth | C++ width/banks/depth | C++ minus GeoClaw | Blockers |
| ---: | --- | --- | --- | --- | --- | --- |
| 0 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.32633` | `11/1-11/0.954315` | `-1/1/0/-0.372017` | `width=False, bank=False, depth=True` |
| 1 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.16904` | `12/0-11/1.01505` | `0/0/0/-0.153993` | `width=False, bank=False, depth=False` |
| 2 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.15892` | `12/0-11/1.09191` | `0/0/0/-0.0670011` | `width=False, bank=False, depth=False` |
| 3 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.26074` | `11/1-11/1.19272` | `0/0/0/-0.0680202` | `width=False, bank=False, depth=False` |
| 4 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.281` | `11/1-11/1.20518` | `0/0/0/-0.0758166` | `width=False, bank=False, depth=False` |
| 5 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.30334` | `11/1-11/1.22137` | `0/0/0/-0.0819643` | `width=False, bank=False, depth=False` |
| 6 | `upstream_approach` | `8/2-9/1.25` | `10/1-11/1.45507` | `11/1-11/1.22756` | `1/0/0/-0.227515` | `width=False, bank=False, depth=False` |
| 7 | `upstream_approach` | `6/3-8/1.25` | `10/1-11/1.25609` | `10/1-11/1.16553` | `0/0/0/-0.0905639` | `width=False, bank=False, depth=False` |
| 8 | `upstream_approach` | `6/3-8/1.25` | `7/3-9/1.48607` | `7/3-9/1.47748` | `0/0/0/-0.0085921` | `width=False, bank=False, depth=False` |
| 9 | `upstream_approach` | `6/3-8/1.25` | `7/3-9/1.13466` | `7/3-9/1.3899` | `0/0/0/0.255238` | `width=False, bank=False, depth=True` |
| 10 | `constriction_throat` | `4/4-7/1.25` | `5/3-7/1.16347` | `5/3-7/1.44385` | `0/0/0/0.280374` | `width=False, bank=False, depth=True` |
| 11 | `constriction_throat` | `4/4-7/1.25` | `4/3-6/1.24796` | `4/3-6/1.25` | `0/0/0/0.00203678` | `width=False, bank=False, depth=False` |
| 12 | `constriction_throat` | `4/4-7/1.25` | `4/3-6/1.12546` | `4/3-6/1.25` | `0/0/0/0.12454` | `width=False, bank=False, depth=False` |
| 13 | `constriction_throat` | `4/4-7/1.25` | `5/3-7/0.839163` | `5/3-7/1.05622` | `0/0/0/0.217058` | `width=False, bank=False, depth=False` |

## Edge Pair Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 0 | `1->0` | `-1->-1` | `True` | `False` | `False` |
| 1 | `1->-1` | `-1->-1` | `True` | `False` | `False` |
| 2 | `1->-1` | `-1->-1` | `True` | `False` | `False` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 4 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 6 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 7 | `1->-1` | `-1->-1` | `True` | `False` | `False` |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- C++ upstream edge face-state signs still disagree with GeoClaw.
- C++ upstream edge face-state volume-flux deltas exceed the diagnostic threshold.
- GeoClaw lower/upper edge opposition is still missing from the C++ face states.
- C++ constriction mean wet depth still differs from GeoClaw beyond the mapping threshold.

## Next Levers

- Start with `lower_edge_face` column 1 rows 1-2; q delta is -2.05596 m3/s, face mean-depth delta is -0.132276 m, wet-width delta is 0 cells, and max bank-row delta is 0 cells.
- Build a geometry-aware face-state reconstruction before y-face flux evaluation; the source split alone did not restore the GeoClaw edge signs.
- Use the authored initial -> GeoClaw final -> C++ final column profiles to retune constriction width/depth mapping before accepting any face-state change.
- Preserve GeoClaw's lower/upper edge opposition in the upstream wet band; a single-sign lateral state remains a blocker.
- Keep feature forcing and stronger source-split tuning off, then rerun the face/source audit, mask/throat diagnostics, threshold report, and Milestone 17 guardrail.
