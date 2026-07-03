# Milestone 18 Constriction Face-State Width/Depth Diagnostic

Schema: `raftsim.milestone18.constriction_face_state_width_depth.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_boundary_outer_lower_shelf_cross_stream_pocket_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_boundary_outer_lower_shelf_cross_stream_pocket_final_support/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Compares authored, GeoClaw final, and C++ final wet-band columns while checking GeoClaw/C++ upstream edge face states before the next constriction solver change.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Depth delta threshold: `0.25` m
Wet-width delta threshold: `1` cells
Bank-row delta threshold: `1` cells

## Summary

- Face-state blockers: `4`
- Face sign mismatches: `0`
- Width mapping blockers: `0`
- Bank alignment blockers: `0`
- Depth mapping blockers: `0`
- Edge opposition mismatches: `0`
- Max abs volume-flux delta: `0.337763` m3/s
- Max abs face mean-depth delta: `0.301868` m
- Max abs wet-width delta: `1` cells
- Max abs bank-row delta: `0` cells
- Recommended levers: `['geometry_aware_face_state_reconstruction', 'preserve_as_guardrail']`

## Worst Face-State Samples

| Face | Column | Rows | Zone | GeoClaw h/v/q/sign | C++ h/v/q/sign | q delta | Depth delta | Width/bank deltas | Blockers | Lever |
| --- | ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| `lower_edge_face` | 8 | `2-3` | `upstream_approach` | `0.33907/0.219158/0.0743101/1` | `0.345255/1.19353/0.412073/1` | 0.337763 | 0.00618442 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `lower_edge_face` | 9 | `2-3` | `upstream_approach` | `0.330975/0.185864/0.0615163/1` | `0.339468/1.1475/0.389537/1` | 0.328021 | 0.00849284 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `lower_edge_face` | 5 | `1-2` | `upstream_approach` | `1.24635/1.17379/1.46296/1` | `1.07584/1.07894/1.16077/1` | -0.302188 | -0.17051 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `lower_edge_face` | 6 | `1-2` | `upstream_approach` | `1.39221/0.523551/0.728892/1` | `1.09034/0.602431/0.656855/1` | -0.0720362 | -0.301868 | `1/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `lower_edge_face` | 2 | `1-2` | `upstream_approach` | `1.01111/1.30241/1.31687/1` | `1.0323/1.39509/1.44015/1` | 0.123282 | 0.0211954 | `0/0/0` | `face=False, width=False, bank=False, depth=False` | `preserve_as_guardrail` |
| `upper_edge_face` | 3 | `8-9` | `upstream_approach` | `1.08534/-1.26068/-1.36827/-1` | `1.15981/-1.26182/-1.46348/-1` | -0.0952054 | 0.0744712 | `0/0/0` | `face=False, width=False, bank=False, depth=False` | `preserve_as_guardrail` |
| `upper_edge_face` | 1 | `8-9` | `upstream_approach` | `1.03834/-2.21375/-2.29862/-1` | `1.01824/-2.34278/-2.38551/-1` | -0.0868945 | -0.020093 | `0/0/0` | `face=False, width=False, bank=False, depth=False` | `preserve_as_guardrail` |
| `lower_edge_face` | 0 | `1-2` | `upstream_approach` | `1.198/1.70761/2.04571/1` | `1.15659/1.70166/1.96812/1` | -0.0775862 | -0.0414057 | `0/0/0` | `face=False, width=False, bank=False, depth=False` | `preserve_as_guardrail` |
| `upper_edge_face` | 9 | `7-8` | `upstream_approach` | `0.983374/-1.39145/-1.36832/-1` | `1.03155/-1.39161/-1.43552/-1` | -0.0671994 | 0.0481774 | `0/0/0` | `face=False, width=False, bank=False, depth=False` | `preserve_as_guardrail` |
| `upper_edge_face` | 6 | `8-9` | `upstream_approach` | `1.15452/-1.44608/-1.66953/-1` | `1.12501/-1.42501/-1.60315/-1` | 0.0663807 | -0.029509 | `1/0/0` | `face=False, width=False, bank=False, depth=False` | `preserve_as_guardrail` |
| `upper_edge_face` | 0 | `8-9` | `upstream_approach` | `1.23942/-1.61985/-2.00767/-1` | `1.23917/-1.65965/-2.05659/-1` | -0.0489147 | -0.000253219 | `0/0/0` | `face=False, width=False, bank=False, depth=False` | `preserve_as_guardrail` |
| `lower_edge_face` | 3 | `1-2` | `upstream_approach` | `1.0627/0.775286/0.823895/1` | `0.99043/0.785205/0.77769/1` | -0.0462046 | -0.0722688 | `0/0/0` | `face=False, width=False, bank=False, depth=False` | `preserve_as_guardrail` |

## Column Profiles

| Column | Zone | Authored width/banks/depth | GeoClaw width/banks/depth | C++ width/banks/depth | C++ minus GeoClaw | Blockers |
| ---: | --- | --- | --- | --- | --- | --- |
| 0 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.32633` | `12/0-11/1.27491` | `0/0/0/-0.051425` | `width=False, bank=False, depth=False` |
| 1 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.16904` | `12/0-11/1.14478` | `0/0/0/-0.0242574` | `width=False, bank=False, depth=False` |
| 2 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.15892` | `12/0-11/1.16015` | `0/0/0/0.00123228` | `width=False, bank=False, depth=False` |
| 3 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.26074` | `11/1-11/1.24107` | `0/0/0/-0.0196697` | `width=False, bank=False, depth=False` |
| 4 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.281` | `11/1-11/1.22307` | `0/0/0/-0.0579293` | `width=False, bank=False, depth=False` |
| 5 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.30334` | `11/1-11/1.21277` | `0/0/0/-0.0905715` | `width=False, bank=False, depth=False` |
| 6 | `upstream_approach` | `8/2-9/1.25` | `10/1-11/1.45507` | `11/1-11/1.23323` | `1/0/0/-0.221841` | `width=False, bank=False, depth=False` |
| 7 | `upstream_approach` | `6/3-8/1.25` | `10/1-11/1.25609` | `10/1-11/1.27064` | `0/0/0/0.014548` | `width=False, bank=False, depth=False` |
| 8 | `upstream_approach` | `6/3-8/1.25` | `7/3-9/1.48607` | `7/3-9/1.4604` | `0/0/0/-0.0256747` | `width=False, bank=False, depth=False` |
| 9 | `upstream_approach` | `6/3-8/1.25` | `7/3-9/1.13466` | `7/3-9/1.15224` | `0/0/0/0.017578` | `width=False, bank=False, depth=False` |
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

- Start with `lower_edge_face` column 8 rows 2-3; q delta is 0.337763 m3/s, face mean-depth delta is 0.00618442 m, wet-width delta is 0 cells, and max bank-row delta is 0 cells.
- Build a geometry-aware face-state reconstruction before y-face flux evaluation; the source split alone did not restore the GeoClaw edge signs.
- Keep feature forcing and stronger source-split tuning off, then rerun the face/source audit, mask/throat diagnostics, threshold report, and Milestone 17 guardrail.
