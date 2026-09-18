# Centered, torso-driven crew vests

September 18, 2026. A scoped visible character improvement in normal South Fork
play, not whole-crew or river acceptance. No captured terrain, hydraulic field,
water solver, body mesh, PPE asset, helmet dimensions or collision changes.

## Diagnosis and correction

The original side capture showed the PFD floating forward of the chest while
its upper rear panel disappeared into the back. The old anchor added 9 cm ahead
of the spine. An opt-in addition to the existing CC0 pose forensics measures
actual CPU-skinned wetsuit vertices in the chest frame, in a central lateral
band within 8 cm of its middle and three 10 cm vertical bands from -12 to 18 cm.
This is posed mesh evidence, not surveyed human dimensions or a full intersection
test. Five distinct bodies were observed; repeated startup appearances are not
independent samples. At the upper band the original front/back extrema are:

| Body | Back x cm | Front x cm | Envelope midpoint cm |
| --- | ---: | ---: | ---: |
| Crew01 | -17.6631 | 7.8979 | -4.8826 |
| Crew02 | -16.9243 | 6.2450 | -5.3397 |
| Crew03 | -16.5702 | 6.7433 | -4.9135 |
| Crew04 | -16.7117 | 7.4343 | -4.6387 |
| Guide | -17.4050 | 7.7241 | -4.8405 |

A 4.5 cm rearward correction (forward offset 9 to 4.5 cm) recenters the vest
without enlarging it or removing body geometry. Actual normal-play comparisons
show the rear panels exposed instead of buried. All-five front/right/rear
turntables confirm reduced forward float. The shared fit is still approximate:
strap gaps, shoulder-edge overlap and an arm/front-panel intersection on Crew03
remain, rather than being hidden or certified.

The broader pose review also exposed a separate orientation defect: the vest's
forward direction was derived from the **face** projected onto the spine plane.
The reentry head pose turned the vest sideways. The chest frame now uses the
rendered right-minus-left shoulder line crossed with spine-up. Head turns no
longer steer or translate worn torso gear; helmet attachment remains head-driven.

`raftsim.CC0VestForwardOfSpineCm` is a review control (4.5 default, 9 reproduces
the previous translation). `raftsim.CC0PoseForensics=1` enables the posed-band
measurements; they do not run during ordinary gameplay. The turntable script
can now write to an explicit review root and refuses to overwrite an existing
capture manifest. No fixture lighting/LOD overrides are used by normal gameplay.

## Regression scope

`RaftSim.Crew.VestFollowsTorsoNotHead` loads all five actual CC0 bodies and checks
four actions at three phases (60 cases). It verifies a real head perturbation,
finite chest transforms, forward handedness when seated, and unchanged chest
position/orientation after the head turns. It is not a garment intersection test.

The runtime rescue test's stale 0.90..1.10 helmet range rejected the September 6
crew correction while accepting oversized shells. It now checks the exact
reviewed role-specific values (0.90 guide / 0.84 crew, tolerance 0.0001), retaining
all existing attachment, orientation, ownership, rescue and other checks.
The MetaHuman branch is unchanged. The matching header comment is corrected.

## Final default validation and limits

The final editor and standalone Development builds succeed (v4:14.11/37.58 s).
The native production asset/pose and runtime rescue tests pass on the unchanged
production code in v3. The new head-invariance regression passes again on v4,
including the actual head-perturbation assertion, with zero warnings/errors.
Its v3 actor-teardown warnings were fixed by letting the scoped world own actor
cleanup. The rescue test still reports the existing `r.MotionVectorSimulation`
render-thread-safety warning; this is not a clean-release-log claim. Four focused
Python helmet/seat-contact contracts also pass.

The all-five v3 turntable uses default placement, not a fit override, with 65
images and 15 action-pose attachment checks. All-five front/right/rear candidate
views and representative final rear/reentry views were inspected; the final
guide, Crew01 and Crew03 reentry views show chest-facing panels, no longer the
sideways vest from the translation-only candidate. Straps and helmet-to-vest
clearance under deep head flexion remain imperfect. Static poses and finite
attachment checks are not continuous rescue-motion/intersection acceptance.

Final normal South Fork start, `south-fork-crew-vest-default-v4-20260918`, has no
fit, forensics or material-audit override. It produces 24 actual engine PNGs and
a15.646-second recording with219 source frames. All469 encoded frames decode;
27 frames after the first second are exact duplicates. Images000/012/023 were
inspected: the rear panels remain exposed in the actual river view while the
raft moves. This does not establish realistic paddle/reentry motion or game FPS.

The separate ordinary rapid cost run uses900 frames, every row60..840, at
station8330, no screenshots or diagnostics. It measures **25.003520FPS,
mean39.994368ms, p9548.329ms**, failing the unchanged30FPS/33.333333ms gate.
This is not a paired FPS comparison; no performance gain is claimed. The wrapper
confirms nonlegacy timing and its one-row water-scope alignment. Nested CPU
scopes are not summed. The existing cook13584 is identity-checked and resumed
successfully after every gameplay capture; final startup/cost CPU brackets are
both unchanged. Games exit zero without timeout. No duplicate cook is started.

[Evidence](crew-vest-torso-fit/evidence.json) retains all unique body-band
observations, source-log hashes, arguments, sampled image/movie hashes, binary
hashes, native/turntable results, decode statistics and full cost metrics.
Raw images/movies/logs remain preserved locally under ignored tmp/Saved paths.
This change is available in default play, not just the turntable. A new packaged
content release, full collision/shoreline/crew/water acceptance and the broader
queue are not completed. Installed terrain/map/4950 fields remain unchanged;
nonlinear stays OFF. The pending cap decision remains unanswered. The next
unaudited baseline snapshot is still11400/local48000 and needs BOTH audits.
