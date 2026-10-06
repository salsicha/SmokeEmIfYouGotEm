# Aerated froth / spray: standalone plunging jet

Status: new synthetic prototype, **not accepted** physically or visually.

`unreal/Scripts/build_water_feature_froth.py` prepares a 2 x 1.6 m closed tank
with a 0.35 m initial pool. A circular 0.145 m-radius source emits liquid
downward at a nominal 1.8 m/s during frames 1..72, then turns off at 73.
The hollow nozzle shares its visible mesh with its collider. Bottom and sides
are closed; three walls are invisible to expose the impact. No level drain
is used. Pool-level rise is part of this transient experiment.

The first domain is 2 x 1.6 x 2.9 m at resolution 96 (30.2 mm cells), 24 fps,
120 frames, FLIP ratio 0.95 and adaptive 2..8 substeps. Jet diameter is only
about 9.6 cells; nozzle voxelization and corrugation are not converged.
Prescribed velocity applies to newly emitted liquid, not a guaranteed flux.
Nominal source flux is 0.118894 m3/s; actual inflow is unverified. No splash
or froth motion is authored.

## Executed checks

`test_water_feature_froth.py` passed: dimensions within float tolerance,
closed tank/open top, finite inflow at frames 1/36/72/73/96/120, no outflow,
shared nozzle collider, separate phases and no animation on the liquid.
The first exact-float dimension assertion was changed to 1e-6 m tolerance;
no physical setting was weakened to pass it.

Matched free-fall calibration (`velocity-calibration-froth96-v1`) finished:
acceleration -10.12197 m/s2, 3.215% gravity error, maximum fit residual 1.337 mm,
grid/particle difference 1.605%. It passes the existing 5% threshold, not
high-accuracy validation. Raw primary velocity scale is 7.4256877 for this
build/domain/resolution. Do not assume it calibrates secondary particles.

Main v1 bake 2323 finished successfully in 573.34 seconds. Phase audit 29619
and preview render 99161 also finished. Do not repeat these unchanged runs.

## Phase checks and optics

`audit_water_feature_froth.py` measures jet bands, distant pool rings, mesh
volume, primary floor/nozzle intrusions and secondary distances to the skin.
Phase labels alone are not physical evidence. Nearest-normal signs and
narrow-band samples are diagnostics, not exact gas fractions or mass balance.
Test frames cover impact, switch-off and decay. Spray trajectories/drag still
need independent checks.

For this case the renderer uses dielectric water for spray and a relative-IOR
1/1.333 glass-sphere surrogate for immersed bubbles instead of opaque foam.
Surface foam remains a white-scattering approximation. Particle sizes are
optical assumptions, not measured bubble populations or resolved air cavities.
Other feature cases retain their existing materials. Appearance alone cannot
validate aeration.

## Observed failure: solver volume growth

Actual frames 48 and 84 were inspected. The jet/impact/splash is visible, but
white particles cover the incoming jet and build an excessive blanket. By
frame 120 there are 518,811 spray, 3,372,257 foam and 6,885,810 bubble samples.
Those counts are not a measured air volume. At frame 24 about 18% of the
sampled spray lies over one cell inside the reconstructed surface; phase
classification and boundary thickness require investigation.

More importantly, mesh volume grows from 1.097 m3 at frame 1 to 2.25 m3 at
72 and 2.734 m3 at 120, continuing after shutoff. Pool-ring heights rise too.
No sampled primary particles were deeply below the floor or inside the nozzle
midwall, but those checks do not establish correct boundary flux.

`audit_water_feature_volume.py` independently reads the original VDB level
sets with Blender's bundled `openvdb` module. Negative-liquid voxel volume
outside solid is 2.263 m3 at frame 73 and 2.706 m3 at 120: about 19.6% growth.
The saved inflow field has zero negative voxels at 73, 84, 96 and 120. Thus
the defect is present in the solver field, not just the render skin or an
inflow that stayed on. Negative-voxel counts are approximate, not exact
cut-cell mass integrals; nevertheless the observed growth is too large to
accept. The precise numerical cause is not yet identified.

Do not produce/promote a full v1 beauty clip as accurate froth. Its completed
cache and previews are retained as failure evidence. A controlled v2 in
`froth-jet-v2-fractions` changes only fractional obstacle handling; preparation
and scene tests passed. Setup comparison confirms only output path and that
setting differ. This is a hypothesis test, not a proven fix, and must be
checked using the same post-shutoff VDB and mesh measures before acceptance.
V2 bake session **32634** is now terminal, successfully finished in 489.76 s.
Disk guard 32658 is also terminal and did not stop the bake. Do not repeat it.

