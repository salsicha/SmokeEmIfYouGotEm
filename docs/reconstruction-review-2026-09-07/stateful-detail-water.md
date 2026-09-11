# Stateful GPU detail water — foundation and opt-in scene integration

September 7, 2026. The previous `ComputeCoupledLocalFluidHeightfieldMeters`
implementation is procedural noise evaluated from coordinates and time. It
does not retain and evolve a fluid state. It remains unchanged in the scene;
this work begins the requested stateful detail simulation rather than claiming
that the existing noise function already satisfies that request.

## Implemented

New runtime module `RaftSimWaterDetail` loads at `PostConfigInit` to register its
compute shader. It is engine-independent apart from Core/RHI/RenderCore; it does
not spawn actors, load terrain, alter materials or replace the native FV solver.

- Persistent GPU buffer contains surface-height perturbation, x/y perturbation
  momentum and transported foam density. State survives separate render graphs.
- Mean-flow input contains depth, horizontal velocity and aeration source.
- First-order finite-volume linear shallow-water perturbation flux carries
  gravity waves over mean flow. This is not Navier–Stokes, overturning geometry,
  surveyed wave shape or a replacement for the existing mean-water surface.
- Foam uses mean-current upwinding, independently of gravity-wave speed, plus
  analytic source/decay integration. It is density, not clipped [0,1] coverage;
  convergence may compress it above one. Shading must convert density to coverage.
- Dry cells and closed domain faces transmit no height or foam flux. A local
  hydrostatic pressure-source balance prevents spurious motion over depth steps.
- A two-dimensional CFL limit of 0.45 rejects excessive timesteps rather than
  clipping height. Sizes are bounded to 512×512. Reset, resizing, cell-size
  changes and boundary-mode changes cannot happen implicitly on persistent state.
- No per-step readback is required. Readbacks in this pass are test-only.

Files: `unreal/Plugins/RaftSim/Source/RaftSimWaterDetail/` and
`unreal/Plugins/RaftSim/Shaders/Private/RaftSimDetailWater.usf`.
Tests: `RaftSimStatefulDetailWaterTest.cpp` in RaftSimAutomation.

## Actual GPU evidence

Final report: `engine-stateful-detail-water-captured/index.json` — **5 tests
passed**, no warnings or failures. Active RHI is D3D12 SM6 on NVIDIA GeForce
RTX 3060 Laptop GPU (the generic device metadata also lists the AMD integrated
GPU; selected-adapter lines in the actual log identify the active device).
The tests explicitly reject NullRHI for GPU evidence.

1. Input and two-dimensional CFL validation pass.
2. Two consecutive 60-step graphs preserve state; implicit reseed and rescale
   are rejected. A 2 m/s current carries foam **2.000000 m** in one simulated
   second, rather than moving it at the wave phase velocity. Foam integral
   error is -1.09642e-6 cell-density units; height integral error 1.38628e-8
   cell-metres. Initial localized crest propagates without amplitude growth.
3. Uneven-depth resting perturbation, slanted shore and dry island: maximum
   spurious momentum **0**, height error **0**, dry-cell state **0** after one
   second. Foam source/decay error is 2.08616e-6.
4. Actual registered-rock candidate mean flow, mapped through the built runtime
   adapter: 2,147 wet cells out of 4,096, maximum sampled current 5.426266 m/s.
   A synthetic perturbation of at most 5 mm remains bounded after two seconds:
   maximum 3.52177 mm, foam density [0,1.498459], finite state and no dry-cell
   water/foam. This uses a frozen mean field and a synthetic seed; it is not yet
   continuously coupled to the running scene. Aeration uses an explicitly
   uncalibrated Froude-based source for this test.
5. Existing SouthForkRegisteredRockCandidateReplay passes alongside the new
   tests. Native solver code/archive and both review maps are unchanged.

## Failures found and corrected

- Initial compile caught an incorrect shared-reference pointer call; corrected.
- RHI/RenderCore calls in the automation module required explicit link
  dependencies; corrected. An unrelated existing D6 runner float warning remains.
