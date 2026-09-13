# Terrain-aware surface integration — September 11

The goal remains active and all requested scene work remains incomplete. This
pass makes numerical implementation progress, not visual or physical acceptance.
The preceding user-status turn was informational only.

## Why the original integral was slow

The scalar-only split integrator partitions changes in vertical liquid
intervals, but the fixed registered bed also clips those intervals. A vertical
crossing can enter/leave the bed between quadrature samples. Merely increasing
the tensor-product order repeatedly spends work across the same discontinuity.

`refine_liquid_shared_volume.py --split-quadrature` was connected to the full
729672-particle early state. Its new diagnostics save nodal gradients and local
column errors when a measurement completes. Sources were snapshotted before
execution. All565 liquid tests passed8.512s before this run.

Run62212/PID30628, `tmp/south-fork-liquid-shared-volume-split-v1-20260911`, was
explicitly stopped after its verified command line matched this owned process.
This was a deliberate cancellation of a superseded comparison, NOT a timeout
inferred to mean termination. Its session subsequently returned exit1.
Latest completed order64:8201/82665 columns unresolved, volume15266.946559m3,
190920404 queries,873.82s. Order128 had not completed. Its progress and source
snapshots remain; there is no completed report, saved per-column integral or
accepted map from this interrupted run. Do not report a full order128 failure
or a successful refinement for it. No source used by it was edited while live.

## Implemented exact terrain partitions

- `liquid_bed_ray_intervals.py`: bounded original-triangle ray clipping, explicit
  edge intervals and affine bed heights. Shared edges integrate once; distinct
  arbitrarily short intervals are retained. Off-mesh queries reject.
- `liquid_bed_contour_intervals.py`: scalar-level roots, bed/Z-slab crossings,
  and quadratic roots of phi evaluated on each affine bed segment. This splits
  contact changes without changing the bed, scalar, or particle volume.
- `liquid_terrain_volume_gradient.py`: both X-edge bed contacts and Y-ray contact
  partitions. Complete, non-overlapping bed intervals are mandatory. The same
  original nodal weights, vertical negative intervals and explicit caps apply.
- `liquid_adaptive_terrain_volume.py`: adaptive X subdivision. Child error
  budgets are proportional shares of the original column budget; estimated
  errors add without cancellation. Depth exhaustion remains failure. Most
  columns use orders2/4; failures use8/16 with subdivision to depth14.

An analytic regression exposed false convergence when both quadrature orders
missed a narrow contact at an X edge: uniform-gradient error.000143125 despite
the apparent local pass. Explicit X-edge bed/contact roots resolve this case
exactly (12 decimal places); the test was retained. A separate curved-contact
case checks adaptive subdivision, analytic volume/gradient, original error
budgets and explicit depth-exhaustion failure. These are estimated quadrature
criteria, not rigorous certified bounds.

## Captured-state bounded evidence

`audit_liquid_terrain_quadrature.py` selects64 deterministic columns from19623
contour-changing captured columns, preserving all source data. This is NOT an
all-river test. It retains coordinates, per-column volumes/gradients and sources.

First Y-bed-only run13808 exited1 after68.87s:
`tmp/south-fork-liquid-terrain-quadrature-sample-v1-20260911`.
At order128 one column remained unresolved, max gradient change.000140886,
volume3.07715388179m3. ReportSHA:
`b89b2ded1f36f4f6d2e19ba004359eecb00db40072cf5177e666f08bfb932af6`.

After explicit X-edge contacts and adaptive subdivision, run18849 exited0 in
9.574s on the SAME64 columns:
`tmp/south-fork-liquid-terrain-quadrature-sample-v2-20260911`.
All64 resolve;2 initially required subdivision, the last at depth8. Total
1219144 queries, volume3.07715399838m3; estimated volume-difference sum1.1260e-6,
gradient-difference sum.000475374 across64 columns. The per-column volume and
gradient gates remain1e-4. All source snapshots unchanged. ReportSHA:
`8034704a6d5f4525be3e9c7bcea374fee824683211bfb50b2a9907ad9fc6ef7d`.
The independent scalar-only order32 comparison still differs by up to
.000407081 in gradient; that lower-order comparison is not an accuracy proof.
Neither timing is gameplay FPS.

