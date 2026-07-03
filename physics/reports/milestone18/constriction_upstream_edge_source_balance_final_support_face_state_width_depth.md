# Milestone 18 Constriction Face-State Width/Depth Diagnostic

Schema: `raftsim.milestone18.constriction_face_state_width_depth.v0`

Decision: **PASS**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_upstream_edge_source_balance_final_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_upstream_edge_source_balance_final_support/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Compares authored, GeoClaw final, and C++ final wet-band columns while checking GeoClaw/C++ upstream edge face states before the next constriction solver change.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Depth delta threshold: `0.25` m
Wet-width delta threshold: `1` cells
Bank-row delta threshold: `1` cells

## Summary

- Face-state blockers: `0`
- Face sign mismatches: `0`
- Width mapping blockers: `0`
- Bank alignment blockers: `0`
- Depth mapping blockers: `0`
- Edge opposition mismatches: `0`
- Max abs volume-flux delta: `0.207968` m3/s
- Max abs face mean-depth delta: `0.0996471` m
- Max abs wet-width delta: `0` cells
- Max abs bank-row delta: `0` cells
- Recommended levers: `['preserve_as_guardrail']`

## Worst Face-State Samples

| Face | Column | Rows | Zone | GeoClaw h/v/q/sign | C++ h/v/q/sign | q delta | Depth delta | Width/bank deltas | Blockers | Lever |
| --- | ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| `lower_edge_face` | 9 | `2-3` | `upstream_approach` | `0.330975/0.185864/0.0615163/1` | `0.339468/0.793843/0.269484/1` | 0.207968 | 0.00849284 | `0/0/0` | `face=False, width=False, bank=False, depth=False` | `preserve_as_guardrail` |
| `lower_edge_face` | 8 | `2-3` | `upstream_approach` | `0.33907/0.219158/0.0743101/1` | `0.345255/0.698421/0.241133/1` | 0.166823 | 0.00618442 | `0/0/0` | `face=False, width=False, bank=False, depth=False` | `preserve_as_guardrail` |
| `lower_edge_face` | 5 | `1-2` | `upstream_approach` | `1.24635/1.17379/1.46296/1` | `1.246/1.0929/1.36175/1` | -0.101202 | -0.000354699 | `0/0/0` | `face=False, width=False, bank=False, depth=False` | `preserve_as_guardrail` |
| `lower_edge_face` | 3 | `1-2` | `upstream_approach` | `1.0627/0.775286/0.823895/1` | `1.06189/0.698403/0.741629/1` | -0.0822662 | -0.000806793 | `0/0/0` | `face=False, width=False, bank=False, depth=False` | `preserve_as_guardrail` |
| `upper_edge_face` | 9 | `7-8` | `upstream_approach` | `0.983374/-1.39145/-1.36832/-1` | `1.03155/-1.39161/-1.43552/-1` | -0.0671994 | 0.0481774 | `0/0/0` | `face=False, width=False, bank=False, depth=False` | `preserve_as_guardrail` |
| `upper_edge_face` | 0 | `8-9` | `upstream_approach` | `1.23942/-1.61985/-2.00767/-1` | `1.23917/-1.65965/-2.05659/-1` | -0.0489147 | -0.000253219 | `0/0/0` | `face=False, width=False, bank=False, depth=False` | `preserve_as_guardrail` |
| `upper_edge_face` | 1 | `8-9` | `upstream_approach` | `1.03834/-2.21375/-2.29862/-1` | `1.01824/-2.2136/-2.25398/-1` | 0.0446391 | -0.020093 | `0/0/0` | `face=False, width=False, bank=False, depth=False` | `preserve_as_guardrail` |
| `upper_edge_face` | 2 | `8-9` | `upstream_approach` | `1.0484/-1.82303/-1.91128/-1` | `1.05645/-1.76699/-1.86674/-1` | 0.0445331 | 0.0080472 | `0/0/0` | `face=False, width=False, bank=False, depth=False` | `preserve_as_guardrail` |
| `upper_edge_face` | 7 | `7-8` | `upstream_approach` | `1.85262/-0.678521/-1.25704/-1` | `1.87485/-0.68993/-1.29352/-1` | -0.0364774 | 0.0222356 | `0/0/0` | `face=False, width=False, bank=False, depth=False` | `preserve_as_guardrail` |
| `upper_edge_face` | 6 | `8-9` | `upstream_approach` | `1.15452/-1.44608/-1.66953/-1` | `1.12501/-1.45218/-1.63372/-1` | 0.0358146 | -0.029509 | `0/0/0` | `face=False, width=False, bank=False, depth=False` | `preserve_as_guardrail` |
| `upper_edge_face` | 5 | `8-9` | `upstream_approach` | `1.10988/-1.15573/-1.28272/-1` | `1.1311/-1.10314/-1.24776/-1` | 0.0349641 | 0.0212157 | `0/0/0` | `face=False, width=False, bank=False, depth=False` | `preserve_as_guardrail` |
| `lower_edge_face` | 2 | `1-2` | `upstream_approach` | `1.01111/1.30241/1.31687/1` | `0.98725/1.3022/1.2856/1` | -0.0312745 | -0.023857 | `0/0/0` | `face=False, width=False, bank=False, depth=False` | `preserve_as_guardrail` |

