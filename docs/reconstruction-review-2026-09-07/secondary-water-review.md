# Bounded secondary-water experiment — 2026-09-08

Not a scene completion or production promotion. The main foam surface is still
visibly too smooth, the registered terrain is angular, and performance still
misses the unchanged gates. All later rivers and remaining tasks stay queued.

## Why this change

The previous falling-spray assets use Niagara **Stateless** plane/cone modules.
`SetNiagaraEmission` supplies a normalized launch direction, source transform,
scale and rate, not the local current speed. Chilko-derived review variants apply
gravity and fixed lifetime; they do not check return to the actual water. Reusing
these assets correctly on the registered map did not fix those limitations.

The [SideFX Whitewater Solver documentation](https://www.sidefx.com/docs/houdini/nodes/dop/whitewatersolver.html)
describes secondary particles driven by source-liquid velocity and surface data,
including gravity, surface attachment and bounded emission. This is an
architectural reference, not a Houdini integration, a claim of equivalent
capability, or photographic validation of this implementation.

## Isolated implementation

`-RaftSimSecondaryWaterReview` requires the registered map and the shared
`-RaftSimStatefulCrestReview` carrier. The new component is tick-disabled by
default. Once its field, surface, mesh and material are ready, the review replaces
the three existing rapid Niagara populations; it does not add duplicate spray.
The ordinary production particle assets, material and behavior are unchanged.

- 128 persistent world-space particles, 60 Hz fixed steps, at most four steps
  per render frame; remaining time is retained, not discarded. Rendering
  interpolates the preceding and current fixed step with one-step latency.
- At most six existing breaking sources and 80 attempted births/second total,
  further thinned by existing intensity/persistence. No new hydraulic sources.
- Birth inherits the sampled horizontal liquid velocity, plus a bounded authored
  ejection of 1.2–2.8 m/s up and ±0.35 m/s cross-flow. These are **presentation
  parameters**, not measurements of turbulence or momentum exchange.
- Airborne positions integrate constant gravity analytically. Birth position and
  velocity are persistent; source movement/re-ranking cannot move an old particle.
- On reaching the shared macro carrier, a fragment becomes short-lived foam
  moving with the sampled flow. Foam shrinks over 0.8 seconds; all particles have
  a three-second maximum lifetime. Dry/missing samples remove the fragment.
- Closed 2–4.5 cm-radius sphere fragments, opaque default-lit material, no
  emission, roughness 0.6, specular 0.25. No new water sheet or physics collision.
- Explicit current/previous instance transforms; pool reuse does not generate a
  velocity vector from the previous occupant. This is tested on the real ISM API.

Files: `RaftSimSecondaryWater.h`, `RaftSimSecondaryWaterComponent.{h,cpp}`,
`RaftSimSecondaryWaterTest.cpp`, the small VFX bridge integration, and
`unreal/Scripts/create_secondary_water_review_material.py`.

Material: `/Game/RaftSim/Environment/SouthForkSurveyCandidate/M_SecondaryWaterReview`
SHA256 `4b871069ce025255b755ff1a0c9e982e13b643b3041f54bf591f68ed1a5a4ea6`.
The script refuses to overwrite an existing asset. No borrowed external art.

## Verification and retained failure

Builds 72095, 36113 and 72507 completed successfully. Material creation 15782
exited 0 with a saved setup report. Actual D3D12 regression run 15100 completed
17 focused tests successfully in `engine-secondary-water/index.json`.

**First scene run failed:** session 43829, `SecondaryWaterMotion.log`, exit 1.
It asserted at `InstancedStaticMesh.cpp:4378` because the explicit-history batch
overload requires internal previous-transform storage. An external history array
alone is insufficient. No finalized video or visual success is claimed for it.

The fix calls `SetHasPerInstancePrevTransforms(true)` before adding the pool.
New `RaftSim.M4.SecondaryWaterInstanceHistory` invokes that exact initializer and
checks the first batch and the last history slot. Run 62204 exited 0:
**18 successful tests, zero warning-successes/failures**, recorded separately in
`engine-secondary-water-history/index.json`. This comprises two new particle/
renderer tests, two existing spray tests and fourteen existing GPU-detail tests.
The particle test covers current inheritance, analytic gravity, birth
independence, step partition equivalence while airborne, return and advection on
flat/sloping carriers, dry rejection, capacity and expiry.

## Actual animation and performance

Corrected recording session 25953 exited 0. All prior review flags remained on:
breaking, lit foam, detail, shared fine crest, second-order detail, South Fork
ballistic assets, unified foam optics and activity memory, plus this new flag.
Same registered map, 1280×720, fixed side camera at station 8/lateral 0; normal
drift, no teleports or force overrides.

Video: `unreal/Saved/VideoCaptures/RaftSim_20260908-000406.mp4`.
696 source frames over 23.837 s; 715 decoded frames. The encoder's 30 Hz timeline
is not a game-FPS measurement. Full decode/report is
`detail-motion/SecondaryWaterHistoryMotion.json`; unmodified frames at 1/8/16/23s.
Inspected 8s and 23s: the former puffy spray is replaced by small sparse white
flecks, but the broad foam face remains smooth. **Not photographic acceptance.**

Runtime at 35.002s: 712 births, 683 return transitions, 16 dry/missing removals,
670 expirations, 26 still alive. Return count is a transition counter, not a
separate removal count. Sampling/particle/render-update CPU mean during recording
was 0.4382ms; accumulated time remainder 0.001952s. These counters verify the
path runs, not exact visual attachment to the final GPU surface.

Separate **no-recording/no-readback** performance session 63964 exited 0:
`survey_performance_secondary_water.json`, 5s warmup + 20s measurement,
Development/offscreen, RTX 3060 Laptop, 1280×720 at 87% screen percentage.

| Diagnostic | Previous native-reuse baseline | Secondary experiment |
|---|---:|---:|
| Mean frame | 13.3260 ms | 13.8784 ms |
| p95 frame | 18.9964 ms | 19.3517 ms |
| Mean GPU | 6.9199 ms | 6.8687 ms |
| Mean solver | 8.0846 ms | 8.0679 ms |
| Wall-clock hitches >33ms | 0 | 0 |

One bounded observation each, not statistical attribution. Secondary component
reported 0.3902ms mean CPU at 20s, with 26 live particles and 0.003904s remainder.
The unchanged 16.667ms p95 and 1.6ms solver gates are not passed. Not a packaged
release qualification. Existing experimental engine Python startup errors remain
in game logs; successful focused test counts do not erase those.

## Remaining limitations / next work

The sampler includes the shared continuous macro crest but **not** the GPU
perturbation height. It is not exact final-surface collision. No swept-solid
collision, sampled liquid vertical velocity, volume/energy conservation, particle
repulsion or feedback into the liquid solver is implemented. Endpoint/midpoint
wet checks do not prove against crossing a thin dry obstacle. Spheres are a
diagnostic fragment representation, not a realistic foam aggregate. Do not
increase counts or promote this path merely because the kernel tests pass.

The persistent particles establish a bounded current/gravity/return lifecycle;
they do not fix the missing deforming **bulk** whitewater. The next realism work
must address that surface/crest dynamics and physically consistent fine-surface
coupling, plus the existing geometry/provenance and performance gates.

Registered map SHA256 remains
`81f31bec7ba8683e3a7479f17333419b6d32eeb277de5630f098d41fdf705ad7`.
Native archive remains
`fd988c73f10f2f1423b421fc3b6e78928d9124acba789e9fae05b75f1a51a35c`.
No production geography promotion, new cook, later-river completion or commit.
