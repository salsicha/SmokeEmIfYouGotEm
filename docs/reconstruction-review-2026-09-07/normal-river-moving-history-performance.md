# Moving-history accuracy and exact-product cost — September 14 UTC

Desktop remains 30 FPS / p95 33.333 ms. This work advances the intended solver,
but does not qualify or replace normal playable water. Terrain, visible breaking
and froth, crew, other rivers, platform and release requirements remain open.

## Live owner completes two moves; full-history accuracy still fails

Fresh FullReach run41400 exits0. The verified cook41820 was temporarily paused
and resumed in `finally`; both statuses were0. Disposable profile, unchanged
station8330, actual source stream,16 slots,4096 total-trial limit and16-observation
queue. No clock, source-interior, ledger or retained-state reset.

`tmp/south-fork-qualified-range-owner-v1-20260914.json`, SHA256
`bf20b0b6c467b78d5d1b02a7174f502e1de3cba89996ee7f3b32cf0dfe5736ec`:

- Requested two moves complete,72 intervals,1080 accepted physical trials.
- Final committed time9.066667139530182s, origin[-5463.5,3576.5]m.
- Summary[16,16,1,1], diagnostics[0,0,0,1], remaining0.
-146 graphs,72 run-ahead graphs, six retained observations; no queue failure.
-80 recorded observations, including same-instant closing/opening move endpoints.

Independent complete retained-history replay67285 exits0 with a valid FAILED
accuracy report, `tmp/south-fork-qualified-range-history-v1-20260914.json`:

- Maximum state error0.004130154590943097, exceeding the unchanged1e-4 gate.
- Relative depth/hu/hv errors[1.872679694e-5,3.296309964e-5,4.587825374e-5];
  momentum exceeds the unchanged2e-5 component gate.
-1306 cells exceed1e-4; worst y55/x71/hu, GPU-0.245499998331070 versus
  CPU-0.241369843740127.
- Moves at3.4666668474674225 and9.066667139530182s, offsets[-16,5]/[-11,16],
  retained overlaps13776/13104 cells.
- Maximum window-inventory error7.699195693e-6; reported GPU float water balance
  -1.858467218e-5m3. Neither quantity overrides the state failures.

This source trajectory differs from the older plateau-owner failure; do not
interpret the smaller maximum error as a controlled accuracy improvement.
Full-history progress is now observable, and provenance includes the dynamically
normalized pressure-reference dependency.35 moving/temporal/CSV tests pass1.08s.

Actual screenshot `unreal/Saved/Screenshots/south-fork-qualified-range-live-v1-
20260914.png` was inspected: rounded water over a large boulder, broad merged
white foam, basic crew and blocky foliage remain. The new solver is diagnostic,
not the surface displayed in this image. The requested300-frame CSV was still
capturing when the30s screenshot command exited at frame233; the file is truncated.
The CSV validator correctly rejects it. No new FPS report was produced, and
ordinary gameplay remains the prior18.899245FPS/p9570.33ms FAIL. Future CSV
captures must finish before the screenshot's exit; do not salvage truncated rows.

## Measured cost and exact two-limb multiplication

Baseline native94096 exits0 with one clean `TemporalEvolutionGPU` check1.968696713s.
Four alternating warm-up intervals, then eight paired direct/indirect samples,
alternating order, on the original128x128 temporal fixture SHA256
`3f5cc321dd82918bb53dd4a3b6811e1ae3ca181359a0da1544fa86463ee4f181`.
Cook41820 and owned CPU-history23520 were verified, temporarily paused and
resumed in `finally`, all statuses0. GPU timestamps include boundary sampling,
both RK2 stages, breaking, pressure, acceptance and ledger; uploads/readbacks
and ordinary rendering are outside the scope. All five records stay exact across
graph partitions and direct/indirect runs. Two physical steps complete the fixture;
the second two-slot graph is inactive and is reported separately.

The old finite-product helper used the18-limb exact affine accumulator. A product
only needs48 significand bits, so it now uses two32-bit words, integer-normalized
operands and one nearest/even rounding. It preserves subnormal values, signed zero,
overflow and explicit nonfinite-input invalidation. The wider affine accumulator
remains for addition and RK2 cancellation. No FP64, hardware denormal dependency,
depth floor, matrix change, shortened CG, tolerance or timestep change.

