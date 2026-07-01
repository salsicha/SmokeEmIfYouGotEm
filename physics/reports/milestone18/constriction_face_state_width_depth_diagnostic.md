# Milestone 18 Constriction Face-State Width/Depth Diagnostic

Schema: `raftsim.milestone18.constriction_face_state_width_depth.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_localized_circulation/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_localized_circulation/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Compares authored, GeoClaw final, and C++ final wet-band columns while checking GeoClaw/C++ upstream edge face states before the next constriction solver change.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Depth delta threshold: `0.25` m
Wet-width delta threshold: `1` cells
Bank-row delta threshold: `1` cells

## Summary

- Face-state blockers: `19`
- Face sign mismatches: `13`
- Width mapping blockers: `1`
- Bank alignment blockers: `0`
- Depth mapping blockers: `3`
- Edge opposition mismatches: `10`
- Max abs volume-flux delta: `2.72633` m3/s
- Max abs face mean-depth delta: `0.828126` m
- Max abs wet-width delta: `2` cells
- Max abs bank-row delta: `1` cells
- Recommended levers: `['geometry_aware_face_state_reconstruction', 'geometry_aware_face_state_reconstruction_with_width_depth_mapping_check', 'preserve_as_guardrail']`

## Worst Face-State Samples

| Face | Column | Rows | Zone | GeoClaw h/v/q/sign | C++ h/v/q/sign | q delta | Depth delta | Width/bank deltas | Blockers | Lever |
| --- | ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| `upper_edge_face` | 6 | `8-9` | `upstream_approach` | `1.15452/-1.44608/-1.66953/-1` | `1.87408/0.563905/1.0568/1` | 2.72633 | 0.719562 | `1/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 7 | `7-8` | `upstream_approach` | `1.85262/-0.678521/-1.25704/-1` | `2.08705/0.5158/1.0765/1` | 2.33354 | 0.234434 | `-1/1/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 1 | `8-9` | `upstream_approach` | `1.03834/-2.21375/-2.29862/-1` | `1.5007/-0.028015/-0.0420422/0` | 2.25658 | 0.462367 | `-1/0/-1` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 5 | `8-9` | `upstream_approach` | `1.10988/-1.15573/-1.28272/-1` | `1.87032/0.438622/0.820362/1` | 2.10309 | 0.760436 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 8 | `7-8` | `upstream_approach` | `1.85053/-0.760508/-1.40735/-1` | `1.97687/0.329316/0.651014/1` | 2.05836 | 0.126334 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `lower_edge_face` | 0 | `1-2` | `upstream_approach` | `1.198/1.70761/2.04571/1` | `0.791026/-0.00162915/-0.0012887/0` | -2.047 | -0.40697 | `-2/1/-1` | `face=True, width=True, bank=False, depth=False` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `lower_edge_face` | 1 | `1-2` | `upstream_approach` | `0.978339/2.01871/1.97499/1` | `0.856628/-0.00737186/-0.00631494/0` | -1.9813 | -0.12171 | `-1/0/-1` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 0 | `8-9` | `upstream_approach` | `1.23942/-1.61985/-2.00767/-1` | `1.37158/-0.022217/-0.0304725/0` | 1.9772 | 0.132162 | `-2/1/-1` | `face=True, width=True, bank=False, depth=False` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `upper_edge_face` | 2 | `8-9` | `upstream_approach` | `1.0484/-1.82303/-1.91128/-1` | `1.60337/-0.0308346/-0.0494393/0` | 1.86184 | 0.554964 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 4 | `8-9` | `upstream_approach` | `1.11127/-1.10838/-1.23171/-1` | `1.77789/0.289872/0.51536/1` | 1.74707 | 0.666616 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 9 | `7-8` | `upstream_approach` | `0.983374/-1.39145/-1.36832/-1` | `1.8115/0.198853/0.360223/1` | 1.72854 | 0.828126 | `0/0/0` | `face=True, width=False, bank=False, depth=True` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `upper_edge_face` | 3 | `8-9` | `upstream_approach` | `1.08534/-1.26068/-1.36827/-1` | `1.67752/0.133581/0.224084/1` | 1.59236 | 0.59218 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |

## Column Profiles

| Column | Zone | Authored width/banks/depth | GeoClaw width/banks/depth | C++ width/banks/depth | C++ minus GeoClaw | Blockers |
| ---: | --- | --- | --- | --- | --- | --- |
| 0 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.32633` | `10/1-10/1.14672` | `-2/1/-1/-0.179607` | `width=True, bank=False, depth=False` |
| 1 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.16904` | `11/0-10/1.15228` | `-1/0/-1/-0.0167568` | `width=False, bank=False, depth=False` |
| 2 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.15892` | `12/0-11/1.13777` | `0/0/0/-0.0211463` | `width=False, bank=False, depth=False` |
| 3 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.26074` | `11/1-11/1.27589` | `0/0/0/0.0151481` | `width=False, bank=False, depth=False` |
| 4 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.281` | `11/1-11/1.34705` | `0/0/0/0.0660587` | `width=False, bank=False, depth=False` |
| 5 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.30334` | `11/1-11/1.41573` | `0/0/0/0.112387` | `width=False, bank=False, depth=False` |
| 6 | `upstream_approach` | `8/2-9/1.25` | `10/1-11/1.45507` | `11/1-11/1.41889` | `1/0/0/-0.0361874` | `width=False, bank=False, depth=False` |
| 7 | `upstream_approach` | `6/3-8/1.25` | `10/1-11/1.25609` | `9/2-11/1.45734` | `-1/1/0/0.201249` | `width=False, bank=False, depth=False` |
| 8 | `upstream_approach` | `6/3-8/1.25` | `7/3-9/1.48607` | `7/3-9/1.72589` | `0/0/0/0.239816` | `width=False, bank=False, depth=False` |
| 9 | `upstream_approach` | `6/3-8/1.25` | `7/3-9/1.13466` | `7/3-9/1.58414` | `0/0/0/0.449485` | `width=False, bank=False, depth=True` |
| 10 | `constriction_throat` | `4/4-7/1.25` | `5/3-7/1.16347` | `5/3-7/1.71896` | `0/0/0/0.555486` | `width=False, bank=False, depth=True` |
| 11 | `constriction_throat` | `4/4-7/1.25` | `4/3-6/1.24796` | `4/3-6/1.25` | `0/0/0/0.00203678` | `width=False, bank=False, depth=False` |
| 12 | `constriction_throat` | `4/4-7/1.25` | `4/3-6/1.12546` | `4/3-6/1.25` | `0/0/0/0.12454` | `width=False, bank=False, depth=False` |
| 13 | `constriction_throat` | `4/4-7/1.25` | `5/3-7/0.839163` | `5/3-7/1.15332` | `0/0/0/0.314157` | `width=False, bank=False, depth=True` |

## Edge Pair Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 0 | `1->0` | `-1->0` | `True` | `False` | `False` |
| 1 | `1->0` | `-1->0` | `True` | `False` | `False` |
| 2 | `1->0` | `-1->0` | `True` | `False` | `False` |
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
- C++ constriction mean wet depth still differs from GeoClaw beyond the mapping threshold.

## Next Levers

- Start with `upper_edge_face` column 6 rows 8-9; q delta is 2.72633 m3/s, face mean-depth delta is 0.719562 m, wet-width delta is 1 cells, and max bank-row delta is 0 cells.
- Build a geometry-aware face-state reconstruction before y-face flux evaluation; the source split alone did not restore the GeoClaw edge signs.
- Use the authored initial -> GeoClaw final -> C++ final column profiles to retune constriction width/depth mapping before accepting any face-state change.
- Preserve GeoClaw's lower/upper edge opposition in the upstream wet band; a single-sign lateral state remains a blocker.
- Keep feature forcing and stronger source-split tuning off, then rerun the face/source audit, mask/throat diagnostics, threshold report, and Milestone 17 guardrail.
