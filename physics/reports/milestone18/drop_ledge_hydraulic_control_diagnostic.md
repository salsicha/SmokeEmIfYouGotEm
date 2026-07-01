# Milestone 18 Drop/Ledge Hydraulic-Control Diagnostic

Schema: `raftsim.milestone18.drop_ledge_hydraulic_control.v0`

Decision: **BLOCKED**

Scenario: `drop_ledge_seed_16`
Dual solver manifest: `outputs/m18cmp/c_drop_corrected/finite_volume_roe/dual_solver_manifest.json`
Scenario package: `outputs/m18cmp/c_drop_corrected/finite_volume_roe/scenario/drop_ledge_seed_16`
Wet-depth threshold: `0.15` m
Velocity depth floor: `0.15` m

## Summary

- Max final-field Linf: `0.830342`
- Max probe Linf: `0.41761`
- Max cross-section Linf: `0.185418`
- Max zone mean eta delta: `0.117793` m

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
| `upstream_pool` | `0.992128/0.932612/2.23078/0.721157` | `1.10992/1.0504/1.86484/0.565751` | `0.117793/0.117793/-0.365941/-0.155406` | `120->120` |
| `hydraulic_control` | `1.133/0.77763/2.26697/0.698012` | `1.24394/0.888569/1.87642/0.539668` | `0.110939/0.110939/-0.390552/-0.158344` | `48->48` |
| `tailwater_recovery` | `1.48669/0.894985/1.69403/0.443822` | `1.44766/0.855956/1.59179/0.422473` | `-0.0390284/-0.0390284/-0.102243/-0.0213492` | `48->48` |
| `downstream_pool` | `1.6371/0.920589/1.54477/0.385683` | `1.53188/0.815362/1.53192/0.395244` | `-0.105227/-0.105227/-0.012851/0.00956066` | `72->72` |

## Worst Final-Frame Field Cells

| Category | Field | Frame | Zone | Cell | x m | y m | GeoClaw | C++ | Delta | Abs error | Threshold | Ratio |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `field` | `u` | `final` | `hydraulic_control` | `0,10` | 10 | -5.5 | 2.86392 | 2.03358 | -0.830342 | 0.830342 | 0.25 | 3.32137 |
| `field` | `h` | `final` | `hydraulic_control` | `0,10` | 10 | -5.5 | 0.85483 | 1.12065 | 0.265816 | 0.265816 | 0.25 | 1.06326 |
| `field` | `eta` | `final` | `hydraulic_control` | `0,10` | 10 | -5.5 | 0.652739 | 0.918555 | 0.265816 | 0.265816 | 0.25 | 1.06326 |
| `field` | `hu` | `final` | `tailwater_recovery` | `0,15` | 15 | -5.5 | 2.51593 | 2.29466 | -0.22127 | 0.22127 | 0.25 | 0.885079 |
| `field` | `normal_x` | `final` | `hydraulic_control` | `0,11` | 11 | -5.5 | -0.0916578 | 0.022075 | 0.113733 | 0.113733 | 0.25 | 0.454931 |
| `field` | `normal_z` | `final` | `hydraulic_control` | `0,11` | 11 | -5.5 | 0.995791 | 0.999756 | 0.00396575 | 0.00396575 | 0.25 | 0.015863 |
| `field` | `v` | `final` | `upstream_pool` | `0,0` | 0 | -5.5 | 0 | 0 | 0 | 0 | 0.25 | 0 |
| `field` | `hv` | `final` | `upstream_pool` | `0,0` | 0 | -5.5 | 0 | 0 | 0 | 0 | 0.25 | 0 |
| `field` | `normal_y` | `final` | `upstream_pool` | `0,0` | 0 | -5.5 | -0 | -0 | 0 | 0 | 0.25 | 0 |

## Worst Raw Probe/Cross-Section Samples

