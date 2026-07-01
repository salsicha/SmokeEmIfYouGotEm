# Milestone 18 Parity Family Retune

Schema: `raftsim.milestone18.parity_family_retune.v0`

Decision: **BLOCKED**

Scenario family: `constriction`
Gate scenario: `constriction_seed_16`
Actual scenario: `constriction_seed_16`
Reference manifest: `physics/outputs/m18cmp/c_constrict_localized_circulation/finite_volume_roe/dual_solver_manifest.json`

## Boundary Semantics

- `bc_lower`: `None`
- `bc_upper`: `None`
- Requires adapter: `None`

## Mode Results

| Mode | Candidate | Decision | Failing checks | Key tuning |
| --- | --- | --- | --- | --- |
| `finite_volume_roe` | `Roe localized throat/recovery circulation` | BLOCKED | field_linf, slope_linf, wet_mismatch_fraction, probe_linf, cross_section_linf, froude_delta | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |

## Threshold Checks

### finite_volume_roe

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 3.69943 | 0.25 | FAIL |
| `slope_linf` | 0.952377 | 0.25 | FAIL |
| `wet_mismatch_fraction` | 0.270833 | 0.02 | FAIL |
| `probe_linf` | 2.15656 | 0.25 | FAIL |
| `cross_section_linf` | 1.6623 | 0.25 | FAIL |
| `mass_drift_delta` | 0.0142295 | 0.05 | PASS |
| `energy_change_delta` | 0.0212464 | 0.25 | PASS |
| `froude_delta` | 0.504034 | 0.5 | FAIL |
| `feature_location_delta` | 3.60555 | 5 | PASS |
| `feature_strength_delta` | 0.785574 | 10 | PASS |

## Notes

- Fixture-scoped localized circulation keeps feature forcing off and adds a bounded, velocity-only, mass-preserving final pass over the center throat and near-recovery wet band. The upstream component was tested and disabled because it regressed the Froude guard; the retained pass improves sampled throat/recovery cross-stream signs while leaving the Froude near-miss unchanged. It is retained as diagnostic plumbing, not promoted, because upstream field/slope/wet-mask and probe/cross-section blockers remain.

