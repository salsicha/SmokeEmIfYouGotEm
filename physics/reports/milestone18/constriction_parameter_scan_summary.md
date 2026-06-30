# Milestone 18 Constriction Parameter Scan

Decision: **BLOCKED**

Scenario family: `constriction`
Gate scenario: `constriction`
Actual scenario: `constriction_seed_16`
Reference manifest: `outputs/m18g/c_constrict_corrected/constriction_seed_16/normalized/manifest.json`

## Scan Matrix

The scan tested 336 finite-volume candidates against the corrected GeoClaw `user`-boundary reference with `feature_strength_scale=0`.

| Parameter | Values |
| --- | --- |
| `flux_scheme` | `hll`, `roe` |
| `roughness_scale` | `0.25`, `0.5`, `0.75`, `1.0`, `1.5`, `2.0` |
| `bed_slope_source_scale` | `0.0`, `0.25`, `0.5`, `0.75`, `1.0`, `1.5`, `2.0` |
| `cfl` | `0.25`, `0.35`, `0.45`, `0.6` |

The generated JSON summary at `constriction_parameter_scan_summary.json` keeps the top 40 ranked candidates. Ranking emphasizes field, cross-section, probe, slope, Froude, wet-mask, mass, and feature-strength error while leaving the threshold report itself as the source of pass/fail truth.

## Best Candidate

The best-ranked candidates were the existing finite-volume Roe configuration family:

| Candidate | Failed checks | Key values |
| --- | --- | --- |
| `roe_r0p5_b0p75_c0p25` through `roe_r0p5_b0p75_c0p6` | `field_linf`, `slope_linf`, `wet_mismatch_fraction`, `probe_linf`, `cross_section_linf`, `mass_drift_delta`, `froude_delta` | `field_linf=3.65866`, `cross_section_linf=2.13506`, `probe_linf=0.829959`, `slope_linf=0.641343`, `wet_mismatch_fraction=0.0277778`, `mass_drift_delta=0.0936647`, `froude_delta=0.5628` |

No parameter-only candidate passed the constriction gate. Varying CFL did not change the best candidate output, and increasing roughness/source scaling traded one failing metric for another without fixing the throat water-shape disagreement.

## Notes

- Feature forcing stayed disabled for every candidate.
- The scan reinforces the earlier source-treatment and hydrostatic-bank reports: scalar source, roughness, CFL, and flux-scheme changes are not sufficient.
- The next constriction implementation should target true throat/water-shape reconstruction or scenario width/depth mapping, then rerun the corrected-reference GeoClaw/C++ comparison and analytic guardrail.
