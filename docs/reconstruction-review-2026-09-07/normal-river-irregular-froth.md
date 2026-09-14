# Irregular transported froth optics — September 14

Candidate REJECTED after actual playable visual inspection; guarded restoration
and independent fresh readback are complete. Original baseline parent SHA256
`adb56123f1e07c7cdfe2f6cd0da2db1c2e44f12d8ebb147a640ad9899a73c0c3`.
This work addresses the observed whole-cell gray transition and smeared clumps,
not the separate sheetlike wave geometry or incomplete nonlinear physics.

## Optical candidate and scope

`RaftSimIrregularFrothCells.ush` replaces the square-grid interpolation with a
smooth normalized blend around jittered cellular regions. All nearby cells
contribute, avoiding a discontinuous nearest-two choice at triple junctions.
Jitter is bounded to0.2cell, border width to0.25cell. The nearest point is at
most sqrt(2)*0.7cell away; an omitted neighbor is at least1.3cells away, so
the3x3 search covers the blend support. An independent5x5 CPU reference checks
this support rather than copying the shader's neighborhood.

Two optical scales use4.5 and17cells/m, with the existing0.7/0.3 blend weights.
These are presentation choices, not measured bubble sizes. Screen footprint
blending resolves subpixel occupancy to its expected coverage. This is not an
exact pixel-area integral. Spatial weights are independent of occupancy;
expected coverage is retained under the independent random-occupancy model,
and finite spatial samples are checked at five densities. This is not exact
local-area conservation or a physical foam/mass law.

Transported amount, optical density mapping `1-exp(-amount*density)`, velocity,
registered committed clock and two-phase backtrace remain unchanged. No new
foam source, water displacement, depth floor, source edit or solver promotion.

## Failed controls retained and diagnosed

- Build34593 PASS21.07s; native38302 (v1) TERMINAL failure. Raw grid agrees with
  independent5x5 to2.6554073e-6, but full material error0.002104402 and large-world
  error0.032934478 exceed the original0.0003 tolerance. Boundedness also fails.
- Build34258 PASS17.40s; native15082 (v2) TERMINAL failure. Independently rounded
  CPU stages plus direct GPU coordinate output expose0.015625cell coordinate
  mismatch. Merely changing reference rounding did NOT resolve the failures.
- Build87960 PASS17.18s; native2525 (v3) TERMINAL failure. Explicit precise
  scalar products/sums replace the shader's dot intrinsic. GPU coordinate
  discrepancy becomes EXACTLY0; full/large-world reference errors fall to
  9.52464478e-7 /1.33136470e-6 without relaxing0.0003. The remaining59 invalid
  outputs are optical roundoff up to1.00000011921, not a transported-density
  overflow. The candidate now saturates its mathematically bounded optical
  blend; no foam density is clamped.

The explicit operation sequence is supported by the distinction between a
precise multiply/add sequence and a fused instruction in Microsoft's
[precise instruction documentation](https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/precise).
The causal evidence here is the direct coordinate output and native comparison,
not an assumption that the documentation alone proves GPU/CPU agreement.

Build37480 PASS17.94s. Candidate helper SHA256
`0af97a746e2f79a3b77c55609cb7694f309f5ca968d1cbbf3f8be436996dd04e`.
Final native98838/v4 TERMINAL exit0: all4tests PASS in0.575071s. Optical
range exactly[0,1], zero invalid outputs, coordinate discrepancy EXACTLY0.
Grid/material/large-world errors2.6554073e-6 /9.52464478e-7 /1.33136470e-6;
phase probe delta1.35600567e-6. Measured means for target.02/.12/.5/.88/.98:
.020385206/.119645819/.498338297/.881050902/.980136992, all within the original
.008 finite-sample tolerance. All earlier failure reports/logs are retained.
The4-test suite also covers existing coverage optics, registered GPU clock,
and committed foam evolution. New test uses83,377 queries, five16,384-point
coverage samples, large world coordinates, zero/negative inputs, density
monotonicity and phase-wrap probes. Native tests alone are NOT visual/FPS
acceptance; actual parent installation, fresh readback, captures and timing
remain required before accepting this candidate.

