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
| `finite_volume_roe_asymmetric_envelope` | `roe_dry_bank_mask_plus_throat_momentum_plus_asymmetric_wet_band_envelope` | BLOCKED | field_linf, slope_linf, wet_mismatch_fraction, probe_linf, cross_section_linf, mass_drift_delta, energy_change_delta, froude_delta | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |

## Threshold Checks

### finite_volume_roe_asymmetric_envelope

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 3.98298 | 0.25 | FAIL |
| `slope_linf` | 1.37558 | 0.25 | FAIL |
| `wet_mismatch_fraction` | 0.315972 | 0.02 | FAIL |
| `probe_linf` | 2.60214 | 0.25 | FAIL |
| `cross_section_linf` | 2.20827 | 0.25 | FAIL |
| `mass_drift_delta` | 0.15954 | 0.05 | FAIL |
| `energy_change_delta` | 0.296172 | 0.25 | FAIL |
| `froude_delta` | 1.23517 | 0.5 | FAIL |
| `feature_location_delta` | 3.60555 | 5 | PASS |
| `feature_strength_delta` | 0.33147 | 10 | PASS |

## Notes

- Feature forcing stayed off; this attempt replaces symmetric center-of-mass span shaping with an authored-length, initial-flow-classified wet-band envelope that expands upstream approach bands, recedes downstream constriction bands, and keeps the center throat strict.

