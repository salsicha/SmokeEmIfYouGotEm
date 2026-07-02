# Milestone 18 Parity Family Retune

Schema: `raftsim.milestone18.parity_family_retune.v0`

Decision: **BLOCKED**

Scenario family: `constriction`
Gate scenario: `constriction_seed_16`
Actual scenario: `constriction_seed_16`
Reference manifest: `physics/outputs/m18g/c_constrict_corrected/constriction_seed_16/manifest.json`

## Boundary Semantics

- `bc_lower`: `['user', 'wall']`
- `bc_upper`: `['extrap', 'wall']`
- Requires adapter: `True`

## Mode Results

| Mode | Candidate | Decision | Failing checks | Key tuning |
| --- | --- | --- | --- | --- |
| `finite_volume_roe` | `boundary_column_depth_support` | BLOCKED | field_linf, slope_linf, wet_mismatch_fraction, probe_linf | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |

## Threshold Checks

### finite_volume_roe

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 3.22762 | 0.25 | FAIL |
| `slope_linf` | 0.722705 | 0.25 | FAIL |
| `wet_mismatch_fraction` | 0.256944 | 0.02 | FAIL |
| `probe_linf` | 0.42056 | 0.25 | FAIL |
| `cross_section_linf` | 0.197768 | 0.25 | PASS |
| `mass_drift_delta` | 0.00909007 | 0.05 | PASS |
| `energy_change_delta` | 0.0922814 | 0.25 | PASS |
| `froude_delta` | 0.466646 | 0.5 | PASS |
| `feature_location_delta` | 3.60555 | 5 | PASS |
| `feature_strength_delta` | 0.75628 | 10 | PASS |

## Notes

- Finite-volume Roe keeps feature forcing off while retuning the existing boundary-sourced inflow-column support to fill the lower relaxed wet-band rows toward the GeoClaw boundary-column depth profile; the manifest records the stronger support rate, depth cap, shelf/lower/interior depth scales, and shelf speed fraction.
- The candidate is not promoted: mass improves from 0.047516 to 0.0090901 and probe improves from 0.472432 to 0.420560, while the lower-edge column 0 q delta improves from -1.34647 to -1.19303 and the depth blocker clears, but field/slope regress to 3.22762/0.722705 and the refreshed queue moves to upper-edge column 1 rows 8-9 with q delta 1.13760 and balance delta 1.63225.

