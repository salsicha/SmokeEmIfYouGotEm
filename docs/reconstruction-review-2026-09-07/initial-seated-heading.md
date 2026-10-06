# Initial seated camera alignment

September24 normal-gameplay correction; river acceptance remains open.

The explicit25.4276352km start in the terrain follow-through produced a bank-facing
view: camera yaw about179.78deg versus raft85.00deg, with angular foreground
geometry crossing the frame. Existing seated-heading transport preserved that
roughly95deg offset because its first observation happened after initial raft
attachment; it carried later raft turns but not the initial spawn-to-seat turn.

The guide pawn now remembers its pre-attachment BeginPlay yaw and seeds the
heading observer with that yaw once, on its first actual flat-screen seated view.
The control rotation receives only the spawn-to-current-seat delta, preserving
user look already accumulated. Delayed possession is supported; subsequent chase,
swimming, cinematic and HMD gates retain the existing no-replay semantics. No
forced per-frame recenter, camera substitution, extra body hiding, source mesh,
water or map edit was made. The world-locked diagnostic still bypasses carry.

Editor build `tmp/initial-seat-heading-editor-v1-20260924.log` succeeds182.84s;
Game build `tmp/initial-seat-heading-game-v1-20260924.log` succeeds140.02s.
Native report `tmp/initial-seat-heading-native-v1-20260924/index.json`:

- `RaftSim.Guide.SeatedHeading`: PASS, including initial180→85deg attachment
  retaining7deg user look, no second-tick replay and later chase-return semantics.
- `RaftSim.Survey.ReviewCameraUsesScenarioDownstream`: PASS.
- `RaftSim.M7.CameraWeather`: FAIL on guide/chase local-exposure highlight/face
  settings at `RaftSimM7PresentationTest.cpp:191`. These are not heading assertions;
  this turn does not change the exposure settings or weaken the test. Retain the
  regression for investigation; do not summarize this run as all tests passing.

Actual-game motion `south-fork-initial-seat-heading-motion-v1-20260924` uses the
same explicit review start and ordinary seated camera with the correction enabled
by default. Logged camera/raft yaw at capture4 is84.958747/84.940151deg,
capture10 is84.137590/84.131708deg, capture20 is83.787338/83.771405deg. The small
differences are observed frame timing, not an exact lock assertion.

Recording `unreal/Saved/VideoCaptures/RaftSim_20260923-205348.mp4`, SHA256
`eda4baa7d8f7a3e81a6614327209cd928ca8c6fee56a330e68f8d6a96f0397d9`, fully decodes
465 frames through15.466667s with29 exact adjacent duplicates. Original decoded
frames/report are under `tmp/initial-seat-heading-motion-decoded-v1-20260924/`.
Inspected3s/6s/11s frames show the downstream crew/river view, no prior angular
foreground obstruction, and continuous terrain at the previously floating ridge
patches while river station advances25.43→25.45km. Only those frames were visually
inspected; full decoding is not all-frame visual acceptance or an FPS measurement.

The engine exits0; the guarded original cook36692 is resumed. This is a delivered
camera alignment correction and bounded temporal terrain evidence, not full-route
travel, scenery/crew realism, shoreline stability or river acceptance. The prior
destination p9533.3562ms failure remains; the changed view requires fresh cost
measurement and normal-start/reentry regression qualification.

## Normal startup and corrected-view cost

`south-fork-aligned-camera-cost-v1-20260924` measures the corrected distant view
with the saved terrain range:900 frames, rows60–840, confirmed FrameTime mode and
offset1. Mean22.084942ms, p9533.7009ms, maximum78.4555ms: FAIL against33.333333ms.
CSV SHA256 `365d76f6723e3ed8df97c1a66f50cf1a608de80d48972f7a28dc82508a12301e`;
audit `tmp/aligned-camera-frame-v1-20260924.json`. This is an explicit review
start, not ordinary-start traversal, and is not evidence of a camera-induced
performance regression without a controlled comparison. The performance gap remains.

Ordinary startup (no station override) is recorded separately as
`south-fork-aligned-normal-start-motion-v1-20260924`. At capture4, camera/raft yaw
is−179.679772/−179.656761deg; at capture10,−178.951761/−178.949383deg. Video
`unreal/Saved/VideoCaptures/RaftSim_20260923-205958.mp4`, SHA256
`7fe3b7996342eaaeca24970cc1d3aaacbf2cb7414b6a9e4283bd3a7fe818e45b`, fully decodes
465 frames through15.466667s,24 exact adjacent duplicates. Original frames and
receipt: `tmp/aligned-normal-start-motion-decoded-v1-20260924/`. Inspected3s/9s/11s
frames retain the seated crew view, moving water and advancing station0.12→0.14km,
without the previous angular foreground obstruction. Shading/crew/water realism
is not accepted by this check. Both guarded engine runs exit0 and resume cook36692.

The M7 exposure failure is traced to obsolete configuration expectations, not a
newly changed exposure implementation: commit `a61d758f9` on August27 deliberately
changed highlight/shadow/blur blend to0.86/0.76/0.70 and detail/kernel to0.75/65%.
`docs/water-visual-feature-plan.md` records that anti-flicker rationale and historical
measurements. The native regression still expected0.78/0.72/0.50. Its independent
literal expectations now follow the documented contract and additionally check
both detail/kernel override flags and exact values. Production exposure and old
failure reports remain unchanged; this does not remeasure or accept flicker.
Editor rebuild succeeds69.64s (`tmp/exposure-contract-editor-v1-20260924.log`).
Fresh native report `tmp/exposure-contract-native-v1-20260924/index.json` passes
all three requested suites, with CameraWeather carrying an engine warning about
`r.MotionVectorSimulation` render-thread access without ECVF_RenderThreadSafe; the
previous failure report is retained. This is configuration-regression repair,
not a new exposure treatment or visual acceptance. Production Game binary from
the preceding camera-fix build remains current for gameplay code; only the native
test changed in this follow-through.

Measured next performance investigation: `RaftSimShorelineMeshComponent::SetMesh`
has mean4.37ms/p955.88ms in this capture, including topology mean1.25ms/p951.74ms
and crest update mean1.80ms/p953.09ms. These scopes overlap/nest and cannot be
added. Inspect unchanged-topology updates and source packing for exact-result
savings before considering any reduction in geometry or water fidelity.
