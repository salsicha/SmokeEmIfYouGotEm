# Milestone 18 Constriction Throat Shape Diagnostic

Schema: `raftsim.milestone18.constriction_throat_shape.v0`

Decision: **PASS**

Scenario: `constriction_seed_16`
Dual solver manifest: `outputs/m18cmp/c_constrict_upstream_recovery_distribution/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_constrict_upstream_recovery_distribution/finite_volume_roe/scenario/constriction_seed_16`
Throat column: `12`
Center row: `6`
Wet-depth threshold: `0.15` m

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

## Profiles

| Profile | Wet cells | Wet width m | Center depth m | Max depth m | Mean wet depth m | Column mass m3 | Center u m/s | Max abs v m/s | Mean abs v m/s | Center Froude |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| authored_initial | 4 | 4 | 1.25 | 1.25 | 1.25 | 5 | 2.88417 | 0 | 0 | 0.823628 |
| geoclaw_final | 4 | 4 | 1.24839 | 1.47238 | 1.12546 | 4.86734 | 3.16583 | 1.18055 | 0.405891 | 0.905059 |
| cpp_final | 4 | 4 | 1.25 | 1.25 | 1.25 | 5 | 2.88417 | 1.18251 | 0.591254 | 0.890166 |

## Deltas

| Delta | Wet width m | Center depth m | Max depth m | Mean wet depth m | Column mass m3 | Center u m/s | Max abs v m/s | Mean abs v m/s | Center Froude |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| C++ minus GeoClaw | 0 | 0.00160956 | -0.222384 | 0.12454 | 0.132664 | -0.281658 | 0.00196364 | 0.185364 | -0.0148934 |
| Authored initial minus GeoClaw | 0 | 0.00160956 | -0.222384 | 0.12454 | 0.132664 | -0.281658 | -1.18055 | -0.405891 | -0.0814316 |

## Next Levers

- Fit constriction throat width/depth mapping from GeoClaw profile evidence before adding feature forcing.
- Add a geometry-aware throat reconstruction that preserves mass while matching wet width and centerline depth.
- Rerun the corrected-reference constriction GeoClaw/C++ comparison and Milestone 17 guardrail after changes.
