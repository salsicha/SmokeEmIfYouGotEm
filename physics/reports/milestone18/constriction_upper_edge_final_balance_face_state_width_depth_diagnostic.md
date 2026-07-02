# Milestone 18 Constriction Face-State Width/Depth Diagnostic

Schema: `raftsim.milestone18.constriction_face_state_width_depth.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_upper_edge_final_balance/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_upper_edge_final_balance/finite_volume_roe/scenario/constriction_seed_16`
Diagnostic scope: Compares authored, GeoClaw final, and C++ final wet-band columns while checking GeoClaw/C++ upstream edge face states before the next constriction solver change.
Wet-depth threshold: `0.15` m
Velocity sign floor: `0.05` m/s
Flux delta threshold: `0.25` m3/s
Depth delta threshold: `0.25` m
Wet-width delta threshold: `1` cells
Bank-row delta threshold: `1` cells

## Summary

- Face-state blockers: `18`
- Face sign mismatches: `1`
- Width mapping blockers: `3`
- Bank alignment blockers: `1`
- Depth mapping blockers: `1`
- Edge opposition mismatches: `1`
- Max abs volume-flux delta: `1.99953` m3/s
- Max abs face mean-depth delta: `0.573318` m
- Max abs wet-width delta: `2` cells
- Max abs bank-row delta: `2` cells
- Recommended levers: `['geometry_aware_face_state_reconstruction', 'geometry_aware_face_state_reconstruction_with_width_depth_mapping_check', 'preserve_as_guardrail', 'width_depth_mapping']`

## Worst Face-State Samples

| Face | Column | Rows | Zone | GeoClaw h/v/q/sign | C++ h/v/q/sign | q delta | Depth delta | Width/bank deltas | Blockers | Lever |
| --- | ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| `upper_edge_face` | 4 | `8-9` | `upstream_approach` | `1.11127/-1.10838/-1.23171/-1` | `1.55275/-0.0351535/-0.0545847/0` | 1.17713 | 0.441478 | `-1/0/-1` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 1 | `8-9` | `upstream_approach` | `1.03834/-2.21375/-2.29862/-1` | `1.3951/-0.214384/-0.299087/-1` | 1.99953 | 0.356761 | `-2/1/-1` | `face=True, width=True, bank=False, depth=False` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `lower_edge_face` | 0 | `1-2` | `upstream_approach` | `1.198/1.70761/2.04571/1` | `0.770347/0.271282/0.208981/1` | -1.83673 | -0.42765 | `-2/1/-1` | `face=True, width=True, bank=False, depth=True` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `upper_edge_face` | 0 | `8-9` | `upstream_approach` | `1.23942/-1.61985/-2.00767/-1` | `1.22809/-0.186999/-0.229651/-1` | 1.77802 | -0.0113311 | `-2/1/-1` | `face=True, width=True, bank=False, depth=True` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `lower_edge_face` | 1 | `1-2` | `upstream_approach` | `0.978339/2.01871/1.97499/1` | `0.852268/0.234145/0.199555/1` | -1.77543 | -0.12607 | `-2/1/-1` | `face=True, width=True, bank=False, depth=False` | `geometry_aware_face_state_reconstruction_with_width_depth_mapping_check` |
| `upper_edge_face` | 2 | `8-9` | `upstream_approach` | `1.0484/-1.82303/-1.91128/-1` | `1.4928/-0.237792/-0.354976/-1` | 1.5563 | 0.444394 | `-1/0/-1` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 6 | `8-9` | `upstream_approach` | `1.15452/-1.44608/-1.66953/-1` | `1.58266/-0.120326/-0.190436/-1` | 1.47909 | 0.428141 | `0/0/-1` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 3 | `8-9` | `upstream_approach` | `1.08534/-1.26068/-1.36827/-1` | `1.52413/-0.0994532/-0.151579/-1` | 1.21669 | 0.438786 | `-1/0/-1` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 5 | `8-9` | `upstream_approach` | `1.10988/-1.15573/-1.28272/-1` | `1.57881/-0.0595841/-0.0940721/-1` | 1.18865 | 0.468931 | `-1/0/-1` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `upper_edge_face` | 9 | `7-8` | `upstream_approach` | `0.983374/-1.39145/-1.36832/-1` | `1.55669/-0.126987/-0.19768/-1` | 1.17064 | 0.573318 | `0/0/0` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `lower_edge_face` | 5 | `1-2` | `upstream_approach` | `1.24635/1.17379/1.46296/1` | `0.931721/0.341889/0.318545/1` | -1.14441 | -0.314634 | `-1/0/-1` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |
| `lower_edge_face` | 2 | `1-2` | `upstream_approach` | `1.01111/1.30241/1.31687/1` | `0.901263/0.205128/0.184874/1` | -1.132 | -0.109844 | `-1/0/-1` | `face=True, width=False, bank=False, depth=False` | `geometry_aware_face_state_reconstruction` |

