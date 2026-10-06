# Exchange-velocity diagnostic — September 8, 2026

Status: flow consistency remains unresolved. This is not a calibrated mass budget.

`analyze_liquid_exchange.py` samples the actual final velocity field at the
physical exchange faces. The collocated face estimate averages the ghost and
adjacent interior cell velocities. It reports both native-profile partial wet
apertures and the whole-cell centre-selected apertures used to normalize the
prescribed boundary velocity. These are distinct: partial-aperture integration
of a quantized-boundary velocity is not the original native discharge.

At 60 seconds, `liquid-outlet-stage-60s/exchange_aperture_audit_60s_v2.json`
reports the following whole-cell-aperture values (m³/s, positive inward):

| Face | Prescribed profile | Actual midpoint velocity estimate |
| --- | ---: | ---: |
| West | 41.413 | 36.804 |
| East | -45.103 | -15.680 |
| South | 2.248 | 2.052 |
| North | 1.474 | -26.138 |

The large redistribution toward the north face is a concrete reason not to
accept the 3D/native handoff yet. An outgoing-stage boundary intentionally does
not clamp outgoing velocity; matching its pressure does not establish matching
discharge. The net midpoint estimate is -2.962 m³/s using the quantized aperture,
or -4.215 m³/s using the partial aperture. Neither is measured storage loss:
actual moving free-surface aperture and integrated temporal flux are not included.

The first retained audit used an ambiguous `native_target` label for the
partial-aperture integral. V2 corrects that distinction and explicitly reports
the centre-selected prescribed value. Do not use V1 as a native-Q comparison.

Three new regressions cover fractional aperture, equal-and-opposite translated
flow, midpoint sampling, solid-adjacent aperture reporting, and nonfinite input
rejection. All 26 focused liquid Python tests pass. Next measure the actual wet
interface/storage evolution and investigate the excessive lateral outlet flow;
do not normalize it away, clamp the exit to a desired number, or treat marker
counts as conserved water mass.