## Fractional comparison rejected; next primary-radius experiment

The completed v2 VDB audit contradicts a boundary fix. Outside-solid negative
level-set volume falls from 1.1154 m3 at frame 1 to 0.6177 at 24 despite inflow.
After shutoff it falls from 0.64814 m3 at 73 to 0.17370 at 120 (73.2% loss).
The inflow level set remains empty after shutoff. Both estimates use exactly
the v1 audit; neither is an exact cut-cell integral. Rendered mesh volume at
120 is only 0.10999 m3. The inspected frame-48 and frame-120 engine renders
show an aerated impact followed by a nearly empty pool, not a plausible
closed-tank decay. No v2 animation or physical acceptance is claimed.

The renderer's new `--view froth` includes the previously cropped nozzle.
V2 previews at 800 x 450, 24 samples took 19.19 and 4.95 s including evaluation.
They still show excessive whiteness in the incoming jet and impact blanket.
Preview session 16560 and both volume audit sessions are terminal. Seven
small failure artifacts are copied and SHA-256 verified in
`docs/water-feature-lab/froth-jet-v2-failure`; original caches are preserved.

Installed Blender 5.2 RNA identifies primary `particle_radius` (default 1.0)
as a liquid-volume reconstruction control and suggests reducing it for volume
gain. This is distinct from mesh radius and secondary optical sphere size.
`build_water_feature_froth.py` now exposes/records that control, and scene tests
check it while keeping the mesh radius at 2.0. V3 in
`tmp/water-feature-lab/froth-jet-v3-radius090` uses primary radius 0.9 and the
original nonfractional boundaries. All other physical setup fields match v1;
scene tests pass. This is a sensitivity experiment, not a calibrated fix.
It must pass the same whole-pulse and post-shutoff volume checks, jet-motion
checks and visual review; cancellation of volume errors alone is insufficient.

**V3 has NOT started baking.** The guarded launch refused before spawning a
process because free disk dropped below its 8 GiB preflight. Last measurement:
8,256,909,312 bytes free (7.69 GiB). V1 occupies 7,772,096,927 bytes and v2
2,472,348,630 bytes. The existing large caches have not been removed. Require
at least 11 GiB free before another full comparison (v1-sized cache plus a
3 GiB guard reserve); keep an owned-process disk guard during the cook.
V3 contains only its prepared blend and setup: no partial bake or live process.
No write-permission failure occurred in these workspace edits or renders.

## Primary reference and scope

