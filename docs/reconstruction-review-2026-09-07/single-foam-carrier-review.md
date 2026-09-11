# South Fork: duplicate foam ownership correction

This continuation changes the isolated review's opt-in presentation only.
Production maps, captured/inferred terrain, collision, hydraulic fields and
raft forces are unchanged. The reconstruction queue remains incomplete.

## Actual cause and corrected test coverage

A non-emissive material comparison barely changed the white streaks. Inspecting
the live mesh sections then exposed a missed layer: `RapidFoamMesh` was still
visible above `SurfaceMesh`. The earlier single-carrier assertion excluded the
volume core, lip and roller but **did not exclude the rapid-foam sheet**. Its
historical passes must not be described as proof that only one foam response
was rendering.

At six seconds, `SurveyLitFoamProbe.log` reports the main section visible with
2,432 wet-alpha vertices, alongside a visible rapid-foam section with 152
vertices above half alpha. Both have 10,465 vertices. Removing the extra sheet
then removes the dominant hard white streaks in the actual fixed-camera view.

For the shared, surface-lit review carrier, `RapidFoamMesh` is now hidden and
its redundant full mesh uploads are skipped. Solver foam remains on the main
surface. The correction is reached only by the already opt-in, exact-map/field
shared-breaking path without a volume core; other river modes are unchanged.
`SurveyOneFoamCarrierCapture.log` verifies main section visible and rapid-foam
section hidden. The guided test now checks this layer too (report schema v2).

## Single-carrier foam shading

`-RaftSimSurveyLitFoamReview` requires `-RaftSimSurveyBreakingReview`. It changes
only existing dynamic material parameters, not assets: solver/drift emissive
glow 0; open-cell/bubble roughness 0.62/0.80; foam intensity 1.5; lace modulation
floor 0.45; patch outside floor 0.15. These keep aeration legible after removing
the duplicate sheet. No additional texture panner, foam mesh or wave is added.
The actual runtime parameter values are asserted by the guided test.

The read-only [serialized material audit](survey-material-audit.json) confirms
the existing graph and parameter names (329 expressions). The review material
SHA remains `415081c36b8a789b6af8a0e725810f1ba14c9a5ffcfb31c333005e360534cb2c`;
the saved map SHA remains
`28a26ed62d95403d964a23dcef00382dbbb063415b3ca85f87df36362b07c6cb`.

## Actual image comparisons

All side-camera bursts use focus station 9 m/lateral -7 m and 6/9/12-second
captures. The intermediate body-strength comparison applied the same final
three values through process-only console overrides at five seconds; those
values are now applied by the opt-in flag from startup.

Before, including the extra sheet:

![Duplicate foam sheet](C:/Users/salsi/repos/SmokeEmIfYouGotEm/unreal/Saved/Screenshots/SurveyFixedLitFoam20260907_000.png)

Single carrier, with its aerated shading restored:

![One carrier with lit foam](C:/Users/salsi/repos/SmokeEmIfYouGotEm/unreal/Saved/Screenshots/SurveyCarrierFoamBody20260907_000.png)

The result is softer, continuous foam shading rather than the hard bright
overlay. It is **not accepted as photorealistic**: the ridge is still angular,
the foam needs better three-dimensional surface detail, spray looks sparse,
and the scene remains plain diagnostic terrain. Three samples show animation
changes but cannot certify absence of intermittent artifacts.

## Scope and next work

Final build succeeds. The engine suite is **2/3 passed**, not all green:
captured-ground contact and candidate replay pass, while guided traversal fails
only its 5 m route-error assertion. The v2 report
`SouthForkGuidedTraversal_20260907_082956.json` reaches the outlet in 89.60 s,
with 5.846 m maximum tracking error, no missed ground queries or grounded
samples, 25.045 cm minimum sampled tube-to-ground clearance and 796 wet samples.
The strengthened one-carrier/foam assertion and all seven actual material
parameter checks pass, with up to ten persistent breaking sites. The failure
is retained in `engine-one-foam-carrier` and [the ledger](guided-review.json).
No controller threshold or collision behavior was changed to force a pass.

Clean 1280 x 720 offscreen performance, 20 s after 5 s warmup, is **20.933 ms
mean / 26.991 ms p95** over 956 frames. The preceding duplicate-sheet experiment
was 21.423 / 28.024 ms. This small difference between individual engineering
runs is not a statistically established speedup. Both still fail the frame and
solver budgets. No captures or builds ran concurrently with this measurement.
See [the new report](survey_performance_one_foam_carrier.json).

Keep both flags opt-in. Continue with crest silhouette/detail and runtime cost,
then repeatably validate the actual river reconstruction. Do not restore the
duplicate foam sheet to compensate for weak main-surface shading, or repeat
the old cook/import as substitute work. Full-route migration, identity/layout
verification, resolution convergence and later rivers remain outstanding.
No commit, push, asset save or new hydraulic cook was performed in this pass.
