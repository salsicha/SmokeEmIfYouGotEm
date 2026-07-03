# Milestone 18 Constriction Face-State Width/Depth Diagnostic

Schema: `raftsim.milestone18.constriction_face_state_width_depth.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_recovery_mid_interior_cross_stream_pocket_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_recovery_mid_interior_cross_stream_pocket_final_support/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Compares authored, GeoClaw final, and C++ final wet-band columns while checking GeoClaw/C++ upstream edge face states before the next constriction solver change.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Depth delta threshold: `0.25` m
Wet-width delta threshold: `1` cells
Bank-row delta threshold: `1` cells

## Summary

- Face-state blockers: `10`
- Face sign mismatches: `0`
- Width mapping blockers: `0`
- Bank alignment blockers: `0`
- Depth mapping blockers: `0`
- Edge opposition mismatches: `0`
- Max abs volume-flux delta: `0.559722` m3/s
- Max abs face mean-depth delta: `0.424249` m
- Max abs wet-width delta: `1` cells
- Max abs bank-row delta: `0` cells
- Recommended levers: `['geometry_aware_face_state_reconstruction', 'preserve_as_guardrail']`

## Worst Face-State Samples

| Face | Column | Rows | Zone | GeoClaw h/v/q/sign | C++ h/v/q/sign | q delta | Depth delta | Width/bank deltas | Blockers | Lever |
| --- | ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| `lower_edge_face` | 5 | `1-2` | `upstream_approach` | `1.24635/1.17379/1.46296/1` | `0.974149/0.927205/0.903236/1` | -0.559722 | -0.272206 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 6 | `8-9` | `upstream_approach` | `1.15452/-1.44608/-1.66953/-1` | `1.12501/-1.11978/-1.25976/-1` | 0.409768 | -0.029509 | `1/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `lower_edge_face` | 8 | `2-3` | `upstream_approach` | `0.33907/0.219158/0.0743101/1` | `0.345255/1.19353/0.412073/1` | 0.337763 | 0.00618442 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `lower_edge_face` | 9 | `2-3` | `upstream_approach` | `0.330975/0.185864/0.0615163/1` | `0.339468/1.1475/0.389537/1` | 0.328021 | 0.00849284 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `lower_edge_face` | 0 | `1-2` | `upstream_approach` | `1.198/1.70761/2.04571/1` | `1.15659/1.5076/1.74367/1` | -0.302035 | -0.0414057 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 9 | `7-8` | `upstream_approach` | `0.983374/-1.39145/-1.36832/-1` | `1.40762/-1.18425/-1.66698/-1` | -0.298664 | 0.424249 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 8 | `7-8` | `upstream_approach` | `1.85053/-0.760508/-1.40735/-1` | `1.63997/-1.02846/-1.68664/-1` | -0.279296 | -0.210563 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `lower_edge_face` | 2 | `1-2` | `upstream_approach` | `1.01111/1.30241/1.31687/1` | `1.0323/1.53708/1.58673/1` | 0.26986 | 0.0211954 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `lower_edge_face` | 1 | `1-2` | `upstream_approach` | `0.978339/2.01871/1.97499/1` | `0.988887/1.72774/1.70854/1` | -0.266445 | 0.0105487 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `lower_edge_face` | 6 | `1-2` | `upstream_approach` | `1.39221/0.523551/0.728892/1` | `1.09034/0.602431/0.656855/1` | -0.0720362 | -0.301868 | `1/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 4 | `8-9` | `upstream_approach` | `1.11127/-1.10838/-1.23171/-1` | `1.17616/-1.23929/-1.45761/-1` | -0.225893 | 0.0648856 | `0/0/0` | `face=False, width=False, bank=False, depth=False` | `preserve_as_guardrail` |
| `upper_edge_face` | 0 | `8-9` | `upstream_approach` | `1.23942/-1.61985/-2.00767/-1` | `1.18363/-1.54162/-1.82471/-1` | 0.182962 | -0.0557906 | `0/0/0` | `face=False, width=False, bank=False, depth=False` | `preserve_as_guardrail` |

## Column Profiles

| Column | Zone | Authored width/banks/depth | GeoClaw width/banks/depth | C++ width/banks/depth | C++ minus GeoClaw | Blockers |
| ---: | --- | --- | --- | --- | --- | --- |
| 0 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.32633` | `12/0-11/1.26565` | `0/0/0/-0.0606812` | `width=False, bank=False, depth=False` |
| 1 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.16904` | `12/0-11/1.15404` | `0/0/0/-0.0150012` | `width=False, bank=False, depth=False` |
| 2 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.15892` | `12/0-11/1.1695` | `0/0/0/0.0105839` | `width=False, bank=False, depth=False` |
| 3 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.26074` | `11/1-11/1.23595` | `0/0/0/-0.024794` | `width=False, bank=False, depth=False` |
| 4 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.281` | `11/1-11/1.21799` | `0/0/0/-0.0630068` | `width=False, bank=False, depth=False` |
| 5 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.30334` | `11/1-11/1.21277` | `0/0/0/-0.0905715` | `width=False, bank=False, depth=False` |
| 6 | `upstream_approach` | `8/2-9/1.25` | `10/1-11/1.45507` | `11/1-11/1.20763` | `1/0/0/-0.247442` | `width=False, bank=False, depth=False` |
| 7 | `upstream_approach` | `6/3-8/1.25` | `10/1-11/1.25609` | `10/1-11/1.23044` | `0/0/0/-0.0256549` | `width=False, bank=False, depth=False` |
| 8 | `upstream_approach` | `6/3-8/1.25` | `7/3-9/1.48607` | `7/3-9/1.41038` | `0/0/0/-0.075691` | `width=False, bank=False, depth=False` |
| 9 | `upstream_approach` | `6/3-8/1.25` | `7/3-9/1.13466` | `7/3-9/1.25968` | `0/0/0/0.125027` | `width=False, bank=False, depth=False` |
| 10 | `constriction_throat` | `4/4-7/1.25` | `5/3-7/1.16347` | `5/3-7/1.18593` | `0/0/0/0.0224615` | `width=False, bank=False, depth=False` |
| 11 | `constriction_throat` | `4/4-7/1.25` | `4/3-6/1.24796` | `4/3-6/1.27273` | `0/0/0/0.0247688` | `width=False, bank=False, depth=False` |
| 12 | `constriction_throat` | `4/4-7/1.25` | `4/3-6/1.12546` | `4/3-6/1.21684` | `0/0/0/0.0913808` | `width=False, bank=False, depth=False` |
| 13 | `constriction_throat` | `4/4-7/1.25` | `5/3-7/0.839163` | `5/3-7/0.866617` | `0/0/0/0.0274543` | `width=False, bank=False, depth=False` |

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

## Next Levers

- Start with `lower_edge_face` column 5 rows 1-2; q delta is -0.559722 m3/s, face mean-depth delta is -0.272206 m, wet-width delta is 0 cells, and max bank-row delta is 0 cells.
- Build a geometry-aware face-state reconstruction before y-face flux evaluation; the source split alone did not restore the GeoClaw edge signs.
- Keep feature forcing and stronger source-split tuning off, then rerun the face/source audit, mask/throat diagnostics, threshold report, and Milestone 17 guardrail.
