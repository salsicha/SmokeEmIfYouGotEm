# Milestone 18 Constriction Mask Alignment Diagnostic

Schema: `raftsim.milestone18.constriction_mask_alignment.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_near_throat_support/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_near_throat_support/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m

## Summary

- Domain wet-mask mismatch: `1` cells (`0.00347222` fraction)
- Max column wet-mask mismatch fraction: `0.0833333`
- Max wet-width delta: `1` m
- Max bank-row delta: `0` rows
- Max mean wet-depth delta: `0.400935` m
- Max column-mass delta: `2.45532` m3

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
| 6 | 6 | 1/12 | 1-11 | 1-11 | 10 | 11 | 1 | -0.976452 | -0.205937 |
| 0 | 0 | 0/12 | 0-11 | 0-11 | 12 | 12 | 0 | -2.45532 | -0.20461 |
| 14 | 14 | 0/12 | 4-8 | 4-8 | 5 | 5 | 0 | -2.28031 | -0.400935 |
| 19 | 19 | 0/12 | 1-9 | 1-9 | 9 | 9 | 0 | 1.99292 | 0.222198 |
| 18 | 18 | 0/12 | 1-9 | 1-9 | 9 | 9 | 0 | 1.59751 | 0.178128 |
| 20 | 20 | 0/12 | 1-9 | 1-9 | 9 | 9 | 0 | 1.58016 | 0.176491 |
| 17 | 17 | 0/12 | 3-9 | 3-9 | 7 | 7 | 0 | 1.56465 | 0.241781 |
| 21 | 21 | 0/12 | 1-9 | 1-9 | 9 | 9 | 0 | 1.14945 | 0.128685 |

## Blocked Reasons

- At least one C++ constriction column differs from GeoClaw mean wet depth by more than 0.25 m.
- At least one C++ constriction column mass differs from GeoClaw beyond the diagnostic budget.

## Next Levers

- Fit wet-band span changes outside the narrowest throat columns before adding feature forcing.
- Retune dry-bank reconstruction so non-throat columns can follow GeoClaw bank expansion, recession, and row shifts.
- Recheck cross-section, slope, conservation, and Froude errors after the wet-mask spans agree.
- Rerun the Milestone 17 analytic guardrail and corrected-reference constriction comparison after the next solver change.
