# Milestone 18 Constriction Mask Alignment Diagnostic

Schema: `raftsim.milestone18.constriction_mask_alignment.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_local_fringe/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_local_fringe/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m

## Summary

- Domain wet-mask mismatch: `7` cells (`0.0243056` fraction)
- Max column wet-mask mismatch fraction: `0.166667`
- Max wet-width delta: `1` m
- Max bank-row delta: `1` rows
- Max mean wet-depth delta: `0.322188` m
- Max column-mass delta: `2.67759` m3

## Feature

- `angle_rad`: `0.0`
- `center_x`: `11.5`
- `center_y`: `0.0`
- `kind`: `constriction`
- `length_m`: `8.64`
- `metadata`: `{'fixture_role': 'dry_bank_throat'}`
- `radius_m`: `2.0`
- `strength`: `2.060119640661019`
- `width_m`: `4.0`

## Worst Columns

| Column | x m | Mask mismatch | Geo rows | C++ rows | Geo wet width m | C++ wet width m | Width delta m | Mass delta m3 | Mean depth delta m |
| ---: | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 12 | 12 | 2/12 | 3-6 | 4-7 | 4 | 4 | 0 | 0.568642 | 0.233534 |
| 11 | 11 | 2/12 | 3-6 | 4-7 | 4 | 4 | 0 | 0.555676 | 0.239744 |
| 6 | 6 | 1/12 | 1-11 | 1-11 | 10 | 11 | 1 | -1.13871 | -0.220687 |
| 9 | 9 | 1/12 | 3-9 | 3-10 | 7 | 8 | 1 | 0.952705 | 0.00776198 |
| 8 | 8 | 1/12 | 3-9 | 3-10 | 7 | 8 | 1 | -0.334987 | -0.19763 |
| 0 | 0 | 0/12 | 0-11 | 0-11 | 12 | 12 | 0 | -2.67759 | -0.223133 |
| 19 | 19 | 0/12 | 1-9 | 1-9 | 9 | 9 | 0 | 2.3823 | 0.265462 |
| 20 | 20 | 0/12 | 1-9 | 1-9 | 9 | 9 | 0 | 1.95338 | 0.217959 |

## Blocked Reasons

- Final-frame C++ wet/dry mask mismatch exceeds the 0.02 comparison threshold.
- At least one C++ constriction column differs from GeoClaw mean wet depth by more than 0.25 m.
- At least one C++ constriction column mass differs from GeoClaw beyond the diagnostic budget.

## Next Levers

- Fit wet-band span changes outside the narrowest throat columns before adding feature forcing.
- Retune dry-bank reconstruction so non-throat columns can follow GeoClaw bank expansion, recession, and row shifts.
- Recheck cross-section, slope, conservation, and Froude errors after the wet-mask spans agree.
- Rerun the Milestone 17 analytic guardrail and corrected-reference constriction comparison after the next solver change.
