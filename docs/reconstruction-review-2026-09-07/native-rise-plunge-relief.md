# Preserve the resolved downstream rise — September 28 UTC

Incremental normal-scene geometry correction, not breaking-water acceptance.
The previous goal turn made progress by correcting the new profile observer's
datum handling and obtaining actual raw/submitted sections. Those sections
exposed a negative downstream residual worth isolating, not an absent native rise.

## Cause and bounded change

`ComputeBreakingPlungePocketPresentation` is a legacy authored height/foam
envelope with fixed meter-scale drawdown, lip, negative plunge and return lobes.
Its negative plunge term is -0.30m times detector intensity, independent of the
native resolved drop/rise and the physical crest's remaining height budget.
The Cartesian physical-crest path was adding this layer even where the native
surface already contains the drop and downstream recovery. This can cancel
part of the native rise; a larger additional crest would mask that interaction.

The normal Cartesian/shared/physical-crest path now omits ONLY `Pocket.X` from
its height accumulation. `RaftSim.Water.LegacyPlungeRelief` defaults to0;1 retains
the old layer for comparison. Legacy/non-Cartesian paths retain their behavior.
Pocket foam generation, foam advection, tongue suppression/drawdown, downstream
boil, hydraulic crest dimensions, native solver, fields, captured terrain and
collision are unchanged. The existing submitted-triangle/detail contact sampler
continues to follow the resulting single carrier; no second surface was added.
This is removal of an independent artistic height layer, not a new measured
hole, bathymetric edit, momentum model or calibrated overturning-water solution.

## Same-build A/B and default confirmation

Trial editor build32361 PASS63.36s; default editor build83776 PASS59.88s.
Both limited to two compile actions. Native regressions84758 PASS3/3:
SharedBreakingRelief, HydraulicCrestScale, PlayableCrestReconstruction; report
`tmp/plunge-default-native-tests-v1-20260928/index.json`. These are focused crest
tests, not collision traversal, all-scene or physical-realism acceptance.

Normal FullReach `-game`, passive8310m approach, ordinary boat camera,
1280x720/D3D12, ephemeral profile. Twenty-four one-second requested captures
after2s, no paddle/quality/solver override. This targeted scene validation does
not substitute for the packaged Boot/menu launch check still required below.

Legacy1: session98730, engine5388, completed exit0.
Legacy0: session82902, engine25872, completed exit0.
Same frozen trial actor82d6468a3d4e92c2d56f7fb5cfceb37e2cadc685c034363a554ec5140a14ebe8
and DLLac3b6c6eb8f42206e3beab6ffde5e6f68f9391780dc45c79b35cc0f0620bc7ce.
Receipts and raw/independent summaries use prefixes
`tmp/sf-plunge-relief-{1,0}-v1-20260928` and
`tmp/sf-plunge-relief-{1,0}-summary-v1-20260928.json`.
Both captures report the requested CVar value. The sequential shell returned
after the first script, so the second was explicitly launched only after the
first was terminal; no duplicate engine or capture was started.

At selected site(-5428,3607)m, along1.75m/across0:

| Mode | Raw stage, m | Submitted macro, m | Macro minus raw, m |
| --- | ---: | ---: | ---: |
| Legacy pocket1 | 8.095978 | 7.945658 | -0.150320 |
| Removal0 | 8.095917 | 8.064289 | -0.031628 |
| Rebuilt default, no override | 8.096024 | 8.064425 | -0.031599 |

The removal restores approximately0.1186m of downstream submitted rise at this
sample while native stage differs by0.000061m across the A/B. The residual is
not eliminated; other relief, interpolation and source/presentation age remain.
World times10.0701/10.0011s and committed water4.7333/4.4667s differ. These are
not synchronized deterministic snapshots or calibrated wave-height measurements.

Actual fine-crest topology audits retain zero source-anchor change. Maximum
target crest errors are1.55090cm legacy and1.54974cm removal; temporal correction
tracking is reported separately. This audit excludes pocket/boil/mean/detail and
cannot establish full contact parity. Ground-contact audit files were absent:
that observer only writes projections>=5mm and is not a complete contact ledger.
No ground-contact or shoreline acceptance is inferred from file absence.

Rebuilt-default session58495 / engine33124 completed exit0, no plunge CVar in
its command line; profile records `legacy_plunge_relief_requested=false`.
Receipt `tmp/sf-plunge-default-v1-20260928-process.json` freezes actor
e6ef99c4a9db6cec33c2f13e5b0b94cd036d07c71391641fb17db55bdc2d7e9d
and DLLd9cf17f10b05c1e266849ced4e6bab4f29c3f83776d652c0b651f1130a086aeb.
Raw profile SHA256d72852861765bd852477a4944ca51c0d05fcee7920978a01608bce64c4b2f4b4.

## Actual appearance and limits

Retained videos in `unreal/Saved/VideoCaptures`:

- Legacy `RaftSim_20260927-182107.mp4`: b7a1c183cfc9b0fec90993b5df10ce2389fa27d79a8490ca2311371149585dbb.
- Removal `RaftSim_20260927-182231.mp4`: fece2956e11870eb351c20614f8e2dbd0489807c04a76e062abf780352c45ba2.
- Default `RaftSim_20260927-182657.mp4`: 0a12941a8870f8e331d57038a59c3c694d588a56751553d47b3fbd0034cdf32c.

Decoded830/832/834 frames respectively. Inspected legacy20s, removal11s/20s
and default20s. The raft advances along the normal corridor; the water remains
one visible carrier in those views. Broad flat white patches and weak breaking
remain; no convincing overturning crest or returning roller is established.
Different camera/raft trajectories preclude pixel-matched claims. The verified
improvement is preserving more of the resolved hydraulic rise, not a claim of
photorealistic motion, complete collision/shoreline stability or river acceptance.

The existing hydraulic continuation33852/28956 stayed live, observed1101s. All
these build/capture runs are explicitly NON-timing evidence; no FPS claim is made.
Native snapshots are not promoted, and v13 still uses the450s fields.

## Playable delivery and next gates

Fresh v14 recipe: `tmp/package-south-fork-v14-20260928.ps1`; package receipt and
log use `tmp/south-fork-v14-package-20260928.{json,log}`. Preserve v13.
Package82230/wrapper32192 is LIVE from01:31:09.0827426Z, source5f05b136d,
UAT/UBT observed35032/16348. Frozen input hashes are in the receipt; no duplicate
build. This live-owner note is not successful packaging or installed delivery.
Measured prior stage5,360,205,592 bytes; reserve two full copies plus4GiB scratch
before launch (15,015,378,480 bytes), including ongoing native snapshots. This
replaces an unmeasured20GiB staging guard, not a quality/performance gate.
The EOL-only WaterSurfaceTest.cpp working copy is preserved and hashed; all
substantive implementation changes must be committed before packaging.

After packaging, verify staged field closure, actual normal Boot/menu launch,
default removal in the packaged scene, motion/contact/shoreline/continuity and
isolated performance AFTER the hydraulic owner/audits finish. Do not start a
second package or cook.20FPS/50ms p95/no100ms hitch gates remain unchanged.
Continue breaking/roller dynamics beyond this static-layer correction; do not
claim the full water objective solved or move to Colorado yet.
