# Milestone 18 Drop/Ledge Hydraulic-Control Diagnostic

Schema: `raftsim.milestone18.drop_ledge_hydraulic_control.v0`

Decision: **PASS**

Scenario: `drop_ledge_seed_16`
Dual solver manifest: `outputs/m18cmp/c_drop_hydraulic_control_lip_slope_balance/finite_volume_hll/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_drop_hydraulic_control_lip_slope_balance/finite_volume_hll/scenario/drop_ledge_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max final-field Linf: `0.192975`
- Max probe Linf: `0.188978`
- Max cross-section Linf: `0.108631`
- Max zone mean eta delta: `0.0444017` m

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
| `upstream_pool` | `0.992128/0.932612/2.23078/0.721157` | `0.996065/0.936548/2.21226/0.712377` | `0.00393678/0.00393678/-0.0185267/-0.00878071` | `120->120` |
| `hydraulic_control` | `1.133/0.77763/2.26697/0.698012` | `1.17305/0.817687/2.26612/0.684951` | `0.0400565/0.0400565/-0.000852436/-0.013061` | `48->48` |
| `tailwater_recovery` | `1.48669/0.894985/1.69403/0.443822` | `1.53109/0.939387/1.71186/0.44175` | `0.0444017/0.0444017/0.017827/-0.00207176` | `48->48` |
| `downstream_pool` | `1.6371/0.920589/1.54477/0.385683` | `1.59679/0.880282/1.69834/0.429166` | `-0.0403072/-0.0403072/0.153565/0.0434828` | `72->72` |

## Worst Final-Frame Field Cells

| Category | Field | Frame | Zone | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `field` | `hu` | `final` | `downstream_pool` | `0,21` | 21 | -5.5 | 2.52836 | 2.72133 | 0.192975 | 0.192975 | 0.35 | 0.551358 |
| `field` | `u` | `final` | `upstream_pool` | `0,8` | 8 | -5.5 | 2.66602 | 2.47997 | -0.186044 | 0.186044 | 0.35 | 0.531553 |
| `field` | `h` | `final` | `hydraulic_control` | `0,13` | 13 | -5.5 | 1.34808 | 1.44109 | 0.0930179 | 0.0930179 | 0.35 | 0.265766 |
| `field` | `eta` | `final` | `hydraulic_control` | `0,13` | 13 | -5.5 | 0.846665 | 0.939683 | 0.0930179 | 0.0930179 | 0.35 | 0.265766 |
| `field` | `normal_x` | `final` | `hydraulic_control` | `0,12` | 12 | -5.5 | -0.0361645 | -0.103968 | -0.0678037 | 0.0678037 | 0.35 | 0.193725 |
| `field` | `normal_z` | `final` | `hydraulic_control` | `0,12` | 12 | -5.5 | 0.999346 | 0.994581 | -0.00476522 | 0.00476522 | 0.35 | 0.0136149 |
| `field` | `v` | `final` | `upstream_pool` | `0,0` | 0 | -5.5 | 0 | 0 | 0 | 0 | 0.35 | 0 |
| `field` | `hv` | `final` | `upstream_pool` | `0,0` | 0 | -5.5 | 0 | 0 | 0 | 0 | 0.35 | 0 |
| `field` | `normal_y` | `final` | `upstream_pool` | `0,0` | 0 | -5.5 | -0 | -0 | 0 | 0 | 0.35 | 0 |

## Worst Raw Probe/Cross-Section Samples

| Category | Sample | Field | Time s | Distance m | Zone | Cell | GeoClaw | C++ | Delta | Abs error | Ref h/u/v/Fr | C++ h/u/v/Fr | Threshold | Ratio |
| --- | --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |
| `probe` | `downstream_center` | `hu` | 3 | n/a | `downstream_pool` | `6,18` | 2.58992 | 2.40094 | -0.188978 | 0.188978 | `1.56668/1.65313/0/0.421681` | `1.52559/1.57378/0/0.40681` | 0.35 | 0.539938 |
| `probe` | `midstream_center` | `hu` | 6 | n/a | `hydraulic_control` | `6,12` | 2.51321 | 2.67757 | 0.164359 | 0.164359 | `1.2529/2.00591/0/0.572161` | `1.2927/2.0713/0/0.581645` | 0.35 | 0.469597 |
| `probe` | `upstream_center` | `u` | 3 | n/a | `upstream_pool` | `6,6` | 1.87626 | 1.72368 | -0.152585 | 0.152585 | `1.12279/1.87626/0/0.565341` | `1.1848/1.72368/0/0.505591` | 0.35 | 0.435957 |
| `probe` | `downstream_center` | `u` | 6 | n/a | `downstream_pool` | `6,18` | 1.60814 | 1.71879 | 0.110647 | 0.110647 | `1.56815/1.60814/0/0.410011` | `1.56334/1.71879/0/0.438895` | 0.35 | 0.316135 |
| `probe` | `midstream_center` | `u` | 3 | n/a | `hydraulic_control` | `6,12` | 1.89158 | 1.78295 | -0.108631 | 0.108631 | `1.32413/1.89158/0/0.524836` | `1.34504/1.78295/0/0.490836` | 0.35 | 0.310376 |
| `cross_section` | `mid_cross_section` | `u` | 3 | -5.5 | `hydraulic_control` | `0,12` | 1.89158 | 1.78295 | -0.108631 | 0.108631 | `1.32413/1.89158/0/0.524836` | `1.34504/1.78295/0/0.490836` | 0.35 | 0.310376 |
| `probe` | `upstream_center` | `hu` | 3 | n/a | `upstream_pool` | `6,6` | 2.10665 | 2.04221 | -0.0644372 | 0.0644372 | `1.12279/1.87626/0/0.565341` | `1.1848/1.72368/0/0.505591` | 0.35 | 0.184106 |
| `probe` | `upstream_center` | `h` | 3 | n/a | `upstream_pool` | `6,6` | 1.12279 | 1.1848 | 0.062009 | 0.062009 | `1.12279/1.87626/0/0.565341` | `1.1848/1.72368/0/0.505591` | 0.35 | 0.177168 |
| `probe` | `upstream_center` | `eta` | 3 | n/a | `upstream_pool` | `6,6` | 1.04896 | 1.11097 | 0.062009 | 0.062009 | `1.12279/1.87626/0/0.565341` | `1.1848/1.72368/0/0.505591` | 0.35 | 0.177168 |
| `probe` | `upstream_center` | `froude` | 3 | n/a | `upstream_pool` | `6,6` | 0.565341 | 0.505591 | -0.0597493 | 0.0597493 | `1.12279/1.87626/0/0.565341` | `1.1848/1.72368/0/0.505591` | 0.35 | 0.170712 |
| `probe` | `downstream_center` | `h` | 3 | n/a | `downstream_pool` | `6,18` | 1.56668 | 1.52559 | -0.0410874 | 0.0410874 | `1.56668/1.65313/0/0.421681` | `1.52559/1.57378/0/0.40681` | 0.35 | 0.117393 |
| `probe` | `downstream_center` | `eta` | 3 | n/a | `downstream_pool` | `6,18` | 0.909088 | 0.868 | -0.0410874 | 0.0410874 | `1.56668/1.65313/0/0.421681` | `1.52559/1.57378/0/0.40681` | 0.35 | 0.117393 |

## Next Levers

- Start with `field`/`hu` at `final` cell 0,21; it is 0.551358x the diagnostic threshold.
- Retune the ledge hydraulic-control free-surface/depth reconstruction and downstream recovery shape before adding gameplay feature forcing.
- Preserve the passing conservation, energy, and Froude checks; this is a water-shape blocker, not permission to hide errors with forcing.
- Inspect depth, stage, and streamwise momentum across the ledge lip and first tailwater recovery columns.
- Use the raw probe/cross-section coordinates as the acceptance surface for the next corrected-reference parity run.
- Keep `feature_strength_scale=0` and rerun the Milestone 17 analytic guardrail after the solver change.
