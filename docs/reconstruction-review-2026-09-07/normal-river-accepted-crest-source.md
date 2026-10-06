# Accepted crest source in moving water — September 12

## Integration gap

The normal moving detail owner prepared depth/u/v and then ran
`FRaftSimDetailEntrainment::Build`, which derives a local compression/Froude
source. It did not use the accepted crest source already computed for the
macro carrier by `ComputeCoupledBreakingReliefMeters(...,&OutCrestFoam)`.
Since the local material replaces the CPU foam input inside its registered
window, accepted crest production could be omitted from persistent detail.
This is an implementation finding, not proof that it explains all observed
smoothness or missing froth.

## Change under verification

The adapter now exposes the exact accepted dimensionless crest source, using
the same retained sites, current flow orientation, spilling fraction and
compact support. It does not require positive missing/subgrid height: a jump
whose mean rise is already resolved can still spill. The moving Cartesian
owner samples that source at its actual half-metre texture coordinates, masks
dry cells, and takes max(existing compression source, accepted crest source).
The estimates are not added; raw depth/u/v and the solver are unchanged.
The merged source enters the existing persistent foam/activity/pressure
forcing update; it does not paint density, add a surface, or reset state.
Legacy fixed review behavior is retained.

This remains an empirical source potential and pressure closure, not measured
bubble production, calibrated turbulence or an overturning 3D liquid solver.
The existing compression source outside accepted crests is still heuristic.
No terrain, macro height profile, source grid, material or acceptance gate was
altered.

The new regression compares22,326 exact oriented source samples across zero
and positive missing height and zero/partial/full spill. It verifies the public
adapter, max merge, wet mask and removal of sites. Actual owner logging at10s
reports augmented wet cells and source bounds, without runtime readback.

## Verified build and actual gameplay

Build98487 succeeds,199.66s, existing D6 damping conversion warnings retained.
Regression12575 exits0:57successes, zero warnings/failures/unrun:
`unreal/Saved/RaftSimValidation/south-fork-accepted-crest-source-regressions-v1-20260912/index.json`.
RaftDLL `0098679b933110eba49acae18e2001b7c78af8f6593161e1f41b7d6048899445`;
WaterDLL `5f517ab05070538e0186c24e3ffa61a4cd99da0b2a5abf4635268e59f83dd239`;
mainDLL `f306c15acbb9a8c7b4751baa15aa2512120ace94867147c6c5af5c07f98dce5b`.

Actual normal-map game58415 exits0. At10s,541wet cells receive additional
accepted-crest source, maxaddition0.850000024, textureorigin[-5458,3567]m.
The integration changes actual simulation input, not just fixtures.
Three GPU snapshots reproduce independent resolve within1.022476675e-7.
Wet-interior detail RMS5.951/7.513/6.469mm, extrema acrosssnapshots
-8.416/+8.152cm; mean coverage.121/.163/.164. This is still centimetric
perturbation, not overturning macro liquid. Reports:
`tmp/south-fork-accepted-crest-source-snapshots-v1-20260912/analysis.json`.

Actual shared-crest mesh audit1,497,240samples: max0.5997479984cm<=2cm,
sourcechange0, finecorrectiontracking0.000844598cm. GPU perturbation and other
relief/contact are excluded. Actual source UV3 transport/UV1 bulk errors0.
Reports `tmp/south-fork-accepted-crest-source-{crest,transport}-v1-20260912.json`
(crest appends `.cartesian-mesh.json`).
Frames000/039 inspected: broad smooth wave and thin foam persist, NOT visual
acceptance.40 unique PNGs span12.012sampled game seconds, fixed camera.
Movie `unreal/Saved/VideoCaptures/RaftSim_20260912-161947.mp4`, SHA256
`5c673ee3a2331668058b5c83be2ff17c8e71e392660f9f9c873f14fff6394626`.
88sourceframes/16.503s; not FPS or continuously viewed footage.
Diagnostic recording lags4.714266s. Motion report
`tmp/south-fork-accepted-crest-source-motion-v1-20260912.json`.

Isolated profile58864 exits0; new cook29104 suspension/resume both return0.
Same151row100..250 interval: mean67.036796ms=**14.917181FPS**, p9582.2928ms,
GPU18.731479ms, crestupdate21.667059ms. This run regresses from17.674567FPS
and STILL FAILS60. Short variable-trajectory intervals cannot isolate all of
that difference to the new source preparation. Measured preparation averages
1.924248ms/update versus prior.904009ms; extra per-cell profile queries are a
real remaining cost. Ordinary detail34.025002s over34.029s, backlog4.013ms,
3 exact remaps,0teleports. At10s,634cells receive accepted source (different
raft trajectory from diagnostic capture), max.849999905.
CSV SHA256 `abc9747841e2984c348f20c1808ac63ec67aedcbbfb852a21fa689aa384bcdee`;
report `tmp/south-fork-accepted-crest-source-performance-v1-20260912.json`.
Mapdb3080cc…, materiale4e9b2f3… and save181d1e57… rehashed unchanged.

NEXT: physical macro crest/overfall, persistent froth optics and GPU/raft
contact still need actual acceptance. The source hookup alone did not fix the
broad smooth macro shape. Reduce remaining current-profile/vertex/refresh/GPU
cost without weakening accuracy/cadence gates; source-only evaluation need not
calculate unused toe/tail heights. Continue complete river/crew/release queue.
New long hydraulic cook96057/PID29104/start23:20:51.6847346UTC continues from
audited2000s toward4000s; next2100/local2000 needs state AND banks. No promotion
from runtime600s and no new real-reference footage viewed.