## Column Profiles

| Column | Zone | Authored width/banks/depth | GeoClaw width/banks/depth | C++ width/banks/depth | C++ minus GeoClaw | Blockers |
| ---: | --- | --- | --- | --- | --- | --- |
| 0 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.32633` | `10/1-10/1.05766` | `-2/1/-1/-0.268673` | `width=True, bank=False, depth=True` |
| 1 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.16904` | `10/1-10/1.19306` | `-2/1/-1/0.0240212` | `width=True, bank=False, depth=False` |
| 2 | `upstream_approach` | `8/2-9/1.25` | `12/0-11/1.15892` | `11/0-10/1.17173` | `-1/0/-1/0.0128134` | `width=False, bank=False, depth=False` |
| 3 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.26074` | `10/1-10/1.2956` | `-1/0/-1/0.0348568` | `width=False, bank=False, depth=False` |
| 4 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.281` | `10/1-10/1.31177` | `-1/0/-1/0.0307705` | `width=False, bank=False, depth=False` |
| 5 | `upstream_approach` | `8/2-9/1.25` | `11/1-11/1.30334` | `10/1-10/1.33363` | `-1/0/-1/0.0302913` | `width=False, bank=False, depth=False` |
| 6 | `upstream_approach` | `8/2-9/1.25` | `10/1-11/1.45507` | `10/1-10/1.33769` | `0/0/-1/-0.117384` | `width=False, bank=False, depth=False` |
| 7 | `upstream_approach` | `6/3-8/1.25` | `10/1-11/1.25609` | `8/2-9/1.41216` | `-2/1/-2/0.156063` | `width=True, bank=True, depth=False` |
| 8 | `upstream_approach` | `6/3-8/1.25` | `7/3-9/1.48607` | `7/3-9/1.46296` | `0/0/0/-0.0231101` | `width=False, bank=False, depth=False` |
| 9 | `upstream_approach` | `6/3-8/1.25` | `7/3-9/1.13466` | `7/3-9/1.37132` | `0/0/0/0.236663` | `width=False, bank=False, depth=False` |
| 10 | `constriction_throat` | `4/4-7/1.25` | `5/3-7/1.16347` | `5/3-7/1.39895` | `0/0/0/0.235476` | `width=False, bank=False, depth=False` |
| 11 | `constriction_throat` | `4/4-7/1.25` | `4/3-6/1.24796` | `4/3-6/1.25` | `0/0/0/0.00203678` | `width=False, bank=False, depth=False` |
| 12 | `constriction_throat` | `4/4-7/1.25` | `4/3-6/1.12546` | `4/3-6/1.25` | `0/0/0/0.12454` | `width=False, bank=False, depth=False` |
| 13 | `constriction_throat` | `4/4-7/1.25` | `5/3-7/0.839163` | `5/3-7/1.04914` | `0/0/0/0.209979` | `width=False, bank=False, depth=False` |

## Edge Pair Summary

| Column | Lower signs | Upper signs | GeoClaw opposed | C++ opposed | Match |
| ---: | --- | --- | --- | --- | --- |
| 0 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 1 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 2 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 3 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 4 | `1->1` | `-1->0` | `True` | `False` | `False` |
| 5 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 6 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 7 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 8 | `1->1` | `-1->-1` | `True` | `True` | `True` |
| 9 | `1->1` | `-1->-1` | `True` | `True` | `True` |

## Blocked Reasons

- C++ upstream edge face-state signs still disagree with GeoClaw.
- C++ upstream edge face-state volume-flux deltas exceed the diagnostic threshold.
- GeoClaw lower/upper edge opposition is still missing from the C++ face states.
- C++ constriction wet-band width still differs from GeoClaw beyond the mapping threshold.
- C++ constriction bank row placement still differs from GeoClaw beyond the mapping threshold.
- C++ constriction mean wet depth still differs from GeoClaw beyond the mapping threshold.

## Next Levers

- Start with `upper_edge_face` column 4 rows 8-9; q delta is 1.17713 m3/s, face mean-depth delta is 0.441478 m, wet-width delta is -1 cells, and max bank-row delta is 1 cells.
- Build a geometry-aware face-state reconstruction before y-face flux evaluation; the source split alone did not restore the GeoClaw edge signs.
- Use the authored initial -> GeoClaw final -> C++ final column profiles to retune constriction width/depth mapping before accepting any face-state change.
- Preserve GeoClaw's lower/upper edge opposition in the upstream wet band; a single-sign lateral state remains a blocker.
- Keep feature forcing and stronger source-split tuning off, then rerun the face/source audit, mask/throat diagnostics, threshold report, and Milestone 17 guardrail.
