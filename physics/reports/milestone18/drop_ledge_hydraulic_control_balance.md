# Milestone 18 Drop/Ledge Hydraulic-Control Diagnostic

Schema: `raftsim.milestone18.drop_ledge_hydraulic_control.v0`

Decision: **PASS**

Scenario: `drop_ledge_seed_16`
Dual solver manifest: `physics/outputs/m18cmp/c_drop_hydraulic_control_tailwater_pulse/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `physics/outputs/m18cmp/c_drop_hydraulic_control_tailwater_pulse/finite_volume_roe/scenario/drop_ledge_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max final-field Linf: `0.194576`
- Max probe Linf: `0.188957`
- Max cross-section Linf: `0.111443`
- Max zone mean eta delta: `0.0698514` m

## Zones

| Zone | Columns |
| --- | --- |
| `upstream_pool` | `0-9` |
| `hydraulic_control` | `10-13` |
| `tailwater_recovery` | `14-17` |
| `downstream_pool` | `18-23` |

## Final Water Shape By Zone

| Zone | GeoClaw h/eta/u/Fr | C++ h/eta/u/Fr | Delta h/eta/u/Fr | Wet cells |
| --- | --- | --- | --- | --- |
| `upstream_pool` | `0.992128/0.932612/2.23078/0.721157` | `0.994072/0.934556/2.21527/0.714198` | `0.00194398/0.00194398/-0.0155091/-0.00695937` | `120->120` |
| `hydraulic_control` | `1.133/0.77763/2.26697/0.698012` | `1.14788/0.79251/2.26467/0.696549` | `0.0148797/0.0148797/-0.00230508/-0.00146274` | `48->48` |
| `tailwater_recovery` | `1.48669/0.894985/1.69403/0.443822` | `1.55654/0.964836/1.71531/0.438966` | `0.0698514/0.0698514/0.0212736/-0.00485619` | `48->48` |
| `downstream_pool` | `1.6371/0.920589/1.54477/0.385683` | `1.59776/0.881251/1.69934/0.429288` | `-0.0393379/-0.0393379/0.154569/0.0436042` | `72->72` |

## Worst Final-Frame Field Cells

| Category | Field | Frame | Zone | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `field` | `hu` | `final` | `downstream_pool` | `0,20` | 20 | -5.5 | 2.52603 | 2.72061 | 0.194576 | 0.194576 | 0.25 | 0.778303 |
| `field` | `u` | `final` | `upstream_pool` | `0,8` | 8 | -5.5 | 2.66602 | 2.48389 | -0.182123 | 0.182123 | 0.25 | 0.728491 |
| `field` | `h` | `final` | `hydraulic_control` | `0,13` | 13 | -5.5 | 1.34808 | 1.47544 | 0.127363 | 0.127363 | 0.25 | 0.509451 |
| `field` | `eta` | `final` | `hydraulic_control` | `0,13` | 13 | -5.5 | 0.846665 | 0.974027 | 0.127363 | 0.127363 | 0.25 | 0.509451 |
| `field` | `normal_x` | `final` | `hydraulic_control` | `0,12` | 12 | -5.5 | -0.0361645 | -0.156137 | -0.119973 | 0.119973 | 0.25 | 0.47989 |
| `field` | `normal_z` | `final` | `hydraulic_control` | `0,12` | 12 | -5.5 | 0.999346 | 0.987735 | -0.0116105 | 0.0116105 | 0.25 | 0.0464418 |
| `field` | `v` | `final` | `upstream_pool` | `0,0` | 0 | -5.5 | 0 | 0 | 0 | 0 | 0.25 | 0 |
| `field` | `hv` | `final` | `upstream_pool` | `0,0` | 0 | -5.5 | 0 | 0 | 0 | 0 | 0.25 | 0 |
| `field` | `normal_y` | `final` | `upstream_pool` | `0,0` | 0 | -5.5 | -0 | -0 | 0 | 0 | 0.25 | 0 |

## Worst Raw Probe/Cross-Section Samples

