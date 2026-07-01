# Milestone 18 Constriction Mask Alignment Diagnostic

Schema: `raftsim.milestone18.constriction_mask_alignment.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_constrict_recovery_cross_stream_momentum/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_constrict_recovery_cross_stream_momentum/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m

## Summary

- Domain wet-mask mismatch: `6` cells (`0.0208333` fraction)
- Max column wet-mask mismatch fraction: `0.166667`
- Max wet-width delta: `2` m
- Max bank-row delta: `1` rows
- Max mean wet-depth delta: `0.555509` m
- Max column-mass delta: `4.21735` m3

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
| 0 | 0 | 2/12 | 0-11 | 1-10 | 12 | 10 | -2 | -4.21735 | -0.179576 |
| 1 | 1 | 1/12 | 0-11 | 0-10 | 12 | 11 | -1 | -1.21479 | -0.016732 |
| 6 | 6 | 1/12 | 1-11 | 1-11 | 10 | 11 | 1 | 0.89113 | -0.0361564 |
| 16 | 16 | 1/12 | 4-9 | 3-9 | 6 | 7 | 1 | 0.865516 | -0.0199166 |
| 7 | 7 | 1/12 | 1-11 | 2-11 | 10 | 9 | -1 | 0.567537 | 0.201322 |
| 9 | 9 | 0/12 | 3-9 | 3-9 | 7 | 7 | 0 | 2.9025 | 0.449507 |
| 10 | 10 | 0/12 | 3-7 | 3-7 | 5 | 5 | 0 | 2.48838 | 0.555509 |
| 23 | 23 | 0/12 | 1-9 | 1-9 | 9 | 9 | 0 | -1.47684 | -0.163104 |

## Blocked Reasons

- Final-frame C++ wet/dry mask mismatch exceeds the 0.02 comparison threshold.
- At least one C++ constriction column differs from GeoClaw wet width by more than one lateral cell.
- At least one C++ constriction column differs from GeoClaw mean wet depth by more than 0.25 m.
- At least one C++ constriction column mass differs from GeoClaw beyond the diagnostic budget.

## Next Levers

- Fit wet-band span changes outside the narrowest throat columns before adding feature forcing.
- Retune dry-bank reconstruction so non-throat columns can follow GeoClaw bank expansion, recession, and row shifts.
- Recheck cross-section, slope, conservation, and Froude errors after the wet-mask spans agree.
- Rerun the Milestone 17 analytic guardrail and corrected-reference constriction comparison after the next solver change.
