# Standing-wave flume: first candidate

This separate synthetic environment is not a renamed hole or full-river scene.
It has a smooth 0.10 m submerged cosine bump centered at x=2.30 m, length 1.30 m,
inside a 6 x 1.6 m flume. Initial water surface is flat at 0.35 m; no wave is
sculpted into the water. Newly emitted fluid speed is configured at 3.2 m/s,
and the downstream level-drain threshold is 0.50 m. These are boundary settings,
not measured discharge or realized tailwater. Nominal approach Froude is 1.727.

Output: `tmp/water-feature-lab/standing-wave-v1`. Resolution 80, approximate
cell size 75 mm, 240 frames at 24 fps. The bump is poorly resolved vertically;
this run tests whether the boundary/obstacle combination creates a useful
candidate before any spatial-convergence or visual-accuracy claim.

`audit_water_feature_crests.py` samples five transverse rays at 95 stations,
retains raw median profiles and reports local maxima over time. A highest
maximum can change identity, so its range alone does not prove stationarity.
Inspect profiles and motion, and verify flow through the crest with the grid
section audit. No acceptance threshold is silently inferred from the result.

Research starting point: White et al. (2026), *Estimating discharge from undular
hydraulic jumps: Feasibility assessment based on flume experiments*, DOI
10.1029/2025WR040997, available through the USGS/US Forest Service publication
records. Their abstract distinguishes a stationary wave train in near-critical
flow from generic rapids. This experiment does not reproduce their measured
flume dataset, and has not been validated against it. No external media or
datasets are bundled; laboratory geometry is authored here.

https://research.fs.usda.gov/treesearch/80539

Status: candidate only. No stationary wave, physical accuracy, visual accuracy,
or real-time performance is yet accepted.

## First bake outcome

The 240-frame bake completed in 126.31 s. Thirteen profile samples spanning
frames 168..240 show no coherent useful crest: the highest small maximum
switches between x=1.6 and 4.1 m, with elevations only 0.517..0.522 m.
Frame 192's section audit estimates negative bulk flow at every section
(approximately -0.04..-0.09 m/s), contradicting the intended forward stream.
The inlet is submerged by the filled flume. An emission velocity is not a
prescribed velocity condition on liquid that already occupies the source.
Rendered foam does not establish ongoing wave production. Rejected as a
standing-wave demonstration; keep the failed evidence, do not encode as success.

## Second candidate

`standing-wave-v2` adds a 0.45 m high approach, descending from x=0.6 to 1.5 m,
while retaining the downstream 0.10 m bump. Inlet emission is 2 m/s, depth
0.35 m; level-drain threshold is 0.30 m. This supplies gravitational head and
keeps the inlet above the initial pool instead of relying on injecting
momentum into already-filled liquid. Still 80 cells / 240 frames. Measure the
realized flow and crest stability after baking; neither is assumed to pass.

Second bake finished in 149.07 s with all data/mesh/particle caches complete.
Four samples (frames 168, 192, 216, 240) now have positive bulk downstream flow
at all measured stations. At the bump section x=2.25 m, estimated bulk speed
is 0.82..1.00 m/s; near-surface speed 0.79..1.09 m/s. Thus the drowned-inlet
failure of v1 is corrected, but actual speeds still differ from configured
emission speed. The section-flux consistency issue remains (roughly 0.38 m³/s
upstream versus 0.48..0.63 m³/s in the downstream sample set).

All thirteen profile samples have a local crest near the bump, but its position
moves approximately x=2.05..2.40 m and elevation 0.442..0.489 m. The global
highest-peak tracker sometimes selects a different downstream crest, so its
2.05..4.50 m range is not the motion of one identified wave. Inspecting the
full peak lists was necessary to avoid that false interpretation.

Frame 192 is rendered in `standing-wave-v2/preview/frame_0192.png`: a small
crest exists, but substantial inherited whitewater obscures its shape and the
surface lacks resolved detail. Not accepted as an accurate standing wave;
no standing-wave animation delivered yet. Next: resolve the bed bump with a
finer grid, obtain a matched velocity calibration, evaluate startup versus
late crest motion, and isolate the effects of downstream level and secondary
particle lifetime. Preserve both candidates rather than overwrite evidence.

Both standing-wave bakes and their audits/one-frame previews are terminal.
There is no live bake or render to wait for at this handoff.

## Refinement in progress

`standing-wave-v3-r160` repeats v2's geometry, boundary settings and 240-frame
duration with resolution 160 (37.5 mm cells). This is a spatial sensitivity
check, not a changed physical scenario. A matching 12-frame free-fall readback
calibration in `velocity-calibration-160-v1` completed: fitted acceleration
-10.0261 m/s², gravity error 2.237%, quadratic position residual 1.059 mm,
grid/particle discrepancy 1.585%; all within its diagnostic tolerances. This
does not establish wave or mass-balance accuracy. It explicitly uses FLIP 0.95.

