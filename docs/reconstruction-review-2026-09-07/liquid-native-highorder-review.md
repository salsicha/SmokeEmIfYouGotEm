# Native wave-preserving surface integration — 2026-09-11

The full goal remains active. South Fork is incomplete; no saved-map promotion,
scene completion, final commit or push. Previous goal turn made progress by
fixing shared physical velocity and testing regional high-order transport.

## Native integration

`-RaftSimRegionalHighOrderInterface` now enables limited BFECC on the retained
native surface, using current post-extrapolation velocity and current boundary
classifications. It requires unified particle/interface transport, shared
velocity and pressure coupling. All twelve regions run the same five stages,
exchanging intermediate scalar AND validity data. The updated surface is retained
for the following native pressure/particle step. The visible renderer is still
not connected to this test runtime.

The operator accepts either an explicit correction-blocked mask or the native
RGBA16F boundary: type 0 fluid, 1 solid, 2 air, 3 prescribed exterior. Types 1 and
3 retain the existing first-order transport instead of receiving high-order
correction. An initial header comment incorrectly called 0 air/2 fluid/3 moving
solid; corrected against the local projection implementation. The actual mask
logic was always 1-or-3 and did not change with this documentation correction.

Invalid/nonfinite scalar or boundary values and unsupported forward/third-forward
traces invalidate the step. Reverse trace failures can only produce explicitly
accounted accuracy fallback. Schema v2 stores all eight counters per owner/step;
the independent audit checks updated counts, failures, high-order-plus-fallback
accounting, limiter counts and reverse failure accounting. No tolerance changed.

Captured source provenance now requires exactly fourteen named snapshots for
the declared high-order/residual-boundary mode, including the native runtime,
GPU operator, shader and header; earlier modes retain their exact seven/ten-file
contracts. Every snapshot is hash checked.

## Independent regional reference and physical exterior limitation

The new CPU reference separately performs the forward/reverse/correction/
forward/limiter stages and all scalar/validity exchanges, rounding stored scalar
stages to float32. It passes a 24-step four-region/corner comparison against the
whole-grid CPU algorithm with an obstacle crossing the cut. Failure, ledger,
disconnected/overlapping-layout and unmodified-input tests also pass.

A strict whole-grid assembly attempt on the actual previous 600-step capture
found duplicate physical-exterior extensions that disagree. They are not averaged
or silently treated as identical. `liquid-exterior-extensions-v1.json` records:

- All shared physical XY samples agree for velocity, phase and scalar.
- 65 velocity samples outside the physical XY domain differ; maximum 93.25 cm/s.
  The first failure encountered by strict assembly was 7.734375 cm/s at owner 7.
- Two outside-domain scalar samples differ by 0.0000076293945 cm.
- Boundary phases agree over all overlapping samples.

The staged regional reference therefore preserves each owner's actual provisional
exterior extension. This proves the implemented regional transport, NOT a
globally consistent physical exterior boundary condition. That boundary remains
required work; the whole-grid assembly rejects inconsistent inputs rather than
fabricating one reference field.

## Verification

- Build 66369: success, 41.06 s.
- `liquid-highorder-native-boundary-engine-v1`: four clean successes. Twelve
  actual native boundary fields match the stored CPU solid-mask references;
  four native-boundary regions match one explicit-mask whole GPU grid.
- Build 11707: success, 20.65 s.
- `liquid-highorder-native-boundary-engine-v2`: four clean successes, including
  invalid phase 4 and NaN in exterior cells. Both invalidate all five stages
  (ten recorded invalid-value events), not only the owned portion of the field.
- Build 69600: success, 37.22 s after the header documentation correction.
- Full liquid suite: 539 tests pass, 8.474 s. Earlier 538-test run also passed.

### Actual twelve-step replay

`liquid-native-highorder-12-v1`, session 61078, exit 0. Source snapshots unchanged.
Diagnostic wall time 37.33 s, not FPS. All eleven retained transport steps and
2,178,720 selected-step samples validate, max CPU scalar error 0.0000457764 cm.
Shared native velocity and all eight-word counters verified. Dense original
729,724 + 412 births - 464 exits = 729,672 survivors, original survey preserved.

### Actual 600-step replay

`liquid-native-highorder-600-v1`, session 9590, exit 0. All snapshots unchanged.
Diagnostic wall time 70.73 s, not FPS. Stages SHA256:
`d9aed7048891f33a239d86c4a4d5445ec655045626f77f892796a8fc4481958a`.

- Dense audit: 729,724 original + 22,533 births - 25,337 exits = 726,920 survivors.
  All 598 compact commits verified. Original outer survey remains intact; one
  internal storage/survey owner difference is retained in the report.
- `liquid-native-highorder-600-advection-v1.json` contains the complete interface
  validation as well as particle motion, avoiding a duplicate verification run.
  599 surface transports, 982,407,920 owned updates, 2,178,720 selected-step scalar
  samples. Max CPU scalar error 0.01354218 cm, below unchanged 0.02 cm; RMS
  0.0000094511 cm. Shared physical velocity is separately verified.
- Higher-order updates 410,664,842; extrema limited 594,574; explicit fallback
  571,743,078; no reverse, forward or third-forward trace failures. These count
  all owned grid cells, not only water or its visible surface. GPU/CPU branch
  counts are retained, not claimed bit-identical.
- All 726,920 particle positions replay within 0.004080523 cm (same 0.02 cm
  gate). Instantaneous interior divergence RMS 0.000272016/s, not a measurement
  of integrated volume conservation.
- Tracked surface coverage: 91 particles outside, zero unsupported stencils;
  66 outside particles lie within 5 cm of the bed. Largest positive scalar
  32.4848 cm is NOT geometric distance. No particle was removed or called spray.
- Physical problems persist: peak particle density 12.36109x; the separate
  fixed-density candidate misses 6,970 particles and 663 occupied columns. This
  candidate is not the tracked scalar or the rendered water.
- Last requested-duration budget interval: inflow 47.0474 vs outflow 37.4138
  m3/s; nominal storage change -59.1875 m3 over 598 commits. Not steady-flow
  or measured-discharge acceptance.

The preceding first-order/shared-velocity capture was independently rechecked
with the SAME native-frame coverage method: 128 outside particles versus 91 in
the high-order replay, zero unsupported stencils in both. Their coupled native
trajectories/populations differ, so this is a matched-configuration replay
comparison, not a same-particle-position experiment or proof of surface-volume
conservation. Largest positive scalar falls from 69.7952 to 32.4848 cm; neither
number is geometric distance. The fixed-density candidate is a different field.

All owned jobs terminal: native61078/9590, audits28652/68402/31831/78704/90407,
tests82523/27756, builds66369/11707/69600, GPU56862/34641. All exited0.
No pending worker or UE process is being left running. Scoped whitespace check
passes with line-ending notices only.

## Next work / handoff

Native high-order surface transport is now integrated and numerically verified,
but remains an opt-in test runtime. Next: couple whole-support density/contact
correction with the transported interface; resolve physical exterior/Z values,
geometric surface volume and sustained discharge; connect/verify a single visible
frothy breaking surface with real references, boat/rock response and gameplay
FPS. Then finish Colorado, Pacuare, Futaleufu and all remaining queue items.

Saved playable map unchanged, SHA256
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
About 2.2 GB free on C:; avoid redundant native captures. No files deleted.
