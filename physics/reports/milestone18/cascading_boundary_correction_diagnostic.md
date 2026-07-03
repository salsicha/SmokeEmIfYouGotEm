# Milestone 18 Cascading Boundary Correction Diagnostic

Schema: `raftsim.milestone18.cascading_boundary_correction.v0`

Decision: **PASS**

Stale comparison report: `physics/reports/milestone16/geoclaw_cpp_comparisons.json`
Corrected threshold reports: `physics/outputs/m18cmp/cascading_low_profile_closure/threshold_evaluation.json, physics/outputs/m18cmp/cascading_med_profile_closure/threshold_evaluation.json, physics/outputs/m18cmp/cascading_high_profile_closure/threshold_evaluation.json`

## Summary

- Boundary-corrected flows: `3` of `3`
- Feature-forcing-off flows: `3` of `3`
- Threshold-passing flows: `3` of `3`
- Failing checks: `none`

## Flow Results

| Flow | Gate scenario | Boundary | Feature forcing | Threshold | Corrected failures | Key stale -> corrected deltas |
| --- | --- | --- | ---: | --- | --- | --- |
| `high_runnable` | `south_fork_cascading_high_runnable` | corrected | `0` | PASS | none | field_linf 51.5977 -> 8.06075e-07; wet_mismatch_fraction 0.304464 -> 0; mass_drift_delta 1.81253 -> 4.58204e-09; energy_change_delta 4.17176 -> 1.07272e-08; froude_delta 0.384427 -> 3.70683e-08; feature_strength_delta 4.34964 -> 0.00176049 |
| `low_runnable` | `south_fork_cascading_low_runnable` | corrected | `0` | PASS | none | field_linf 39.6354 -> 5.05502e-07; wet_mismatch_fraction 0.327679 -> 0; mass_drift_delta 1.91183 -> 5.1664e-10; energy_change_delta 3.20291 -> 1.73319e-09; froude_delta 0.53995 -> 2.46868e-08; feature_strength_delta 4.94943 -> 5.64093e-09 |
| `median_runnable` | `south_fork_cascading_median_runnable` | corrected | `0` | PASS | none | field_linf 48.9428 -> 9.55311e-07; wet_mismatch_fraction 0.310714 -> 0; mass_drift_delta 1.87646 -> 4.80672e-09; energy_change_delta 3.42177 -> 4.77443e-09; froude_delta 0.278228 -> 1.66674e-08; feature_strength_delta 4.12386 -> 5.01862e-09 |

## Next Levers

- Use the corrected GeoClaw user-boundary manifests as the South Fork cascading reference; do not retune against stale extrapolated Milestone 16 outputs.
- Use stitched whole-window cascading comparisons for acceptance; reach-local seam passes already exist and cannot hide water-field errors.
- Keep `feature_strength_scale=0` until conservation, Froude, field, probe, and cross-section parity pass against GeoClaw.
