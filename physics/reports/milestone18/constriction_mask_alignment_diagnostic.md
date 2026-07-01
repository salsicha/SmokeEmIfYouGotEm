# Milestone 18 Constriction Mask Alignment Diagnostic

Schema: `raftsim.milestone18.constriction_mask_alignment.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_momentum_shape/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_momentum_shape/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m

## Summary

- Domain wet-mask mismatch: `46` cells (`0.159722` fraction)
- Max column wet-mask mismatch fraction: `0.333333`
- Max wet-width delta: `4` m
- Max bank-row delta: `3` rows
- Max mean wet-depth delta: `0.427354` m
- Max column-mass delta: `5.44445` m3

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
| 0 | 0 | 4/12 | 0-11 | 2-9 | 12 | 8 | -4 | -5.44445 | -0.0173906 |
| 7 | 7 | 4/12 | 1-11 | 3-8 | 10 | 6 | -4 | -4.64509 | 0.0811817 |
| 1 | 1 | 4/12 | 0-11 | 2-9 | 12 | 8 | -4 | -3.60322 | 0.134117 |
| 2 | 2 | 4/12 | 0-11 | 2-9 | 12 | 8 | -4 | -3.52649 | 0.138646 |
| 5 | 5 | 3/12 | 1-11 | 2-9 | 11 | 8 | -3 | -4.18425 | -0.025172 |
| 4 | 4 | 3/12 | 1-11 | 2-9 | 11 | 8 | -3 | -3.88585 | 0.00511222 |
| 3 | 3 | 3/12 | 1-11 | 2-9 | 11 | 8 | -3 | -3.65544 | 0.031268 |
| 6 | 6 | 2/12 | 1-11 | 2-9 | 10 | 8 | -2 | -5.23848 | -0.270264 |

## Blocked Reasons

- Final-frame C++ wet/dry mask mismatch exceeds the 0.02 comparison threshold.
- At least one C++ constriction column differs from GeoClaw wet width by more than one lateral cell.
- At least one C++ constriction bank span differs from GeoClaw by more than one row.
- At least one C++ constriction column differs from GeoClaw mean wet depth by more than 0.25 m.
- At least one C++ constriction column mass differs from GeoClaw beyond the diagnostic budget.

## Next Levers

- Fit wet-band span changes outside the narrowest throat columns before adding feature forcing.
- Retune dry-bank reconstruction so non-throat columns can follow GeoClaw bank expansion, recession, and row shifts.
- Recheck cross-section, slope, conservation, and Froude errors after the wet-mask spans agree.
- Rerun the Milestone 17 analytic guardrail and corrected-reference constriction comparison after the next solver change.
