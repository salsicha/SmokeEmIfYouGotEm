# Paired source terrain/water motion and the wrong-viewport capture defect

September 18, 2026. Supporting integration evidence, **not an accepted river or
normal-play terrain update**. The preceding commit-only turn made concrete
progress by committing the paired-review code and passing 94 related tests.
This turn actually exercises that pair in FullReach, exposes and fixes a capture
defect, and records the remaining visible problems rather than accepting them.

## What is now exercised together

The source-supported candidate from [the union review](constriction-union-review.md)
is reused on the original ground actor, with the existing captured cap retained.
No second ground, changed material, saved level, or persistent profile is added.
The old height-only revision contract remains strict. A separate explicitly
unaccepted PIE descriptor binds 3,273 dependencies; it does not exercise the
linked C++ preview loader or promote anything to ordinary scenario launches.
Descriptor SHA256: `f65cacda107df659c3e0e67bcd4b71fbfaab51d3c9757e000a760bf0d8308463`.

The candidate's fresh 50-second atlas uses all 799 source packets. Eight packets
change, with 8,648 changed source samples; 791 are reused only after exact
decoded comparison. All 42,185,039 exported bed intersections match the source
union. Coverage retains all 406,823 original water probes and the unchanged
8m minimum interior-margin gate (actual minimum 10m). The existing allowed
repair excludes unsupported physical-exterior cells in region_0002; it does not
fill missing cells or move the original reference water probes.
Live window centres remain unchanged for403,001 probes and shift for3,822
(maximum102m), as explicitly recorded by the coverage audit.

The [native result](constriction-paired-motion/constriction-runtime-50s-native-v1-20260918.json)
passes all 70,017 full-map collision queries and all 25,600 changed-core water
queries. Bed/surface maximum error is 7.62939453125e-6m; velocity error is below
2.358e-7m/s; wet/dry mismatches are zero. Every actual play launch repeats the
native field check, then confirms exactly one candidate ground, no old ground,
one retained cap and the exact paired water configuration in the PIE world.
These numerical checks do not classify the original class1 returns as rock.

The unsafe old station8330 start is not reused. At station8300 the actual
native field gives centre depth2.5223498m, bed6.7007446m and surface9.2230988m
above the220m datum. A wet centre alone is explicitly not full-hull clearance.
The existing progress axis is unchanged and is not a surveyed navigation line.

## Captures that were rejected, and the actual defect

The first launch's nested startup quoting never executed Python. Only that
owned editor was stopped; both original cooks resumed through retained handles.
The second run did execute the paired scene but captured1014x550 instead of
1280x720. An editor-only, offscreen-PIE viewport-size helper now resizes the real
game target without changing saved editor preferences or resampling images.

The third run still had two wrong-size frames; the fourth had one, despite an
explicit two-second presentation delay. Inspecting the fourth run's rejected
frame proved that this was **an empty editor viewport, not the player view**:

![Rejected editor viewport](constriction-paired-motion/rejected-editor-viewport.png)

Unreal's screenshot request is global, and both editor and game viewport clients
can consume it. A successful request or PNG file therefore did not prove that
the player viewport was captured. This is a demonstrated cause of misleading
screenshots in this review, not a claim that every historical screenshot had
the same cause.

`RaftSim.CaptureSeries` now explicitly reads the current game's backbuffer for
offscreen PIE before yielding the request to editor rendering. It refuses an
editor fallback when that read fails. No extra physics/render step or image
resampling is introduced. These stills are the last rendered player frame;
they are not a GPU-fenced match to the game-thread pose logged at the request.
The ordinary standalone asynchronous capture path is unchanged.

The final v5 run finishes successfully:96/96 native player-viewport confirmations,
96/96 actual1280x720 PNGs, no timeout, and all saved source/map/profile hashes
checked by the play script remain unchanged. Missing/duplicate/failed native
capture confirmations are rejected by the launcher. All failed reports are
retained alongside the successful [process report](constriction-paired-motion/south-fork-constriction-paired-v5-20260918-process.json).

