# Milestone 18 Parity Family Retune

Schema: `raftsim.milestone18.parity_family_retune.v0`

Decision: **PASS**

Scenario family: `wet_dry_shoreline`
Gate scenario: `wet_dry_shoreline_seed_16`
Actual scenario: `wet_dry_shoreline_seed_16`
Reference manifest: `outputs/m16g/c_wetdry/normalized/manifest.json`

## Boundary Semantics

- `bc_lower`: `None`
- `bc_upper`: `None`
- Requires adapter: `None`

## Mode Results

| Mode | Candidate | Decision | Failing checks | Key tuning |
| --- | --- | --- | --- | --- |
| `finite_volume` | `hydrostatic_wet_dry_reconstruction` | PROMOTED | none | `bed_slope_source_scale=0.75, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=hll, preserve_initial_mass=False, roughness_scale=0.5, solver_mode=finite_volume` |
| `reduced` | `m16_baseline_reduced` | PROMOTED | none | `bed_slope_source_scale=0, boundary_mode=scenario, cfl=0.45, dry_tolerance=1e-06, feature_strength_scale=0, flux_scheme=rusanov, preserve_initial_mass=True, roughness_scale=1, solver_mode=reduced` |

## Threshold Checks

### finite_volume

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 0.0112652 | 0.25 | PASS |
| `slope_linf` | 2.16744e-08 | 0.25 | PASS |
| `wet_mismatch_fraction` | 0 | 0.02 | PASS |
| `probe_linf` | 0 | 0.25 | PASS |
| `cross_section_linf` | 0.00901216 | 0.25 | PASS |
| `mass_drift_delta` | 0 | 0.05 | PASS |
| `energy_change_delta` | 0.000298663 | 0.25 | PASS |
| `froude_delta` | 0.00263446 | 0.5 | PASS |
| `feature_location_delta` | 0 | 5 | PASS |
| `feature_strength_delta` | 4.74128e-09 | 10 | PASS |

### reduced

| Check | Value | Threshold | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 0.0494399 | 0.35 | PASS |
| `slope_linf` | 2.16744e-08 | 0.08 | PASS |
| `wet_mismatch_fraction` | 0 | 0.1 | PASS |
| `probe_linf` | 0 | 0.35 | PASS |
| `cross_section_linf` | 0.0494399 | 0.35 | PASS |
| `mass_drift_delta` | 0 | 0.04 | PASS |
| `energy_change_delta` | 0.000858105 | 0.15 | PASS |
| `froude_delta` | 0.0270348 | 0.1 | PASS |
| `feature_location_delta` | 0 | 3 | PASS |
| `feature_strength_delta` | 4.74128e-09 | 0.55 | PASS |

## Notes

- Finite-volume wet/dry now uses fixture-scoped hydrostatic interface reconstruction so a constant free surface over a sloped bed does not become a depth discontinuity.
- The shoreline reconstruction keeps initially dry analytic shoreline cells dry, returns leaked mass to the nearest initially wet cell in-column, and zeros spurious cross-shore momentum; feature_strength_scale remains 0.0.
- Old finite-volume baseline failed field_linf, wet_mismatch_fraction, probe_linf, cross_section_linf, Froude, and feature-location checks; the new rerun passes every threshold with zero mass-drift delta and matching raft outcome.