The coarse v2 scene is also being rendered as a 36-frame motion sequence using
the corrected per-particle-size native-point representation. Its persistent
crest instability is not hidden or labeled as acceptance. Both active outputs
must be checked before starting additional bakes/renders.

The section auditor now additionally clips its reconstructed-mesh wet mask
against the known authored bed; it retains the old un-clipped results for
comparison. At v2 frame 192, downstream x=5.25 m flux changes from 0.6142 to
0.5487 m³/s, while x=0.75 m remains 0.3838 m³/s. Thus some discrepancy comes
from the reconstructed skin extending into the solid bed, but this does not
explain all of it. Neither value is an exact solver mass budget. A rendered
mesh extending into a collider does not by itself prove particles penetrated
that collider. Keep these distinct when assessing visual/physics consistency.
Evidence: `standing-wave-v2/sections-bed-clipped.json`.

## Coarse motion clip delivered; finer bake still active

`docs/water-feature-lab/standing-wave-prototype-v1/feature.mp4` and `feature.png`
show v2 frames 168..238 at stride 2, 12 fps, three seconds at normal speed.
All 36 APNG frames match source images exactly and all 36 MP4 frames decode;
no adjacent duplicate frames. This is repeating playback, not a seamless
simulation loop. Beginning/middle/end rendered frames were inspected.
The low unsteady crest, excess foam coverage and coarse surface remain visible.
This is a standing-wave *candidate*, not a demonstrated stable accepted wave.
MP4 SHA256: `5c1b8ae1e18e569359e988b0372674d133bd68147df157507c250ad65a7ec13c`.

Current live work: v3-r160 bake, exec session 88203 / Blender PID 14448.
Resume that session or inspect that exact process/cache; do not launch a duplicate.
Its calibration is finished. The v2 animation render/encode and particle-size
preview are finished. After v3 finishes, verify its bake receipt, run the crest
and bed-clipped section audits with `velocity-calibration-160-v1/calibration.json`,
then render actual late frames. Do not infer success merely from a completed bake.

## Matched early-frame resolution comparison

While the finer bake was confirmed live, already-finished frame 96 was read
without modifying its blend/cache. Matching v2/v3 previews use the same camera,
16 samples, 800 px width and per-particle sizes at t=3.9583 s. This is an early
transient comparison, not the late stationarity test.

- Coarse: 528,569 foam / 218,282 bubble particles; reconstructed volume 3.20825 m³.
- Fine: 3,548,006 foam / 2,614,645 bubble particles; reconstructed volume 3.57526 m³.
- Thus foam count rises 6.71x and bubble count 11.98x with unchanged render radii.
  The finer full render is more uniformly white. It is NOT a demonstrated
  visual improvement or spatially converged air-entrainment result.
- Mesh bottom extends to -0.05375 m in coarse versus -0.00222 m in fine, relative
  to the authored downstream floor z=0. This shows improvement in this one
  reconstructed-boundary measure, not a complete collision proof.

Blender's secondary-particle controls sample per generating cell (official
manual: https://docs.blender.org/manual/en/5.0/physics/fluid/type/domain/liquid/particles.html).
With different cell counts, fixed visible radii cannot be presumed to give
resolution-independent foam coverage. Actual emission/lifetime, air-volume
representation and optical coverage need a separate convergence assessment;
do not silently divide counts until the picture looks desirable.

`liquid-only-preview/frame_0096.png` hides secondary particles solely to inspect
the unchanged fine water surface. The image and report explicitly flag this
diagnostic; it is not a final clear-water replacement for a breaking wave.
The completed coarse clip remains unchanged. The fine bake is still active.

The early finer section audit (`early-sections.json`, frame 96) still estimates
0.5006 m³/s near x=0.75 versus 0.7099 m³/s near x=5.25. This early result neither
closes the flow budget nor proves a late-state failure; compare storage change
and the finished run. The finer mesh's better bed boundary alone is insufficient.

## Spray phase material correction

The renderer now assigns the water dielectric (IOR 1.333) to airborne spray
instead of the opaque-white foam material, in both sphere-point and instance
paths. Foam and unresolved bubble scattering remain explicit approximations.
This changes no cached positions, velocities, counts or liquid geometry.
The frame-96 coarse `phase-material-preview` completed and was visually checked
against the prior matched preview. Airborne dots no longer all use the same
opaque-white response as foam. This is a material correction, not validation
of entrainment or a solution to excessive foam coverage. Prior delivered clips
are preserved; a future animation must exercise the corrected renderer.

Handoff: fine bake still confirmed running as session 88203 / PID 14448; latest
observed mesh count exceeded 158 of 240, and CPU time continues increasing.
All early diagnostic renders/audits are terminal. The boulder-pillow scene is
prepared and initial-exclusion-tested but deliberately not baking concurrently.

