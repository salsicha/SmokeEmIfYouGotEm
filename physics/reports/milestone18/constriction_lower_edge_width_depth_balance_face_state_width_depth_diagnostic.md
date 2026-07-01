# Milestone 18 Constriction Face-State Width/Depth Diagnostic

Schema: `raftsim.milestone18.constriction_face_state_width_depth.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_lower_edge_width_depth_balance/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_lower_edge_width_depth_balance/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Compares authored, GeoClaw final, and C++ final wet-band columns while checking GeoClaw/C++ upstream edge face states before the next constriction solver change.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Depth delta threshold: `0.25` m
Wet-width delta threshold: `1` cells
Bank-row delta threshold: `1` cells

## Summary

- Face-state blockers: `19`
- Face sign mismatches: `10`
- Width mapping blockers: `2`
- Bank alignment blockers: `1`
- Depth mapping blockers: `5`
- Edge opposition mismatches: `10`
- Max abs volume-flux delta: `2.97684` m3/s
- Max abs face mean-depth delta: `0.976824` m
- Max abs wet-width delta: `2` cells
- Max abs bank-row delta: `2` cells
- Recommended levers: `['geometry_aware_face_state_reconstruction', 'geometry_aware_face_state_reconstruction_with_width_depth_mapping_check', 'preserve_as_guardrail']`

## Worst Face-State Samples

| Face | Column | Rows | Zone | GeoClaw h/v/q/sign | C++ h/v/q/sign | q delta | Depth delta | Width/bank deltas | Blockers | Lever |
| --- | ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| `upper_edge_face` | 6 | `8-9` | `upstream_approach` | `1.15452/-1.44608/-1.66953/-1` | `2.01026/0.650319/1.30731/1` | 2.97684 | 0.855736 | `1/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 7 | `7-8` | `upstream_approach` | `1.85262/-0.678521/-1.25704/-1` | `2.25091/0.602099/1.35527/1` | 2.61231 | 0.398292 | `-2/1/-2` | `face=True, width=True, bank=True, depth=True` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `upper_edge_face` | 1 | `8-9` | `upstream_approach` | `1.03834/-2.21375/-2.29862/-1` | `1.48246/0.0444801/0.0659398/0` | 2.36456 | 0.44412 | `-1/0/-1` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 5 | `8-9` | `upstream_approach` | `1.10988/-1.15573/-1.28272/-1` | `1.98861/0.535998/1.06589/1` | 2.34861 | 0.878728 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 8 | `7-8` | `upstream_approach` | `1.85053/-0.760508/-1.40735/-1` | `2.13075/0.408218/0.869809/1` | 2.27716 | 0.280214 | `0/0/0` | `face=True, width=False, bank=False, depth=True` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `upper_edge_face` | 0 | `8-9` | `upstream_approach` | `1.23942/-1.61985/-2.00767/-1` | `1.35128/0.0158199/0.0213771/0` | 2.02905 | 0.111857 | `-2/1/-1` | `face=True, width=True, bank=False, depth=False` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `upper_edge_face` | 2 | `8-9` | `upstream_approach` | `1.0484/-1.82303/-1.91128/-1` | `1.59752/0.067072/0.107149/1` | 2.01843 | 0.54912 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 4 | `8-9` | `upstream_approach` | `1.11127/-1.10838/-1.23171/-1` | `1.85813/0.398085/0.739692/1` | 1.97141 | 0.746853 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 9 | `7-8` | `upstream_approach` | `0.983374/-1.39145/-1.36832/-1` | `1.9602/0.272113/0.533395/1` | 1.90171 | 0.976824 | `0/0/0` | `face=True, width=False, bank=False, depth=True` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `upper_edge_face` | 3 | `8-9` | `upstream_approach` | `1.08534/-1.26068/-1.36827/-1` | `1.69379/0.241342/0.408781/1` | 1.77705 | 0.608444 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `lower_edge_face` | 0 | `1-2` | `upstream_approach` | `1.198/1.70761/2.04571/1` | `0.778616/0.0693232/0.0539762/1` | -1.99173 | -0.41938 | `-2/1/-1` | `face=True, width=True, bank=False, depth=False` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `lower_edge_face` | 1 | `1-2` | `upstream_approach` | `0.978339/2.01871/1.97499/1` | `0.845313/0.0977679/0.0826445/1` | -1.89234 | -0.133026 | `-1/0/-1` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |

## Column Profiles

| Column | Zone | Authored width/banks/depth | GeoClaw width/banks/depth | C++ width/banks/depth | C++ minus GeoClaw | Blockers |
| ---: | --- | --- | --- | --- | --- | --- |
| 0 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.32633` | `10/1-10/1.13224` | `-2/1/-1/-0.194088` | `width=True, bank=False, depth=False` |
| 1 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.16904` | `11/0-10/1.14047` | `-1/0/-1/-0.0285739` | `width=False, bank=False, depth=False` |
| 2 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.15892` | `12/0-11/1.13549` | `0/0/0/-0.0234252` | `width=False, bank=False, depth=False` |
| 3 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.26074` | `11/1-11/1.29268` | `0/0/0/0.0319355` | `width=False, bank=False, depth=False` |
| 4 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.281` | `11/1-11/1.41069` | `0/0/0/0.129693` | `width=False, bank=False, depth=False` |
| 5 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.30334` | `11/1-11/1.50482` | `0/0/0/0.201482` | `width=False, bank=False, depth=False` |
| 6 | `upstream_approach` | `8/2-9/1.25` | `10/1-11/1.45507` | `11/1-11/1.51813` | `1/0/0/0.0630603` | `width=False, bank=False, depth=False` |
| 7 | `upstream_approach` | `6/3-8/1.25` | `10/1-11/1.25609` | `8/2-9/1.74319` | `-2/1/-2/0.487092` | `width=True, bank=True, depth=True` |
| 8 | `upstream_approach` | `6/3-8/1.25` | `7/3-9/1.48607` | `7/3-9/1.85778` | `0/0/0/0.371713` | `width=False, bank=False, depth=True` |
| 9 | `upstream_approach` | `6/3-8/1.25` | `7/3-9/1.13466` | `7/3-9/1.7116` | `0/0/0/0.57694` | `width=False, bank=False, depth=True` |
| 10 | `constriction_throat` | `4/4-7/1.25` | `5/3-7/1.16347` | `5/3-7/1.88255` | `0/0/0/0.719075` | `width=False, bank=False, depth=True` |
| 11 | `constriction_throat` | `4/4-7/1.25` | `4/3-6/1.24796` | `4/3-6/1.25` | `0/0/0/0.00203678` | `width=False, bank=False, depth=False` |
| 12 | `constriction_throat` | `4/4-7/1.25` | `4/3-6/1.12546` | `4/3-6/1.25` | `0/0/0/0.12454` | `width=False, bank=False, depth=False` |
| 13 | `constriction_throat` | `4/4-7/1.25` | `5/3-7/0.839163` | `5/3-7/1.15484` | `0/0/0/0.315674` | `width=False, bank=False, depth=True` |

## Edge Pair Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 0 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 1 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 2 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 3 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 4 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 5 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 6 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 7 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 8 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 9 | `1->1` | `-1->1` | `True` | `False` | `False` |

## Blocked Reasons

- C++ upstream edge face-state signs still disagree with GeoClaw.
- C++ upstream edge face-state volume-flux deltas exceed the diagnostic threshold.
- GeoClaw lower/upper edge opposition is still missing from the C++ face states.
- C++ constriction wet-band width still differs from GeoClaw beyond the mapping threshold.
- C++ constriction bank row placement still differs from GeoClaw beyond the mapping threshold.
- C++ constriction mean wet depth still differs from GeoClaw beyond the mapping threshold.

## Next Levers

- Start with `upper_edge_face` column 6 rows 8-9; q delta is 2.97684 m3/s, face mean-depth delta is 0.855736 m, wet-width delta is 1 cells, and max bank-row delta is 0 cells.
- Build a geometry-aware face-state reconstruction before y-face flux evaluation; the source split alone did not restore the GeoClaw edge signs.
- Use the authored initial -> GeoClaw final -> C++ final column profiles to retune constriction width/depth mapping before accepting any face-state change.
- Preserve GeoClaw's lower/upper edge opposition in the upstream wet band; a single-sign lateral state remains a blocker.
- Keep feature forcing and stronger source-split tuning off, then rerun the face/source audit, mask/throat diagnostics, threshold report, and Milestone 17 guardrail.
