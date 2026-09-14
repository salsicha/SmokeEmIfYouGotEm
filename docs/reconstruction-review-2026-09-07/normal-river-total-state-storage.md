# Conserved GPU state and render projection — September 12

This goal turn made implementation and verification progress. It does not
complete playable water, physical breaking, froth or 30 FPS qualification.
The complete remaining scene/terrain/reference/other-river/crew/release/commit
scope remains active. No game screenshot or new reference playback is claimed.

## Real GPU storage component, not an evolution solver

Added `RaftSimTotalDepthStateGPU.h/.cpp`, `RaftSimTotalDepthState.usf` and
`RaftSimTotalDepthStateTest.cpp` in the existing WaterDetail module.
The component consumes total `(h, hu, hv, foam density)` directly. It copies
surviving cells exactly across signed integer window shifts and uses explicitly
supplied total state for newly exposed cells. A changed or dry reference mean
does not erase surviving water. There is no implicit zero initialization,
periodic wrap, relative-height re-encoding, density clamp or simulation-clock
advance. Invalid descriptors fail before allocating output; invalid selected
state/reference values are counted and never repaired in conserved storage.

The same immutable input produces a separate float4 surface projection:
`(bed-reference_surface)+h`, its spatial derivatives, and bounded foam coverage.
Conserved state is never reconstructed from this output. This prevents the
previously demonstrated float32 cancellation of a 1e-12 m depth encoded as eta
relative to a 0.1 m mean. The projected surface is not an additional liquid level.
It is the render/contact output that a future completed-frame owner must publish
together, only after rejecting invalid-frame diagnostics.

This component is an RDG storage/projection stage. **It is not yet called by the
playable perturbation owner and does not implement total-depth evolution,
pressure, physical inflow/outflow, bed-change reconciliation, source exchange,
breaking or foam generation.** Existing gameplay state interpretation and
shaders are unchanged. Do not enable it by merely reinterpreting old eta/q as
h/hu/hv, and do not call the new storage test a gameplay integration pass.

At 128x128, its two float4 output buffers hold 0.5 MiB plus 16 diagnostic bytes;
that is buffer payload accounting, not a complete frame/process memory or GPU
cost measurement. The existing 512x512 dimension limit is retained. The full
8,192 MB release memory budget and other solver/performance gates are unchanged.
No cost-equivalence or frame-rate improvement is inferred from the test duration.

## Build and actual-device verification

Build session 58956 succeeds in 18.32 s, with five actions, using the existing
Win64 Development Editor target and four-action limit. WaterDetail DLL SHA-256:
`6f93cff88dcebc36809c203a295691e1b28350a6e33cd2748fad380cf47aed55`.
No ordinary-play water algorithm was switched by this build.

Single-test session 14068 exits zero and its actual report records one success,
zero warnings/failures/unrun cases:
`unreal/Saved/RaftSimValidation/south-fork-total-state-storage-v1-20260912/index.json`.
It runs on the AMD Radeon graphics device with D3D12 SM6, not NullRHI.
The 17x13 non-square fixture exercises partial thread groups and six shifts,
including zero displacement/changed reference, both signs, and near-total
window replacement. It verifies 1,326 bit-exact state cells, including 225 tiny
positive depths down to 1e-30 m. Derived surface maximum component error is
8.94069672e-8 against the CPU projection. Bad shapes/strides/no-overlap/spacing
are rejected; negative depth/foam, orphan dry momentum and nonfinite selected
data are explicitly reported rather than clipped away.

Full established native suite session 9239 exits zero. Report:
`unreal/Saved/RaftSimValidation/south-fork-total-state-regressions-v1-20260912/index.json`.
It records **66 successes, zero warnings/failures/unrun tests**, 18.720861 s test
duration. Coverage includes water/detail, shoreline, support, atlas, history,
window transfer and career/progression. The catalog fixture explicitly rejects
`troublemaker_challenge` and any scenario launching the bounded Troublemaker
map; progression migration returns an old rapid selection to
`south_fork_full_descent`, preserves historical rapid completion without marking
the river completed, and removes the rapid from selectable unlocks. These are
fresh native checks of the user's scenario distinction, not a fresh menu video.