- Initial shader startup (`StatefulDetailWaterV1.log`) failed UE's shader-root
  parser when several scalar root parameters shared one declaration. Individual
  declarations compile successfully; failed startup log retained.
- Initial uneven-depth GPU test **failed**: artificial perturbation momentum
  0.02792478 m²/s and height error 0.00893691 m. Dry cells remained zero.
  `engine-stateful-detail-water-shore-before` retains that failure. Balancing
  face pressure with the local hydrostatic source fixes it without changing
  thresholds. `engine-stateful-detail-water-shore-balanced` has 3 passing tests.

## First visible integration (September 7 continuation)

`URaftSimStatefulDetailComponent` now supplies a fixed, world-registered 64 m
square crux window (128² cells at 0.5 m) to the existing carrier. It is selected
only on `SouthForkRegisteredRockPlayable`, with the exact registered-rock field
package and `-RaftSimSurveyBreakingReview -RaftSimSurveyLitFoamReview
-RaftSimStatefulDetailReview`. Neither review map nor the original V2 material
was changed. Production remains unaffected.

The GPU resolves height in metres, two surface slopes and density-to-coverage
foam into a float4 UAV texture. Displacement is vertical WPO on the same mesh;
slopes modify its normal and transported foam modifies color/roughness. There
is no additional sheet, runtime readback or camera-triggered reset. Detail
tapers to zero on dry cells and at the fixed window edge. The material is
`M_RaftSim_LiveRiverSurface_StatefulDetailReview`; its default enable is zero.
See `stateful-detail-material-setup.json` for immutable asset hashes.

Time-continuous, source-weighted pressure fluctuations now excite the persistent
wave state. The 0.06 m pressure head and Froude-based source are empirical,
uncalibrated choices, not measured wave heights. A pressure forcing is not
rendered noise height. Simulation time accumulates actual successful substeps,
and implicit world-origin changes are rejected. Live flow updates run at 8 Hz;
the simulation advances with bounded CFL steps, retaining rather than dropping
backlog. This is a fixed crux window, **not** a completed moving-window solution.

Actual capture `SurveyStatefulDetailBank_000.png` through `_011.png` was taken
with the same fixed station/lateral focus as the registered-rock bank baseline.
Runtime logged 1,199 completed steps at 10.010 s and 0.001291 s backlog. There
were no water shader/dispatch errors. Existing EditorToolset `AgentSkill` and
ToolsetRegistry `PythonTestRunner` startup errors remain unrelated and open.
Inspection of frame 11 shows **more homogeneous white coverage**, not accepted
whitewater improvement; the foreground angular rock silhouette also persists.
The burst spans only about 1.1 game seconds and is not long-duration animation
acceptance. Do not promote this result merely because the integration works.

`engine-stateful-detail-water-resolve/index.json`: **7 passed**, including the
five earlier tests. New pressure-excitation test produces maximum 0.0470908321 m
relief from zero initial state, identical results across one versus two render
graphs, and zero dry state. Disabling the source gives exactly zero turbulence.
New texture-readback test checks the independent CPU values for height, tapered
slopes and density conversion: maximum RGBA error 5.96046448e-8, dry/edge output
exactly zero. These are actual D3D12 GPU tests, not visual acceptance.

First clean integration timing **regressed**: V2 matched baseline p95 18.908 ms
versus stateful p95 30.564 ms, with 34 wall/frame hitches over 33 ms. Mean frame
time became 16.237 ms; GPU mean was only 6.527 ms. Both runs remain failed against
the existing frame and solver gates. Reports:
`survey_performance_registered_detail_v2_baseline.json` and
`survey_performance_registered_stateful_detail.json`. An earlier baseline used
the wrong spelling of the V2 flag and actually loaded SurfaceLitReview; retain
`survey_performance_registered_detail_baseline.json` as unmatched evidence,
not the V2 comparison. No screenshots or concurrent compilation during timing.