## Next boundary test and serial bake queue

`standing-wave-v4-low-tail` is prepared but NOT baking: it keeps the v2
resolution/geometry/inlet and lowers the drain threshold to 0.05 m. It tests
whether the existing downstream boundary drowns the bump. Actual water depth
and velocity must be measured; the setting alone is not a successful condition.

The finer bake remains session 88203 / PID 14448. A one-shot serial runner,
session 26447, is waiting for that process to exit. It checks the completed
fine bake receipt before starting the prepared boulder case. Do not manually
start a duplicate boulder bake while this runner is live. Its bake script refuses
existing cache files or a previous receipt, preserves partial failures, and
does not erase any cache. No recurring automation has been changed.

The crest audit now separately reports the highest local maximum within the
fixed bump footprint x=1.65..2.95 m, while retaining whole-flume maxima and raw
profiles. This avoids treating a far-downstream crest as the same wave, but
can still switch between peaks in the fixed zone; no automatic acceptance.
The section audit additionally reports bed-clipped Froude estimates.

## Fine run complete: not accepted

The v3-r160 bake completed all 240 frames/data/mesh/particles in 1485.47 s.
Session 88203 is terminal. Thirteen late profiles have a bump-zone local peak,
but its x position spans 2.05..2.65 m (0.60 m range), with z=0.4398..0.4672 m.
This is not the desired stable isolated standing wave. The full preview still
has excessive whitewater coverage; no replacement animation is delivered for
this failed refinement merely because it has a finer mesh.

The added approach sections explain the next boundary test. At x=1.125 m,
four late bed-clipped Froude estimates are 1.40..1.44. By x=1.35 m they are
0.69..0.88, and at x=2.25 m only 0.58..0.64. The fast shallow approach flow has
already slowed before reaching the bump, consistent with excessive downstream
backwater for this target. This is a diagnostic inference, not a calibrated
hydraulic-jump experiment. Downstream section flux still disagrees with upstream
(approximately 0.61..0.65 versus 0.49..0.50 m³/s), so conservation remains open.

Evidence: `late-crests.json`, `late-sections.json`, `late-preview/frame_0168.png`.
The prepared 0.05 m drain variant tests the inferred cause at lower cost before
another high-resolution run. The boulder bake has now started via serial runner
26447; inspect its handle rather than treating this old fine bake as live.

## Lower-tailwater trial completed

The v4-low-tail 240-frame bake completed in 148.66 s; runner 56278 is terminal.
The peak now remains within x=2.35..2.55 m (0.20 m range) over thirteen late
samples, versus the broad movement in prior trials. Peak elevation is
0.2687..0.2922 m. Estimated Froude is 1.82..1.94 at x=1.95, 1.17..1.23 at
x=2.25 and approximately 0.98..1.02 at x=2.70. Faster flow now reaches the
bump, supporting the boundary diagnosis. This is a promising candidate, not
an accepted wave: the downstream depth is only about 0.08..0.10 m at 75 mm
cell size, so section estimates are poorly resolved and remain uncertain.

The frame-192 preview was inspected; a low crest is visible and whitewater
coverage is much lower (153,633 foam particles) without thinning the renderer's
particles. This follows a changed flow boundary, not proof of correct foam
production. Next: refine this boundary configuration and examine motion,
bed contact and mass balance. Do not repeat the completed v3 high-tail bake.

## Matched lower-tailwater refinement

`standing-wave-v5-low-tail-r120` preserves v4's physical settings and raises
resolution from 80 to 120 (cell size 75 to 50 mm). The corresponding free-fall
calibration passed: gravity error 0.416%, maximum quadratic residual 0.891 mm,
grid/particle peak disagreement 1.584%. This calibrates velocity units only.
The prepared-scene bake finished in 749.64 seconds; session 39269 is terminal.
Late crest/section audits also finished (session 74747). No v5 result is accepted.

The 13 late bump-zone peaks span x=2.25..2.50 m (0.25 m), versus 0.20 m in
the coarser v4. Peak z is 0.2400..0.2713 m, versus 0.2687..0.2922 m. Estimated
bed-clipped Froude at the bump x=2.25 is now 1.90..2.04, versus roughly 1.2
in v4, so the hydraulic quantities are not converged. Upstream bed-clipped
section flux is 0.456..0.477 m³/s; downstream at x=4.5 it is 0.499..0.590 m³/s.
The finest tested low-tailwater case still fails a demonstrated mass balance.

The frame-192 full render was inspected. Foam count rises from 153,633 in v4
to 793,010 in v5 with unchanged physical rendering radii, again increasing
opaque coverage. The mesh also extends about 61 mm below the authored flat
floor somewhere in the domain. More geometry is not evidence of a solved
shoreline/bed boundary or improved optics. Do not make v5 the accepted wave
or duplicate its bake; resolve boundary/mass and secondary-phase behavior.
