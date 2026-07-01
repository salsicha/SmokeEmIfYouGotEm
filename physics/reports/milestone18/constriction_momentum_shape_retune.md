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
| `finite_volume_roe_momentum_shape` | `roe_dry_bank_mask_plus_throat_momentum_reconstruction` | BLOCKED | field_linf, slope_linf, wet_mismatch_fraction, probe_linf, cross_section_linf, mass_drift_delta, energy_change_delta, froude_delta | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |

## Threshold Checks

### finite_volume_roe_momentum_shape

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 3.31114 | 0.25 | FAIL |
| `slope_linf` | 0.819008 | 0.25 | FAIL |
| `wet_mismatch_fraction` | 0.402778 | 0.02 | FAIL |
| `probe_linf` | 1.19647 | 0.25 | FAIL |
| `cross_section_linf` | 2.20827 | 0.25 | FAIL |
| `mass_drift_delta` | 0.141796 | 0.05 | FAIL |
| `energy_change_delta` | 0.6197 | 0.25 | FAIL |
| `froude_delta` | 1.93 | 0.5 | FAIL |
| `feature_location_delta` | 0 | 5 | PASS |
| `feature_strength_delta` | 1.15783 | 10 | PASS |

## Notes

- Feature forcing stayed off; this attempt keeps the dry-bank mask and adds geometry-scoped momentum reconstruction only at the narrowest authored throat columns, restoring authored downstream speed and bounded edge convergence velocity.