Build22614 exits0 in17.29s.34,875 new independent rational product cases, including
all exponent boundaries, ties, subnormal/normal/overflow transitions, signed zeros,
nonfinite inputs and32,768 random finite pairs, pass bit-exactly on the GPU.
Fixture `tmp/south-fork-two-limb-product-fixtures-v1-20260914.bin`, SHA256
`a7214b30584500a40f130e5a6ce9a6e5addb020e1275c7375db2d33c084fa224`.
Portable arithmetic shader SHA256
`1d77717690e1981427f994cff1294e1907e8ec066ecd8464bae823a240f1026e`.
Native27888 exits0 with124 clean checks,106.590637207s automation duration:
`tmp/south-fork-two-limb-product-native-v1-20260913/index.json`.
The actual retained-state capture is byte-identical to the pre-optimization
capture, SHA256 `5667023e7f7c62891d533a6b1e1e643bd5d6d115b9b3ac2d89d5bc2494dd69d1`.
67 focused arithmetic/reference/history checks pass3.95s; eight timing-parser
checks pass0.19s. No full-history accuracy improvement is claimed from this exact
arithmetic optimization.

Repeat warmed timing95988 exits0 with one clean test1.391647220s, same inputs,
warm-up, device and temporary background-job pauses; all resume statuses0.
`tmp/south-fork-two-limb-product-timing-comparison-v1-20260914.json` retains every
sample and hashes both clean native reports/logs and the unchanged fixture.

| GPU scope | Before mean | After mean |
| --- | ---: | ---: |
| Indirect active graph, two physical steps |27.485625ms |18.005750ms |
| Indirect inactive graph, two slots |3.815375ms |2.189750ms |
| Indirect complete four-slot interval |31.301000ms |20.195500ms |
| Direct active graph, two physical steps |27.371125ms |17.994125ms |

Active indirect mean drops34.49%; p95 drops27.643→18.059ms. This is a short
component measurement, not playable FPS or release acceptance. It is still too
expensive for the intended120Hz simulation plus rendering at30FPS. Continue
profiling/optimization without changing the physical requirements.

## Endpoint capture (subsequent comparison now complete)

Current result: CPU18242 completed with the same full-history failure. The first
burst is a discontinuous shoreline reconstruction rule; an optional continuous
CPU candidate now passes bounded sensitivity and physics checks, not gameplay.
See [first divergence and candidate](normal-river-shoreline-continuity.md).
The job-launch notes below preserve the earlier sequence, not current status.

The optional recorded-stage diagnostic now supports `-RaftSimRecordedEndpoints`:
it evolves every original trial and move but retains only first-trial stage
readbacks at interval starts. The original128-record memory cap and exact final
equality to the live state remain mandatory. This allows all72 interval starts
to be compared without replacing the evolved interior. The independent endpoint
audit also records every transitive pressure/transport/reference implementation hash.

Build76406 exits0 in16.25s. Endpoint capture61113 exits0 in25.387599945s:
72 first-trial records,1080 evolved trials, two moves and final byte equality to
the actual live state. It has ONE descriptor-cache fallback warning, so it is
not a clean native pass. Prefix `tmp/south-fork-qualified-range-endpoints-v1-20260914`,
binary SHA256 `ac005c23a9149f62e3f33ec6c4b2094e3f98f1511beb22c6fb5abbb9a2675e4d`.
Independent endpoint-history audit18242 is now running with reusable CPU states:
`tmp/south-fork-qualified-range-endpoint-history-v1-20260914.json` and
`tmp/south-fork-qualified-range-endpoint-cpu-v1-20260914.npz` (outputs pending).
Initial0.06666667014360428s checkpoint is exact.74 focused endpoint, timing,
arithmetic and moving-history Python checks pass2.02s; scoped diff check passes.
No accuracy tolerance changes or normal playable promotion are authorized by
these diagnostic results. Cook74818/PID41820 is resumed and live; BOTH6400s/
local8000 snapshot audits pass, still unsettled. Next complete6500s/local10000
needs both state and artificial-bank audits. Runtime600s source is unchanged.