## Actual raft motion and remaining visible failures

The ordinary seated camera and unsteered raft start at8300. No camera pose,
teleport sequence, artificial steering, or altered solver is used.140 observed
raft poses span world0.4..49.96264s. The last screenshot request reports
station8385.913m; this is a bounded approach, not full-river or full-rapid
traversal acceptance. Observed pitch spans-19.234..15.499degrees and roll
-20.774..5.189degrees. Four ten-second drift samples are wet, have zero dry/
ground support points and zero reported ground penetration. That sparse contact
telemetry does not establish collision clearance at every intermediate frame.

The47.479s recording has402 source frames. Its complete1424-frame decode passes,
with65 exact adjacent duplicates; encoded30Hz is **not game FPS**. Source movie
SHA256: `13087f3d75e41b8ccec4f805558ced95c28316a3d23fab0da6487ed425f2be9d`.
The [decode report](constriction-paired-motion/decoded-motion-v5.json) binds the
original movie and sampled images. Recording begins after the explicit2s
presentation delay; the raft pose record includes the earlier start.

Inspected20/30/40/47s frames show the raft approaching and turning around the
rock mass, descending and tilting with the live water. They also show broad
smooth white bands, rigid angular/spiky rock flanks, repeated angular canopy
and unfinished crew/gear presentation. These are not convincing breaking/frothy
water or source-faithful exposed rock acceptance. The previously inspected
bank/raft references remain qualitative, not a metric registration; this turn
does not claim a new reference-video observation.

![Actual movie at30s](constriction-paired-motion/movie-30s.png)

![Actual movie at40s](constriction-paired-motion/movie-40s.png)

Do not mistake the source-exact vertex/collision proof for acceptance of the
inferred flanks between samples. The newly observed spiky mass needs its own
source/actor identification from these downstream views before changing it;
the earlier foreground identification at8330 cannot simply be reused there.

## Continuing work and unchanged limits

Baseline9500,9550,9600 and candidate100s pass BOTH full-state and artificial-bank
audits, retained here. Neither cook is accepted as settled. Both exact original
jobs remain active; every capture launch verifies PID, start time, executable
hash and command line before suspending either, and resumes both via the held
handles in `finally`, including every failed capture. No cook was restarted.

The candidate still uses an interpreted338-return extension plus explicitly
inferred flanks. No new certification of class1 points, source registration,
underwater survey, or measured rock outline is implied. Installing the full
fresh50s atlas would change all799 windows; this one local motion review does
not qualify that whole-river replacement. Saved FullReach terrain and its
installed4950s water remain unchanged. South Fork remains the scenario and
Troublemaker remains a rapid, not a menu entry.

119 focused Python tests and the non-mutating PowerShell identity/capture
controls pass. The actual native viewport guard cases reject null world and
out-of-range dimensions, and the final motion run verifies the valid resize.
Editor AND standalone game builds pass, and the existing native
`RaftSim.M4.CarrierCaptureIndex` test passes. The builds retain the unrelated C4701
warning in `RaftSimDetailSourceFootprintTest.cpp`. Unreal's existing Concert
initialization errors are also retained; this is not a clean-log release pass.
The saved FullReach map SHA256 is still
`c6bda5ff5f680d22b291eb30a6c902488acd909bb7f2b6177fa7103cdd40399f`.

No new performance acceptance is claimed: these screenshot/recording/PIE runs
are not benchmarks. Latest ordinary-game24.937420FPS/p9549.3295ms still fails
the user's30FPS target. Nonlinear runtime remains OFF. Next work remains
source-supported flank/rapid-shape correction and convincing coupled crest/
breaking/froth, followed by qualified incremental normal-play integration and
fresh normal-launch motion/cost checks. Colorado, Pacuare, Futaleufu, the other
water/crew reviews, regressions and release gates all remain open.
