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
| `finite_volume_roe` | `lower_edge_transition_source_depth` | BLOCKED | field_linf, slope_linf, wet_mismatch_fraction, probe_linf | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |

## Threshold Checks

### finite_volume_roe

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 3.25397 | 0.25 | FAIL |
| `slope_linf` | 0.703749 | 0.25 | FAIL |
| `wet_mismatch_fraction` | 0.256944 | 0.02 | FAIL |
| `probe_linf` | 0.381449 | 0.25 | FAIL |
| `cross_section_linf` | 0.198026 | 0.25 | PASS |
| `mass_drift_delta` | 0.00138704 | 0.05 | PASS |
| `energy_change_delta` | 0.0711608 | 0.25 | PASS |
| `froude_delta` | 0.455471 | 0.5 | PASS |
| `feature_location_delta` | 3.60555 | 5 | PASS |
| `feature_strength_delta` | 0.783294 | 10 | PASS |

## Notes

- Finite-volume Roe keeps feature forcing off and adds a bounded transition-weighted lower-edge source/depth balance after the lower-edge flux-magnitude pass.
- The same pass shapes the upper donor edge velocity after depth transfer so the upper face remains a shallow/fast GeoClaw-compared guardrail.
