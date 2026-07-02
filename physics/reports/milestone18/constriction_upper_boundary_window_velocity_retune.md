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
| `finite_volume_roe` | `upper_boundary_window_velocity` | BLOCKED | field_linf, slope_linf, wet_mismatch_fraction, probe_linf | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |

## Threshold Checks

### finite_volume_roe

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 3.27443 | 0.25 | FAIL |
| `slope_linf` | 0.704537 | 0.25 | FAIL |
| `wet_mismatch_fraction` | 0.256944 | 0.02 | FAIL |
| `probe_linf` | 0.384079 | 0.25 | FAIL |
| `cross_section_linf` | 0.198152 | 0.25 | PASS |
| `mass_drift_delta` | 0.000827123 | 0.05 | PASS |
| `energy_change_delta` | 0.0649788 | 0.25 | PASS |
| `froude_delta` | 0.451696 | 0.5 | PASS |
| `feature_location_delta` | 3.60555 | 5 | PASS |
| `feature_strength_delta` | 0.79105 | 10 | PASS |

## Notes

- Finite-volume Roe retunes the retained upstream boundary upper-edge velocity window with feature forcing off and no additional depth transfer.
- A bounded upper shelf depth-transfer trial was rejected before retention because it failed the Froude guardrail.
