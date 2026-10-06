# Uninterrupted South Fork liquid-fixture timing — September 9

This is a cost measurement of the unsaved 21 m captured-terrain fixture, not
photorealistic acceptance, calibrated hydraulics, or packaged-game FPS. The
production map/system is unchanged. The prior goal turn completed the final
distance guard regression; this turn advances the previously missing live cost
measurement. The full queue remains active.

## Measurement

`capture_south_fork_liquid_terrain.py -RaftSimLiquidTerrainBenchmark` advances
the real Niagara simulation at 1/60 s per editor callback and renders the same
960×640 fixed-oblique scene capture on each callback. Frames 240–720 supply
480 uninterrupted wall-clock intervals. Image/particle exports occur at frames
230 and 720, outside the timed interval. There are no particle/grid readbacks
or image exports inside it. This measures fixed-step editor-fixture throughput;
it includes editor/scene-capture overhead and is not a game-loop FPS test.

The optional live reconstruction benchmark uses a 16-slot ring of four GPU
timestamp queries. It polls without waiting, skips busy slots rather than
reusing pending queries, and exports results only after the window. GPU
timestamps bracket packing+density, distance generation and the SimRT copy.
The first 240 reconstruction updates are excluded explicitly. That GPU sample
window is not asserted to equal the Python callback window exactly. The last
pending queries are intentionally omitted rather than forcing a timing wait.
Ordinary live motion captures do not enable the timestamp ring.

The runs used identical launch settings except `-RaftSimLiquidLiveDensity` and
output names. Both used PIC/FLIP .75, the transported-foam candidate, corrected
normal/ray frames and the same optical controls. They ran sequentially on the
existing RTX 3060 Laptop GPU. Runtime clock/thermal state and all frame-cap
cvars were not recorded; these two runs do not establish a stable performance
distribution across sessions or a release target.

## Actual results

| Measured interval | Native surface | Live reconstruction |
|---|---:|---:|
| Editor fixture mean | 16.773 ms | 23.315 ms |
| Editor fixture median | 16.692 ms | 23.274 ms |
| Editor fixture p95 | 18.430 ms | 25.348 ms |
| Editor fixture maximum | 31.956 ms | 33.983 ms |
| Simulated seconds / wall second | 0.994 | 0.715 |

Sources: `liquid-native-benchmark-12s/benchmark_audit.json` and
`liquid-live-benchmark-owned-12s/benchmark_audit.json`. Each audit verifies 480
positive intervals, their exact wall-time sum, no image exports inside the
window, and no engine error lines. Both editor processes exited 0.

The 471 post-warmup live GPU samples show:

- Packing and density: mean 5.365 ms, p95 5.865 ms.
- Distance generation: mean 0.577 ms, p95 0.584 ms.
- Copy to the existing visible SimRT: mean 0.0239 ms.
- Total reconstruction: mean 5.966 ms, p95 6.467 ms, maximum 6.587 ms.

All timestamps are ordered, stage sums match total intervals, no busy slots
were skipped, all four reconstruction diagnostics are zero, and the live run
completed 715 GPU updates. The observed 6.542 ms increase in mean editor frame
interval is consistent with the measured reconstruction cost, but is not an
independent whole-scene GPU profile. The density stage—not distance generation—
is the main measured reconstruction expense. Prior blocking single-dispatch
timings must not replace these streaming measurements or be presented as FPS.

## Retained failure and correction

`liquid-live-benchmark-12s` completed simulation but crashed during cleanup.
The report alone is not success: the log and exit code show
`FRHIPooledRenderQuery::~FRHIPooledRenderQuery` asserting that destruction must
occur on the render thread. Even default/empty query objects have this rule.
The corrected helper constructs its query array on the render thread and
destroys the array/pool there after removing the callback. The corrected run
`liquid-live-benchmark-owned-12s` subsequently exits cleanly. Do not reuse the
failed run as passing performance evidence.

## Visual result and next action

The before/after images were actually viewed. Both native and reconstructed
surfaces remain cyan/plastic, with weak froth and exposed rectangular diagnostic
window walls. Reconstruction adds detail but does not solve the whitewater
appearance on its own. No visual/physics/performance acceptance is granted.

Next implement coherent solver-fluid interior support and foam placement on the
same current reconstructed surface, with independent actual-GPU parity against
the existing occupancy reference. This must not create liquid in solver-solid,
air or external-stage cells or mutate particle/solver state. Then judge actual
motion and optics against the retained real references and repeat cost checks.
Only after that should whole-scene shoreline, carrier and boat integration be
accepted. Density gathering is the measured optimization target if the visual
benefit justifies retaining this reconstruction.

Validation: all 78 liquid Python tests pass (2.783 s); the engine liquid fixture
suite passes all 11 tests with zero warnings/failures (23.18 s). The corrected
helper build passes in 18.25 s. Saved system, review map and project SHA-256
values remain unchanged. No production promotion or commit occurred.
