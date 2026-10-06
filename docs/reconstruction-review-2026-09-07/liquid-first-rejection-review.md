# First GPU rejection and physical-coordinate routing

September10,2026. South Fork and the full requested queue remain incomplete.

Previous snapshots could miss the first failure because its timing differed
between runs. A1280-byte persistent GPU latch now captures one actual rejected
particle at the first failed exit step. It stores the native step/owner/index,
reason bits, full raw particle payload, route, and actual float32 frame/points.
An atomic claim prevents later threads/owners/steps from overwriting it. Storage
is allocated once per simulation generation and read only after stop. It never
changes the exit gate, particle data, ledger, or normal successful execution.

`diagnose_liquid_first_rejection.py` validates the fixed record/layout/generation
and matches it to the first failed exit transaction. It then independently
classifies the captured original segment against source geometry in float64.
It is diagnostic evidence, not an acceptance shortcut. Four unit tests cover
raw bits, stale/truncated/malformed records, empty initialization and valid JSON
representation of invalid floating-point values.

## Verified recorder and first clean replay

- Build40528 succeeded147.08s.312 liquid Python tests pass.
- `engine-liquid-first-rejection`, UE16700 terminal0: all14 engine tests pass,
  with no test warnings/failures. GPU regression verifies first-step retention
  through later dispatches and every raw payload word, including NaN/int bits.
- `liquid-native-first-rejection-flow`, UE62191 terminal0:120steps/118commits,
  no rejected crossing. The original dense/P2G audit91929 terminal0 passes:
  712453 final particles, all12 raw transfers, zero reduction mismatches,
  20156 nonzero shared cells, physical volume14830.9418315m³ versus nominal
  14842.7712757m³ within the original172.0937425m³ numeric bound.
  This is only a two-second native replay, not sustained discharge or visuals.

## Repeat exposes the exact mismatch

`liquid-native-first-rejection-flow-v2`, UE99304 terminal0, is REJECTED atstep40.
The latch matches the first failed commit and preserves owner11/index37333:

- The routing record says interior owner11 (`route.w=1`).
- Exit classification computes lateral8100.00048828125cm, outside8100cm.
- Independent original-frame calculation gives8100.000424677762cm, also outside.
- The independent crossing is valid outgoing north face3, row1252.
- The exit shader rejects the disagreement (reason2/status8), not dry water,
  terrain penetration, inlet reversal, or a wrong source particle.

The router divided coordinates by50cm before comparing with cell extent162.
GPU reciprocal rounding can map this one-ULP exterior point back to162 exactly.
The exit classifier compares centimetres directly, causing incompatible topology.
This explains why a clean run alone did not prove the previous issue resolved.

## Correction verified in two short replays

Both shaders now share `RaftSimLiquidPhysicalFrame.ush`, using the same precise
world-to-physical calculation. Routing compares physical centimetres before any
normalization; regional ownership also uses physical half-open rectangles,
closing only the parent's final outer edge. No epsilon-expanded river boundary,
clamping, deletion, or looser exit predicate was introduced.

The GPU routing regression now covers the actual8100cm extent, points one float32
ULP above/below it, the exact edge, internal cuts, full payload and empty/overflow
cases. Build49119 succeeded22.10s. UE11072 (`engine-liquid-physical-routing`)
terminal0:14 regressions pass (one unrelated HTTP warning, no test failures).
UE37573 and UE55575 are terminal0: `liquid-native-physical-routing-flow` and
`liquid-native-physical-routing-flow-v2`. Both120-step/118-commit replays have
empty rejection latches and pass original dense identity/mass/P2G audits
(37257 and47472 terminal0). Both retain719335 initial+4474 births-11354 approved
exits=712455 survivors. All12 raw transfers pass with zero reduction mismatches.
Physical volume14830.962112/14830.967512m³ versus nominal14842.812942m³ remains
within the original172.097315/172.093999m³ numeric bounds. No bounds relaxed.
These are two-second replays, not sustained discharge, water surface/foam, raft,
real-reference or performance acceptance. No map promotion/commit/push.
