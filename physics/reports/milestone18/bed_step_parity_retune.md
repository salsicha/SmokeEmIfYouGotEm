# Milestone 18 Parity Family Retune

Schema: `raftsim.milestone18.parity_family_retune.v0`

Decision: **PARTIAL_PROMOTION**

Scenario family: `bed_step`
Gate scenario: `bed_step`
Actual scenario: `bed_step_seed_16`
Reference manifest: `outputs/m16g/c_step/normalized/manifest.json`

## Boundary Semantics

- `bc_lower`: `None`
- `bc_upper`: `None`
- Requires adapter: `None`

## Mode Results

| Mode | Candidate | Decision | Failing checks | Key tuning |
| --- | --- | --- | --- | --- |
| `finite_volume` | `finite_volume_augmented_topography_bed_step` | PROMOTED | none | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=hll, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |
| `reduced` | `reduced_baseline_feature0` | BLOCKED | field_linf, slope_linf, probe_linf, mass_drift_delta, energy_change_delta | `bed_slope_source_scale=0, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=rusanov, preserve_initial_mass=True, roughness_scale=1, solver_mode=reduced` |

## Threshold Checks

### finite_volume

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 0.295881 | 0.35 | PASS |
| `slope_linf` | 0.0797631 | 0.08 | PASS |
| `wet_mismatch_fraction` | 0 | 0.1 | PASS |
| `probe_linf` | 0.256897 | 0.35 | PASS |
| `cross_section_linf` | 0.100698 | 0.35 | PASS |
| `mass_drift_delta` | 0.0056486 | 0.04 | PASS |
| `energy_change_delta` | 0.0350211 | 0.15 | PASS |
| `froude_delta` | 0.0336858 | 0.1 | PASS |
| `feature_location_delta` | 0 | 3 | PASS |
| `feature_strength_delta` | 0.156548 | 0.55 | PASS |

### reduced

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 0.610705 | 0.35 | FAIL |
| `slope_linf` | 0.104595 | 0.08 | FAIL |
| `wet_mismatch_fraction` | 0 | 0.1 | PASS |
| `probe_linf` | 0.392414 | 0.35 | FAIL |
| `cross_section_linf` | 0.269168 | 0.35 | PASS |
| `mass_drift_delta` | 0.0948885 | 0.04 | FAIL |
| `energy_change_delta` | 0.16485 | 0.15 | FAIL |
| `froude_delta` | 0.00820177 | 0.1 | PASS |
| `feature_location_delta` | 2 | 3 | PASS |
| `feature_strength_delta` | 0.0141865 | 0.55 | PASS |

## Notes

- Finite-volume bed-step parity is promoted with feature forcing off: the augmented topography source distribution passes field, slope, probe, cross-section, wet-mask, mass, energy, Froude, and feature checks.
- The augmented topography path remains scoped to fixture_kind=bed_step so boulder, drop, wet/dry, and cascading acceptance lanes keep their own validation gates.
- Reduced mode remains blocked on field_linf, slope_linf, probe_linf, mass_drift_delta, and energy_change_delta; Milestone 18 scopes it to diagnostic/smoke-only bed-step evidence until a separate reduced-dynamics redesign is justified.
