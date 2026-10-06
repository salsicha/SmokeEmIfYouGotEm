# Normal-start briefing stays on screen

September 23, 2026 UTC. Delivered HUD layout correction in the normal game,
not completion of South Fork reconstruction or a water/performance improvement.

The preceding final-serial recording (`RaftSim_20260923-085916.mp4`, SHA256
`f84f49050788854c4dfbf81ae7926474bb35fd61cbf54285758b54055893d81f`)
showed the briefing's rescue controls cut off below the 720p image. The old
text region began at canvas Y=760, with only 240 units of allotted height,
despite a longer wrapped title/briefing/controls string.

The normal HUD now uses a bottom-left anchored, viewport-bounded region.
Explicit wrapping provides stable desired text height; a down-only ScaleBox
fits the entire text when needed without removing words or adding a scroll
interaction during gameplay. The region accounts for the root's centre-based
saved UI scale, rather than multiplying its bottom edge off-screen. Only a
viewport-size change updates the layout. Original wording and fade logic remain.
No new command-line opt-in is required. Run-complete text uses the same region.

## Verification

- Editor/game rebuilt successfully, 12.19/64.65 seconds for the final build.
  Initial v1 failed a local variable/member shadow warning-as-error; v2 fixes
  the name rather than suppressing the compiler check. Both logs are retained.
- Three native tests pass with zero warnings/failures/skips: new
  `RaftSim.M7.TransitionSafeRegion`, existing career catalog and progression
  migration. The new test covers five viewport shapes and all four supported
  UI scales (0.75/1/1.25/1.5), checking transformed bounds, bottom margin and
  the lower-40-percent limit. This is region math, not font rendering or
  interactive resize acceptance at every setting.
- The rebuilt editor's normal South Fork Full Guided Descent game launch uses
  no station override or layout flag, with an ephemeral profile. Not a menu-click
  or packaged-executable test. A 15.558-second actual-engine recording contains
  235 source frames; all 467 encoded frames decode at 1280x720 through 15.533333
  seconds, with 39 exact adjacent duplicates. Encoded 30Hz is not game FPS.
- Decoded 1/3-second views show the full title, briefing and `E/R/F: rescue`
  line inside the bottom edge. At 6 seconds it is fading; at 11 seconds it is
  gone while status/environment HUD and raft motion continue. Source PNG
  capture requests hide UI; these PNGs are not the text-layout evidence. The
  decoded back-buffer movie frames are. Canopy, soft water and crew/lighting
  artifacts remain visibly unfinished.
- Separate ordinary D3D12 1280x720/4-lane capture: 300 CSV samples, all rows
  60..240 selected (181). Measured 25.504336 FPS, mean 39.209019ms,
  p95 47.7349ms: FAIL 30FPS/33.333333ms. Game-thread mean 38.927552ms;
  GPU mean 13.060088ms. Not a causal before/after UI-cost comparison or sustained
  acceptance. Timing mode confirmed as nonlegacy with scope offset1.

[Native and motion receipts](transition-fit/evidence.json) and
[ordinary cost, process and build hashes](transition-fit/cost-and-builds.json)
retain exact evidence. The source audit6480/startUTC2026-09-23T15:18:43.5347928Z
was validated, suspended/resumed through a retained handle for both captures;
all statuses zero, CPU brackets zero, and CPU advances afterward. It remains
live on case1 with no complete report. No new cook/replay, protected import,
captured source, terrain, collision, bed, water field or solver change. The
rejected base-vertex candidate remains diagnostic-only; nonlinear stays OFF.

## Remaining scope

This closes only the observed default 720p intro clipping. Other UI-scale and
portrait renders, all-scene UI overlaps and long localized/run-complete text
still need broader visual review. South Fork water realism, source qualification,
geometry/physics consistency, collision/traversal and 30FPS acceptance remain
open. Colorado, Pacuare, Futaleufu and the rest of the user's full queue are not
advanced or marked complete by this HUD fix.
