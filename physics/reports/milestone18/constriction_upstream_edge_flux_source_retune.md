# Milestone 18 Parity Family Retune

Schema: `raftsim.milestone18.parity_family_retune.v0`

Decision: **BLOCKED**

Scenario family: `constriction`
Gate scenario: `constriction_seed_16`
Actual scenario: `constriction_seed_16`
Reference manifest: `physics/outputs/m18cmp/c_constrict_upstream_edge_flux_source/finite_volume_roe/dual_solver_manifest.json`

## Boundary Semantics

- `bc_lower`: `None`
- `bc_upper`: `None`
- Requires adapter: `None`

## Mode Results

| Mode | Candidate | Decision | Failing checks | Key tuning |
| --- | --- | --- | --- | --- |
| `finite_volume_roe` | `Roe upstream-edge flux/source` | BLOCKED | field_linf, slope_linf, wet_mismatch_fraction, probe_linf, cross_section_linf, froude_delta | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |

## Threshold Checks

### finite_volume_roe

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 3.69942 | 0.25 | FAIL |
| `slope_linf` | 0.952462 | 0.25 | FAIL |
| `wet_mismatch_fraction` | 0.270833 | 0.02 | FAIL |
| `probe_linf` | 2.20322 | 0.25 | FAIL |
| `cross_section_linf` | 1.69192 | 0.25 | FAIL |
| `mass_drift_delta` | 0.0144205 | 0.05 | PASS |
| `energy_change_delta` | 0.016676 | 0.25 | PASS |
| `froude_delta` | 0.504034 | 0.5 | FAIL |
| `feature_location_delta` | 3.60555 | 5 | PASS |
| `feature_strength_delta` | 0.787911 | 10 | PASS |

## Notes

- Fixture-scoped upstream-edge flux/source treatment keeps feature forcing off, preconditions the inflow edge state, moves excess edge depth through lateral face flux, and applies a bounded momentum source. It is retained as diagnostic plumbing but not promoted: mass and energy remain inside threshold, but field, slope, wet-mask, probe, cross-section, and Froude checks still block full constriction parity.

