# Actual rendered-liquid aperture audit

September 8 continuation. This is diagnostic evidence, not scene acceptance or
a calibrated fluid-mass balance. The full project goal remains active.

`physics/scripts/analyze_liquid_surface_exchange.py` integrates actual GPU
velocity over negative intervals of the actual rendered SDF, clipped above the
native boundary bed. It interpolates both grids at their respective cell centers,
includes partial vertical intervals and disconnected liquid intervals, and keeps
air gaps empty. Four independent numerical tests pass. The SDF is a rendered
particle reconstruction, not a calibrated conserved-volume field.

At 60 seconds in `liquid-outlet-stage-60s`, positive flow is inward:

| Face | SDF wet area at boundary (m²) | Flow at boundary (m³/s) | SDF wet area one grid cell inside (m²) | Flow one grid cell inside (m³/s) |
|---|---:|---:|---:|---:|
| West | 6.495 | 0.817 | 36.233 | 31.207 |
| East | 3.710 | -1.830 | 15.279 | -6.700 |
| South | 1.454 | 0.207 | 6.386 | 0.834 |
| North | 9.815 | -9.736 | 36.408 | -22.521 |

The inset is 32.8125 cm. Inset columns still use the original boundary bed/stage
as a reference, not a freshly sampled inset terrain profile. The planes are not
an exact closed terrain-clipped control volume. Neither sum is a mass-loss rate.
Highest liquid top can be a separate fragment; it is not necessarily a hydraulic
head measurement.

This establishes severe edge-aperture erosion but does **not** explain away the
excessive northward exit: it remains substantial inside the patch. Source points
are only 1 cm inside the physical exchange boundary, with particle retirement
outside that boundary. The rendered reconstruction has less neighboring particle
support at this edge. A continuous full-scene handoff is not yet demonstrated.

Retained reports: `sdf_exchange_60s.json`, `sdf_exchange_60s_inset.json`, and
`sdf_exchange_0p1s.json` in the capture directory. No saved scene or system was
changed by the audit.
