# Milestone 18 Constriction Upstream Lateral Transport Rejection

Schema: `raftsim.milestone18.constriction_retune_rejection.v0`

Decision: **REJECTED**

Scenario: `constriction_seed_16`
Feature forcing scale: `0`
Implementation retained: `false`

## Summary

A bounded upstream lateral mass/momentum transport pass was tested after the localized throat/recovery circulation baseline, then removed. The candidate transferred mass from upper upstream approach shoulder donors into lower-fringe/interior receiver rows and coupled that transfer to donor/receiver velocity targets. It kept feature forcing off and stayed inside mass/energy thresholds, but it worsened the field, slope, and Froude gates and did not move the probe or cross-section blockers.

## Threshold Comparison

| Check | Baseline localized circulation | Rejected upstream lateral transport | Result |
| --- | ---: | ---: | --- |
| `field_linf` | 3.69943 | 3.86487 | worse FAIL |
| `slope_linf` | 0.952377 | 0.997733 | worse FAIL |
| `wet_mismatch_fraction` | 0.270833 | 0.270833 | unchanged FAIL |
| `probe_linf` | 2.15656 | 2.15656 | unchanged FAIL |
| `cross_section_linf` | 1.6623 | 1.6623 | unchanged FAIL |
| `mass_drift_delta` | 0.0142295 | 0.0330179 | PASS but worse |
| `energy_change_delta` | 0.0212464 | 0.0532743 | PASS but worse |
| `froude_delta` | 0.504034 | 1.45 | worse FAIL |
| `feature_location_delta` | 3.60555 | 3.60555 | PASS |
| `feature_strength_delta` | 0.785574 | 0.787699 | PASS |

## Diagnostic Cells

| Cell | Zone | GeoClaw h/u/v/Fr | Baseline C++ | Rejected C++ | Readout |
| --- | --- | --- | --- | --- | --- |
| `9,1` | upstream upper edge | `0.380904/3.43843/-3.72743/2.6234` | `1.49294/1.80208/-0.028008/0.470945` | `1.46336/2.10796/-0.493718/0.57141` | Upper-edge velocity moves in the right sign direction, but the cell remains far too deep and low-Froude. |
| `1,1` | upstream lower fringe | `0.302/3.854/3.457` | `0.22/1.78219/-0.01074/1.21315` | `0.2215/2.05247/-0.38284/1.41639` | Lower-fringe velocity moves farther away from GeoClaw and becomes the new field Linf blocker. |
| `9,5` | upstream upper edge near throat | `0.417236/3.397/-1.974` | `1.87015/1.73549/0.439837` | `1.95313/1.85323/-0.235117` | The sign improves, but depth/slope worsens, so the shallow fast edge state is still wrong. |

## Decision

Do not retain the upstream lateral transport pass. The next constriction lever should first diagnose GeoClaw's face-level lateral flux/source balance in the upstream approach rows, because the reference is generating opposite-signed lower and upper edge velocities that the current post-step transport cannot reproduce without damaging Froude shape. Keep feature forcing off and continue to run Milestone 17 guardrails around the next attempt.