Raft DLL, South Fork FullReach map, V4 water material and saved game rehash
unchanged after these tests:

- Raft DLL `ebd2936315c832530d1ebb32a25ee77b78f07ce3a0600c7eb893aa2ae5c1b3f6`.
- Map `db3080cc87f82bafbcb5403757fead35ca6b7a5d4b52dc74c35548d5faf7abb6`.
- Material `26aa5029c579afad38fd603f96df9da304bd32ed338097d2580c9a29545ea82a`.
- Save `181d1e570485d1ec3139aec4e1d9b56d0a420fd107ce5a94218368324207f5b1`.

Latest measured ordinary-play performance remains the prior 21.571211 FPS /
p95 52.6052 ms report. No FPS capture was made with this new DLL; neither old
measurements nor this native test establish the required 30 FPS pass.

## Longer CPU replay found another arithmetic failure

The first weighted 20-second replay (session 4864 / PID 25112) is **finished,
failed**, not still running. Preserve
`tmp/south-fork-depth-weighted-pressure-bank-twenty-second-v1-20260912.json`.
It reports `Invalid nonlinear pressure RHS or iteration budget`; the console
also records reciprocal overflow in `1/h` followed by invalid multiplication.
This is not evidence of an iteration-budget change. The input state was never
clipped or repaired. That version did not preserve a state on first-stage rate
errors, so its exact failure time/state is unavailable; the last emitted
progress was 4.008333 s, not its failure time.

The reference now divides proportional hydrostatic force directly by depth,
instead of forming the potentially overflowing reciprocal first. A regression
with positive depth 1e-310 m checks finite pressure/acceleration under strict
overflow/invalid/divide error handling, without adding a film floor. This is an
arithmetic correction, not a change to equations, iteration count or tolerance.
Further first-stage rate failures after accepted steps now save the exact
last-accepted state and elapsed time, separately from budget exhaustion and
invalid initial input. An injected-failure test verifies that evidence path.

116 unique focused Python tests pass in 37.76 s (session 37327). Current hashes:

- Bank driver `3a53a35fb0a0ec774a69a04e594350383932f5c01ab02b057d291ed74432257c`.
- Pressure module `4a63c91038ba15915d5a0757c9ddca29e057308d6b6f004776a85f992850ae61`.

Corrected 20-second v2 is live as session 20297 / PID 30532, started local
22:19:55, report
`tmp/south-fork-depth-weighted-pressure-bank-twenty-second-v2-20260912.json`.
At 4.008333 s it has 481 accepted steps and no retries. It starts from the
original paired capture, not a repaired failed state. Preserve its live handle.
Original centered five-second session 2816 / PID 14124 remains live and has no
final report yet; do not restart it because a poll times out.

## Hydraulic checkpoint and next work

The separate source-exact cook remains live as session 96057 / PID 29104.
The 3,000 s / local 20,000 checkpoint now passes BOTH finite-state/conservation
and artificial-bank audits: 5,382,400 finite cells, 86,720 artificial-face cells
exactly dry, maximum depth 4.198490394 m and speed 7.135705088 m/s.
Volume is 2,938,391.655052163 m3; driver error 3.725290298e-9 m3 and maximum
step conservation residual 1.425201424e-8 m3. Outflow 89.397159194 versus inflow
45.306954547 m3/s still indicates settling. Runtime stays at 600 s. Next audit
is 3,100 s / local 22,000 after its completion marker exists. Full record:
[expanded checkpoint](full-river-expanded-checkpoint.md).

Next: inspect the corrected long replay and its retained failure state if any;
then evolve conserved GPU state with paired bathymetry, compatible nonlinear
pressure and explicit boundary/mean exchange, using this storage/projection
contract. The full physical breaking/froth and single completed render/contact
frame still need implementation and engine motion/reference validation. Do not
substitute this transfer-only component or a hydrostatic-only control for that
end state. All remaining rivers, terrain/collision, crew, normalization,
performance, release checks and final commit remain required.