The first implementation repeated costly world-to-river inversions for every
sample at every update. The follow-up caches the fixed coordinates and local
basis once, retaining exactly the same live flow sampling and update frequency.
Added cached-versus-world sampling checks to the captured-flow GPU fixture.
Build succeeded. `engine-stateful-detail-water-cached/index.json`: **7 passed**,
including cached-versus-world depth/velocity agreement within 1e-6.
Clean cache timing (`survey_performance_registered_stateful_detail_cached.json`):
**13.868 ms mean / 19.016 ms p95**, zero >33 ms hitches; matched V2 baseline
13.877 / 18.908 ms. GPU mean 6.527 versus baseline 6.440 ms. Live flow preparation
averaged **0.414 ms**, maximum 0.709 ms, over 184 updates; 0.001602 s backlog at
24.485 s. This removes the *new* regression, not the pre-existing performance
failure: solver still averaged 8.880 ms against 1.6 ms, and frame p95 remains
above 16.667 ms. No quality, resolution or update-frequency reduction.

The next code change replaces the runtime blanket-Froude source with
`FRaftSimDetailEntrainment::Build`. It requires local convergence/deceleration
and nearby Froude activity; a dry neighbour is not a fabricated stationary
water sample. Wet one-sided derivatives preserve behavior near banks. Thresholds
0.65–1.1 Froude and 0.05–0.65 /s are stated empirical settings, not calibration
to footage. Only the source W channel changes; density is still transported by
the GPU. `engine-stateful-detail-water-entrainment/index.json`: **8 passed**.
The added source fixture gives exactly zero in uniform fast water (including
dry shore/island), source maximum 1 at the decelerating transition, zero dry
source, zero beyond the transition and zero error under 90-degree rotation.
`SurveyStatefulEntrainmentBank_000.png` through `_011.png`: inspected frames
0, 6 and 11. Runout whitening is reduced relative to the blanket-Froude source,
but the main crest is still too homogeneous and the angular rock edge remains.
No claim of continuous-animation acceptance from three inspected frames.
Latest clean timing (`survey_performance_registered_stateful_entrainment.json`):
**14.140 ms mean / 19.229 ms p95**, zero >33 ms hitches, GPU mean 6.530 ms,
solver mean 8.992 ms. Source/preparation averages 0.752 ms (max 1.026 ms).
Backlog 0.007600 s at 24.458 s. Both unchanged frame/solver gates still fail.
The live component now also refuses initialization without a real live field
and coordinate map, and disables itself if that field is lost instead of
accepting the adapter's diagnostic flat-water fallback.

## Conforming fine-geometry experiment

Added `FRaftSimSurfaceRefinement` and `UpdateSurfaceCarrierMesh` to the existing
water actor. Opt-in `-RaftSimStatefulDetailGeometryReview` requires the existing
stateful review selection; no production setting or material asset changed.
Two local red/green subdivision levels refine the river-coordinate [-32,32]²
crux to 0.375 m grid edges (0.5303 m triangle diagonals). Neighbouring triangles
are stitched to split edges, not left with T-junctions. Distant geometry remains
coarse. Original piecewise-linear positions, normals, colors, flow UVs and wake
data are interpolated from cached midpoint parents; there are no additional
hydraulic samples and no second sheet. Topology is rebuilt only when the source
lattice changes, not on each refresh; the GPU fluid state remains independent.

`engine-stateful-detail-water-refinement/index.json`: **9 passed**. The new
conforming test checks edge incidence, winding, conserved area and affine
data reproduction: area 144 m², plane error 4.44e-16 m, color error 6.52e-9,
maximum crux edge 0.530330086 m and 80 untouched distant source triangles.
`engine-water-refinement-legacy-regression/index.json`: **3 passed**, including
the actual dev-tank WaterSurfaceRenders test, linear water data encoding and
texture precision. Editor build passed (21 actions, 82.45 s).

Actual `SurveyStatefulFineGeometryBank_000..011.png` captured with matching
flags/fixed-bank camera; frame 11 inspected. Runtime confirms **38,721 render
vertices / 76,992 triangles** in the same section versus 10,465 hydraulic
vertices / 20,480 triangles. At a subsequent world-lattice recenter the refined
count becomes 38,980 / 77,510. Main crest still looks sheet-like and the rock
edge remains angular; small-amplitude detail on a finer carrier is not a
reconstructed one-metre breaking wave. No visual acceptance from this capture.

