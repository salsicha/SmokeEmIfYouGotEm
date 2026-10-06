# Longer native flow: lossless stage journal and inlet frame

September 10, 2026. South Fork and the full scene queue remain incomplete.
The preceding status-only reply was not implementation progress. This pass
extends actual simulation testing and diagnoses another boundary disagreement.

## Bounded evidence, unchanged water gates

Dense stage capture now interns exact complete observed participant records,
including every iteration, loop, reset, birth count and generation. Each actual
group retains its render frame, graph ordinal and template address. Nothing is
sampled or inferred from an expected schedule. Limits:262144 groups,4096
templates,8388608 template characters; overflow fails closed. Native histories
still retain304 bytes/commit. Only one optional full diagnostic snapshot is
allowed. Dense replay supports3600 native steps (60s at the driver's1/60 step),
with an1800s diagnostic wall-time bound. This is not production FPS evidence.

The reader supports both old and new captures, checks schema, complete counts,
addresses, generation, entry layouts and alignment counters, and supplies the
original records to all existing birth/identity/mass/generation auditors.
No mass, exit, transfer or P2G tolerance was loosened. Runtime solver unchanged
by the journal. Native memory allocation/dispatch reservations remain bounded.

Actual old capture `liquid-native-physical-routing-flow-v2`: all6424 groups
round-trip exactly through435 templates (1017757 characters), with its original
generation/birth audit unchanged. Build69790 passed16.85s after correcting the
new test's include path (failed build11190 retained). Engine89217 terminal0:
15 regressions pass, one unrelated HTTP warning.317 liquid Python tests pass.

## Ten-second run finds an inlet coordinate discrepancy

`liquid-native-journal-flow-10s`, UE59202 terminal0, completed600 requested
steps and saved31864 observed groups/435 templates/598 commit summaries.
Capture wall time65.128s is diagnostic time, not playable scene performance.
The dense/P2G audit REJECTS the capture: first commit failure atstep67,
control `[0,64,715737,105]`. The1280-byte GPU latch preserves the first failure.

Owner7 particle122024 crosses east face1,row277, with local end
24500.001953125cm outside the24500cm parent boundary. It is36.8074cm above the
original triangle bed; stage647.8179cm, prescribed inward speed3.18623cm/s.
The actual inlet marker is0: inlet advection did not correct this trajectory.
Routing and exit now agree on exterior status. Independent float64 calculation
also finds an exterior, wet, non-outgoing face. This is not an allowed exit.

The inlet code still reconstructed local positions from a separately rounded
centre plus half extent. It could round this one-ULP outside endpoint onto the
face, skipping correction. The new code uploads the exact float32 lower corner
and axes used by routing/exit in a separate read-only three-vector interface.
Niagara imports `RaftSimLiquidPhysicalFrame.ush` through its virtual include
property and calls the same precise physical-coordinate function. Existing
inlet momentum prescription and subsequent terrain contact remain unchanged.
No boundary expansion, particle deletion or reverse-inlet permission added.

Build90182 passed40.09s; additional compiled-frame regressions build20411
passed25.99s.318 Python tests pass, including the captured step67 input and
unchanged tangential/normal-response assertions. Engine31479 terminal0:
all15 regressions pass with no warnings/failures, including actual compiled
Niagara helper calls and bit-exact bound frame comparisons.

## Corrected frame replay: a different failure above prescribed stage

`liquid-native-inlet-frame-flow-10s`, UE88830 terminal0, completed600 requested
steps (64.500s diagnostic wall time). Original dense/P2G audit rejects it at
step306, control `[0,64,702151,126]`. The retained first failure is owner8,
particle887, west face0,row137. Its first-hit Z909.66375cm is above prescribed
stage879.21075cm and89.46167cm above actual terrain820.20208cm. Local start
X0.213806cm and end X-0.260185cm establish a real crossing, not near-edge
rounding. Inlet marker0 agrees with the intentional above-stage exclusion.

The unchanged exit policy forbids reverse flow at that row regardless of Z,
while inlet advection intentionally leaves above-stage particles unconstrained.
This is a different free-surface/boundary-policy issue, not evidence that the
shared-coordinate correction failed. Above the prescribed stage does NOT prove
this particular particle is disconnected spray: it may be part of elevated
bulk water. Do not relabel it or loosen the exit gate to pass the replay.

The exact compact accounting independently passes304 consecutive commits
through step305:719335 initial+11431 births-28652 approved exits=702114 live.
Five complete60-step bins have births2254/2256/2257/2256/2257 versus approved
exits5630/5945/5704/5639/5380. At nominal1/48m³ per particle and the driver's
1/60s step, inflow is about47m³/s but initial outflow is112–124m³/s. Stored
water is declining. These are startup figures, not stable calibrated discharge.
No final P2G acceptance exists for the rejected state.

Next: inspect local particle/free-surface history at the physical inlet and
reconcile the prescribed bulk boundary with above-stage water/possible spray,
including storage/discharge behavior, while preserving explicit particle
identity and mass accounting. Do not hide the issue with deletion, reflection
off an imaginary wall, increased stage, or changed allowed-exit labels.
The [DualSPHysics open-boundary formulation](https://github.com/DualSPHysics/DualSPHysics/wiki/3.-SPH-formulation#315-open-boundary-conditions)
describes support-width buffers, prescribed or extrapolated free-surface levels,
and explicit fluid/buffer transitions. That is design context for a consistent
boundary model, not validation of our FLIP implementation or permission to
change a gate without independent evidence.

All build/UE/audit handles from this pass are terminal, and a process check
found no UE/python/compiler running. Sustained discharge, rendered surface/foam,
raft/terrain collision, real-reference comparison and performance are still
required. No saved scene promotion, commit or push. Full queue remains active.
