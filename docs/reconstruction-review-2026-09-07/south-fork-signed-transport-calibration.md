# Signed transport screening, not settling acceptance

September27,2026. Calibration-tool correction; no playable asset change.

The previous analyser called `sum(h * hypot(u,v) * area) / station_bin_length`
"local discharge" and used its0.85-1.25Q range as a `--settled-only` filter.
Counterflow and transverse flow both contributed positively. That was not
signed downstream transport and did not establish temporal equilibrium.

The analysis now projects native east/north velocity onto the local downstream
route tangent before summing. Route normals and station order are validated;
the route hash is recorded. This remains a cell-centred transport proxy, not
a conservative numerical face-flux section integral: it does not include the
station-coordinate Jacobian. Use actual face-flux and temporal/regional storage
evidence for physical acceptance.

The preferred flag is `--transport-screen-only`; `--settled-only` remains a
documented legacy alias with the corrected signed semantics. Schema v2 writes
both signed and unsigned proxies and explicitly sets `settling_accepted=false`
and `normal_map_integrated=false`. `local_discharge` remains a legacy alias for
the signed proxy. Unsupported grid spacing, incomplete frames and invalid
thresholds are rejected. No eligible bias bins now raises an error instead of
fabricating a zero calibration.

The fit tool likewise labels its outputs as simulated-minus-captured-surface
bias, not measured bathymetry or verified settled data. The old `measured` mask
is retained for consumers but explicitly aliases `simulated_samples`; fit
numerics are unchanged and a new provenance field records that distinction.

## Tests and retained-snapshot comparison

All18 tests pass, including forward/reverse/transverse flow, native north versus
Unreal reflected Y, curved tangent normalization, endpoint context, dry cells,
invalid inputs, full analysis output and the legacy flag. An exact counterflow
fixture that previously passed the magnitude screen is rejected for calibration.
A complete fit fixture confirms identical numerical output with corrected labels.

On the retained v2/300s snapshot (1,632,290 captured-water-mask cells):

- Old magnitude-screen bins:3,393; signed-screen bins:3,442.
- 116 bins leave the screen; 165 enter it. A lower estimate can move a bin below
  the lower threshold or back beneath the upper threshold; this is not a count
  of "newly settled" bins. No bin has negative net proxy in this snapshot.
- Largest magnitude-minus-signed difference:27.32456m3/s.
- Unsigned proxy exactly reproduces the previous reported values. Raw bias,
  station, wet fraction and default unscreened selection are exactly unchanged.
- Historical smoothed bias differs by at most2.22e-16m; it is not byte-identical.
  Re-evaluating the prior unscreened smoothing formula in the same NumPy runtime
  exactly reproduces the new output. The historical file remains untouched.

Report: `tmp/discharge-bed-v2-signed-analysis-20260927/report.json`, SHA-256
`697c9f0635c4e6525609e54dbecd458b476caed9e8952db1cf8684dc64c8ec9c`.
Read-only comparison: `tmp/compare-v2-signed-analysis-20260927.py`.
The completed native restart and running300-450s continuation are separate
evidence; no live cook file or physical setting was edited by this correction.

No existing calibration, bed, captured data, runtime field, normal scene or
packaged game was replaced. This fixes a future calibration decision tool, not
the outstanding water appearance, geometry, motion, shoreline or20FPS gates.
