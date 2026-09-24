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