## Full-state refinement now running

UPDATE23:10UTC: this run is now TERMINAL, not running. Session66257 returned
exit1; no process35912 remains. Total3437.496s, all source snapshots unchanged.
ReportSHA2a25bcfab6180c1bd60f3a6a64740f05e4999ca85e8e09f27e6a2e2c0571e988.
The complete initial82665-column integral now resolves (volume15266.946413m3,
excess65.445960m3). The1324-constraint shared volume/contact solve converged
in3 geometry iterations. Neither nonlinear trial was accepted: alpha1 had
volume15203.82m3 but1 unresolved column; alpha.5 had15235.18m3 and2 unresolved
columns. Smaller trials failed exact bed/skin checks after native rounding.
Failure is `Nonlinear shared volume/contact line search failed`. Saved state
is unchanged seed,115 outside particles, not an accepted correction. Do not
restart this unchanged failure. Local diagnostic NPZ files are now available
to inspect the1/2 unresolved columns and rounded-contact failures separately.

New full-grid wrapper retains partial physical edge cells and scatters local
derivatives into the original ZYX field. `--terrain-quadrature` selects it for
both the initial derivative and every nonlinear trial. Fixed terrain/IDs/
particle volume, native rounding, swept bed/survey, continuous no-fold and
same-inverse-map checks remain unchanged. No global surface-height offset.

Run66257/PID35912:
`tmp/south-fork-liquid-shared-volume-terrain-v1-20260911`.
Started with729672 particles and target15201.500453040006m3. Revalidate this
specific handle before any restart. At14336/82665 columns, no unresolved
columns had been retained; that is partial progress, NOT a full result.
Algorithm files are snapshotted; do not edit them while the run is alive.
Full liquid suite579PASS9.004s, session27078terminal0. Scoped diff and added-file
whitespace checks pass. No native/GPU runtime code changed in this pass.

Latest saved playable map SHA remains
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
No UE/build, production promotion, commit or push occurred this pass. Native
density/contact/momentum coupling, exterior/Z conditions, sustained discharge,
single visible frothy breaking water, raft collision/response, gameplay FPS,
all later rivers, crew and final cleanup/release remain open.

## Actual normal playable scene inspected23:10UTC

Launched the real `/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach` with `-game`
at the frontend challenge's8320m start. No replacement review map. Baseline
session84302 exited0; eight actual1280x720 moving-raft screenshots:
`unreal/Saved/Screenshots/southfork_playable_baseline_20260911_2310_000.png`
through007; matching log in Saved/Logs. A second bounded comparison37669 also
exited0 with the existing `-RaftSimSpatialBreakingReview` flag; corresponding
`southfork_playable_spatial_20260911_2310` files. These were transient tests,
not a default flag change or shipped feature. First and last frames inspected
for both runs: water remains broad smooth pale bands with weak crest detail;
the flag does NOT visibly remedy that. Do not enable it as a purported fix.

Baseline log confirms one visible surface, material
`M_RaftSim_SouthForkRaftTransmissionWaterV4`,1.5m render spacing,26065 vertices,
initial refresh22.985ms, mean foam.0067, maximum hydraulic relief.2348m, no
boulder-wake foam vertices. One interior breaking site has crest.047m; four
edge sites are rejected. Logged live solver average~10.27ms, maximum14.65ms;
this is solver cost, NOT total gameplay frame time. Spatial comparison solver
average~10.56ms, max14.86ms. Screenshot writes stall capture frames, so no FPS
claim from the eight-frame burst. No terrain penetration in the logged raft
sample, but this does not verify boulder collision or full traversal.

Playable-first next step remains actual runtime/asset integration on FullReach.
The spatial-review switch alone is insufficient. Use the now-captured normal
material/geometry baseline when changing the visible surface and verify the
same normal launch path; do not return solely to repeated offline volume runs.
All numerical and engine sessions above are terminal. No build/map/asset edit,
production promotion, commit or push occurred during this heartbeat.