[Dev et al., JFM 978 A23 (2024)](https://doi.org/10.1017/jfm.2023.1019)
provides optical-probe void-fraction measurements for circular plunging jets
and distinguishes inertia- and buoyancy-controlled cloud depths. Sections
3.2..3.4 and the conclusions describe approximately Gaussian radial profiles
and the influence of fall height. The article is CC BY 4.0 and lists dated
supplementary movies with nozzle/impact conditions. No media/data are bundled.
Its 2.7/8/10 mm nozzles do **not** match this 290 mm synthetic source. No
reproduction or measured match is claimed. Later calibration must match the
relevant nondimensional conditions and check media-specific licenses.

## Modular staging and disk-full recovery (2026-09-29)

A MODULAR copy of the pristine radius-0.9 scene is prepared in
`tmp/water-feature-lab/froth-jet-v3-radius090-modular`. Reopening the saved copy
passed all scene invariants, equality of writable domain settings and native
base-data operator availability. Cache is empty; no bake has started.
Mesh and all secondary phases remain enabled but will be baked separately.
Measured v1 cache sizes: data 678,239,201 bytes, mesh 184,448,157 bytes,
secondary particles 6,907,674,976 bytes. The new base-data launcher requires
3 GiB free and guards its own child at 1.5 GiB; full-cache preflight remains
11 GiB. Run the same VDB volume audit before any downstream stage. Staging
does not replace the final froth goal with a liquid-only diagnostic.

Disk briefly recovered to 405 MB, then returned to zero during documentation
save. This review was restored from the preceding complete read. One redundant
temporary bubble-pair blend was removed only after its SHA-256 matched the
delivered `docs/water-feature-lab/bubble-pair-reference-v1/feature.blend`.
That delivered scene remains the authoritative editable copy. Both froth
caches, scripts, reports, images and source data are preserved. Await free
space or user authorization before any froth-cache deletion. No bake is live.

### Resumed staged run

The goal resumed with about 75 GiB free. Guarded base-data bake session 15863
(owned Blender PID 11616) is DONE: all 120 data frames, 190.09 seconds,
699,154,364 cache bytes. No mesh or secondary particle files were generated.
The original VDB audit at 1, 24, 48, 72, 73, 84, 96 and 120 is also DONE.
Outside-solid negative-phi volume rises from 2.03013 m3 at frame 73 to
2.30290 m3 at 120, about **13.4% growth after shutoff**. Inflow phi is empty
at every post-shutoff sample. This is less growth than v1, but still a rejected
liquid solution. Do not promote v3 to a froth beauty clip or duplicate its bake.

The builder now accepts `--modular` directly. V4 at
`froth-jet-v4-radius080-modular` changes only primary `particle_radius` from
0.9 to 0.8. Saved domain snapshots were compared: that is the only changed
writable setting, apart from intentionally excluded cache path/type. The
closed-pool/inlet/nozzle/phase scene tests pass. Both runs retain the complete
120-frame pulse and decay at resolution 96, with mesh radius 2 unchanged.
Guarded v4 base bake session **65701**, owned Blender PID **17008**, is DONE:
120 frames, 189.81 seconds, 698,795,525 cache bytes, no mesh/secondary bake.
Its original VDB audit is DONE and rejects this candidate too: 1.78344 m3
at frame 73 rises to 1.92267 m3 at 120, about **7.8% post-shutoff growth**.
Every sampled post-shutoff inflow field is empty. Neither run was rendered
as an accurate froth feature. No Blender process remains live.

Eight small setup/domain/receipt/volume-report files were copied and SHA-256
verified in `docs/water-feature-lab/froth-radius-comparison-v1`. Original VDB
data and all older evidence are preserved. Modular staging avoided baking
several gigabytes of known-unqualified secondary data. This is diagnostic
progress, not a visible delivered improvement or acceptance.

The monotonic reduction from roughly 19.6% to 13.4% to 7.8% establishes
sensitivity to liquid reconstruction, not correctness of a fitted radius.
Stop this radius sweep here. Next isolate drift in a matched still-pool or
inflow-disabled control and measure actual source flux/temporal sensitivity,
rather than choose a radius solely because its net volume error crosses zero.
Only promote a justified, stable liquid candidate to mesh/phase rendering;
the final goal still requires a complete impact/froth/spray animation.

The [Blender settings manual](https://docs.blender.org/manual/en/4.0/physics/fluid/type/domain/settings.html)
describes primary radius as a liquid-cell reconstruction control and suggests
adjustment for unwanted volume drift; installed RNA agrees. It is not a
measured bubble radius. A fortuitous cancellation of volume errors is not
physical acceptance: source flux, jet evolution, mesh/collision agreement,
resolution sensitivity and the missing aeration/optical checks remain required.
No old cache has been deleted.

## Matched unforced pool and corrected flux readback

`froth-still-pool-r080-control-v1` retains the v4 geometry and every writable
domain setting, with the jet disabled at all 120 native frames. Its guarded
base bake 19844 (owned PID 4684) is DONE: 106.60 s, 643,771,096 cache bytes,
120 data frames, no mesh or secondary stage. The reopened scene tests pass.
This is not an exactly hydrostatic initialization: the original pool begins
20 mm above the floor, so settling remains. Negative-phi outside-solid volume
is 1.07211 m3 at frame 1 and 1.07972 m3 at frame 2; it is identical at sampled
frames 12, 24, 48, 72, 73, 84, 96 and 120. Inflow phi is empty after the initial
GEOMETRY injection at frame 1. Cached velocities are nonzero and decay; equal
voxel counts do not mean the scene was frozen. This rules out comparable late
volume drift in this unforced control at the audit's voxel-count resolution,
not volume drift in arbitrary moving liquid. The jet case remains rejected.
The old `initial_depth_m=0.35` label is the upper elevation, not the thickness
of the initialization box (z=0.02..0.35 m). New metadata, including v5, records
bottom, top and thickness 0.33 m separately. Geometry and old reports are
preserved; this metadata correction does not change the simulation.

The first jet-flux audit stopped before writing a report because it incorrectly
required the engine cell sizes to equal the VDB storage transform. Inspection
found engine spacing (0.03030303, 0.03018868, 0.03020833) m versus isotropic
VDB spacing 0.03020833 m, with no world translation in the VDB transform.
Blender rounds horizontal grid counts, then maps them over its object bounds;
its [domain mapping source](https://raw.githubusercontent.com/blender/blender/main/source/blender/blenkernel/intern/fluid.cc)
supports that convention. The installed scene's bounds/resolution check passes.
The corrected audit uses engine spacing and translation for world-plane flux,
preserving the original volume-count method for comparisons. The constant
storage/engine volume-factor difference cannot explain temporal drift.

The cached velocity metadata identifies a staggered grid. Native VDB arrays
match Blender's transposed grid readback exactly at every audited frame.
Mantaflow's [MAC-grid implementation](https://raw.githubusercontent.com/blender/blender/main/extern/mantaflow/preprocessed/grid.h)
places the stored z component on a cell face. The audit now samples that face,
with neighboring level-set signs estimating occupancy, rather than pairing a
face velocity with center occupancy. Three synthetic indexing/quadrature tests
pass; these are not hydraulic validation. The upstream source conventions
were checked against the installed readback, not assumed to be a build match.

At frame 24, 48 and 72 the coarse v4 plane estimates are 0.18527..0.18531 m3/s
at z=1.350 m and 0.19391..0.19584 m3/s at z=1.28958 m. Both planes are empty
at frames 84 and 120. These differ substantially from nominal nozzle flux
0.11889 m3/s; sampled areas also exceed nominal nozzle area. Whole-face sign
quadrature, coarse nozzle geometry and the calibration's 3.22% gravity error
prevent calling this exact injection or locating all error in the inlet.
Source-region and partial-face budgets remain open. No cached fields changed.

The next controlled case `froth-jet-v5-r080-time2-modular` refines only temporal
settings: minimum/maximum substeps 2/8 to 4/16, CFL 2 to 1. Snapshot comparison
finds exactly these three changes; geometry/inlet/radius/phase scene tests pass.
Do not infer actual doubled substeps or physical convergence from settings.
Its guarded base bake **58513**, owned PID **35748**, is DONE: 392.51 s,
795,859,510 cache bytes, all 120 data frames, no mesh/secondary stage. Original
VDB audit and reopened scene tests are DONE. Outside-solid negative-phi volume
at frame 73 is 1.86277 m3, rising to 2.07749 m3 at frame 120: **11.53% growth**
after shutoff, worse than v4's 7.81%. Every post-shutoff inflow sample is empty.
V5 is rejected; do not duplicate or promote it. Temporal refinement increased
cost about 2.07x but did not establish improved conservation or convergence.
No new animation, visual acceptance, or full-river integration is claimed.
Five small control/flux reports are copied and SHA-256 verified in
`docs/water-feature-lab/froth-control-flux-v1`; original fields are untouched.
Four more v5 setup/domain/receipt/volume reports are copied there and hash
verified. All Blender jobs are terminal. No cache was deleted.

Next distinguish interface-reconstruction/voxel-count changes from actual
liquid-budget error with an independently refined partial-cell integral and
source-region accounting. Do not continue a blind radius or timestep sweep,
or choose settings whose errors happen to cancel. Neither still-pool stability
nor a coarse plane flux validates the moving jet. Mesh/collision, jet thinning,
impact/aeration, separate-phase optics and a complete animation remain required.

## Independent interface integral and contained-inlet correction (2026-09-30)

`water_feature_cell_volume.py` now integrates trilinearly reconstructed liquid
phi intersected with nonnegative obstacle phi. It covers the full engine domain,
using constant extension from cell centers through boundary half cells. Midpoint
quadrature is refined through 2, 4, 8, 16 and 32 samples per interval dimension.
This removes whole-cell sign-count quantization; it does not measure conserved
particle mass or resolve an air phase. Five analytic/synthetic tests pass:
anisotropic full/empty domains, liquid/solid planar intersection, independent
midpoint-error bounds, oblique-plane edge extension and sphere spatial refinement.
An initial arbitrary oblique-plane tolerance failed; it was replaced by an
analytic bound derived from the maximum coordinate variation in a subinterval,
plus refinement and interval-enclosure checks, not a claimed tighter accuracy.

The finer midpoint estimates retain substantial jet growth: v4 at 32 subdivisions
is 1.81171 to 1.94845 m3 at frames 73/120, about 7.55%; v5 is 1.89527 to
2.10735 m3, about 11.19%. The unforced control changes from 1.08499 to 1.08791
m3 at frames 2/120, about 0.27%, despite identical whole-cell counts. Thus the
old still-pool statement means stable at voxel-count resolution, not exact
constant liquid mass. At frames 73/120 its 16-subdivision estimates change
only 1.08869 to 1.08964 m3 (about 0.088%).

The new subinterval-corner bounds use multilinear extrema and a roundoff guard.
They bound these particular reconstructed fields, not the unknown continuum
solution. V4's frame-73 interval is [1.79948, 1.82947] m3; frame 120 is
[1.93955, 1.96292] m3. Even the most favorable endpoints require **6.02% growth**
(upper growth bound 9.08%). Whole-cell counting cannot explain away this
reconstructed-volume error. The control's late intervals overlap. No exact
mass or hydraulic acceptance is claimed from either result.

The original v4 inflow field at frames 24/48/72 contains 688 negative centers:
86 are below the nozzle bottom and 64 outside the 0.15 m inner radius. The
emitter itself extends to z=1.42 m below the nozzle's z=1.45 m exit; its 0.5-cell
surface distance also dilates the source field. Blender's
[mesh-emission source](https://raw.githubusercontent.com/blender/blender/main/source/blender/blenkernel/intern/fluid.cc)
subtracts that thickness from mesh distances. This is a supported geometric
correction target, not evidence that it causes all post-shutoff volume growth.

`froth-jet-v6-contained-inlet-modular` retains every writable v4 domain setting,
including radius 0.8 and temporal settings 2/8, CFL 2. Only the emitting cylinder
changes: z=1.48..1.65 m, inside the nozzle, and zero artificial surface distance.
The prescribed radius 0.145 m and downward speed 1.8 m/s remain unchanged.
Reopened scene tests check actual source vertices against the bore and nozzle
ends. Guarded base bake **68798**, owned PID **19704**, is DONE: 208.94 s,
668,894,307 cache bytes, 120 data frames, no mesh/secondary bake. All audits
and saved-scene tests are terminal. The new cached inflow has 444 negative
centers, **zero below the nozzle and zero outside the bore** at all three on
samples; off samples are empty. This fixes the sampled source containment.
It does not prove an exact interpolated source/collider boundary or flux.

V6 is still **rejected as a physically accurate froth solution**. Whole-cell
outside-solid volume rises 1.67620 to 1.79347 m3 after shutoff, 7.00%. Refined
16-subdivision interface volume rises 1.70299 to 1.81815 m3. Its interval bounds
still require at least 5.24% growth (upper bound about 8.33%). Coarse below-nozzle
flux remains about 0.180 m3/s at z=1.35 m, above nominal 0.11889 m3/s; jet speed
also changes. Do not call the corrected source a conservation fix or promote
this cache to an accurate aerated-froth clip. No new rendered animation exists.

Fourteen small original reports are copied and SHA-256 verified in
`docs/water-feature-lab/froth-interface-inlet-review-v1`. Original VDB hashes
are in the interface reports; no cache was altered or deleted. The next task
is moving-liquid reconstruction/transport and inlet-budget consistency, not
another radius fit. Preserve the contained-inlet fix. A controlled alternative
transport method needs motion/calibration/conservation checks, not merely a
smaller net volume error. Separate-phase appearance remains part of the final
froth deliverable; all eight original feature cases remain open.

## Transport preflight and spatial refinement (2026-09-30)

V7 tests APIC against the contained-inlet v6 FLIP case. Prepared JSON snapshots
differ only in `simulation_method`; native geometry tests pass. This does not
qualify the solver. Its matched 96-resolution free-fall calibration fails:
particle-centroid acceleration is -6.09629 m/s2 instead of -9.80665 (37.84%
error), and grid/particle velocity disagreement reaches 99.63%. An independent
centroid from original negative-phi VDB cells gives -5.61796 m/s2 (42.71%
gravity error), confirming slow actual cached liquid motion, not only an API
units mismatch. This is a failure of this installed build/case, not a general
claim about all APIC implementations. The APIC
[method paper](https://disneyanimation.com/publications/the-affine-particle-in-cell-method/)
motivates retaining affine particle velocity information; it does not guarantee
liquid-volume conservation in this setup.

V7 is **rejected before a full jet bake**. Its setup records that rejection,
and the modular baker now refuses it before writing a marker or cache. The
native rejection check passes with no receipt/marker/data files created.
An initial comparison of baked v6 versus pristine v7 native snapshots failed
because cache pause/baked-state flags also differ. The corrected comparison
uses both prepared JSON snapshots and proves only the transport method changes;
no physics comparison was broadly relaxed. Calibration and independent-field
audits are terminal; do not repeat or promote this APIC case.

The flux diagnostic now optionally integrates bilinearly reconstructed partial
face area and signed velocity, with constant extension through domain-edge
half cells. Four synthetic tests pass, including anisotropic area, liquid/solid
intersection, independent bidirectional flux and empty/invalid inputs. The
four existing MAC-layout tests also pass. V6 frame 24 at z=1.35 m refines to
0.179049 m3/s at 32 subdivisions versus 0.179527 with whole-face counting;
16 versus 32 differs about 0.044%. At z=1.28958 m it refines to 0.183114
versus 0.193866 m3/s, about 6% lower. Partial-face counting is not the main
explanation for the nozzle-plane discrepancy. These are integrals of the
reconstructed grid, not exact conservative source budgets.

Crucially, nominal 0.118894 m3/s is nozzle area times prescribed initial
emitter velocity, **not an imposed flux boundary**. Gravity acts within the
volume emitter. Comparing exit-plane flux to that nominal value alone cannot
prove an injection error. Source overwrite/injection, stored liquid and
transport accounting remain open. The prior source containment correction
remains valid; no original cached fields were changed.

V8 `froth-jet-v8-contained-flip-r144-modular` refines spatial resolution 96 to
144, retaining the contained inlet, FLIP, radius 0.8, nonfractional obstacles
and temporal settings 2/8, CFL 2. Prepared snapshots differ only in
`resolution_max`. Nozzle wall thickness is about 1.32 versus 1.99 grid cells,
and bore diameter about 9.6 versus 14.4 cells. This is a geometry/transport
resolution comparison, not another radius fit. Native setup tests pass.
Its matched FLIP144 free-fall calibration passes: particle acceleration
-10.12784 m/s2 (3.275% error), grid/particle disagreement 1.61%. Independent
cached-field acceleration is -9.99891 m/s2 (1.960% error); sign-volume range
is 0.771%. The same independent FLIP96 check gives -9.92113 m/s2 (1.167%
error). These readback checks do not establish hydraulic acceptance.

Guarded v8 base bake **81802**, owned Blender PID **38880**, is now DONE:
1030.09 seconds, 120 data frames, 1,686,880,053 cache bytes, no mesh or secondary
stage. Reopened scene tests, volume/flux audit **74387**, interface bounds
**69580** and paired cached-divergence audit **56433** all finish successfully.
No Blender process remains live; do not duplicate these terminal jobs.
Ten small source reports/settings are copied and SHA-256 verified in
`froth-transport-review-v1`; original scenes/caches remain preserved.
No new animation or visual acceptance is claimed. All eight cases remain open.

### V8 rejection and the next mechanism check

Higher spatial resolution does not fix the error: outside-solid sign volume
at frames 73/120 increases from 1.84220 to 2.06562 m3, **12.13%** after shutoff,
versus v6's 7.00%. The refined engine-mapped integral is 1.90337 to 2.12794 m3
at 16 subdivisions (11.80%). Bounds at frame 73 are [1.88789, 1.90951] m3;
frame 120 [2.11496, 2.13185] m3. Even favorable endpoints require **10.76%
growth** (upper bound 12.92%). Inflow phi is empty after shutoff, and all three
on samples retain zero negative source centers below/outside the nozzle.
V8 is rejected; no mesh/secondary promotion. It costs 4.93x v6's base runtime
and 2.52x cache space without improved conservation. Stop this resolution sweep.

Height profiles use the matched calibration and refined partial-face integrals.
At v8 frame 24, descending from z=1.39028 to 1.00764 m, the represented liquid
area narrows 0.070642 to 0.048503 m2 while mean downward speed rises 2.39678
to 3.61604 m/s. Plane fluxes across four sampled heights span 0.16931..0.17849
m3/s. V6 similarly narrows and accelerates, but spans roughly 9.5..10.5% in
section flux relative to the upper section over frames 24/48/72. These are
actual cached motion/shape diagnostics, not a measured jet validation, exact
injection budget or completed animation. The mesh/phase audit now also rejects
transport-mismatched calibrations and removes the obsolete hardcoded 1.42 m
emitter speed reference; it was not valid for the contained volume emitter.

Four new synthetic tests verify native lower-face MAC divergence on constant,
linear anisotropic and divergence-free rotating fields, plus interface/solid/
neighbor exclusion and invalid inputs. Paired v6/v8 original-field checks
confirm exact native velocity readback. After shutoff, isotropic-grid-scaled
interior mean divergence is within about 1e-5 per second; v8 RMS decays
0.01015 to 0.00539 per second at frames 84..120. Using engine anisotropic
spacing with the same velocity scale gives different residuals, so both are
reported separately, not silently conflated. Interfaces, obstacles and cells
without six liquid neighbors are excluded. End-frame interior consistency
does **not** prove substep pressure accuracy or rule out interface/boundary
flux errors. It does not establish particle reconstruction as the sole cause.

The upstream
[liquid step source](https://raw.githubusercontent.com/blender/blender/main/intern/mantaflow/intern/strings/liquid_script.h)
advects the level set, combines a particle-union reconstruction, and adjusts
particle populations. This motivates inspecting those stage-wise interface
budgets in a controlled moving-liquid case; upstream text is not proof of an
exact installed-build match. Next isolate stage-wise reconstruction/resampling
and boundary contributions, rather than repeat resolution/radius/timestep
fits or hide drift with a post-hoc mesh-volume correction. A passing net-volume
number alone would still leave motion, collision, aeration and optics open.

Seven additional reports are copied and SHA-256 verified in
`froth-spatial-rejection-v1`. Original v8 frame-73/120 VDB hashes are rechecked
unchanged. Every old scene/cache and all completed feature clips are preserved.
No new clip or visual acceptance; full foam/froth and all eight cases remain open.

## Installed-build local-step reconstruction check (2026-09-30)

This advances the isolated-feature goal, not full-river acceptance. The installed
Blender 5.2.0 LTS build `fbe6228777e7` exports its actual liquid script through
an explicit export-only option. A corrected one-frame v6 export probe finishes
in 1.79 seconds, without mesh/secondary output or promotion. Its script SHA-256
is `33b4f64e327308019962bab6139c6008f73f7a7fb20b013fd91edca24f01c2ea`.
The first export probe accidentally disabled the emitter at frame 1 because
its end-frame key overrode the start key; the builder now prevents that in
short probes. Both trials remain preserved. A matched exported free-fall
calibration still passes (3.215% particle gravity error).

`probe_water_feature_solver_stages.py` loads original frame-96 v6 jet and
still-pool state into separately named native solvers. Loaded phi/obstacle
arrays match the original VDB exactly. Every primary particle position and
velocity, plus counts 213,762/263,101, matches Blender's native particle API.
This is **one 0.02083333-second liquid step**, not a reproduced frame or bake:
scene/source/pre-step rebuilding is excluded. Only top-level operations are
observed; nested pressure/FLIP/outflow calls are not separately instrumented.
The excluded exported main loop also contains an invalid Windows path literal.
Two unused I/O enums and Blender's Vec3Grid alias require compatibility handling;
RK4 enum value 2 follows upstream Manta, not an independent RK4-accuracy test.

The native API comparison establishes an important distinction: displayed
particles use isotropic 0.0302083333-m cells centered on the object, with origin
[0.003125, -0.8005208333, -0.1] m. RNA field cell spacing instead is approximately
[0.0303030312, 0.0301886797, 0.0302083343] m, origin [0, -0.8, -0.1] m.
Conflating them produces up to about 3.04 mm of position disagreement. The
comparison was corrected by measuring the mapping, not by loosening tolerance.
Field integrals below retain the field mapping; particle positions use their
independently validated mapping. Mesh/particle/field collision alignment still
needs explicit checking before physical/visual acceptance.

The public particle pointer returns a native vector header, not its payload.
The adapter validates this build's MSVC begin/end/capacity layout and element
strides against native counts and readback. Early exploratory adapters failed
on aliases, pointer conversion and mapping; two native cleanup crashes are
preserved under the export-v2 folder. Releasing exception traceback references
before children and solvers repairs cleanup. Later failed preflights exit cleanly;
both completed v4 and extended v5 paired probes exit 0. No original cache is
written by these local probes.

Eight saved checkpoints now separate inside extrapolation, outside extrapolation
and the outer-boundary operation. Independent n8/n16/n32 midpoint audits validate
snapshot hashes, reproduce n8 and recheck original VDB hashes. Approximate n32
fixed-field integrals, in m3, are:

| Checkpoint | Moving jet | Still control |
|---|---:|---:|
| Before liquid step | 1.78014067 | 1.08745350 |
| Phi advection | 1.77535784 | 1.08745415 |
| Deliberate one-cell shrink | 1.56864845 | 0.87453179 |
| Join particle-union phi | 1.76962586 | 1.07605378 |
| Inside extrapolation | 1.77642079 | 1.08166216 |
| Outside extrapolation | 1.77523007 | 1.08166216 |
| Outer-boundary operation | 1.78204659 | 1.08746395 |
| After particle resampling | 1.78204659 | 1.08746395 |

Net jet change at n8/n16/n32 is +0.00189104/+0.00190494/+0.00190592 m3;
control +0.000019053/+0.000011820/+0.000010456 m3. At n32 the isolated
outer-boundary checkpoint changes these reconstructed integrals by about
+0.00681653/+0.00580180 m3, without changing outside-solid negative-phi counts.
Thus the previous grouped extrapolation/boundary result cannot be assigned
solely to extrapolation, nor treated as added physical mass. Shrink/reconstruction
and boundary handling substantially redistribute subcell interface shape even
in the still control. The jet's sign volume also increases from 1.76053269 to
1.76221841 m3; control sign volume stays 1.08240137 m3. Resampling reduces
primary populations to 213,135/262,350 without a measured volume change in
this step; that does not rule out its influence on later reconstruction.

These are integrals of fixed reconstructed fields, **not conserved mass**.
Refinement differences are not rigorous uncertainty bounds; absolute integrals
are nonmonotonic with subdivision, while the paired net differences settle.
This local experiment does not establish the sole cause of whole-run drift,
justify disabling the boundary condition, or qualify the rejected v6 cache.
Next spatially locate the union/extrapolation/boundary changes and compare
controlled moving-liquid transport with proper source/boundary budgets. Do not
apply a post-hoc volume fit or repeat radius/resolution sweeps.

Latest native probes 79892/control inline run and refinements 94088/57773 are
terminal exit 0. Earlier refinement sessions 43987/77802 are terminal exit 0.
Twenty-three synthetic/analytic/AST tests pass, including exact removal-of-
captures AST roundtrips and executable call order. An initial suite invocation
used a nonexistent test-module name; the corrected six-suite invocation passes.
No Blender process remains live. Eight small reports are SHA-256 verified in
`froth-stage-reconstruction-v1`; saved fields remain in the original tmp cases.
Every prior scene/cache/clip remains preserved. No new rendered animation,
playable integration, game-FPS result or physical/visual acceptance is claimed.
All eight feature cases remain open; no access blocker prevents this work.

### Spatial localization of those changes

Independent saved-field regional audits at n16/n32 partition every integration
interval exactly once: outer half cells, full intervals touching an outermost
grid center, and all remaining interior intervals. No region is omitted from
the total. The jet's n32 interior integral increases from 1.65920814 to
1.66109303 m3 (+0.00188489), while outer-adjacent full intervals increase only
0.000021039 m3. Thus about98.90% of this local net reconstructed increase is
interior; n16 similarly gives about99.08%. Control interior increase at n32 is
only0.000010614 m3. These are quadrature estimates of the same fixed fields,
not rigorous uncertainty bounds or conserved mass.

The Neumann checkpoint changes exactly28,992 outermost centers and zero
non-outermost centers. Its5192/2808 new negative centers in jet/control are
all inside the obstacle mask: zero newly negative outside-solid centers.
Nevertheless, interpolation across neighboring centers changes the small
outside-solid subcell integral near the edge. This explains why counting all
negative centers would confuse ghost/solid-region updates with physical water.
The interior excess appears across shrink/particle union and subsequent level-
set extrapolation, not in the outer-boundary operation. Leave that boundary
operation intact; removing it would not target the measured interior drift.
No alternate solver or mass correction has been enabled. Four regional reports
are copied and hash-verified in `froth-stage-reconstruction-v1`. All regional
audits are terminal; original VDB/snapshot hashes remain unchanged.
