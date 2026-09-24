# Exact source bounds reduction in normal South Fork

2026-09-24 UTC. This is a normal-play performance increment, not new visual
detail, corrected geography, hydraulic settling or river acceptance.

## Attribution and change

The retained seat-anchor capture showed SetMesh6.38ms mean, with roughly1.3ms
outside its existing child scopes. New scopes separate CrestSourceGather,
OutputStorage and BoundsAndNotify without changing output or cadence. The
normal900-frame diagnostic reports means0.35,0.12 and0.90ms respectively;
BoundsAndNotify p951.40ms. Overall p9535.89ms still failed. Source:
`tmp/shoreline-residual-scopes-frame-v1-20260924.json`; process receipt
`unreal/Saved/RaftSimValidation/south-fork-shoreline-residual-scopes-v1-20260924-process.json`.

The bounds helper now reduces independent1024-vertex blocks and combines their
boxes in source order. Every current source vertex is included. Source geometry,
attribute values, crest padding500cm, notification behavior, draw topology,
update rate, material and physical solver are unchanged. No stale-height cache,
approximate culling box, reduced detail or altered frame budget was introduced.
Normal South Fork uses this exact parallel calculation. Other maps retain
their original default until qualified. `-RaftSimSerialWaterBounds` retains a
serial control; `-RaftSimParallelWaterBounds` explicitly selects the candidate.

## Exactness and retained failure

- Native seven input sizes0..65537, four changing epochs: exact extrema and
  validity, every point enclosed, both sides of1024-node boundaries exercised.
  Bounds plus existing referenced-water suites:3 passed,0 failed,0 warnings in
  `tmp/water-source-bounds-native-v2-20260924/index.json`.
- Initial native v1 terminates during Unreal HTTP/DDC startup at frame0 with
  an InheritedContext assertion, before any test runs. Its log is preserved;
  it is not a test pass. A single fresh launch above succeeded.
-64 actual-game comparisons, alternating order every two frames, all exact.
  Source: `unreal/Saved/Logs/south-fork-water-bounds-pair-v1-20260924.log`;
  checked report: `tmp/water-source-bounds-pairs-v1-20260924.json`.
  Reference/candidate mean costs:0.8362/0.2556ms when candidate second,
  0.5682/0.3764ms when candidate first. This is component timing, not game FPS.
-17 Python audit/parser tests pass, including missing/duplicate/reordered pairs,
  mismatches, invalid durations, optional historical scope columns and explicit
  frame-time phase. No acceptance threshold was relaxed.

## Normal whole-frame controls

Four isolated900-frame captures in reference/candidate/candidate/reference order,
same normal FullReach/full_descent start,4 solver lanes, D3D12,1280×720. Exact
cook identity guarded, suspend/resume successful, no competing build/decode.
Elapsed samples60–840 inclusive; confirmed frame-time scope offset1. No crew
input, alternate camera, shadow override, candidate terrain or nonlinear mode.

| Run | Mean frame ms | p95 ms | Bounds/notify mean ms |30FPS p95 gate|
| --- | ---: | ---: | ---: | --- |
|Reference A|25.508230|35.1387|0.783688|FAIL|
|Candidate A|22.949067|31.0480|0.365181|PASS|
|Candidate B|23.130847|31.0448|0.393914|PASS|
|Reference B|23.764554|31.8753|0.652345|PASS|
|Promoted default, no opt-in|22.853096|30.8299|0.400777|PASS|

Both orders favor the candidate; reference variation means the entire observed
frame difference must not be assigned to this component. These are short first-
pool observations, not sustained rapid/full-route acceptance. Historical failures
remain retained. Frame budget stays33.333333ms. Per-run reports, source hashes
and metrics: `tmp/water-bounds-{reference-a,candidate-a,candidate-b,reference-b,default}-frame-v1-20260924.json`.
Process receipts share `south-fork-water-bounds-` plus those run names and
`-v1-20260924-process.json` under `unreal/Saved/RaftSimValidation/`.

## Final default delivery and motion

Editor v2 build succeeds18.71s; Game v1 succeeds82.83s:
`tmp/water-source-bounds-{editor-v2,game-v1}-20260924.log`. The existing unrelated
detail-source uninitialized `Current` warning remains, not waived. Normal
runtime log confirms `WaterBoundsMode parallel=1 serial_override=0` with no
optimization flag. Rebuilt Game target is separate from editor-hosted captures;
packaged release remains unqualified.

Separate default motion capture produces24 stills and
`unreal/Saved/VideoCaptures/RaftSim_20260923-192221.mp4`, SHA256
`12e6e94d7948d169447b626fdc51516cc7624e0d968cbdf90a0d4ffd2d94373e`.
Full decode:464 frames through15.4333s,19 adjacent exact duplicates;
`tmp/water-bounds-motion-v1-20260924/report.json`. Original3s/9s inspected:
boat advances0.12→0.13km, water changes, zero incidents/swimmers; no disappearance
or new holes in those views. This does not prove off-camera culling, full-route
shoreline/contact stability or realism. Smooth water, coarse canopy and crew
pose limitations remain. Encoded video rate is not the performance measurement.

Captured sources, installed4950s fields, physical geometry/collision and native
nonlinear OFF remain unchanged. Original cook36692 continues alone. South Fork
is unfinished; Colorado, Pacuare and Futaleufu must not be advanced prematurely.