Clean `survey_performance_registered_stateful_fine_geometry.json`: mean frame
**15.418 ms**, p95 **22.226 ms**, no >33 ms hitches; GPU mean 6.635 ms, render mean
7.904 ms / p95 11.359 ms, solver mean 8.916 ms. Pre-refinement source variant was
14.140 / 19.229 ms. Fine CPU interpolation and procedural-buffer updates add
cost; this experiment remains opt-in and **fails** the unchanged budgets.
Do not promote it or reduce the sampled hydraulic resolution to hide that cost.
The next fine-surface architecture should interpolate the same coarse authority
on the GPU, retaining the tested conforming topology but avoiding fine CPU
vertex-buffer reconstruction each refresh.

## GPU-interpolated fine carrier

The CPU cost above is now addressed by an additional isolated mode:
`-RaftSimStatefulGPUCarrierReview` (requires the same registered-rock stateful
review flags and implies its conforming geometry). It retains the same fine
triangles but uploads only a 161×260 float4 atlas for the 10,465 coarse source
vertices. Four bands contain world position, world normal, linear hydraulic
color/coverage, and flow/wake UV data. UV3 holds coarse-grid coordinates. The
fine mesh is uploaded only when its lattice changes; the live coarse fields
continue to refresh at the existing cadence. No freeze or reduced resolution.

`RaftSimMacroSurfaceSample.ush` uses the original (A,C,B)/(B,C,D) barycentric
interpolation. It explicitly does **not** use bilinear filtering of nonplanar
water cells. Material `M_RaftSim_LiveRiverSurface_StatefulGPUCarrierReview` was
created from the prior opt-in material; original maps/material unchanged.
`stateful-gpu-carrier-material-setup.json` records rewired inputs and hashes.
Its WPO places the fine mesh on the current macro surface plus persistent
detail; normals, foam, flow and wake data consume the same uploaded authority.
Macro colors remain float linear values (no accidental sRGB conversion).

New `URaftSimWaterCarrierMeshComponent` uses live coarse hydraulic bounds plus
a one-metre vertical detail margin for culling; it does not use the immutable
mesh's startup height. Ordinary mode retains inherited bounds behavior. Actual
saved-map capture logs `dynamic_bounds=1`. A bounds-reset test covers returning
to ordinary mode. Missing candidate material disables the GPU-only mesh path.
The optional material's normal expression guards zero-length normals when the
atlas is absent; see `stateful-gpu-carrier-safe-default.json` for that bounded
repair of the newly created asset and its exact before/after code.

`engine-stateful-gpu-carrier-bounds/index.json`: **14 successful tests**, one
with a warning, zero failures. The warning is the existing engine render-thread
read of `r.MotionVectorSimulation` during WaterSurfaceRenders, not suppressed.
The new shared-HLSL GPU fixture checks 128 queries over all atlas bands, both
triangle halves, diagonal and clamped borders: max RGBA error **2.38418579e-7**;
a bilinear substitute differs by **0.25**, so the fixture distinguishes them.
Live bounds and the previous numerical/geometry/rendering tests also pass.
Final `engine-stateful-gpu-carrier-final/index.json` repeats all fourteen
successfully after the bounds-reset/missing-material guards (13 clean, one
with the same retained engine warning). The safe-default material repair
compiled and saved without errors; its active-data formula is unchanged.
An earlier bounds compile failed on a parameter shadowing USceneComponent::Bounds;
renamed the parameter and rebuilt successfully. The preceding 13-test report
`engine-stateful-gpu-carrier` predates that corrected bounds build; keep this
distinction rather than counting it as bounds coverage.

Actual `SurveyStatefulGPUCarrierBank_000..011.png`: same fixed bank camera,
frame11 inspected. No disappearance in that frame; same fine count and coherent
macro profile. Main crest still sheet-like; shoreline rock edge still angular.
This is not a long-animation acceptance or a measured photographic match.

