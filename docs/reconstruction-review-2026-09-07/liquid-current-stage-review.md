# Current-surface ordering for secondary whitewater

September 9, 2026. Isolated South Fork review, not production promotion or
photorealistic acceptance. This follows the [endpoint/contact review](liquid-secondary-exact-endpoint-review.md).

## What changed

An owned editor-only Niagara data interface, `URaftSimLiquidStageInterface`, now
provides a real pre-stage callback for the existing secondary emitter. With the
opt-in `RaftSimLiquidSecondaryCurrentSurface` flag, reconstruction runs after
primary integration and before secondary stages. It publishes to the existing
single visible SimRT and the read-only secondary cache. No engine asset/source,
primary particle state or hydraulic grid is rewritten by the reconstruction.

The previous post-render callback remains for the control path and paused
rendering. The current-stage path refuses a late simulation fallback when a
required pre-stage callback was missed. The shader's binding marker and actual
dispatch counters are both inspected; merely adding a DI to a graph is not proof.

An additional defect was found in the old once-per-render-frame guard: captured
GPU time jumped by two simulation steps after five blocking diagnostic captures.
The final implementation reconstructs **every secondary first stage**. Graph-local
clock/foam history carries intermediate states when multiple ticks share an RDG
graph. It reads primary `CurrentData`, which advances after each primary dispatch
group, rather than a rendering pointer only promoted after the final queued tick.

The existing end-of-step classifier now samples that current field. Its legacy
transport prediction still handles the previous-field control; residual timestamp
rounding is not misrepresented as exact analytic surface reconstruction.

## GPU synchronization corrections

RHI validation, not screenshots alone, exposed three resource-use defects:

1. Between dependent Niagara groups the live particle-count buffer remains in
   UAV state. A read-only UAV packing permutation and an explicit UAV handoff
   barrier now respect the preceding group's ended overlap. The count is never
   modified. A new actual-GPU test compares SRV and UAV reads for empty, partial
   and over-capacity counts, arbitrary stride/offset, rotation/translation and
   unit conversion, and confirms all original counter entries stay unchanged.
2. The water material reads SimRT through an external texture binding in an early
   depth pass. A later RDG compute-only read could be transitioned ahead of that
   untracked graphics use in paused capture views. The view-initialization hook
   now declares graphics/compute read access before scene passes. The old-timing
   control reproduced this defect, so it was not caused solely by moving stages.
3. Diagnostic raw GPU buffer copies omitted copy-source usage and tracked
   transitions. Exported reconstruction buffers now declare `BUF_SourceCopy`,
   and blocking inspection uses RDG readback passes. Two older test-fixture
   diagnostic buffers received the same required usage flag. Pool-reused buffer
   debug names initially looked like unrelated instance-culling resources; the
   corrected readback path removes those errors too.

## Measured evidence so far

| Actual capture | Airborne spray inside rendered water | Foam absolute interface distance p95 | Engine/RHI errors |
| --- | --- | --- | --- |
| Previous endpoint prediction, 60 s | 1,290 / 10,544 | 4.96 cm | 0 without RHI validation |
| `liquid-secondary-current-stage-tracked-12s` | 0 / 11,668 | 0.936 cm | 0 with RHI validation |
| `liquid-secondary-current-stage-tracked-60s` | 0 / 11,737 | 0.941 cm | 0 with RHI validation |
| `liquid-secondary-current-substeps-12s` (final per-step path, two substeps/frame) | 0 / 11,392 | 0.919 cm | 0 with RHI validation |
| `liquid-secondary-current-every-step-60s` (final per-step path) | 0 / 11,942 | 0.952 cm | 0 with RHI validation |

These are separate stochastic simulations, not identical-trajectory causal
comparisons. All final sampled bubbles in the listed current-stage runs are
inside the rendered water; foam can straddle the interface. None of these
statistics proves sprite visibility, all contact trajectories, calibrated river
physics or photorealism. The water still looks cyan/glossy and has rounded
fragments and the visible rectangular bounds of this diagnostic window.

The two-substep capture verifies **1,428 first-stage events, 1,428 reconstructions
and 1,428 positive GPU time increments**, with up to four simulation steps in one
RDG graph. Maximum GPU delta is 0.0087890625 s, consistent with 1/120 s steps and
the established split-half clock quantization. The final GPU age is 12 s versus
independent simulation telemetry 11.999903 s. Pause, live reconstruction, actual
affine gradients, exact sampled secondary terrain/domain contact and unchanged
foam source/history tolerances pass. There are 1,472 total reconstruction updates
including rendering-only callbacks. See its `stage_order_audit.json` and other
independent audits; do not substitute callback counts for simulation time.

157 numerical tests pass. All 15 engine liquid regressions pass without test
warnings or errors under RHI validation in
`engine-liquid-current-stage-validated-readbacks`. That suite precedes the final
per-step guard/history edit; the subsequent two-substep actual capture exercises
that edit with RHI validation and independently verified clock/field results.

The final 60-second run verifies all **3,594 first-stage dispatches,
reconstructions and positive GPU time steps**, with maximum delta 0.01708984375 s.
GPU age 59.9990234375 s agrees with independent age 59.999256 s within the existing
clock tolerance. All 13,135 sampled bubbles are inside; sampled foam has median
absolute distance 0.458 cm and maximum 1.203 cm. Captured secondary bed/domain
contact, pause stability, live positions, affine gradients and foam transport
pass. There are 3,667 total updates including rendering-only callbacks and 30
distinct motion frames. This does not prove every trajectory or visible spray.

`liquid-secondary-current-every-step-benchmark` has 480 uninterrupted editor
intervals: mean **26.038 ms**, p95 **28.732 ms**, p99 **30.695 ms**, maximum
**101.764 ms**. The spike is retained, not trimmed. Reconstruction GPU mean is
**5.410 ms** (density 4.613, distance 0.580, foam/copy 0.216). No engine errors;
independent benchmark audit passes. This is an isolated 960x640 scene-capture
fixture, not packaged-game FPS or full-scene performance acceptance. Relative
to the separate prior endpoint benchmark, mean is slightly lower but p95 is
slightly higher; these runs do not establish a statistically significant speedup.

## Retained failures and controls

- `liquid-secondary-current-stage-12s`: first ordering capture, useful alignment
  evidence but no RHI validation; superseded for resource correctness.
- `liquid-secondary-current-stage-validation-60s`: improved alignment but failed
  RHI validation. Not accepted despite completed capture and zero exit status.
- `liquid-secondary-current-stage-handoff-12s`: counter handoff fixed, but graphics
  and readback errors remain; rejected.
- `liquid-secondary-stage-control-validation-12s`: old timing reproduces the
  graphics error; tracked readback errors no longer occur.
- `engine-liquid-current-stage-validated`: 13 passes / 2 failures due to missing
  copy-source flags in the older foam and occupancy test fixtures. Retained.

## Remaining scope

Address physically plausible hole/crest geometry and the cyan/glossy optics
against real reference footage. An isolated fixed-geometry extinction/roughness
comparison is in progress; its authored coefficients are not measured turbidity.
Integrate the result into the continuous single playable surface and verify
shoreline, raft support/current, boulder interaction and whole-scene cost. The
captured-source provenance and inferred bed/discharge uncertainties are unchanged.
South Fork and the full Colorado -> Pacuare -> Futaleufu / other-river / crew /
cleanup / release queue remain active. No production promotion or commit.
