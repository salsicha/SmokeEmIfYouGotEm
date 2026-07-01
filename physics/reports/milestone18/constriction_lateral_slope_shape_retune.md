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
| `finite_volume_roe_lateral_slope_shape` | `roe_lateral_slope_shape` | BLOCKED | field_linf, slope_linf, wet_mismatch_fraction, probe_linf, cross_section_linf, froude_delta | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |

## Threshold Checks

### finite_volume_roe_lateral_slope_shape

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 3.69455 | 0.25 | FAIL |
| `slope_linf` | 0.855161 | 0.25 | FAIL |
| `wet_mismatch_fraction` | 0.270833 | 0.02 | FAIL |
| `probe_linf` | 2.25322 | 0.25 | FAIL |
| `cross_section_linf` | 1.73192 | 0.25 | FAIL |
| `mass_drift_delta` | 0.0127905 | 0.05 | PASS |
| `energy_change_delta` | 0.159078 | 0.25 | PASS |
| `froude_delta` | 0.504034 | 0.5 | FAIL |
| `feature_location_delta` | 3.60555 | 5 | PASS |
| `feature_strength_delta` | 0.779907 | 10 | PASS |

## Notes

- Feature forcing stayed off; this fixture-scoped pass adds mass-conservative dry-bank depth caps, side-specific shallow-fringe targets, and bounded bank-side lateral velocity/slope shaping. It improves field, slope, wet-mask, mass, and energy errors versus the flux/mass/Froude attempt, but remains blocked by field/probe/cross-section errors and a near-threshold Froude regression.

