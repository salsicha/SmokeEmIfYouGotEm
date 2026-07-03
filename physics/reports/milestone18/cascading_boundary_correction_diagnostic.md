# Milestone 18 Cascading Boundary Correction Diagnostic

Schema: `raftsim.milestone18.cascading_boundary_correction.v0`

Decision: **BLOCKED**

Stale comparison report: `physics/reports/milestone16/geoclaw_cpp_comparisons.json`
Corrected threshold reports: `physics/outputs/m18cmp/cascading_low_corrected_boundary/finite_volume_hll/threshold_evaluation.json, physics/outputs/m18cmp/cascading_med_corrected_boundary/finite_volume_hll/threshold_evaluation.json, physics/outputs/m18cmp/cascading_igh_corrected_boundary/finite_volume_hll/threshold_evaluation.json`

## Summary

- Boundary-corrected flows: `3` of `3`
- Feature-forcing-off flows: `3` of `3`
- Threshold-passing flows: `0` of `3`
- Failing checks: `cross_section_linf=3, energy_change_delta=3, feature_location_delta=3, feature_strength_delta=3, field_linf=3, froude_delta=3, mass_drift_delta=3, probe_linf=3, slope_linf=3`

## Flow Results

| Flow | Gate scenario | Boundary | Feature forcing | Threshold | Corrected failures | Key stale -> corrected deltas |
| --- | --- | --- | ---: | --- | --- | --- |
| `high_runnable` | `south_fork_cascading_high_runnable` | corrected | `0` | BLOCKED | `field_linf`, `slope_linf`, `probe_linf`, `cross_section_linf`, `mass_drift_delta`, `energy_change_delta`, `froude_delta`, `feature_location_delta`, `feature_strength_delta` | field_linf 51.5977 -> 22.9041; wet_mismatch_fraction 0.304464 -> 0.0642857; mass_drift_delta 1.81253 -> 0.236037; energy_change_delta 4.17176 -> 1.35458; froude_delta 0.384427 -> 1.26515; feature_strength_delta 4.34964 -> 1.89475 |
| `low_runnable` | `south_fork_cascading_low_runnable` | corrected | `0` | BLOCKED | `field_linf`, `slope_linf`, `probe_linf`, `cross_section_linf`, `mass_drift_delta`, `energy_change_delta`, `froude_delta`, `feature_location_delta`, `feature_strength_delta` | field_linf 39.6354 -> 17.8908; wet_mismatch_fraction 0.327679 -> 0.0633929; mass_drift_delta 1.91183 -> 0.306369; energy_change_delta 3.20291 -> 1.17975; froude_delta 0.53995 -> 1.94118; feature_strength_delta 4.94943 -> 1.37504 |
| `median_runnable` | `south_fork_cascading_median_runnable` | corrected | `0` | BLOCKED | `field_linf`, `slope_linf`, `probe_linf`, `cross_section_linf`, `mass_drift_delta`, `energy_change_delta`, `froude_delta`, `feature_location_delta`, `feature_strength_delta` | field_linf 48.9428 -> 20.0395; wet_mismatch_fraction 0.310714 -> 0.0580357; mass_drift_delta 1.87646 -> 0.336047; energy_change_delta 3.42177 -> 1.46741; froude_delta 0.278228 -> 1.6299; feature_strength_delta 4.12386 -> 1.73696 |

## Blocked Reasons

- south_fork_cascading_high_runnable still fails corrected-boundary thresholds: field_linf, slope_linf, probe_linf, cross_section_linf, mass_drift_delta, energy_change_delta, froude_delta, feature_location_delta, feature_strength_delta.
- south_fork_cascading_low_runnable still fails corrected-boundary thresholds: field_linf, slope_linf, probe_linf, cross_section_linf, mass_drift_delta, energy_change_delta, froude_delta, feature_location_delta, feature_strength_delta.
- south_fork_cascading_median_runnable still fails corrected-boundary thresholds: field_linf, slope_linf, probe_linf, cross_section_linf, mass_drift_delta, energy_change_delta, froude_delta, feature_location_delta, feature_strength_delta.

## Next Levers

- Use the corrected GeoClaw user-boundary manifests as the South Fork cascading reference; do not retune against stale extrapolated Milestone 16 outputs.
- Use stitched whole-window cascading comparisons for acceptance; reach-local seam passes already exist and cannot hide water-field errors.
- Keep `feature_strength_scale=0` until conservation, Froude, field, probe, and cross-section parity pass against GeoClaw.
- Address whole-window mass/energy drift before tuning visual feature strength or raft outcomes.
- Retune the cascading drop/tailwater water-shape response from the corrected field, probe, and cross-section failures.
- Preserve transcritical hydraulic-control behavior across drops and recovery pools while reducing Froude deltas.
