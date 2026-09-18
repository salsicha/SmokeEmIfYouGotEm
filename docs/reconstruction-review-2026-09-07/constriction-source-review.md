# Foreground rock provenance and a source-supported constriction candidate

September 18, 2026. The preceding commit-only turn found a clean worktree and
made no reconstruction progress. This turn changes the next reconstruction
action through actual engine rays and creates two isolated geometry candidates.
Neither candidate is installed or visually/physically accepted.

## Actual player view: which surface is wrong?

`south-fork-rock-source-rays-v1-20260918` runs the existing FullReach map at
review station8330, normal lit1280x720, four solver lanes. No geometry, material,
flow or BFECC override. Exit0,24 PNGs, no timeout. Exact cook13584 is suspended
and resumed with status0; CPU is18852.5s before suspension and before resume.
The two pre-existing experimental-toolset Python errors remain (`AgentSkill`
and `PythonTestRunner` unavailable). This is not a clean-log/release pass or
a performance measurement. No new movie or reference-video review this turn.

Inspected unmodified frame016 (world8.356s/game87). Its eleven native complex
terrain rays are independently intersected with BOTH archived original meshes,
without assuming that engine face indices equal source triangle indices.
All eleven nearest-source hits reproduce the native actor and position at the
existing0.1cm gate; maximum error0.000063354cm. These are game-thread terrain
rays, not GPU-depth/refraction/crew visibility or a render-thread fence.

Ten rays hit the source-matched registered ground actor, including the large
foreground face. ALL ten triangles include authority5 inferred flank vertices;
five contain only authority5. Five include authority3 original-return anchors.
The remaining left-background ray
hits the separately installed captured cap. The primary foreground problem
therefore is not that cap's vertical closing walls or a cosmetic normal patch.

The captured anchors sit near the southwest edge of the old
`constriction_north_bedrock` search polygon. That polygon was an interpreted
search region, never a surveyed rock outline. A registered source plot retains
the original aerial pixels, lower original LiDAR returns, installed height
differences and vertex authority. It shows omitted returns continuing through
apparent rock beyond that edge. The diagnostic viewport contains893 outside-
selection above-water candidate bins; this count is NOT an acceptance decision.
2019 LiDAR and2022 imagery differ in date; registration uncertainty remains3m.

## Isolated candidates, not a cosmetic runtime replacement

The new [interpreted selection](constriction-selection-20260918.json) binds the
original mesh, point cloud, aerial image and export hashes. It covers the
southwest exposed-looking patches and excludes the broad southeast dark-water
gap. Individual class1 returns are still unclassified, not certified rock.

`recover_constriction_source_candidate.py` retains the lowest ORIGINAL return
in each nominal0.5m cell with at least two eligible samples and four-connected
support to existing captured rock. Existing class/height/water eligibility is
unchanged. Diagonal contact cannot bridge gaps. No existing captured XYZ is
moved; new XY comes directly from the source, and ground Z retains its existing
float32 storage precision. Unrelated triangles and vertices remain unchanged.

- v1:338 additional original returns, all class1;20 triangle index rows change
  to maintain valid local partitions. Direct insertion leaves sharp inferred
  faces around unsampled cells. Scoped >60-degree face area rises from30.2173
  to275.5473m². Retained as an explicit unpromoted first attempt.
- v2: same338 returns, plus432 explicitly inferred connecting vertices using
  the existing2m harmonic support prior. Original uncalibrated bed floor is
  independently reconstructed exactly before interpolation; no old shelf/plunge
  is restored. Maximum new-source distance1.992957m;118 iterations, residual
  8.301554e-7m at the unchanged1e-6 iteration tolerance. No extra measured
  support is claimed. Scoped steep area40.3261m²: lower than v1, still above
  the installed30.2173m². Minimizing this number is not the physical criterion.

All403,200 vertices and803,842 triangles are independently sampled at vertices,
centroids, asymmetric interior positions and shared edges. Maximum vertex
error0; maximum triangle error2.048139e-12m versus unchanged1e-7m gate. Every
new source ID/coordinate and every previous captured vertex is checked after
reload. Matched source cross-sections were inspected; unlike the installed
selection cutoff, the candidate follows the additional original returns.
Its unsurveyed flanks and semantic classification still require review.

v1 mesh SHA256: `7d131f4088585b370d36d254b92c8f752228647e7e20564bc120f5255afa23a0`.
v2 mesh SHA256: `eebb713b6adac50447353c1abf1bda616ef6e9bb1838c937d1f2b837dd8a0dca`.
Generated meshes remain under ignored `tmp/constriction-source-candidate-v{1,2}-20260918`;
the versioned generator, selection, original inputs and retained manifests
define their reconstruction. No redundant generated FBX/build output is added.

## Important integration finding: the old approach is invalid for v2

At the original recorded near-plane XYs, installed terrain clearance is
2.953819..2.980942m. The SAME positions have clearance **-1.217977..-1.190876m**
against v2: all eleven origins are inside the candidate terrain. This is not
a hull-traversal test, but it rules out reusing that moving-camera pose as an
unobstructed candidate preview. Simply installing a larger source-supported
rock with the old water and approach would not be a working integration.

Next: qualify the interpreted extent and incoming channel against the original
sources, construct a matching physical union/fresh hydraulic state, and validate
the approach and hull contacts together before an actual engine-motion review.
Do not transplant the evolved old-bed state, move source anchors to fit the
old route, or hide the added rock for a better screenshot. FullReach remains
unchanged, SHA256 `c6bda5ff5f680d22b291eb30a6c902488acd909bb7f2b6177fa7103cdd40399f`.

## Tests and ongoing hydraulics

23 focused tests PASS: stable source-ID selection, two-return support, no
diagonal-only bridge or unsupported fill, protected captures, bounded inferred
flanks, nearest reflected source rays and existing camera-ray controls.
No C++ or shipping asset changed; no new engine build or30FPS result is claimed.
Latest ordinary performance remains24.937420FPS/p9549.3295ms: FAIL30.

9200/local4000 and9250/local5000 both pass full5,382,400-cell state and86,720-cell
artificial-bank audits. Banks remain exactly dry; maximum step conservation
residual1.340195e-8m³. At9250 depth3.780648m, speed5.353156m/s, outflow102.903903
versus inflow45.306955m³/s: NOT settled. Installed4950 remains unchanged.
Same cook13584/startUTC2026-09-18T12:17:39.4321093Z/session95293 continues to12000.
Next9300/local6000 needs completion and BOTH audits; never restart on timeout.

Durable evidence is in [constriction-source-review](constriction-source-review/):
actual PNG/view/process receipt, independent source rays, registered source
plot/report, both candidate manifests/audits/sections, and hydraulic audits.
All source-class uncertainty and failures are retained. South Fork breaking,
froth, complete geometry/flow/contact validation and30FPS remain OPEN, followed
by Colorado, Pacuare, Futaleufu, Chilko/Zambezi water reviews, crew, normalization,
regressions and release. Nonlinear runtime remains OFF.
