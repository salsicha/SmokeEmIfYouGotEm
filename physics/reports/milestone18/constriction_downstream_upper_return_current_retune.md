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
| `finite_volume_roe` | `downstream_upper_return_current_late` | BLOCKED | field_linf, slope_linf, wet_mismatch_fraction, probe_linf | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |

## Threshold Checks

### finite_volume_roe

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 3.1507 | 0.25 | FAIL |
| `slope_linf` | 0.719087 | 0.25 | FAIL |
| `wet_mismatch_fraction` | 0.256944 | 0.02 | FAIL |
| `probe_linf` | 0.463334 | 0.25 | FAIL |
| `cross_section_linf` | 0.197127 | 0.25 | PASS |
| `mass_drift_delta` | 0.0473101 | 0.05 | PASS |
| `energy_change_delta` | 0.172191 | 0.25 | PASS |
| `froude_delta` | 0.431294 | 0.5 | PASS |
| `feature_location_delta` | 3.60555 | 5 | PASS |
| `feature_strength_delta` | 0.635308 | 10 | PASS |

## Notes

- Finite-volume Roe keeps feature forcing off and adds a manifest-recorded, bounded, velocity-only late downstream upper-edge return-current balance in widened downstream constriction columns.
- Field Linf improves versus the upstream centerline-balance checkpoint from 3.20012 to 3.15070 and hu Linf improves from 3.20012 to 3.15070 while cross-section, mass, energy, Froude, and feature checks remain passing; field, slope, wet-mask, and probe still block promotion.