| Category | Sample | Field | Time s | Distance m | Zone | Cell | GeoClaw | C++ | Delta | Abs error | Ref h/u/v/Fr | C++ h/u/v/Fr | Threshold | Ratio |
| --- | --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |
| `probe` | `upstream_center` | `u` | 6 | n/a | `upstream_pool` | `6,6` | 2.35076 | 1.93315 | -0.41761 | 0.41761 | `0.957294/2.35076/0/0.767099` | `1.08822/1.93315/0/0.591661` | 0.25 | 1.67044 |
| `probe` | `downstream_center` | `hu` | 3 | n/a | `downstream_pool` | `6,18` | 2.58992 | 2.28564 | -0.304285 | 0.304285 | `1.56668/1.65313/0/0.421681` | `1.51967/1.50404/0/0.389538` | 0.25 | 1.21714 |
| `probe` | `midstream_center` | `hu` | 3 | n/a | `hydraulic_control` | `6,12` | 2.5047 | 2.30504 | -0.199658 | 0.199658 | `1.32413/1.89158/0/0.524836` | `1.34132/1.71849/0/0.473747` | 0.25 | 0.798632 |
| `probe` | `midstream_center` | `u` | 6 | n/a | `hydraulic_control` | `6,12` | 2.00591 | 1.82049 | -0.185418 | 0.185418 | `1.2529/2.00591/0/0.572161` | `1.29047/1.82049/0/0.511659` | 0.25 | 0.741671 |
| `cross_section` | `mid_cross_section` | `u` | 6 | -5.5 | `hydraulic_control` | `0,12` | 2.00591 | 1.82049 | -0.185418 | 0.185418 | `1.2529/2.00591/0/0.572161` | `1.29047/1.82049/0/0.511659` | 0.25 | 0.741671 |
| `probe` | `upstream_center` | `froude` | 6 | n/a | `upstream_pool` | `6,6` | 0.767099 | 0.591661 | -0.175438 | 0.175438 | `0.957294/2.35076/0/0.767099` | `1.08822/1.93315/0/0.591661` | 0.25 | 0.701754 |
| `probe` | `downstream_center` | `u` | 3 | n/a | `downstream_pool` | `6,18` | 1.65313 | 1.50404 | -0.149094 | 0.149094 | `1.56668/1.65313/0/0.421681` | `1.51967/1.50404/0/0.389538` | 0.25 | 0.596377 |
| `probe` | `upstream_center` | `hu` | 6 | n/a | `upstream_pool` | `6,6` | 2.25037 | 2.1037 | -0.146673 | 0.146673 | `0.957294/2.35076/0/0.767099` | `1.08822/1.93315/0/0.591661` | 0.25 | 0.586692 |
| `probe` | `upstream_center` | `h` | 6 | n/a | `upstream_pool` | `6,6` | 0.957294 | 1.08822 | 0.130928 | 0.130928 | `0.957294/2.35076/0/0.767099` | `1.08822/1.93315/0/0.591661` | 0.25 | 0.52371 |
| `probe` | `upstream_center` | `eta` | 6 | n/a | `upstream_pool` | `6,6` | 0.883463 | 1.01439 | 0.130928 | 0.130928 | `0.957294/2.35076/0/0.767099` | `1.08822/1.93315/0/0.591661` | 0.25 | 0.52371 |
| `probe` | `downstream_center` | `h` | 6 | n/a | `downstream_pool` | `6,18` | 1.56815 | 1.49312 | -0.0750263 | 0.0750263 | `1.56815/1.60814/0/0.410011` | `1.49312/1.56106/0/0.407885` | 0.25 | 0.300105 |
| `probe` | `downstream_center` | `eta` | 6 | n/a | `downstream_pool` | `6,18` | 0.910559 | 0.835533 | -0.0750263 | 0.0750263 | `1.56815/1.60814/0/0.410011` | `1.49312/1.56106/0/0.407885` | 0.25 | 0.300105 |

## Blocked Reasons

- C++ drop/ledge final-field Linf still exceeds the GeoClaw/C++ threshold.
- C++ drop/ledge point-probe raw samples still exceed the GeoClaw/C++ threshold.
- The remaining drop/ledge error is localized to hydraulic-control or tailwater-recovery water shape.

## Next Levers

- Start with `field`/`u` at `final` cell 0,10; it is 3.32137x the diagnostic threshold.
- Retune the ledge hydraulic-control free-surface/depth reconstruction and downstream recovery shape before adding gameplay feature forcing.
- Preserve the passing conservation, energy, and Froude checks; this is a water-shape blocker, not permission to hide errors with forcing.
- Inspect depth, stage, and streamwise momentum across the ledge lip and first tailwater recovery columns.
- Use the raw probe/cross-section coordinates as the acceptance surface for the next corrected-reference parity run.
- Keep `feature_strength_scale=0` and rerun the Milestone 17 analytic guardrail after the solver change.