Clean `survey_performance_registered_stateful_gpu_carrier.json`: mean frame
**14.055 ms**, p95 **19.203 ms** versus CPU-fine 15.418 / 22.226 ms. Render mean
7.062 ms / p95 8.044 ms; GPU mean 6.598 ms. One wall-clock hitch at 33.987 ms;
frame-metric maximum 28.033 ms. Solver mean 8.905 ms. Same fine geometry and
coarse update rates, one lattice recenter from 38,721 to 38,980 render vertices.
This removes the recurring fine CPU-update regression, not the original failed
16.667 ms frame and 1.6 ms solver gates. No promotion or full acceptance.

## Previous-render-frame texture history (opt-in)

`-RaftSimStatefulMotionReview` requires the same registered-rock/detail/breaking
review gates and implies the GPU carrier. It selects the separate
`M_RaftSim_LiveRiverSurface_StatefulMotionReview`; the GPU-carrier baseline and
both review maps remain byte-identical. No shipping scene is promoted.

`FRaftSimWaterTextureHistory` copies each current float4 texture into a separate
previous texture at `FCoreDelegates::OnEndFrameRT`, after rendering, rather than
at physics-step cadence. This handles frames with no hydraulic update and frames
with several detail steps. Startup seeds the current state. Recreating the macro
lattice explicitly seeds its new geometry rather than interpreting old indices
as motion. That reset is not spatial history remapping or seamless recentering
acceptance. EndPlay/reconfiguration unregister the render-thread callbacks.
Neither texture requires runtime readback or a second visible water surface.

The material uses `PreviousFrameSwitch` on macro world-position and detail
height samples. It enables translucent depth/velocity output, not depth-only
camera velocity. `create_stateful_motion_review_material.py` records the exact
graph rewires and unchanged source hashes in `stateful-motion-material-setup.json`.
New material SHA256: `a142f3362a039a4a03b8060634a50eb2579b2689339393a3385c4f095544f4f0`.

`engine-stateful-motion-history/index.json`: **11 passed, no warnings/failures**.
The new real-GPU history fixture checks bootstrap, two updates without a rendered
frame, frame completion, no-update frame, and explicit lattice reset. Six sampled
RGBA states match exactly (maximum error zero). Aliased/mismatched targets are
rejected; repeated teardown is safe. Existing numerical/refinement GPU tests pass.
`engine-stateful-motion-legacy-regression/index.json` adds **four successful**
existing rendering/data/precision/registered-rock replay checks (three clean,
one with the retained engine `r.MotionVectorSimulation` render-thread warning).
Combined: fifteen successful tests, fourteen clean, no failures.

Actual saved-map capture `SurveyStatefulMotionBank_000..011.png` completed;
frame11 inspected. Both histories logged **857 rendered-frame snapshots** and
clean teardown. The crest remains sheet-like and the foreground rock outline
angular. This is not photographic or continuous-animation acceptance.

The first velocity inspection, `SurveyStatefulMotionVelocity_*`, used the wrong
view-mode token and produced ordinary lit images: **not velocity evidence**.
The corrected `viewmode VisualizeBuffer` run produced
`SurveyStatefulMotionVelocityBuffer_000..002.png`. Frame1 contains 4,685 pixels
with RGB(127,128,0) versus the stationary RGB(127,127,0), over x0..302/y302..478
in the crest area; frames0/2 quantize uniformly to RGB(127,127,0). This is only
an 8-bit smoke check for nonzero output, not a quantitative motion-vector test
or proof of subpixel detail velocity. The active engine settings were
`r.Velocity.EnableVertexDeformation=2`, `r.VelocityOutputPass=0` (automatic WPO
velocity enabled). No global settings were changed. The corrected run logged
882 snapshots for each history. Existing engine toolset Python startup errors
remain unrelated and were not suppressed.

