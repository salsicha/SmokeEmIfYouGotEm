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
| `finite_volume_roe` | `roe_upper_edge_flux_magnitude_balance` | BLOCKED | field_linf, slope_linf, wet_mismatch_fraction, probe_linf, cross_section_linf | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |

## Threshold Checks

### finite_volume_roe

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 3.43854 | 0.25 | FAIL |
| `slope_linf` | 0.78465 | 0.25 | FAIL |
| `wet_mismatch_fraction` | 0.263889 | 0.02 | FAIL |
| `probe_linf` | 2.15656 | 0.25 | FAIL |
| `cross_section_linf` | 1.6623 | 0.25 | FAIL |
| `mass_drift_delta` | 0.0410125 | 0.05 | PASS |
| `energy_change_delta` | 0.102797 | 0.25 | PASS |
| `froude_delta` | 0.400383 | 0.5 | PASS |
| `feature_location_delta` | 3.60555 | 5 | PASS |
| `feature_strength_delta` | 0.785562 | 10 | PASS |

## Notes

- Use bounded final upper-edge flux-magnitude balance after shelf support fixed the immediate width/bank-row mismatch; feature forcing remains off.
- Do not promote: field, slope, mass, energy, and Froude improve, but wet-mask, probe, cross-section, field, and slope parity remain blocked.
