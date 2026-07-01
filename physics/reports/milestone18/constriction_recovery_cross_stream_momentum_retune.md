# Milestone 18 Parity Family Retune

Schema: `raftsim.milestone18.parity_family_retune.v0`

Decision: **BLOCKED**

Scenario family: `constriction`
Gate scenario: `constriction_seed_16`
Actual scenario: `constriction_seed_16`
Reference manifest: `physics/outputs/m18cmp/c_constrict_recovery_cross_stream_momentum/finite_volume_roe/dual_solver_manifest.json`

## Boundary Semantics

- `bc_lower`: `None`
- `bc_upper`: `None`
- Requires adapter: `None`

## Mode Results

| Mode | Candidate | Decision | Failing checks | Key tuning |
| --- | --- | --- | --- | --- |
| `finite_volume_roe` | `Roe recovery cross-stream momentum source` | BLOCKED | field_linf, slope_linf, wet_mismatch_fraction, probe_linf, cross_section_linf, froude_delta | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |

## Threshold Checks

### finite_volume_roe

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 3.69943 | 0.25 | FAIL |
| `slope_linf` | 0.952384 | 0.25 | FAIL |
| `wet_mismatch_fraction` | 0.270833 | 0.02 | FAIL |
| `probe_linf` | 2.20322 | 0.25 | FAIL |
| `cross_section_linf` | 1.69192 | 0.25 | FAIL |
| `mass_drift_delta` | 0.0142722 | 0.05 | PASS |
| `energy_change_delta` | 0.0203663 | 0.25 | PASS |
| `froude_delta` | 0.504034 | 0.5 | FAIL |
| `feature_location_delta` | 3.60555 | 5 | PASS |
| `feature_strength_delta` | 0.78572 | 10 | PASS |

## Notes

- Fixture-scoped recovery-only cross-stream momentum source keeps feature forcing off and adds a bounded, mass-preserving finite-volume momentum source in recovery columns. It is retained as a partial diagnostic improvement, not promoted: recovery center v moves toward the GeoClaw sign while mass, energy, throat shape, and the near-threshold Froude summary stay clean, but upstream/throat field, probe, cross-section, wet-mask, and slope blockers remain.

