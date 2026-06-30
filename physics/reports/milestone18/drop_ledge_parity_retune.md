# Milestone 18 Parity Family Retune

Schema: `raftsim.milestone18.parity_family_retune.v0`

Decision: **BLOCKED**

Scenario family: `drop_ledge_tailwater`
Gate scenario: `drop_ledge`
Actual scenario: `drop_ledge_seed_16`
Reference manifest: `outputs/m18g/c_drop_corrected/drop_ledge_seed_16/normalized/manifest.json`

## Boundary Semantics

- `bc_lower`: `['user', 'wall']`
- `bc_upper`: `['extrap', 'wall']`
- Requires adapter: `True`

## Mode Results

| Mode | Candidate | Decision | Failing checks | Key tuning |
| --- | --- | --- | --- | --- |
| `finite_volume_hll` | `finite_volume_hll_corrected_boundary_feature0` | BLOCKED | field_linf, probe_linf | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=hll, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |
| `finite_volume_roe` | `finite_volume_roe_corrected_boundary_feature0` | BLOCKED | field_linf, probe_linf | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=roe, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |
| `reduced` | `reduced_corrected_boundary_feature0` | BLOCKED | field_linf, probe_linf, cross_section_linf, mass_drift_delta | `bed_slope_source_scale=0, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=rusanov, preserve_initial_mass=True, roughness_scale=1, solver_mode=reduced` |

## Threshold Checks

### finite_volume_hll

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 0.833169 | 0.25 | FAIL |
| `slope_linf` | 0.116126 | 0.25 | PASS |
| `wet_mismatch_fraction` | 0 | 0.02 | PASS |
| `probe_linf` | 0.421073 | 0.25 | FAIL |
| `cross_section_linf` | 0.177578 | 0.25 | PASS |
| `mass_drift_delta` | 0.0237546 | 0.05 | PASS |
| `energy_change_delta` | 0.0132272 | 0.25 | PASS |
| `froude_delta` | 0.362509 | 0.5 | PASS |
| `feature_location_delta` | 1 | 5 | PASS |
| `feature_strength_delta` | 0.369264 | 10 | PASS |

### finite_volume_roe

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 0.830342 | 0.25 | FAIL |
| `slope_linf` | 0.114126 | 0.25 | PASS |
| `wet_mismatch_fraction` | 0 | 0.02 | PASS |
| `probe_linf` | 0.41761 | 0.25 | FAIL |
| `cross_section_linf` | 0.185418 | 0.25 | PASS |
| `mass_drift_delta` | 0.0235848 | 0.05 | PASS |
| `energy_change_delta` | 0.0135054 | 0.25 | PASS |
| `froude_delta` | 0.360854 | 0.5 | PASS |
| `feature_location_delta` | 1 | 5 | PASS |
| `feature_strength_delta` | 0.367689 | 10 | PASS |

### reduced

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 1.07214 | 0.25 | FAIL |
| `slope_linf` | 0.170105 | 0.25 | PASS |
| `wet_mismatch_fraction` | 0 | 0.02 | PASS |
| `probe_linf` | 0.497429 | 0.25 | FAIL |
| `cross_section_linf` | 0.484536 | 0.25 | FAIL |
| `mass_drift_delta` | 0.145542 | 0.05 | FAIL |
| `energy_change_delta` | 0.229712 | 0.25 | PASS |
| `froude_delta` | 0.33454 | 0.5 | PASS |
| `feature_location_delta` | 2.23607 | 5 | PASS |
| `feature_strength_delta` | 0.180085 | 10 | PASS |

## Notes

- Corrected drop-ledge GeoClaw reference now records west user-boundary inflow via bc2amr.f90 instead of the stale west extrap boundary in the Milestone 16 snapshot.
- No drop-ledge lane is promoted: finite-volume HLL and Roe pass slope, wet-mask, cross-section, mass, energy, Froude, and feature checks with feature forcing off, but field_linf and probe_linf remain outside the frozen thresholds.
- Next retune lever is drop/ledge water-shape reconstruction around the hydraulic control and downstream recovery, not feature forcing or scalar conservation tuning.