Baseline23618 TERMINAL exit0, but strict CSV audit REJECTED duplicate header
series `LightCount/UpdatedShadowMaps` and `ShadowCacheUsageMB`. No timing report
was written; raw capture retained. Baseline29333/v2 is a fresh repeat with the
same unchanged parent and settings, not an edited CSV or weakened parser.
First install29604 TERMINAL failure before any backup/material write because
Unreal's native report starts with a UTF-8 BOM. The reader now explicitly uses
utf-8-sig; the material hash remained the original baseline at that failure. Candidate
installation still requires all four exact named tests and the qualified helper
SHA. No test result or asset edit is inferred from a process exit alone.

## Actual installation and rejection

Baseline29333/v2 passed the strict complete-300-frame CSV audit. Warm rows
120–250 give9.038802496 FPS, frame p95133.1675ms, GPU mean37.163290840ms and
GPU p9538.9199ms. This shared-load run FAILS30FPS; it does not replace the
last isolated18.899245FPS/p9570.33ms result.

Install70647 TERMINAL exit0, zero commandlet errors. All459 protected map,
save, captured-ground and external-actor files retain their hashes. Source,
clock, all other nodes and the four optical consumers are unchanged. Candidate
parent SHA256 `55a6cea17d87ff6baef3d067ba319e02518b743fb741d355b113ad7c193de8c5`.
Fresh read-only process25999 TERMINAL exit0 independently confirms all six
saved graphs and the material hash without modifying the asset.

Ordinary playable capture97791 TERMINAL exit0, recording
`unreal/Saved/VideoCaptures/RaftSim_20260914-064958.mp4`:44 actual source frames
over6.451s, all194 encoded frames decoded. Encoding at30FPS does not mean
the game ran at30FPS. The unmodified extracted image is
`detail-motion/south-fork-irregular-froth-normal-v1-20260914_01s.png`.
Inspected beside the previous post-midpoint baseline: broad blur becomes
sharper, but the result is flat, angular white chips, especially downstream
of the rock chain and across the foreground sheet. It is not convincing
froth. Sheetlike water geometry remains. Native arithmetic/coverage passes
do not override this actual visual failure. No new physical source was added.
The shots are not identical physical states; no pixel-difference attribution
or motion/physical acceptance is claimed. The game log also contains optional
engine Python AgentSkill/PythonTestRunner initialization errors; the recording
completion and full decode, not a claim of an error-free game log, establish
that the observed capture exists.

Candidate timing21315 TERMINAL exit0, but the strict CSV parser rejects an
unexpected repeated header. Raw CSV is retained and no valid timing report
was produced. No candidate cost or improvement is inferred. Because the
candidate already fails appearance, it was restored rather than
reinstalled to repeat a rejected visual candidate's timing. The builder keeps
the original helper, so regeneration will not introduce the rejected optics.

Restoration39142 TERMINAL exit0; fresh read-only28914 TERMINAL exit0. All six
original graphs match exactly, including original coverage code. All459
protected files retain their hashes. Restored serialized parent SHA256 is
`44c07f419a3a0a9f27f420871e4f1594184e57476de0960e560337ce6a93b31d`;
this is a verified semantic restoration through Unreal, not a claim that
reserialization reproduces the original binary bytes. Backup, failed controls,
candidate helper/test and capture remain available for regression/research.
Do not enable this helper in the builder or ordinary gameplay.

All five original long jobs remain live and were not restarted or suspended.
The417/422 implementation guards are unchanged. Cook was at8744.5s; latest
complete8700 checkpoint passes both state and bank audits but is unsettled.
Next complete8800/local16000 requires both audits; it was not complete at check.

Desktop target remains30FPS/p9533.333ms, physics120Hz unchanged; the eight
strict CSV/budget tests pass again. Full playable visual and performance
acceptance remain OPEN.