Clean `survey_performance_registered_stateful_motion.json`: mean **13.975 ms**,
p95 **19.064 ms**, GPU mean **6.823 ms**, solver mean **8.892 ms**. One wall-clock
hitch at **33.876 ms**. Previous GPU-carrier baseline was 14.055/19.203 ms with
6.598 ms GPU mean: no material frame-time gain claimed from this small difference.
Same 1280×720, 87% screen percentage, RTX3060 Laptop, five-second warmup and
20-second offscreen Development measurement. Original frame/solver budgets
remain failed; not packaged qualification.

## Single foam coverage authority (opt-in)

`-RaftSimStatefulFoamReview` implies the motion/GPU-carrier path, under the same
registered-rock/detail/breaking review gates. It selects the separate
`M_RaftSim_LiveRiverSurface_StatefulFoamReview`. The earlier material added GPU
foam color and roughness over an already foamy coarse material: transported
coverage could add white but could not replace the existing white sheet.

The new material routes final coverage through one scalar expression:
`saturate(old_final_coverage * (1 - window_ownership) + resolved_detail_coverage)`.
The four-metre boundary transition matches the resolve's outer cell centres;
resolved coverage already carries that fade and wet-depth attenuation, so it
must not be faded again. Outside the domain or with detail disabled the original
coverage remains. The final clamp bounds optical coverage only, not transported
foam density. Color, roughness and opacity consume this single coverage; the two
additional whitening/roughness coats are bypassed. Displacement and the two
previous-frame branches are unchanged. No solver/terrain/collision data changed.

The first version replaced raw aeration, leaving the old lace/web mask to cut
holes into simulated coverage again. `SurveyStatefulFoamBank_000..011.png`
shows that rejected too-sparse version, asset hash `31985a10...5610e4e`.
The bounded `repair_stateful_foam_coverage.py` restored the raw RGB consumers
and moved replacement to final coverage. Its first attempt failed on Unreal's
unnamed Clamp input (`None`, not `Input`); no asset save occurred. Corrected
repair compiled/saved successfully. Current hash:
`9cd016469d473916bf9758c8e22568ec14fe4b36ff2a6e18d94457e028190527`.
`stateful-foam-coverage-repair.json` retains before/after code, hashes and rewires.
The builder now creates the corrected version from the retained motion baseline.

`audit_stateful_foam_material.py` verifies that base color, roughness and opacity
reach the one coverage expression; no old final-coverage consumer bypasses it;
additive coats are unreachable; the WPO graph matches the motion baseline; both
previous-frame switches and velocity flags remain. Report
`stateful-foam-graph-audit.json` passes. Its read-only editor process returned1
despite the successful report and no logged Python/shader errors; retain this
exit-status qualification rather than calling it a clean process pass.

Actual corrected `SurveyStatefulFoamFinalBank_000..011.png`: frames0/6/11
inspected. Broad downstream duplicate whitening is gone, but the main white
crest remains sheet-like and the foreground rock silhouette angular. This
change fixes coverage ownership, not the missing large-scale crest geometry
or continuous-motion acceptance. No claim of photographic completion.

Clean `survey_performance_registered_stateful_foam.json`: mean13.965ms,
p9519.027ms, GPUmean6.819ms, solvermean8.874ms, one33.469ms wall-clock hitch.
Same20-second/5-second-warmup offscreenDevelopment1280x720/87%RTX3060Laptop
protocol. Performance is close to the motion baseline; frame/solver budgets
remain failed. No production scene promoted.

## Still required

The opt-in binding and conforming fine topology are implemented, but moving-window
state remapping, affordable fine geometry and raft-support coupling are not
complete. The base hydraulic carrier is still 1.5 m; fine interpolation cannot
invent missing macro crest physics or measured bathymetry. Localized entrainment
improves blanket whitening but the main crest still lacks convincing froth shape.
No screenshot improvement or frame-time improvement is claimed. No scene is
promoted; none of numbered items 4–6 is declared finished by these tests.

Next: improve macro crest/foam behavior from verified rapid geometry, preserve
macro water level/raft support, quantitatively verify the new previous-frame
motion vectors and long-run temporal behavior of the GPU texture path,
and inspect actual motion and settled
cost against the retained baseline. Geometry/shoreline, geographic identity, route robustness,
all later rivers, crew, maintenance, release and final commit remain open.
