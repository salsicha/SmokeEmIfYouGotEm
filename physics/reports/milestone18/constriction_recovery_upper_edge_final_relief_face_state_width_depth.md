# Milestone 18 Constriction Face-State Width/Depth Diagnostic

Schema: `raftsim.milestone18.constriction_face_state_width_depth.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_recovery_upper_edge_final_relief/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_recovery_upper_edge_final_relief/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Compares authored, GeoClaw final, and C++ final wet-band columns while checking GeoClaw/C++ upstream edge face states before the next constriction solver change.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Depth delta threshold: `0.25` m
Wet-width delta threshold: `1` cells
Bank-row delta threshold: `1` cells

## Summary

- Face-state blockers: `13`
- Face sign mismatches: `0`
- Width mapping blockers: `0`
- Bank alignment blockers: `0`
- Depth mapping blockers: `1`
- Edge opposition mismatches: `0`
- Max abs volume-flux delta: `0.706344` m3/s
- Max abs face mean-depth delta: `0.486703` m
- Max abs wet-width delta: `1` cells
- Max abs bank-row delta: `0` cells
- Recommended levers: `['geometry_aware_face_state_reconstruction', 'geometry_aware_face_state_reconstruction_with_width_depth_mapping_check', 'preserve_as_guardrail']`

## Worst Face-State Samples

| Face | Column | Rows | Zone | GeoClaw h/v/q/sign | C++ h/v/q/sign | q delta | Depth delta | Width/bank deltas | Blockers | Lever |
| --- | ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| `lower_edge_face` | 5 | `1-2` | `upstream_approach` | `1.24635/1.17379/1.46296/1` | `0.973781/0.776985/0.756613/1` | -0.706344 | -0.272574 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `lower_edge_face` | 8 | `2-3` | `upstream_approach` | `0.33907/0.219158/0.0743101/1` | `0.825773/0.77533/0.640247/1` | 0.565937 | 0.486703 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 8 | `7-8` | `upstream_approach` | `1.85053/-0.760508/-1.40735/-1` | `1.6523/-1.19257/-1.97049/-1` | -0.56314 | -0.198237 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 1 | `8-9` | `upstream_approach` | `1.03834/-2.21375/-2.29862/-1` | `1.0434/-1.78241/-1.85978/-1` | 0.438844 | 0.0050675 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `lower_edge_face` | 9 | `2-3` | `upstream_approach` | `0.330975/0.185864/0.0615163/1` | `0.668494/0.729291/0.487527/1` | 0.42601 | 0.337519 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 4 | `8-9` | `upstream_approach` | `1.11127/-1.10838/-1.23171/-1` | `1.33464/-1.23591/-1.64949/-1` | -0.417778 | 0.223365 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 9 | `7-8` | `upstream_approach` | `0.983374/-1.39145/-1.36832/-1` | `1.46159/-1.19192/-1.7421/-1` | -0.373781 | 0.478215 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 5 | `8-9` | `upstream_approach` | `1.10988/-1.15573/-1.28272/-1` | `1.38457/-1.17968/-1.63335/-1` | -0.350627 | 0.274687 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `lower_edge_face` | 2 | `1-2` | `upstream_approach` | `1.01111/1.30241/1.31687/1` | `1.09064/1.52207/1.66003/1` | 0.343161 | 0.0795326 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `lower_edge_face` | 4 | `1-2` | `upstream_approach` | `1.15499/0.20444/0.236126/1` | `0.97784/0.588987/0.575935/1` | 0.339809 | -0.177153 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 3 | `8-9` | `upstream_approach` | `1.08534/-1.26068/-1.36827/-1` | `1.3036/-1.29529/-1.68853/-1` | -0.320258 | 0.218255 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 6 | `8-9` | `upstream_approach` | `1.15452/-1.44608/-1.66953/-1` | `1.4199/-1.11751/-1.58674/-1` | 0.082787 | 0.265377 | `1/0/0` | `face=True, width=False, bank=False, depth=True` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |

## Column Profiles

| Column | Zone | Authored width/banks/depth | GeoClaw width/banks/depth | C++ width/banks/depth | C++ minus GeoClaw | Blockers |
| ---: | --- | --- | --- | --- | --- | --- |
| 0 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.32633` | `12/0-11/1.12047` | `0/0/0/-0.205863` | `width=False, bank=False, depth=False` |
| 1 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.16904` | `12/0-11/1.13445` | `0/0/0/-0.0345851` | `width=False, bank=False, depth=False` |
| 2 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.15892` | `12/0-11/1.166` | `0/0/0/0.00708046` | `width=False, bank=False, depth=False` |
| 3 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.26074` | `11/1-11/1.23465` | `0/0/0/-0.0260912` | `width=False, bank=False, depth=False` |
| 4 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.281` | `11/1-11/1.21659` | `0/0/0/-0.0644098` | `width=False, bank=False, depth=False` |
| 5 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.30334` | `11/1-11/1.21121` | `0/0/0/-0.092127` | `width=False, bank=False, depth=False` |
| 6 | `upstream_approach` | `8/2-9/1.25` | `10/1-11/1.45507` | `11/1-11/1.20453` | `1/0/0/-0.250542` | `width=False, bank=False, depth=True` |
| 7 | `upstream_approach` | `6/3-8/1.25` | `10/1-11/1.25609` | `10/1-11/1.15471` | `0/0/0/-0.101381` | `width=False, bank=False, depth=False` |
| 8 | `upstream_approach` | `6/3-8/1.25` | `7/3-9/1.48607` | `7/3-9/1.4852` | `0/0/0/-0.000875535` | `width=False, bank=False, depth=False` |
| 9 | `upstream_approach` | `6/3-8/1.25` | `7/3-9/1.13466` | `7/3-9/1.36303` | `0/0/0/0.228375` | `width=False, bank=False, depth=False` |
| 10 | `constriction_throat` | `4/4-7/1.25` | `5/3-7/1.16347` | `5/3-7/1.33612` | `0/0/0/0.172644` | `width=False, bank=False, depth=False` |
| 11 | `constriction_throat` | `4/4-7/1.25` | `4/3-6/1.24796` | `4/3-6/1.21921` | `0/0/0/-0.0287577` | `width=False, bank=False, depth=False` |
| 12 | `constriction_throat` | `4/4-7/1.25` | `4/3-6/1.12546` | `4/3-6/1.21458` | `0/0/0/0.0891243` | `width=False, bank=False, depth=False` |
| 13 | `constriction_throat` | `4/4-7/1.25` | `5/3-7/0.839163` | `5/3-7/0.864965` | `0/0/0/0.025802` | `width=False, bank=False, depth=False` |

## Edge Pair Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 4 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 6 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 7 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- C++ upstream edge face-state volume-flux deltas exceed the diagnostic threshold.
- C++ constriction mean wet depth still differs from GeoClaw beyond the mapping threshold.

## Next Levers

- Start with `lower_edge_face` column 5 rows 1-2; q delta is -0.706344 m3/s, face mean-depth delta is -0.272574 m, wet-width delta is 0 cells, and max bank-row delta is 0 cells.
- Build a geometry-aware face-state reconstruction before y-face flux evaluation; the source split alone did not restore the GeoClaw edge signs.
- Use the authored initial -> GeoClaw final -> C++ final column profiles to retune constriction width/depth mapping before accepting any face-state change.
- Keep feature forcing and stronger source-split tuning off, then rerun the face/source audit, mask/throat diagnostics, threshold report, and Milestone 17 guardrail.
