# Shared fine crest reconstruction

September 7, 2026, local time. Opt-in South Fork registered-rock candidate;
not production promotion or photographic acceptance.

## Measured problem

`stateful-crest-sampling-audit.json` compares the existing CPU support crest
against its original two macro triangles at quarter-cell positions, including
the same interpolated shoreline weight. At world time10.0666s, six persistent
sites and2,984 all-wet cells produce74,600 samples (shared cell edges counted
again). Maximum error is0.184039531m, RMS0.004723651m; the largest sampled
absolute crest is0.545408249m. Worst point is station8.250305/lateral−0.75m.

This supersedes the earlier inference from the initial strongest-site log
(0.022m): that initialization value is not the mature maximum of all sites.
The audit isolates the shared analytic component, not the hydraulic mean,
render-only plunge pocket/boil or persistent GPU perturbation. It does not
measure photographic wave heights. Source amplitudes were not changed.

## Implementation

Flag`-RaftSimStatefulCrestReview` requires the registered-rock map and existing
`-RaftSimSurveyBreakingReview -RaftSimStatefulDetailReview` gates; use the
existing`-RaftSimSurveyLitFoamReview` as before. It implies foam/motion/GPU
carrier/fine-mesh review. Other maps and the prior comparison assets are unchanged.

- Atlas extends from161×260 to161×262 float4 texels. Two metadata rows contain
  river origin/spacing/relief scale and the exact accepted physical support sites.
- Previously unused W values store the exact coarse crest displacement and
  shore weight. The fine vertex substitutes the continuous crest for that coarse
  component once; it does not add a second physical wave or surface.
- `RaftSimCrestSurfaceSample.ush` mirrors the existing depth-scaled CPU crest,
  curved lateral profile, toes, tail train, local/global overlap caps and their
  analytic derivatives. World slopes use the actual triangle XY Jacobian.
- A vertex interpolator keeps the derivative site loop out of the pixel shader.
  The corrected version adds full crest slope to crest-free macro normals; this is still
  smooth shading over a finite triangle mesh, not an exact continuum normal.
- Current and previous-render-frame atlases both contain their respective site
  records. Existing history copies include both new rows; no previous-state
  evaluation against current site parameters. Explicit lattice reset remains.
- Bounds add a conservative two-maximum-crest-height margin. Legacy-height
  sites or atlas capacity overflow are rejected with an error and the original
  coarse surface is retained, not silently truncated. No new runtime readback.
- New material retains the single transported coverage/color/roughness/opacity
  graph from FoamReview. Neither native hydraulic solve nor raft amplitudes changed.

Initial material`M_RaftSim_LiveRiverSurface_StatefulCrestReview` SHA256 (superseded below):
`22ee21bb778a01b912f0b97c6b6793d58644d9b577a9d6edde8873b04a6534fc`.
Retained FoamReview SHA256:
`9cd016469d473916bf9758c8e22568ec14fe4b36ff2a6e18d94457e028190527`.

## Validation and remaining limits

Native build8165:28 actions,91.34s, exit0. Actual-GPU test run15804:
`engine-stateful-crest/index.json`,12 successes,0 warnings/failures.
New test independently calls the existing CPU support implementation, including
overlapping local/global caps, changed site positions, zero sites, shore weights,
both triangle halves and rotated/sheared world coordinates.1,020 GPU queries:
maximum height error0.000078606cm, slope error0.0000189713, coarse vertex change0cm,
recovered subgrid difference21.8037663cm. Existing transport, dry shore, resolve,
history and original macro triangle tests also pass. This is not a physical
fluid-model validation or proof of geographic accuracy.

Material setup40873 exited0. Editing the live normal input array produced a
transient compile warning about its then-unconnected CrestSlope input. Subsequent
saved-asset graph audit39538 exited0 and passed; actual game capture88373 exited0
with no material fallback/compile warning, atlas161×262 and correct candidate MID.
Both history objects report948 rendered-frame snapshots at teardown.
`stateful-crest-graph-audit.json` verifies persisted current/previous bindings,
vertex-only slope, two history switches and unchanged three foam property graphs.

