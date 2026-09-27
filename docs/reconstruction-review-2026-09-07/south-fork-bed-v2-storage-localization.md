# South Fork v2: regional storage has not settled

September 27, 2026. Supporting hydraulic diagnosis only; no new playable change.
The current v2 cook's net filling was known, but its spatial distribution had
not been independently checked. This audit uses the five existing completed
snapshots at0,75,150,225 and300seconds. No duplicate cook, engine launch, source
download, geometry change, field replacement or package rebuild was started.
Other shared engine work was active at the initial check.

## Conservation versus equilibrium

`audit_cartesian_storage_regions.py` verifies the copied/original manifest,
every scenario and bed hash, unique tile ownership, all5,382,400 depth cells,
snapshot clocks/layouts and independently summed water volumes. Changes in
snapshot storage agree with the solver's time-integrated exterior boundary
volume within5.85e-11m3 over the audited intervals. This is numerical volume
closure, **not equilibrium or evidence that bathymetry is measured**.

| Cook interval (s) | Net storage rate (m3/s) |
| --- | ---: |
| 0-75 | 6.04 |
| 75-150 | 7.21 |
| 150-225 | 7.05 |
| 225-300 | 6.164 |

Over the final75seconds, regions gaining storage sum to+86.149m3/s and regions
losing storage sum to-79.985m3/s. Their cancellation leaves only+6.164m3/s
globally (about13.6% of45.307m3/s inlet discharge). These are regional
**storage-change rates**, not independent source/sink flows, cross-section
discharges or additional water creation. The nearest-route,1km bands partition
all cells, including dry terrain and endpoint context, exactly once.

| Route attribution band (km) | Final75s storage rate (m3/s) | Common-wet median stage change (m) |
| --- | ---: | ---: |
| 28-29 | +18.40 | +0.0600 |
| 26-27 | +9.31 | +0.0142 |
| 10-11 | +9.16 | +0.0132 |
| 12-13 | +9.08 | +0.0175 |
| 13-14 | -17.13 | -0.0243 |
| 29-30 | -12.23 | -0.0391 |
| 8-9 | -11.85 | -0.0124 |

Thus a small net-volume change alone would not establish local settling.
Stage statistics cover cells wet at both endpoints; storage includes wetting
and drying as well. The audit does not identify whether any particular
transition is caused by initialization, inferred bed shape or a physical
boundary, and does not prove causation for in-game turning or frame cost.

## Calibration caution and next step

Code inspection found that the existing cook-comparison tool's
`local_discharge_m3s` is `sum(h * hypot(u,v) * cell_area) / bin_length`.
It is an unsigned transport-magnitude proxy: reverse and transverse currents
also contribute positively. Its0.85-1.25Q screen and `--settled-only` name do
not establish signed through-flow, numerical face-flux balance or temporal
equilibrium. The retained v2 analysis used all6,782 eligible bias bins;3,393
passed that magnitude screen. This does not establish that the installed bed
was calibrated from those particular bins or that its geometry is wrong.
Existing bed, calibration files, snapshots and source evidence are preserved.

Before another bed correction, use actual temporal/regional storage and signed
face-flux evidence; do not treat that magnitude screen as a settling gate.
If continuing the unchanged cook, resume its saved300s state and compare these
same regions over the new interval rather than restarting or repeating this
snapshot audit. Preserve all inputs and distinguish inferred bed changes from
measured terrain. No new cook is justified merely by this report's existence.

## Evidence and validation

- Report: `tmp/discharge-bed-v2-storage-20260927.json`.
- SHA-256: `1cf0034d4ab89e489095166d1ce1aede45bba6e0d61cb818df700bf8ab61064d`.
- Input: `tmp/discharge-bed-v2-20260926/cook_v2_full_out`.
- Steps:0,1500,3000,4500,6000; existing1km regional-audit implementation.
- All17 existing storage-audit regressions pass, including corrupted inputs,
  volume/flux/clock failures, wet/dry cases and native-coordinate checks.
- Initial sandbox run could not read SciPy; scoped approval allowed existing
  dependencies. First test invocation lacked pytest on its import path; adding
  the existing test dependency directory resolved it. Nothing was installed.

No rendered-view, animation, collision, shoreline, surface-continuity or20FPS
acceptance follows from this audit. South Fork remains first and unfinished.
