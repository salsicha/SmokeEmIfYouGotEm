# Cartesian boulder relief and foam integration — September 12

This is a runtime integration correction, not acceptance of the normal South
Fork scene. The normal FullReach map and real save remain unchanged. Troublemaker
remains a rapid inside South Fork, not a selectable scenario.

## Corrected production paths

The configured boulder support helper now accepts a unit downstream vector in
hydraulic coordinates. Its default is still +X for station/lateral fields.
The actual surface refresh uses the same local along/across transform for the
pressure pillow, signed Y-wake, aerated collar, trailing foam and eddy seam.
Rock dimensions and the existing speed/amplitude envelopes were not increased.

The first integration test exposed a second bug in the preceding Cartesian
work: `SampleWaterFieldAtRiverCoordinates` returns **field** velocity, not world
velocity. Multiplying north by `world_y_sign` at that point reflected it twice.
Corrected the sampled-current frame used by hydraulic curvature, breaking-site
detection, boulder relief and raft support. Foam backtraces now consume field
velocity directly instead of projecting it again. Conversely, breaking sites
now transform field velocity into world velocity exactly once for world-space
lip/roller/spray placement. This also corrects the extra foam projection in
legacy curved grids; actual world-space clock probes retain their projection.

The generic rotated-profile check alone did not catch the wrong call-site frame.
The new tests therefore exercise the actual sampler, public raft-support query,
surface refresh and persistent foam backtrace, with independent field-frame
expectations. The initial failed report is retained. The surface test uses
0.5 m presentation sampling over the same 22 x 20 m analytic fixture, to sample
the narrow pillow/wake rather than reducing its coverage or lowering a gate.

## Verified evidence

- Build `south-fork-boulder-direction-build-20260912.log`: 41 actions, success,
  295.35 s. Two pre-existing damping-literal C4305 warnings remain.
- Corrected build `south-fork-boulder-direction-build-v2-20260912.log`: 13
  actions, success, 66.59 s.
- `unreal/Saved/RaftSimValidation/south-fork-boulder-direction-v1-20260912/index.json`:
  1 pass, 2 failed tests; retained evidence of the incorrect north conversion
  and sparse 1 m pillow sampling.
- `unreal/Saved/RaftSimValidation/south-fork-boulder-direction-v2-20260912/index.json`:
  **24 native/D3D12 tests pass**, no failed/unrun tests or test warnings/errors.
  Includes the existing crest GPU, streaming, crop/overlap, source catalog,
  menu/migration and water regressions, plus the new boulder/foam checks.
- `unreal/Saved/RaftSimValidation/south-fork-boulder-direction-gameplay-20260912/index.json`:
  **2 actual-game tests pass**, crew commands and scoring/save, with no test
  errors/warnings. Ephemeral profile used; the real save was not replaced.
- 109,368 translated/rotated/reversed boulder profile samples, 26,064 above
  1 cm displacement: maximum scalar profile error **0 m**.
- Actual world-space boulder support error **3.75393e-6 m**; actual surface
  refresh error **4.87438e-6 m**, 25 vertices above 1 cm. The prior +X assumption
  differs by **0.0615613 m**, so this is not a vacuous zero-height comparison.
- Actual advected foam ramp error **4.38690e-8** versus a wrong-north difference
  of **0.00252735**. World/field conversion checks also cover reflected and
  rotated source tangents and reverse currents.
- Both the 201 s / 832-tile and 301 s / 833-tile real atlases match independent
  dense exports across 151,875 cells each and three subsequent live steps,
  bit-exact. Each river atlas is loaded once across its three full 224 m crops.

These numbers verify software coupling and data identity, not observed river
wave heights, photographic resemblance, long-run motion or frame-time budgets.

## Exact source dependency reuse

`export_cartesian_runtime_atlas.py --reuse-source-packets PRIOR_EXPORT` now
references immutable bed and capture-mask arrays instead of copying them again.
It checks source geometry identity, datum, grid origin/shape/spacing, actual file
hashes/dtypes/shapes, and every decoded value against freshly hash-verified
captured source data. It never reuses old h/u/v, accepted status or safe-center
decisions. Release packaging must explicitly stage these dependencies.

Six numerical dependency tests pass, including corrupt hashes, rehashed but
incorrect bed/mask values, float32 replacement and wrong source/frame rejection.

Real export `tmp/south-fork-runtime-atlas-301s-v1-20260912` verifies 799 source
packets, 833 solved tiles and 41,869,798 exact bed intersections. It reuses
**741,172,375 bytes** of source arrays from the 201 s export; new state references
the immutable 301 s pilot snapshot. It does not touch the live continuing cook.

- Atlas manifest SHA256:
  `22cdcadb86b122efcf34df22f02ab40a3a359549ded522d5dbc991681b51a0cd`.
- Export audit SHA256:
  `cc790b459baa86627617b3cddadb5d6f091cfaf10d0086c390d7f65394c77238`.
- Use **`streaming_manifest_verified.json`**, SHA256
  `ac4449ffe5ae94a971096c3050a57cf5a6ce11bb344ed2112884959effdbba10`.
  The raw catalog is not accepted: region_0002 still needs the physical-inlet
  exclusion repair. All 406,823 original captured-water positions remain
  covered, 3,822 with shifted centers, minimum raft margin 10 m, full 224 m crops.
- Fresh independent verified coverage audit SHA256:
  `afb658ab2b23fa6e8da4ff825c036a9293074c961d236199ae5eeb484faaff64`.
  All 797 continuous center rectangles are safe; no failed rectangles.

## Remaining integration and live process

At 11:42 UTC PID8116/session48811 is verified live, local step1640 / 382 s,
maximum step conservation residual 1.38441e-8 m3. The next complete snapshot is
local step2000 / 400 s. Keep the same native executable/input/output, inspect
every complete snapshot for artificial-bank wetting and section discharge,
and distinguish stable conservation from hydraulic settling.

Still required before a coherent normal FullReach promotion:

1. Replace the legacy station-band render baseline's fabricated depth/current
   with actual shared Cartesian atlas samples outside the moving live crop.
2. Finish two-dimensional crop authority, wet/dry islands and shoreline
   topology. Boulder eligibility still uses a column-wide wet span; support
   receives all footprints while rendering prunes them. Shore weighting also
   needs explicit render/support alignment. Do not call those paths finished.
3. Integrate the complete source terrain/collision, route, water, start/finish
   and progression stations together; the new route is 33.334 km, not the old
   normal map's 49 km. Promote the common full-river carrier configuration,
   not the removed rapid scenario or a relabeled short slice.
4. Inspect actual playable motion and reference comparisons, settle flow,
   resolve guided traversal and meet frame-time gates. Later rivers, crew,
   normalization, release verification and final commit remain in the goal.
