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
