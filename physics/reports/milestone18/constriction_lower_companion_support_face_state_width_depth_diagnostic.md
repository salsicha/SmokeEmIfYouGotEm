# Milestone 18 Constriction Face-State Width/Depth Diagnostic

Schema: `raftsim.milestone18.constriction_face_state_width_depth.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_lower_companion_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_lower_companion_support/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Compares authored, GeoClaw final, and C++ final wet-band columns while checking GeoClaw/C++ upstream edge face states before the next constriction solver change.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Depth delta threshold: `0.25` m
Wet-width delta threshold: `1` cells
Bank-row delta threshold: `1` cells

## Summary

- Face-state blockers: `19`
- Face sign mismatches: `12`
- Width mapping blockers: `1`
- Bank alignment blockers: `0`
- Depth mapping blockers: `7`
- Edge opposition mismatches: `8`
- Max abs volume-flux delta: `4.54348` m3/s
- Max abs face mean-depth delta: `0.992194` m
- Max abs wet-width delta: `2` cells
- Max abs bank-row delta: `1` cells
- Recommended levers: `['geometry_aware_face_state_reconstruction', 'geometry_aware_face_state_reconstruction_with_width_depth_mapping_check', 'width_depth_mapping']`

## Worst Face-State Samples

| Face | Column | Rows | Zone | GeoClaw h/v/q/sign | C++ h/v/q/sign | q delta | Depth delta | Width/bank deltas | Blockers | Lever |
| --- | ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| `lower_edge_face` | 5 | `1-2` | `upstream_approach` | `1.24635/1.17379/1.46296/1` | `1.03856/-2.96617/-3.08053/-1` | -4.54348 | -0.207799 | `-1/1/0` | `face=True, width=False, bank=False, depth=True` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `lower_edge_face` | 6 | `1-2` | `upstream_approach` | `1.39221/0.523551/0.728892/1` | `1.0945/-2.17693/-2.38264/-1` | -3.11153 | -0.29771 | `1/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 6 | `8-9` | `upstream_approach` | `1.15452/-1.44608/-1.66953/-1` | `2.03006/0.5378/1.09176/1` | 2.7613 | 0.875537 | `1/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 7 | `7-8` | `upstream_approach` | `1.85262/-0.678521/-1.25704/-1` | `2.27078/0.508064/1.1537/1` | 2.41074 | 0.418162 | `-1/1/0` | `face=True, width=False, bank=False, depth=True` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `upper_edge_face` | 1 | `8-9` | `upstream_approach` | `1.03834/-2.21375/-2.29862/-1` | `1.49687/0.0447544/0.0669915/0` | 2.36561 | 0.458534 | `-1/0/-1` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 5 | `8-9` | `upstream_approach` | `1.10988/-1.15573/-1.28272/-1` | `2.01172/0.456189/0.917725/1` | 2.20045 | 0.901838 | `-1/1/0` | `face=True, width=False, bank=False, depth=True` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `upper_edge_face` | 8 | `7-8` | `upstream_approach` | `1.85053/-0.760508/-1.40735/-1` | `2.14288/0.339704/0.727947/1` | 2.13529 | 0.292348 | `0/0/0` | `face=True, width=False, bank=False, depth=True` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `upper_edge_face` | 0 | `8-9` | `upstream_approach` | `1.23942/-1.61985/-2.00767/-1` | `1.36526/0.0160319/0.0218877/0` | 2.02956 | 0.125839 | `-2/1/-1` | `face=True, width=True, bank=False, depth=False` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `upper_edge_face` | 2 | `8-9` | `upstream_approach` | `1.0484/-1.82303/-1.91128/-1` | `1.61403/0.0675464/0.109022/1` | 2.0203 | 0.565623 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 4 | `8-9` | `upstream_approach` | `1.11127/-1.10838/-1.23171/-1` | `1.88419/0.333288/0.627976/1` | 1.85969 | 0.772915 | `-1/1/0` | `face=True, width=False, bank=False, depth=True` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `upper_edge_face` | 9 | `7-8` | `upstream_approach` | `0.983374/-1.39145/-1.36832/-1` | `1.97557/0.218975/0.4326/1` | 1.80092 | 0.992194 | `0/0/0` | `face=True, width=False, bank=False, depth=True` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `upper_edge_face` | 3 | `8-9` | `upstream_approach` | `1.08534/-1.26068/-1.36827/-1` | `1.73234/0.213004/0.368995/1` | 1.73727 | 0.646995 | `-1/1/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |

## Column Profiles

| Column | Zone | Authored width/banks/depth | GeoClaw width/banks/depth | C++ width/banks/depth | C++ minus GeoClaw | Blockers |
| ---: | --- | --- | --- | --- | --- | --- |
| 0 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.32633` | `10/1-10/1.14362` | `-2/1/-1/-0.182715` | `width=True, bank=False, depth=False` |
| 1 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.16904` | `11/0-10/1.15102` | `-1/0/-1/-0.0180205` | `width=False, bank=False, depth=False` |
| 2 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.15892` | `12/0-11/1.14652` | `0/0/0/-0.0123918` | `width=False, bank=False, depth=False` |
| 3 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.26074` | `10/2-11/1.42671` | `-1/1/0/0.16597` | `width=False, bank=False, depth=False` |
| 4 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.281` | `10/2-11/1.54647` | `-1/1/0/0.265474` | `width=False, bank=False, depth=True` |
| 5 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.30334` | `10/2-11/1.64935` | `-1/1/0/0.346015` | `width=False, bank=False, depth=True` |
| 6 | `upstream_approach` | `8/2-9/1.25` | `10/1-11/1.45507` | `11/1-11/1.52699` | `1/0/0/0.0719138` | `width=False, bank=False, depth=False` |
| 7 | `upstream_approach` | `6/3-8/1.25` | `10/1-11/1.25609` | `9/2-11/1.5795` | `-1/1/0/0.323402` | `width=False, bank=False, depth=True` |
| 8 | `upstream_approach` | `6/3-8/1.25` | `7/3-9/1.48607` | `7/3-9/1.86819` | `0/0/0/0.382114` | `width=False, bank=False, depth=True` |
| 9 | `upstream_approach` | `6/3-8/1.25` | `7/3-9/1.13466` | `7/3-9/1.72477` | `0/0/0/0.590115` | `width=False, bank=False, depth=True` |
| 10 | `constriction_throat` | `4/4-7/1.25` | `5/3-7/1.16347` | `5/3-7/1.89871` | `0/0/0/0.735241` | `width=False, bank=False, depth=True` |
| 11 | `constriction_throat` | `4/4-7/1.25` | `4/3-6/1.24796` | `4/3-6/1.25` | `0/0/0/0.00203678` | `width=False, bank=False, depth=False` |
| 12 | `constriction_throat` | `4/4-7/1.25` | `4/3-6/1.12546` | `4/3-6/1.25` | `0/0/0/0.12454` | `width=False, bank=False, depth=False` |
| 13 | `constriction_throat` | `4/4-7/1.25` | `5/3-7/0.839163` | `5/3-7/1.15512` | `0/0/0/0.315956` | `width=False, bank=False, depth=True` |

## Edge Pair Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 0 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 1 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 2 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 3 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 4 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 5 | `1->-1` | `-1->1` | `True` | `True` | `True` |
| 6 | `1->-1` | `-1->1` | `True` | `True` | `True` |
| 7 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 8 | `1->1` | `-1->1` | `True` | `False` | `False` |
| 9 | `1->1` | `-1->1` | `True` | `False` | `False` |

## Blocked Reasons

- C++ upstream edge face-state signs still disagree with GeoClaw.
- C++ upstream edge face-state volume-flux deltas exceed the diagnostic threshold.
- GeoClaw lower/upper edge opposition is still missing from the C++ face states.
- C++ constriction wet-band width still differs from GeoClaw beyond the mapping threshold.
- C++ constriction mean wet depth still differs from GeoClaw beyond the mapping threshold.

## Next Levers

- Start with `lower_edge_face` column 5 rows 1-2; q delta is -4.54348 m3/s, face mean-depth delta is -0.207799 m, wet-width delta is -1 cells, and max bank-row delta is 1 cells.
- Build a geometry-aware face-state reconstruction before y-face flux evaluation; the source split alone did not restore the GeoClaw edge signs.
- Use the authored initial -> GeoClaw final -> C++ final column profiles to retune constriction width/depth mapping before accepting any face-state change.
- Preserve GeoClaw's lower/upper edge opposition in the upstream wet band; a single-sign lateral state remains a blocker.
- Keep feature forcing and stronger source-split tuning off, then rerun the face/source audit, mask/throat diagnostics, threshold report, and Milestone 17 guardrail.
