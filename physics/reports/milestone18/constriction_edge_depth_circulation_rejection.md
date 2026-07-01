# Milestone 18 Constriction Edge-Depth/Circulation Rejection

Schema: `raftsim.milestone18.constriction_retune_rejection.v0`

Decision: **REJECTED**

Scenario: `constriction_seed_16`
Feature forcing scale: `0`
Implementation retained: `false`

## Summary

Two mass-balanced upstream edge-depth variants were tested after the center-throat circulation pass, then removed. A depth-plus-circulation variant kept conservation inside threshold but worsened field, slope, and Froude errors. A depth-only variant avoided the worst regression, but barely changed the over-deep upstream edge cells and still worsened Froude versus the baseline.

## Threshold Comparison

| Check | Baseline center-throat | Depth + circulation | Depth only | Result |
| --- | ---: | ---: | ---: | --- |
| `field_linf` | 3.69455 | 3.90843 | 3.6948 | no improvement |
| `slope_linf` | 0.855161 | 0.891738 | 0.850006 | tiny depth-only improvement |
| `wet_mismatch_fraction` | 0.270833 | 0.270833 | 0.270833 | unchanged |
| `probe_linf` | 2.20322 | 2.20322 | 2.20322 | unchanged |
| `cross_section_linf` | 1.69192 | 1.69192 | 1.69192 | unchanged |
| `mass_drift_delta` | 0.0127906 | 0.0142033 | 0.0116555 | PASS |
| `energy_change_delta` | 0.159088 | 0.0192026 | 0.153776 | PASS |
| `froude_delta` | 0.504034 | 1.47423 | 0.671046 | worse |

## Diagnostic Cells

| Cell | Zone | GeoClaw h/u/v/Fr | Baseline C++ | Depth only | Depth + circulation | Readout |
| --- | --- | --- | --- | --- | --- | --- |
| `9,1` | upstream upper edge | `0.380904/3.43843/-3.72743/2.6234` | `1.62776/1.05583/-0.0328864/0.264348` | `1.617/1.08/-0.033/0.271` | `1.646/1.666/-0.584/0.439` | Depth transfer barely shallows the edge; velocity forcing is still not enough and worsens summary Froude. |
| `6,6` | upstream center | `1.83972/0.97954/-0.511441/0.260112` | `1.67972/1.07991/0.636971/0.308862` | `1.686/1.112/0.622/0.313` | `1.760/1.644/-0.236/0.400` | Circulation helps v sign but over-accelerates u/Froude. |

## Decision

Do not retain the edge-depth/circulation pass. The next constriction implementation should move upstream edge behavior into the flux/source treatment, because post-step column-local redistribution cannot produce GeoClaw's shallow, fast upstream edge without degrading Froude shape.
