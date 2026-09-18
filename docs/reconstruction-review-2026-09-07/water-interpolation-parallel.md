# Parallel water interpolation in normal gameplay

September 18, 2026. A measured CPU-pass improvement, not geographic, visual,
30 FPS, packaged-game or release acceptance. The preceding heartbeat recorded
cook checks only; this continuation changes default gameplay code and rebuilds
both editor and standalone Development targets.

## Delivered change and exactness

Cartesian water now advances the five rendered histories in independent
1,024-vertex batches, joining before the existing publication. Position, normal
normalization, color, bulk flow and wake use the original expressions and
per-vertex operation order. No timestep, update cadence, vertex, source field,
crest, foam formula, threshold, collision or support rule is omitted or changed.
Non-Cartesian water retains serial scheduling. The same-binary control is
`-RaftSimSerialWaterInterpolation`; ordinary play needs no enable flag.

The native regression independently evaluates the original expressions over
16 evolving frames for 0, 1, 1,023, 1,024, 1,025 and 50,625 vertices. It checks
all five fields bit-for-bit, zero normals, zero/unit/intermediate blend factors,
large world coordinates and rejecting inconsistent history sizes before writes.
The initial nine native tests pass; the final default-enabled ten pass with
zero warnings, failures, skipped or in-progress tests, including the Cartesian
shoreline actor, fine crests, exact/moving/target caches, packing and foam/clock.

Two actual FullReach runs at station 8,330 compare all 64 consecutive frames
120–183 in alternating execution order. All 128 pairs preserve every field bit
over 6,480,000 vertex updates. Every pair is faster. Run A uses serial production;
run B uses the then-opt-in parallel production. Copying and comparison are
outside the measured pass; batch scheduling and joins are inside it.

| Run / first path | Serial mean ms | Parallel mean ms |
| --- | ---: | ---: |
| A / serial | 1.746041 | 0.644759 |
| A / parallel | 1.705622 | 0.504815 |
| B / serial | 1.723909 | 0.448588 |
| B / parallel | 1.849206 | 0.441456 |

The [pair receipts and delivery summary](water-interpolation-parallel/) retain
all original pair timings and source-log hashes. Final builds succeed: editor
64.42 s, standalone game 111.49 s. Logs are
`tmp/water-interpolation-{editor,game}-v2-20260918.log`; native report is
`tmp/water-interpolation-native-v2-20260918/index.json`. Rebuilt binary hashes
are in the delivery summary. This is not a new packaged-content release.

## Whole-frame result: mixed, still fails 30 FPS

One uninterrupted serial/parallel/parallel/serial sequence uses the same final
binary, ordinary FullReach scenario at the rapid review station, D3D12 1280×720,
900 frames each, all rows 60–840, unchanged physics/quality and no pair audit.
The existing identified cook is suspended/resumed successfully for every run;
all wrappers/games exit zero without timeout. The recorded CPU bracket includes
0.015625 s in A before suspension completes; B/C/D brackets are zero. No other
diagnostic workload is run during the sequence.

| Run | FPS | Mean frame ms | p95 ms |
| --- | ---: | ---: | ---: |
| Serial A | 26.084241 | 38.337324 | 46.2513 |
| Default B | 25.600678 | 39.061465 | 46.9624 |
| Default C | 27.421104 | 36.468262 | 43.7452 |
| Serial D | 23.932085 | 41.784909 | 52.1756 |

All fail the unchanged p95 ≤33.333333 ms gate. The forward pair gets worse;
the reverse pair improves. Do not claim a reliable whole-frame gain from these
variable trajectories/shared-host measurements or hide either result. The
default change is supported by the exact same-input pass saving, not by an
FPS pass. Inclusive nested water scopes must not be added together.
Complete analysis: `tmp/water-interpolation-timing-v2-20260918.json`; all raw
CSVs/logs/process receipts remain under `unreal/Saved` with the summary's labels.

## Normal starting point and actual rendered evidence

No review-station or interpolation enable flag is used in the final startup
capture. The ordinary South Fork Full Guided Descent starts near station 120 m,
advances past 134 m and saves all 24 player-view PNGs. This directly launches
the normal scenario/map; it does not exercise clicking through the boot menu.
The 15.614 s recording fully decodes to 468 frames, with 207 actual engine source
frames and 24 identical decoded frame pairs after the first second. Encoder
30 Hz timestamps are NOT gameplay FPS.

Inspected screenshots 000/012/023 and unmodified decoded 3 s/13 s frames show
raft/camera progression, water and the bank. Early crew/material appearance
changes, soft water presentation and coarse/repeated canopy remain unresolved;
this is not a controlled visual before/after comparison or rapid/breaking-wave
acceptance. Fixed decoder ROI names are not semantic measurements in this view.

At 10.026818 s, 2,034 independent barycentric presented-water/support probes
have zero dry, unavailable or ground-occluded points; maximum difference is
0.000189971 cm, RMS 0.000111235 cm. Includes the paired detail field, not GPU
latency, full-hull/traversal collision, complete shoreline or physical accuracy.
Contact source: `tmp/water-interpolation-startup-contact-v2-20260918.json`.
Startup label: `south-fork-water-interpolation-startup-v2-20260918`.
Decoder output: `tmp/water-interpolation-motion-v2-20260918/`.

The cap fidelity decision is still pending. No source, map or installed 4,950 s
field is changed; nonlinear runtime remains OFF. The original cook 13584 is
confirmed live and resumed (local 52,810 / physical 11,640.5 s at observation).
No new cook or snapshot promotion; the last independently audited checkpoint
remains 11,350/local47,000. South Fork and the entire ordered queue remain open.
