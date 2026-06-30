# Milestone 18 Parity Family Retune

Schema: `raftsim.milestone18.parity_family_retune.v0`

Decision: **PARTIAL_PROMOTION**

Scenario family: `uniform_channel`
Gate scenario: `uniform_channel`
Actual scenario: `uniform_channel_seed_16`
Reference manifest: `/private/tmp/m18_uniform_corrected_after_cpp/geoclaw_export/uniform_channel_seed_16/normalized/manifest.json`

## Boundary Semantics

- `bc_lower`: `['user', 'wall']`
- `bc_upper`: `['extrap', 'wall']`
- Requires adapter: `True`

## Mode Results

| Mode | Candidate | Decision | Failing checks | Key tuning |
| --- | --- | --- | --- | --- |
| `finite_volume` | `hll_c0p45_roughness0p5_bed0p75_feature0` | PROMOTED | none | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=hll, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |
| `reduced` | `reduced_baseline_feature0` | BLOCKED | field_linf, slope_linf, probe_linf, cross_section_linf, mass_drift_delta | `bed_slope_source_scale=0, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=rusanov, preserve_initial_mass=True, roughness_scale=1, solver_mode=reduced` |

## Threshold Checks

### finite_volume

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 0.142587 | 0.15 | PASS |
| `slope_linf` | 0.0124597 | 0.035 | PASS |
| `wet_mismatch_fraction` | 0 | 0.04 | PASS |
| `probe_linf` | 0.131428 | 0.15 | PASS |
| `cross_section_linf` | 0.131428 | 0.15 | PASS |
| `mass_drift_delta` | 0.00425207 | 0.02 | PASS |
| `energy_change_delta` | 0.0208375 | 0.08 | PASS |
| `froude_delta` | 0.0331442 | 0.04 | PASS |
| `feature_location_delta` | 0 | 1.25 | PASS |
| `feature_strength_delta` | 0 | 0.25 | PASS |

### reduced

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 0.284129 | 0.15 | FAIL |
| `slope_linf` | 0.0933009 | 0.035 | FAIL |
| `wet_mismatch_fraction` | 0 | 0.04 | PASS |
| `probe_linf` | 0.245022 | 0.15 | FAIL |
| `cross_section_linf` | 0.183799 | 0.15 | FAIL |
| `mass_drift_delta` | 0.0244759 | 0.02 | FAIL |
| `energy_change_delta` | 0.0358936 | 0.08 | PASS |
| `froude_delta` | 0.02572 | 0.04 | PASS |
| `feature_location_delta` | 0 | 1.25 | PASS |
| `feature_strength_delta` | 0 | 0.25 | PASS |

## Notes

- Corrected GeoClaw reference uses generated user-boundary bc2amr.f90 for the authored west inflow.
- Finite-volume mode is promoted for the uniform-channel family; reduced mode remains blocked and should not be used as the strict parity lane for this family until its reduced dynamics are redesigned or scoped down.

