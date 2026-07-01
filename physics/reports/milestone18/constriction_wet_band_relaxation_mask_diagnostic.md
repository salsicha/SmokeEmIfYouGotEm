# Milestone 18 Constriction Mask Alignment Diagnostic

Schema: `raftsim.milestone18.constriction_mask_alignment.v0`

Decision: **BLOCKED**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_wet_band_relaxation/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_wet_band_relaxation/finite_volume_roe/scenario/constriction_seed_16`
Wet-depth threshold: `0.15` m

## Summary

- Domain wet-mask mismatch: `34` cells (`0.118056` fraction)
- Max column wet-mask mismatch fraction: `0.25`
- Max wet-width delta: `3` m
- Max bank-row delta: `2` rows
- Max mean wet-depth delta: `0.509843` m
- Max column-mass delta: `4.5064` m3

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
| 15 | 15 | 3/12 | 4-8 | 2-9 | 5 | 8 | 3 | 1.02052 | -0.320277 |
| 0 | 0 | 2/12 | 0-11 | 1-10 | 12 | 10 | -2 | -4.5064 | -0.208478 |
| 7 | 7 | 2/12 | 1-11 | 2-9 | 10 | 8 | -2 | -4.07198 | -0.19614 |
| 1 | 1 | 2/12 | 0-11 | 1-10 | 12 | 10 | -2 | -2.33765 | -0.0245248 |
| 2 | 2 | 2/12 | 0-11 | 1-10 | 12 | 10 | -2 | -2.25197 | -0.0153643 |
| 6 | 6 | 2/12 | 1-11 | 1-10 | 10 | 10 | 0 | -4.33237 | -0.429323 |
| 11 | 11 | 2/12 | 3-6 | 4-7 | 4 | 4 | 0 | -1.31812 | -0.228707 |
| 12 | 12 | 2/12 | 3-6 | 4-7 | 4 | 4 | 0 | -0.771293 | -0.101449 |

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
