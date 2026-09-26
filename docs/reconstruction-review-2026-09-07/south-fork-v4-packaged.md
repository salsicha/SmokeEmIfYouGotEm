# South Fork v4 packaged execution — September 26

Follow-up: the startup detail failure below is repaired by the
[range-preserving entrainment change](south-fork-entrainment-roundoff.md).
This report and its binary hash describe the original failed candidate. The
same stage now contains the repaired executable; the old executable/symbols
are retained separately for rollback. Original receipts remain unchanged.

The Development package at `tmp/south-fork-playable-v4-20260926/Windows`
completed build, cook, stage and package with exit 0 in 751.53 seconds.
This delivers the current bed-v2 / bundle-v4 scene and far-field presentation
to an actual cooked executable, not only editor play. Previous stages remain
untouched. This is a validation candidate, **not river or release acceptance**.

## Identity and self-contained data

- Inner executable SHA-256: `66a090e969d27a4adc13a0aa4e94fd7a56c50f3ed4fef4486dfecd6343eb1df1`.
- Package log retained at `tmp/south-fork-v4-package-success-20260926.log`,
  SHA-256 `9e5abbe736b2f5d35fdb865f26d955f680ce354b5e373d08e58baa104ca08ad1`.
- [Payload receipt](south-fork-v4-packaged/payload.json): all 2,405 files,
  917,958,633 bytes and the exact dependency closure match active v4 manifest
  `8963a44e2ef1798e4926ac4a17f2928ab35050636c5eb637a4d672ea10127cbe`.
- The first verifier invocation failed on a 268-character path. PowerShell
  confirmed the file existed; rerunning with a Windows `\\?\` extended path
  passed without copying or repairing any payload. Use extended paths for
  Python verification of this deep stage. The failure receipt is retained in
  `tmp/south-fork-v4-packaged-payload-20260926.json`.

The native non-editor resolver checks packaged project-binaries/base-dir data
first. Its remaining relative fallback is within this staged Windows tree,
not the source checkout. Runtime logs confirm both coordinate maps bound.
This is supported by the exact packaged closure check, not a new file-I/O trace.
Other-river material edits overlapped the original cook; this candidate does
not certify the entire project. South Fork code/config/map/terrain/canopy/v4
inputs matched the build-start revision at the subsequent check.

## Actual normal launch: timing passes, health fails

The inner packaged executable was launched twice without a project or map
override, at 1280x720, through Boot → main menu → FullReach → post-travel CSV.
No solver, station or quality overrides; ephemeral profile; offscreen rendering.
Both exited 0 with unchanged executable hash. Each captured 1,200 frames and
audited rows 30..1169 under the existing policy. These are start-section runs,
not full-route performance tests.

| Run | Mean ms | p95 ms | Max ms | Frames >100 ms | Runtime health |
| --- | ---: | ---: | ---: | ---: | --- |
| First | 25.3617 | 39.3731 | 45.0082 | 0 | failed |
| Health rerun | 25.0867 | 38.8723 | 46.3444 | 0 | failed |

[First timing](south-fork-v4-packaged/menu-timing-first.json),
[health-gated rerun](south-fork-v4-packaged/menu-timing-health.json),
[rerun log](south-fork-v4-packaged/menu-health.log).

Both logs contain `Stateful detail dispatch rejected: Invalid mean-flow depth,
velocity or aeration`. The 128x128, 0.5 m moving detail component stopped after
3.260 / 3.243 seconds and 20 / 21 flow preparations. Failure happens **before
the post-travel CSV starts**. Thus the favorable frame cost is measured with
a failed detail subsystem and cannot establish healthy 20 FPS acceptance.
The raft/live mean-water continue; do not confuse that with continuing detail.

The profiler now retains Error/Fatal log lines, exposes runtime health and a
combined healthy-timing gate, and explicitly leaves physical acceptance false.
The new parser regression and existing packaged-path regression pass. The
existing p95/hitch metrics remain unchanged, rather than hiding the timing data.

## Separate rendered motion check

A separate packaged direct-FullReach review-camera run used the ordinary spawn,
no station relocation and `CaptureRaftSeries 12 10 0.5 ... 7 2 3 6 paddle`.
It is not the normal-menu performance run. All 10 numbered PNGs exist in the
stage's `SmokeEmIfYouGotEm/Saved/Screenshots/`, with advancing render frames
332..404 and world times 12.346483..16.844851. Logged speeds are 1.89..2.50 m/s.
The game exited 0. [Motion log](south-fork-v4-packaged/motion.log).

Frames 0, 4 and 9 were visually inspected: raft/paddle poses and terrain-relative
position change; the water and shore remain rendered without a gross open seam
in this short view. The water remains broadly smooth here. This is neither a
rapid-breaking-wave acceptance nor proof of long-duration shoreline stability.

![Packaged motion first frame](south-fork-v4-packaged/motion-000.png)
![Packaged motion last frame](south-fork-v4-packaged/motion-009.png)

Normal-launch raft samples remained wet, had zero ground points/penetration,
~14 cm rendered floor freeboard and zero reported support delta. That verifies
short starting-water support, **not boulder collision or the full shoreline**.
No new source evidence or reconstructed geometry was promoted this run; bed
under water remains inferred, and far-field presentation remains non-colliding.

## Next bounded repair

Instrument the invalid detail input with its cell index and exact depth,
velocity and aeration values, and trace it through `UpdateMeanFlow` sampling,
interpolation, entrainment and accepted-crest merge. The present error does
not establish which component is invalid. Repair the producer with a focused
regression; do not relax the guard, clamp unexplained bad values, disable detail
to meet FPS, or enable experimental strain. Rebuild/restage and recheck healthy
normal-menu play before treating frame times as acceptance. Busy-rapid cost
(already measured over 50 ms elsewhere), reconstructed collisions, stable
shoreline/surface continuity and physical validation remain open. South Fork
is unfinished; Colorado, Pacuare and Futaleufu stay queued.
