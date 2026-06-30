# Milestone 18 Parity Family Retune

Schema: `raftsim.milestone18.parity_family_retune.v0`

Decision: **BLOCKED**

Scenario family: `constriction`
Gate scenario: `constriction`
Actual scenario: `constriction_seed_16`
Reference manifest: `outputs/m18g/c_constrict_corrected/constriction_seed_16/normalized/manifest.json`

## Boundary Semantics

- `bc_lower`: `['user', 'wall']`
- `bc_upper`: `['extrap', 'wall']`
- Requires adapter: `True`

## Mode Results

| Mode | Candidate | Decision | Failing checks | Key tuning |
| --- | --- | --- | --- | --- |
| `finite_volume_roe_baseline` | `finite_volume_roe_corrected_boundary_feature0` | BLOCKED | field_linf, slope_linf, probe_linf, cross_section_linf, mass_drift_delta, froude_delta, feature_strength_delta | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |
| `finite_volume_roe_source15` | `finite_volume_roe_throat_source_scale_1_5_feature0` | BLOCKED | field_linf, slope_linf, probe_linf, cross_section_linf, froude_delta, feature_strength_delta | `bed_slope_source_scale=1.5, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |

## Threshold Checks

### finite_volume_roe_baseline

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 3.65866 | 0.35 | FAIL |
| `slope_linf` | 0.641343 | 0.08 | FAIL |
| `wet_mismatch_fraction` | 0.0277778 | 0.1 | PASS |
| `probe_linf` | 0.829959 | 0.35 | FAIL |
| `cross_section_linf` | 2.13506 | 0.35 | FAIL |
| `mass_drift_delta` | 0.0936647 | 0.04 | FAIL |
| `energy_change_delta` | 0.131454 | 0.15 | PASS |
| `froude_delta` | 0.5628 | 0.1 | FAIL |
| `feature_location_delta` | 0 | 3 | PASS |
| `feature_strength_delta` | 1.76149 | 0.55 | FAIL |

### finite_volume_roe_source15

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 5.08737 | 0.35 | FAIL |
| `slope_linf` | 1.10944 | 0.08 | FAIL |
| `wet_mismatch_fraction` | 0.0277778 | 0.1 | PASS |
| `probe_linf` | 1.22252 | 0.35 | FAIL |
| `cross_section_linf` | 3.26552 | 0.35 | FAIL |
| `mass_drift_delta` | 0.0307949 | 0.04 | PASS |
| `energy_change_delta` | 0.0086376 | 0.15 | PASS |
| `froude_delta` | 0.878536 | 0.1 | FAIL |
| `feature_location_delta` | 0 | 3 | PASS |
| `feature_strength_delta` | 1.60397 | 0.55 | FAIL |

## Notes

- Constriction source-treatment sweep keeps feature forcing off and raises finite-volume bed_slope_source_scale from 0.75 to 1.5 for the Roe candidate.
- The stronger throat source treatment brings mass_drift_delta and energy_change_delta inside Milestone 16 constriction thresholds, but field_linf, slope_linf, probe_linf, cross_section_linf, froude_delta, and feature_strength_delta still fail.
- Do not promote this lane yet: the remaining error is water-shape/throat reconstruction, so the next implementation step needs geometry-aware reconstruction rather than more scalar source scaling.

