# Milestone 18 Constriction Upstream/Recovery Circulation Rejection

Schema: `raftsim.milestone18.constriction_retune_rejection.v0`

Decision: **REJECTED**

Scenario: `constriction_seed_16`
Feature forcing scale: `0`
Implementation retained: `false`

## Summary

A fixture-scoped non-throat upstream/downstream/recovery velocity-only circulation pass was tested after the center-throat circulation pass, then removed. The candidate was bounded and instantaneously mass-preserving, but it changed transport enough to fail conservation parity and made the Froude envelope worse.

## Threshold Comparison

| Check | Baseline center-throat | Rejected velocity-only | Threshold result |
| --- | ---: | ---: | --- |
| `field_linf` | 3.69455 | 3.64276 | still FAIL |
| `slope_linf` | 0.855161 | 0.895307 | worse FAIL |
| `wet_mismatch_fraction` | 0.270833 | 0.277778 | worse FAIL |
| `probe_linf` | 2.20322 | 2.20322 | unchanged FAIL |
| `cross_section_linf` | 1.69192 | 1.69192 | unchanged FAIL |
| `mass_drift_delta` | 0.0127906 | 0.0575969 | regressed to FAIL |
| `energy_change_delta` | 0.159088 | 0.111671 | PASS |
| `froude_delta` | 0.504034 | 1.48585 | worse FAIL |

## Diagnostic Cells

| Cell | Zone | GeoClaw h/u/v/Fr | Baseline C++ h/u/v/Fr | Rejected C++ h/u/v/Fr | Readout |
| --- | --- | --- | --- | --- | --- |
| `9,1` | upstream upper edge | `0.380904/3.43843/-3.72743/2.6234` | `1.62776/1.05583/-0.0328864/0.264348` | `1.658/1.663/-0.296/0.419` | Velocity moves in the right direction, but the cell remains far too deep and too low-Froude. |
| `6,18` | recovery center | `1.2504/2.97973/0.51569/0.863428` | `1.03777/1.69791/-0.611037/0.565554` | `0.764/2.25/0.157/0.824` | Velocity sign improves, but recovery depth/mass timing moves away from GeoClaw. |

## Decision

Do not retain a velocity-only upstream/recovery circulation pass. The next constriction lever should be a mass-balanced edge-depth plus circulation reconstruction: shallow the over-deep upstream edge cells, redistribute water into under-depth interior/support cells, and only then retune lateral velocity and Froude timing.
