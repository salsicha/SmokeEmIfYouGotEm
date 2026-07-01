# Milestone 18 Constriction Mask Alignment Diagnostic

Schema: `raftsim.milestone18.constriction_mask_alignment.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_span_shaping/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_span_shaping/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m

## Summary

- Domain wet-mask mismatch: `56` cells (`0.194444` fraction)
- Max column wet-mask mismatch fraction: `0.416667`
- Max wet-width delta: `5` m
- Max bank-row delta: `3` rows
- Max mean wet-depth delta: `0.90552` m
- Max column-mass delta: `4.2909` m3

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
| 14 | 14 | 5/12 | 4-8 | 1-10 | 5 | 10 | 5 | -3.28671 | -0.89228 |
| 15 | 15 | 5/12 | 4-8 | 1-10 | 5 | 10 | 5 | -3.02121 | -0.90552 |
| 17 | 17 | 5/12 | 3-9 | 0-11 | 7 | 12 | 5 | 0.128728 | -0.392982 |
| 16 | 16 | 4/12 | 4-9 | 1-10 | 6 | 10 | 4 | -2.92085 | -0.709551 |
| 8 | 8 | 3/12 | 3-9 | 1-10 | 7 | 10 | 3 | -2.42001 | -0.663821 |
| 18 | 18 | 3/12 | 1-9 | 0-11 | 9 | 12 | 3 | 1.05724 | -0.159445 |
| 9 | 9 | 3/12 | 3-9 | 1-10 | 7 | 10 | 3 | -0.687517 | -0.384744 |
| 23 | 23 | 3/12 | 1-9 | 0-11 | 9 | 12 | 3 | -0.669334 | -0.348634 |

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
