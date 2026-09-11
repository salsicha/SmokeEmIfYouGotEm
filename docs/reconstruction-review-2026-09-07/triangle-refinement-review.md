# Same-triangle fine-grid investigation

This pass continues South Fork only. The current isolated review still loads
the one-metre triangle-sampled fields and is not accepted. No production map,
terrain/collision, raft force or engine-linked solver is changed here.

## Why another resolution comparison is needed

The earlier half-metre histories used bilinear terrain interpolation. They
cannot be compared as a resolution-only test against the corrected triangle
package. The new run uses `render_triangles` on both grids, preserving source
geometry, physical cell-edge domain, fixed timestep, CFL, roughness, native
binary and exact parent boundary forcing. It starts from the parent's final
state with documented wet-weighted resampling, not a fresh cold water sheet.

Run: `0.5m-mixed-inlet-mesh-triangles-refined-20260907`, 2,400 steps at 0.1 s /
CFL 0.2 (240 simulated seconds), parent `1m-mixed-inlet-mesh-triangles-20260907`.
Initial resampling changes storage by -3.74749 m3 (-0.0222%); this is explicitly
non-conservative initialization and requires settling. No fine package is
exported or promoted merely because a solve completes.

## Geometry sampling is still resolution-dependent

The [static bed audit](triangle-subgrid-geometry.json) compares each one-metre
sample to its four half-metre child samples. At narrow rock edges the mean
difference reaches **2.282 m**, although its crux median absolute difference
is only 2.4 mm and p95 is 7.8 cm. This is spatial sample loss, not the former
triangle-versus-bilinear interpolation bug, a vertical-datum error, or proof
that either grid is a converged representation of the source surface.

At the frozen diagnostic stage 7.687 m above the 220 m NAVD88 datum, 91 m2 of
coarse-dry cells contain some fine water, and 77 m2 of coarse-wet cells contain
some fine dry rock. The net storage discrepancy is only -3.842 m3 over the
crux box, so aggregate volume alone hides local rock/channel differences.
These are areas of **whole coarse cells with mixed children**, not newly
measured inundation areas. Four point samples are not exact cell integrals.

This audit does not compute flow or establish which local mismatch causes
the prior roughly 23 cm hydraulic stage sensitivity. It supports resolving
narrow rock controls before accepting more detailed visible waves.

The independent area/mixed-wet regression suite passes with the existing
sampling/comparison checks: **18 tests plus 27 subtests**.

## Additional primary visual evidence

The [CDFW survey memorandum](https://nrm.dfg.ca.gov/FileHandler.ashx?DocumentID=177207)
contains labeled topographic/aerial figures and photographs of Meatgrinder
and Triple Threat. The survey took place in late October/early November 2018
with a coordinated 300 cfs release target. The detailed figures stop near
Slusebox, **not Troublemaker**. They do not publish the GPS tracks mentioned in
the methods or provide measured boulder coordinates/bathymetry. Photos are
not substituted for the 1600 cfs Troublemaker scenario.

The PDF skill's visual review of pages 4, 5, 12 and 13 keeps those location and
flow limits explicit. No embedded geospatial PDF dictionaries were found.
The source and hash are retained with a separate provenance file. Its content
is reference-only: [CDFW's policy](https://wildlife.ca.gov/Conditions-of-Use)
does not establish blanket clearance for third-party photos or basemap artwork.
No reference imagery is imported as shipping textures or geometry.

## Flow result

The run completed 240 simulated seconds in 1,373.262 wall seconds. The native
runner reports success, but the independent saved-history screen **rejects
the candidate**: frame 5 (100 s) reaches 23.7504 m/s, above the unchanged
20 m/s safety limit. The other twelve saved frames pass the generous numerical
screen. A sane final frame does not erase the failed intermediate frame.

The [comparison report](triangle-resolution-comparison.json) records every
frame hash and the failure. It deliberately emits no accepted final-state
resolution comparison. Regional settling and final-frame conservation checks
are not used to rehabilitate this rejected history; no fine fields are exported,
loaded in Unreal or promoted. The previous one-metre engine review remains
unchanged, with its existing visual, tracking, settling and performance failures.

### Localized shallow-cell velocity spike

Only one cell exceeds 20 m/s in the failed saved frame: row 104, column 230,
downstream/left coordinates (-20.25, -28.25) m, UTM EPSG:32610
(683834.349695056, 4296692.276994233). Its bed is 227.857211604 m NAVD88.
This is a shallow, roughly 9.5 cm water cell, **not an almost-zero-depth cell**
that can simply be excluded from the safety screen.

| Saved time | Depth (m) | Downstream velocity (m/s) | Left velocity (m/s) |
| --- | ---: | ---: | ---: |
| 80 s | 0.105898 | 0.041856 | -0.004538 |
| 100 s | 0.095411 | 4.003748 | -23.410533 |
| 120 s | 0.080193 | -0.009808 | 0.087479 |

The 100 s Froude number is 24.5493. Adjacent saved times are quiet at this
location, but 20-second sampling cannot bound the spike's duration or exclude
other unsaved spikes. The local bed slopes across the bank; its 3x3 elevations
above the 220 m datum are:

```
8.297672  8.159331  8.385830
7.933329  7.857212  7.917255
7.714772  7.648177  7.682097
```

The failure is localized, not yet causally attributed to a particular numerical
operator. Next work should reproduce this shallow-bank momentum excursion with
denser bounded output and examine wet/dry reconstruction, source terms and
momentum limiting. Do not extend the same run, increase the speed tolerance,
flatten captured rock or add fine visible waves as a substitute for that check.
No later river is eligible yet.

Final regression verification: **27 tests plus 27 subtests pass**, covering
subgrid capacity, nested comparisons, mesh sampling, failure screening and
export geometry identity (`triangle-refinement-regressions.xml`). Map, native
cook executable and engine-linked archive hashes remain unchanged.
