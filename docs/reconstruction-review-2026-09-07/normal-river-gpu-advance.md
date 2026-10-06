# Bounded GPU interval continuation — September 13

South Fork remains the first unfinished river. This adds the bounded controller
above the verified single-trial RK path; it is supporting implementation, not a
new visible playable scene or a 30 FPS pass.

## Implementation

`RaftSimAdvanceTotalDepthGPU` schedules 1–8 trial slots per graph, with an
explicit cumulative interval limit of 1–4096 trials. State, compensated
progress, cumulative summary and last effective trial diagnostics persist
together across graphs. A pending interval can continue without reconstructing
its clock or discarding its remainder. There is no CPU readback in the helper.

Each effective trial uses the existing same-stage FV/pressure/RK gates.
Rejected trials keep the last accepted state and clock, and use the proposed
half-step on retry. Complete, fatal and cumulative-budget-exhausted statuses
are latched. Later scheduled slots or later calls cannot erase the terminal
diagnostics, restart an exhausted interval, increment its counts, or advance
its time. A fatal trial after an accepted one retains that accepted state, not
the original interval input. Changing the total limit does not clear a latch.
Starting a new interval requires explicitly new summary/diagnostic records.

Inactive slots use a scratch zero-duration progress record, never overwrite
the real remaining interval, and retain its last effective diagnostics. They
still schedule the underlying water kernels: this is bounded graph work, NOT
an indirect-dispatch or zero-cost early-out optimization. This implementation
must not be promoted as a performance improvement. Physical timesteps,
pressure iteration budget, state/residual gates and equations are unchanged.

Files are `RaftSimTotalDepthAdvanceGPU.h/.cpp`,
`RaftSimTotalDepthAdvance.usf` and `RaftSimTotalDepthAdvanceTest.cpp` in the
existing RaftSimWaterDetail public/private/shader/test locations.

## Actual-device verification

Initial build40913 failed because the test aggregate needed an explicit UE
float4 initializer. Fixed build16419 succeeded13.74s. Single actual-D3D12 test
81789 CLOSED exit0, one clean pass,0.954937518s:
`unreal/Saved/RaftSimValidation/south-fork-total-advance-gpu-v1-20260913/index.json`.

Eight cases compare four trial slots in one graph against four separately
executed graphs with actual pooled-buffer extraction/re-registration. A final
extra graph tests terminal persistence. State, progress, summary and diagnostics
must be bit-exact across these graph partitions, not merely numerically close.
The clock starts at1048576s, and moving water must really change while retaining
finite/nonnegative state, unchanged foam, and periodic mass conservation.

Cases and observed (trials, accepted, status):

- Complete0.02s: (3,3,complete).
- Injected second-stage rejection then retry/complete0.004s: (3,2,complete).
- Fatal first trial: (1,0,fatal), original state/clock/remaining exact.
- One-trial budget after0.001s: (1,1,budget), remaining retained.
- Already complete: (0,0,complete), no state/clock change.
- Repeated second-stage rejection: (3,0,budget), proposed0.0005s retained.
- Fatal trial after0.004s accepted: (2,1,fatal), accepted state retained.
- Negative requested remainder: (1,0,fatal), invalid-progress diagnostics retained.

Invalid host trial-slot budgets, cumulative limits and unpaired continuation
records also fail before invoking the stage callback. Test-only bad fractions
exercise failures; production has no fault-injection options. No gates relaxed.

Shader SHA256:
`06dae8f7887ead3f37ae02c9f1572ebc02cb47b9f493333775e91bc53f9956c9`.
Water-detail DLL SHA256:
`28641cab4685819cc692ab4560c8e773267cfecd52626ff3b9b64ec5826c64f1`.
CPU equations are unchanged this turn; the preceding137-test CPU result stays
historical evidence for that unchanged code, not a claimed new test run.

Full actual-D3D12 regression48199 CLOSED exit0:72clean passes, zero warnings,
failures or unrun tests,16.850071s. Report:
`unreal/Saved/RaftSimValidation/south-fork-total-advance-regressions-v1-20260913/index.json`.
The selection retains the three explicit pressure/transport/step fixture flags
and adds `RaftSim.WaterDetail.TotalDepthAdvanceGPU`. Map, water material and
career save hashes were rechecked and remain unchanged.

## Integration still required

This helper does not add wall time, own the game-thread/render-thread handoff,
provide physical open-river boundaries or mean/window/bed exchange, transport
or generate foam, classify breaking fronts, or publish the shared completed
render/contact surface. It is not enabled in the normal game. Those remaining
pieces must be integrated incrementally into the normal South Fork run, with
actual motion and cost checked; no known-broken solver should be enabled merely
to alter a screenshot. Current normal-play21.571211FPS/p9552.6052ms still fails
the requested30FPS/33.333ms target. Reference videos remain unviewed; no repeated
unchanged browser failure was attempted on this heartbeat.

The plan's stale rapid-challenge launch paragraph is now explicitly historical:
South Fork is the scenario, Troublemaker stays off-menu, and all five normal
South Fork launch contracts retain the full river map. No menu/content/save
mutation was needed for that documentation correction.

Cook96057/PID29104 continues without restart. BOTH independent state/artificial-
bank audits pass for3500/local30000 and3600/local32000. All5,382,400 cells finite,
all86,720 artificial-face cells exactly dry. At3600s outlet88.396459 versus
inlet45.306955m3/s still indicates settling; no runtime promotion. Next complete
3700/local34000 snapshot requires both audits. Latest live progress3667.5s /
local33350. Full goal remains active.
