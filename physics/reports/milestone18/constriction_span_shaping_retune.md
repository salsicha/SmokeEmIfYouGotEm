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
| `finite_volume_roe_span_shaping` | `roe_dry_bank_mask_plus_throat_momentum_plus_non_throat_span_shaping` | BLOCKED | field_linf, slope_linf, wet_mismatch_fraction, probe_linf, cross_section_linf, mass_drift_delta, froude_delta | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |

## Threshold Checks

### finite_volume_roe_span_shaping

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 4.19584 | 0.25 | FAIL |
| `slope_linf` | 1.07971 | 0.25 | FAIL |
| `wet_mismatch_fraction` | 0.159722 | 0.02 | FAIL |
| `probe_linf` | 2.75977 | 0.25 | FAIL |
| `cross_section_linf` | 2.37727 | 0.25 | FAIL |
| `mass_drift_delta` | 0.14879 | 0.05 | FAIL |
| `energy_change_delta` | 0.00230886 | 0.25 | PASS |
| `froude_delta` | 0.61292 | 0.5 | FAIL |
| `feature_location_delta` | 3.60555 | 5 | PASS |
| `feature_strength_delta` | 0.389541 | 10 | PASS |

## Notes

- Feature forcing stayed off; this attempt keeps all narrowest throat columns on the existing strict reconstruction while mass-balancing wider non-throat wet-band relaxation windows, preserving their non-dry support count, and shifting each retained span by the current column center of mass.

