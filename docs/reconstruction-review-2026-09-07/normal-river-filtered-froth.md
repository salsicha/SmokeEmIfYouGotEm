# Pixel-filtered froth boundaries — September 12

Current desktop target is30FPS, by the user's explicit revision; frame p95
budget33.333ms and two-frame hitch threshold66.667ms. Other quality, source,
physics and contact requirements remain unchanged. This is unfinished work.

## Rejected visual experiment — prior playable material restored

The candidate described below is NOT the current playable material. Fresh
read-only Python commandlet85592 exited0 and verified all six candidate graphs;
actual gameplay capture43881 also exited0. Forty PNGs were captured. Frames000
and039 were inspected: the sharpened foam forms conspicuous rectangular patches
and does not improve the broad, smooth wave shape. Continuous movie playback was
not reviewed. Numerical checks did not establish convincing froth.

The candidate was rejected and the exact prior material was restored from the
verified backup. Restored SHA256:
`26aa5029c579afad38fd603f96df9da304bd32ed338097d2580c9a29545ea82a`.
The rejected asset is preserved at
`tmp/south-fork-filtered-froth-recovery-v1-20260912/rejected-filtered-froth.uasset`.
The primary helper `RaftSimFrothCells.ush` was restored. Experimental shader code
now lives separately in `RaftSimFilteredFrothCells.ush`; the experimental GPU test
and installer reference that file. The 61-test result below precedes this
include-path move; it is evidence for the experimental code, not a fresh test of
the restored production helper. No performance acceptance is claimed.

Next visual work must address physical surface motion and entrainment rather
than sharpening grid interpolation again. The source, terrain, collision,
other-river and release work remains unfinished.

## Experiment and retained verification history

The previous advected clump field blends each pair of corner occupancies over
a whole cell. At1.7 cells/m its coarse transition spans approximately59cm.
The candidate narrows that transition to20% of a cell, approximately12cm.
This changes interpolation weights, NOT the transported density or final
coverage threshold. All weights remain convex; independent corner occupancies
still have expected coverage p. This is a statistical optical property, not
exact local area or liquid-mass conservation.

The smooth cubic is integrated analytically over the pixel footprint rather
than rendered as an unfiltered edge. Subpixel cells still fade to expected
coverage. Existing two-scale UV3 flow backtraces and their clock are retained.
World/phase arithmetic is marked precise to avoid amplified CPU/GPU coordinate
roundoff at narrower transitions. No geometry, pressure forcing or raft-support
surface is changed; this cannot establish physical breaking-wave acceptance.

GPU fixture now covers five pixel footprints and retains the original.0003
CPU/GPU parity gate. Independent4096-point quadrature checks the pixel filter;
resolved borders must reach zero/full occupancy without the whole-cell grey
ramp. Existing16,384-point expected-coverage sampling remains. Build96580 is
finished successfully in175.50s, with existing D6 damping conversion warnings.
Native63246 exits0:61 successes, no warnings/failures/unrun. Optical GPU test:
16,576queries, CPU/GPUerror.000298082829 within the unchanged.0003 gate;
finite16,384-point mean.118952689 for.12 target. Pixel-filter quadrature maximum
error2.50339508e-6. These are numerical tests, not visual or physical acceptance.

Installer `unreal/Scripts/integrate_south_fork_filtered_froth.py` is guarded to
current material26aa5029… and a fresh report/backup. It changes only the
existing optical custom node's code, with all links, four consumers, WPO,
normal/wetmask graphs and map/actor/ground/save files protected. Python syntax
check passes. Installer79661 saved material
`b7fee1312851ef0fd08a1c6a8dad9a537fd70d88e0a3b49dec63318fac1ba9f6`;
four consumers and459 protected files retained, all other nodes exact.
Backup SHA387bb750555aaae70fe03d2253f766d1c57d23dff2cff2b5c751137e10e9aaf7.
The installer exited1 despite writing a complete report and no logged error.
Fresh10411 all-six-graph equality and material hash pass, but it also exits1
without a logged error. These are NOT clean process passes. Both are retained;
a read-only commandlet recheck and actual gameplay are next. Save181d1e57…
remains unchanged. The installer now avoids interactive quit_editor when run
as a Python commandlet; no source/material code changed by that control fix.

Reports: `unreal/Saved/RaftSimValidation/south-fork-filtered-froth-install-v1-20260912.json`,
same-stem `.backup.zip`, `south-fork-filtered-froth-fresh-v1-20260912.json`, and
`south-fork-filtered-froth-regressions-v1-20260912/index.json`.

The previous goal turn made progress by recording and testing the user-authorized
30FPS target. This turn continues local visual implementation; unavailable
reference-video playback does not put the entire goal at an impasse.
