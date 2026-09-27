# Healthy v4 motion through the Troublemaker approach

September 27, 2026. Actual rebuilt-game validation, **not a new playable change
or completed rapid reconstruction**. The earlier repaired v4 run covered the
11,520 m section; this check covers the previously problematic captured-rock
approach at 8,330 m with the repaired detail simulation still running.

## Run and observed motion

The unchanged packaged v4 executable launched the normal FullReach map and
`south_fork_full_descent`, using the explicit 8,330 m review start, ephemeral
profile, D3D12/RTX3060, 1280x720 and ordinary solver/contact settings. No
continuous-contact override, altered geometry, water/material mask, lowered
quality or physics cadence was supplied. This is direct station access, not a
fresh Boot/menu traversal; the prior normal-menu result is not extended here.
The existing capture command issued AllForward and retained the normal camera.

Process37672 exited0. Runtime contains no `Error:` lines. Detail remained healthy
for38.079s:820 paired commits,823 rendered-frame snapshots,239 flow preparations,
zero PDE backlog, five exact moving-window remaps and zero teleports.

Twelve requested screenshots span world12.437..34.066s. Recorded station changes
from8341.408 to8367.994m. Progress briefly slows/turns near8343m, then near8364m;
the latter samples are8364.357 at28.049s,8363.902 at30.066s,8364.515 at32.070s,
and8367.994 at34.066s. This is not proof that the entire rapid has been traversed.

The recording completes with529 source frames over25.720s. Full decoding
successfully reads772 presentation frames,0..25.7s,1280x720, with four exactly
identical adjacent decoded pairs. The encoded cadence, interpolation and
recording overhead **do not establish gameplay FPS**. No FPS qualification is
claimed; the previously recorded busy-rapid20FPS failure remains authoritative.

Inspected original decoded frames at video1s,9s and20s: raft/camera position,
orientation, paddles and water pattern change, with the raft beside exposed
rock and then downstream. No gross roof-height jump or open water seam is
obvious in those three views. They still show coarse/angular inferred rock
flanks, broad white foam patches and smooth water faces; physical/photographic
acceptance remains open. Full decoding is not full visual inspection of every
frame, and does not establish uninterrupted hull clearance.

## Contact observations narrow the remaining question

The existing read-only observer records54 corrections >=5mm (below its64-row
cap), all on `SourceMatched20260917/SM_SourceMatchedGround`. Independent native
re-queries match the solver's float height in every observation. Maximum
vertical correction is0.014087863m; accumulated corrections total0.493569058m,
which is **not net raft rise or a complete energy balance**.

All54 observations occur at world1.327..12.673s. Thus the later turn/brief
station reversal at28..32s has no recorded >=5mm height correction and did not
hit the observer's capacity. This distinguishes it from a large roof-projection
jump; it does **not** exclude smaller corrections, ordinary friction/contact,
water forces or paddle torque. Do not delete an inferred flank or enable an
experimental contact solver on the strength of these data. The next causal
check should separate those forces at the later turn rather than repeating
the unchanged source-identity lookup or this capture.

## Evidence and limits

- [Game log](south-fork-v4-troublemaker-motion/game.log), SHA256
  `71dc1176ebb769a6060037d6bed122ffcc252d8c62b029f8a3888816afb4ec90`.
- [Contact observations](south-fork-v4-troublemaker-motion/contact.json), SHA256
  `575fcbb8c724d4885e64d7245dbd0c1f295c83f46f733f136a0086dc987c03ed`.
- [Full decode report](south-fork-v4-troublemaker-motion/decode.json), SHA256
  `3b1dbdb0a0b666828caaafb9a82d6188e555e784575ab3bbcd29112b52c06b8e`.
- Original recording remains only under the staged game's
  `Saved/VideoCaptures/RaftSim_20260926-210257.mp4`, SHA256
  `522c5c7b57d3f05660e672a520b36dec320a2674937256b7479977080a985c04`.
  It was not duplicated into tracked evidence. Decoded original views are in
  `tmp/sf-v4-troublemaker-decoded-20260927/`.
- Reproduction helper: `tmp/run-v4-troublemaker-motion-20260927.ps1`. It refuses
  pre-existing evidence or competing engine/build processes and checks the
  executable hash before and after. Both match
  `12d71f2830633d51d9b8851e9b4524b58fd74be33176d331092e6fd76433e523`.

No source/scene/cooked-field edits or new build/cook. Existing work from the
other session is preserved. South Fork remains first unfinished; hydraulic
settling, convincing breaking water, geometry/shoreline/continuous contact and
busy-rapid performance are still required before moving down the queue.