## Column Profiles

| Column | Zone | Authored width/banks/depth | GeoClaw width/banks/depth | C++ width/banks/depth | C++ minus GeoClaw | Blockers |
| ---: | --- | --- | --- | --- | --- | --- |
| 0 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.32633` | `12/0-11/1.28484` | `0/0/0/-0.0414914` | `width=False, bank=False, depth=False` |
| 1 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.16904` | `12/0-11/1.13919` | `0/0/0/-0.0298474` | `width=False, bank=False, depth=False` |
| 2 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.15892` | `12/0-11/1.14264` | `0/0/0/-0.0162765` | `width=False, bank=False, depth=False` |
| 3 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.26074` | `11/1-11/1.24107` | `0/0/0/-0.0196697` | `width=False, bank=False, depth=False` |
| 4 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.281` | `11/1-11/1.22307` | `0/0/0/-0.0579293` | `width=False, bank=False, depth=False` |
| 5 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.30334` | `11/1-11/1.24371` | `0/0/0/-0.0596342` | `width=False, bank=False, depth=False` |
| 6 | `upstream_approach` | `8/2-9/1.25` | `10/1-11/1.45507` | `10/1-11/1.41583` | `0/0/0/-0.0392465` | `width=False, bank=False, depth=False` |
| 7 | `upstream_approach` | `6/3-8/1.25` | `10/1-11/1.25609` | `10/1-11/1.2629` | `0/0/0/0.00680584` | `width=False, bank=False, depth=False` |
| 8 | `upstream_approach` | `6/3-8/1.25` | `7/3-9/1.48607` | `7/3-9/1.4604` | `0/0/0/-0.0256747` | `width=False, bank=False, depth=False` |
| 9 | `upstream_approach` | `6/3-8/1.25` | `7/3-9/1.13466` | `7/3-9/1.15224` | `0/0/0/0.017578` | `width=False, bank=False, depth=False` |
| 10 | `constriction_throat` | `4/4-7/1.25` | `5/3-7/1.16347` | `5/3-7/1.16715` | `0/0/0/0.00367999` | `width=False, bank=False, depth=False` |
| 11 | `constriction_throat` | `4/4-7/1.25` | `4/3-6/1.24796` | `4/3-6/1.28436` | `0/0/0/0.0364001` | `width=False, bank=False, depth=False` |
| 12 | `constriction_throat` | `4/4-7/1.25` | `4/3-6/1.12546` | `4/3-6/1.19869` | `0/0/0/0.0732323` | `width=False, bank=False, depth=False` |
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

## Next Levers

- Start with `lower_edge_face` column 9 rows 2-3; q delta is 0.207968 m3/s, face mean-depth delta is 0.00849284 m, wet-width delta is 0 cells, and max bank-row delta is 0 cells.
- Keep feature forcing and stronger source-split tuning off, then rerun the face/source audit, mask/throat diagnostics, threshold report, and Milestone 17 guardrail.