`SurveyStatefulFineCrestBank_000..011.png` are actual game captures. Frame11
was inspected against the baseline audit image: sharper/localized crest shape
is now sampled, but the broad white face remains sheet-like and the foreground
rock silhouette remains angular. Sparse images are not long-animation acceptance.

Clean performance run95655, exit0:
`survey_performance_registered_stateful_crest.json`.1280×720 at87%screen percentage,
RTX3060Laptop, Development offscreen,5swarmup/20smeasurement, no concurrent build
or capture. Mean14.225076ms, p9519.356300ms, GPUmean6.886099ms, solvermean8.985214ms;
one33.906002ms wall-clock hitch. Prior FoamReview mean13.964790/p9519.026800ms.
No speedup claimed; original16.667ms frame and1.6ms solver gates STILL FAIL.
Not packaged-release qualification.

## Close-up normal correction

Paired station8/lateral0 captures33875 (both processes exited0):
`SurveyCrestFocusBaseline_000..002` and`SurveyCrestFocusReconstructed_000..002`.
Frame2 of each inspected. The initial fine-crest candidate exposed a sharper
diagonal reflection crease: subtracting a piecewise triangle slope from an
already-smoothed full macro normal is not a consistent smooth-shading normal.
Do not accept that first version as the final reflection correction.

The existing wet-neighbour normal pass now derives a crest-free mean/pocket
normal in this opt-in mode, and the vertex shader adds the FULL continuous
crest slope. Positions are unchanged from the first candidate. The independent
GPU test now checks full and correction slopes, not just the correction.
An initial compile attempt incorrectly referenced the function-local wet mask
from UploadMacroSurface and failed; no such reference remains. Build23536 then
succeeded (five actions24.55s), using the existing scoped normal pass.

Bounded material repair54542 saved new SHA256
`52194d117dd2f21b55df3dd160526d05948b6bb564346ebeb1c947d5f858438f`.
Report`stateful-crest-normal-repair.json` preserves old/new code and hashes.
Its process exited1 despite a saved report and no Python/material compile errors;
do not call that a clean process pass.

Fresh verification58665 exited0: `engine-stateful-crest-normal/index.json`,
16 successful tests (15 clean, one retained `r.MotionVectorSimulation`
render-thread warning in WaterSurfaceRenders), zero failures. Expanded GPU
fixture now has1,404 queries; maximum height/slope errors and recovered height
remain as above. Existing registered-rock replay and three legacy render/data
tests also pass.

Sequential final verification83168 completed all three processes with exit0:
saved graph audit (`stateful-crest-normal-graph-audit.json`), actual capture
`SurveyCrestNormalFinal_000..011`, then a separate clean performance run.
Capture frames2 and11 inspected, no material compile fallback or rejected crest
sites logged. The normal decomposition is now consistent, but a visible crest
ridge remains and the aerated face is STILL too smooth/sheet-like; do not claim
all reflection stripes are eliminated or that this is photographic acceptance.
Spray positions differ between the separately started runs, so these images
are not a deterministic pixel-difference test or a continuous-motion proof.

Final same-protocol performance:
`survey_performance_registered_stateful_crest_normal.json` mean14.350345ms,
p9519.443399ms, GPUmean6.904082ms, solvermean8.930903ms, one35.110001mswallhitch.
The original frame/solver budgets still fail. No performance improvement or
release qualification claimed. Native solver archive and both original/registered
review maps were SHA256-checked unchanged in this pass.

Next: continuous motion and remaining ridge/sheet appearance,
resolve the still-sheet-like aerated face/raft support perturbation difference,
verify geographic identity and rock silhouette, robust traversal and solver cost.
All later ordered rivers, other-scene/crew/normalization/release/final-commit work
remain open. Do not repeat unchanged tests as a substitute for these requirements.