| Category | Sample | Field | Time s | Distance m | Zone | Cell | GeoClaw | C++ | Delta | Abs error | Ref h/u/v/Fr | C++ h/u/v/Fr | Threshold | Ratio |
| --- | --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |
| `probe` | `downstream_center` | `hu` | 3 | n/a | `downstream_pool` | `6,18` | 2.58992 | 2.40097 | -0.188957 | 0.188957 | `1.56668/1.65313/0/0.421681` | `1.5256/1.57378/0/0.406808` | 0.25 | 0.755826 |
| `probe` | `upstream_center` | `u` | 3 | n/a | `upstream_pool` | `6,6` | 1.87626 | 1.72442 | -0.151844 | 0.151844 | `1.12279/1.87626/0/0.565341` | `1.18454/1.72442/0/0.505865` | 0.25 | 0.607376 |
| `probe` | `downstream_center` | `u` | 6 | n/a | `downstream_pool` | `6,18` | 1.60814 | 1.7212 | 0.113064 | 0.113064 | `1.56815/1.60814/0/0.410011` | `1.56613/1.7212/0/0.43912` | 0.25 | 0.452255 |
| `probe` | `midstream_center` | `u` | 3 | n/a | `hydraulic_control` | `6,12` | 1.89158 | 1.78013 | -0.111443 | 0.111443 | `1.32413/1.89158/0/0.524836` | `1.34654/1.78013/0/0.489789` | 0.25 | 0.445772 |
| `cross_section` | `mid_cross_section` | `u` | 3 | -5.5 | `hydraulic_control` | `0,12` | 1.89158 | 1.78013 | -0.111443 | 0.111443 | `1.32413/1.89158/0/0.524836` | `1.34654/1.78013/0/0.489789` | 0.25 | 0.445772 |
| `probe` | `midstream_center` | `hu` | 3 | n/a | `hydraulic_control` | `6,12` | 2.5047 | 2.39701 | -0.107681 | 0.107681 | `1.32413/1.89158/0/0.524836` | `1.34654/1.78013/0/0.489789` | 0.25 | 0.430724 |
| `probe` | `upstream_center` | `hu` | 3 | n/a | `upstream_pool` | `6,6` | 2.10665 | 2.04264 | -0.0640118 | 0.0640118 | `1.12279/1.87626/0/0.565341` | `1.18454/1.72442/0/0.505865` | 0.25 | 0.256047 |
| `probe` | `upstream_center` | `h` | 3 | n/a | `upstream_pool` | `6,6` | 1.12279 | 1.18454 | 0.0617466 | 0.0617466 | `1.12279/1.87626/0/0.565341` | `1.18454/1.72442/0/0.505865` | 0.25 | 0.246986 |
| `probe` | `upstream_center` | `eta` | 3 | n/a | `upstream_pool` | `6,6` | 1.04896 | 1.1107 | 0.0617466 | 0.0617466 | `1.12279/1.87626/0/0.565341` | `1.18454/1.72442/0/0.505865` | 0.25 | 0.246986 |
| `probe` | `upstream_center` | `froude` | 3 | n/a | `upstream_pool` | `6,6` | 0.565341 | 0.505865 | -0.059476 | 0.059476 | `1.12279/1.87626/0/0.565341` | `1.18454/1.72442/0/0.505865` | 0.25 | 0.237904 |
| `probe` | `downstream_center` | `h` | 3 | n/a | `downstream_pool` | `6,18` | 1.56668 | 1.5256 | -0.0410725 | 0.0410725 | `1.56668/1.65313/0/0.421681` | `1.5256/1.57378/0/0.406808` | 0.25 | 0.16429 |
| `probe` | `downstream_center` | `eta` | 3 | n/a | `downstream_pool` | `6,18` | 0.909088 | 0.868015 | -0.0410725 | 0.0410725 | `1.56668/1.65313/0/0.421681` | `1.5256/1.57378/0/0.406808` | 0.25 | 0.16429 |

## Next Levers

- Start with `field`/`hu` at `final` cell 0,20; it is 0.778303x the diagnostic threshold.
- Retune the ledge hydraulic-control free-surface/depth reconstruction and downstream recovery shape before adding gameplay feature forcing.
- Preserve the passing conservation, energy, and Froude checks; this is a water-shape blocker, not permission to hide errors with forcing.
- Inspect depth, stage, and streamwise momentum across the ledge lip and first tailwater recovery columns.
- Use the raw probe/cross-section coordinates as the acceptance surface for the next corrected-reference parity run.
- Keep `feature_strength_scale=0` and rerun the Milestone 17 analytic guardrail after the solver change.
