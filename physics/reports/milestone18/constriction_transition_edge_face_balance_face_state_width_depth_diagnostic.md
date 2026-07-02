# Milestone 18 Constriction Face-State Width/Depth Diagnostic

Schema: `raftsim.milestone18.constriction_face_state_width_depth.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_transition_edge_face_balance/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_transition_edge_face_balance/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Compares authored, GeoClaw final, and C++ final wet-band columns while checking GeoClaw/C++ upstream edge face states before the next constriction solver change.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Depth delta threshold: `0.25` m
Wet-width delta threshold: `1` cells
Bank-row delta threshold: `1` cells

## Summary

- Face-state blockers: `18`
- Face sign mismatches: `6`
- Width mapping blockers: `3`
- Bank alignment blockers: `1`
- Depth mapping blockers: `1`
- Edge opposition mismatches: `6`
- Max abs volume-flux delta: `2.00203` m3/s
- Max abs face mean-depth delta: `0.575696` m
- Max abs wet-width delta: `2` cells
- Max abs bank-row delta: `2` cells
- Recommended levers: `['geometry_aware_face_state_reconstruction', 'geometry_aware_face_state_reconstruction_with_width_depth_mapping_check', 'preserve_as_guardrail', 'width_depth_mapping']`

## Worst Face-State Samples

| Face | Column | Rows | Zone | GeoClaw h/v/q/sign | C++ h/v/q/sign | q delta | Depth delta | Width/bank deltas | Blockers | Lever |
| --- | ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| `upper_edge_face` | 6 | `8-9` | `upstream_approach` | `1.15452/-1.44608/-1.66953/-1` | `1.60919/0.0383548/0.0617202/0` | 1.73125 | 0.45467 | `0/0/-1` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 9 | `7-8` | `upstream_approach` | `0.983374/-1.39145/-1.36832/-1` | `1.55907/0.211466/0.32969/1` | 1.69801 | 0.575696 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 8 | `7-8` | `upstream_approach` | `1.85053/-0.760508/-1.40735/-1` | `1.67781/0.145554/0.244211/1` | 1.65156 | -0.172729 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 5 | `8-9` | `upstream_approach` | `1.10988/-1.15573/-1.28272/-1` | `1.59371/0.00594836/0.00947995/0` | 1.2922 | 0.483826 | `-1/0/-1` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 7 | `7-8` | `upstream_approach` | `1.85262/-0.678521/-1.25704/-1` | `1.81114/-0.00812977/-0.0147242/0` | 1.24231 | -0.0414753 | `-2/1/-2` | `face=True, width=True, bank=True, depth=False` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `upper_edge_face` | 4 | `8-9` | `upstream_approach` | `1.11127/-1.10838/-1.23171/-1` | `1.55455/-0.0311795/-0.0484702/0` | 1.18324 | 0.443281 | `-1/0/-1` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 1 | `8-9` | `upstream_approach` | `1.03834/-2.21375/-2.29862/-1` | `1.39025/-0.213333/-0.296586/-1` | 2.00203 | 0.351911 | `-2/1/-1` | `face=True, width=True, bank=False, depth=False` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `lower_edge_face` | 0 | `1-2` | `upstream_approach` | `1.198/1.70761/2.04571/1` | `0.767775/0.272533/0.209244/1` | -1.83647 | -0.430222 | `-2/1/-1` | `face=True, width=True, bank=False, depth=True` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `upper_edge_face` | 0 | `8-9` | `upstream_approach` | `1.23942/-1.61985/-2.00767/-1` | `1.22262/-0.186088/-0.227514/-1` | 1.78016 | -0.0168034 | `-2/1/-1` | `face=True, width=True, bank=False, depth=True` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `lower_edge_face` | 1 | `1-2` | `upstream_approach` | `0.978339/2.01871/1.97499/1` | `0.849901/0.235487/0.200141/1` | -1.77484 | -0.128437 | `-2/1/-1` | `face=True, width=True, bank=False, depth=False` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `upper_edge_face` | 2 | `8-9` | `upstream_approach` | `1.0484/-1.82303/-1.91128/-1` | `1.48897/-0.236828/-0.352631/-1` | 1.55865 | 0.440567 | `-1/0/-1` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 3 | `8-9` | `upstream_approach` | `1.08534/-1.26068/-1.36827/-1` | `1.52287/-0.0986038/-0.150161/-1` | 1.21811 | 0.437533 | `-1/0/-1` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |

## Column Profiles

| Column | Zone | Authored width/banks/depth | GeoClaw width/banks/depth | C++ width/banks/depth | C++ minus GeoClaw | Blockers |
| ---: | --- | --- | --- | --- | --- | --- |
| 0 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.32633` | `10/1-10/1.05314` | `-2/1/-1/-0.273186` | `width=True, bank=False, depth=True` |
| 1 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.16904` | `10/1-10/1.18907` | `-2/1/-1/0.020027` | `width=True, bank=False, depth=False` |
| 2 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.15892` | `11/0-10/1.16885` | `-1/0/-1/0.0099371` | `width=False, bank=False, depth=False` |
| 3 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.26074` | `10/1-10/1.29457` | `-1/0/-1/0.0338316` | `width=False, bank=False, depth=False` |
| 4 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.281` | `10/1-10/1.31275` | `-1/0/-1/0.031754` | `width=False, bank=False, depth=False` |
| 5 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.30334` | `10/1-10/1.33764` | `-1/0/-1/0.0342971` | `width=False, bank=False, depth=False` |
| 6 | `upstream_approach` | `8/2-9/1.25` | `10/1-11/1.45507` | `10/1-10/1.34342` | `0/0/-1/-0.111648` | `width=False, bank=False, depth=False` |
| 7 | `upstream_approach` | `6/3-8/1.25` | `10/1-11/1.25609` | `8/2-9/1.41746` | `-2/1/-2/0.161367` | `width=True, bank=True, depth=False` |
| 8 | `upstream_approach` | `6/3-8/1.25` | `7/3-9/1.48607` | `7/3-9/1.46828` | `0/0/0/-0.0177963` | `width=False, bank=False, depth=False` |
| 9 | `upstream_approach` | `6/3-8/1.25` | `7/3-9/1.13466` | `7/3-9/1.36493` | `0/0/0/0.230276` | `width=False, bank=False, depth=False` |
| 10 | `constriction_throat` | `4/4-7/1.25` | `5/3-7/1.16347` | `5/3-7/1.37204` | `0/0/0/0.208566` | `width=False, bank=False, depth=False` |
| 11 | `constriction_throat` | `4/4-7/1.25` | `4/3-6/1.24796` | `4/3-6/1.25` | `0/0/0/0.00203678` | `width=False, bank=False, depth=False` |
| 12 | `constriction_throat` | `4/4-7/1.25` | `4/3-6/1.12546` | `4/3-6/1.25` | `0/0/0/0.12454` | `width=False, bank=False, depth=False` |
| 13 | `constriction_throat` | `4/4-7/1.25` | `5/3-7/0.839163` | `5/3-7/1.04923` | `0/0/0/0.21007` | `width=False, bank=False, depth=False` |

## Edge Pair Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 4 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 5 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 6 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 7 | `1->1` | `-1->0` | `True` | `False` | `False` |
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

- Start with `upper_edge_face` column 6 rows 8-9; q delta is 1.73125 m3/s, face mean-depth delta is 0.45467 m, wet-width delta is 0 cells, and max bank-row delta is 1 cells.
- Build a geometry-aware face-state reconstruction before y-face flux evaluation; the source split alone did not restore the GeoClaw edge signs.
- Use the authored initial -> GeoClaw final -> C++ final column profiles to retune constriction width/depth mapping before accepting any face-state change.
- Preserve GeoClaw's lower/upper edge opposition in the upstream wet band; a single-sign lateral state remains a blocker.
- Keep feature forcing and stronger source-split tuning off, then rerun the face/source audit, mask/throat diagnostics, threshold report, and Milestone 17 guardrail.
