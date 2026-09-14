# Dry rock is not a water elevation — September 14

The preceding turn committed reviewed source and evidence. This turn changes
the ordinary runtime sampler, not just diagnostics. Full reconstruction remains
unfinished; the actual new game image still fails the visual target.

## Verified defect and correction

The existing live-window and shared-atlas samplers separately interpolated bed
and depth, then summed them. At a flat pool beside dry high rock this made the
rock top contribute a fictitious water elevation. An actual native test against
the original implementation failed: at the exact shoreline of an eta=1 m pool
beside a bed ramp from 0 to 2 m, it returned depth=0.5 m and surface=1.5 m,
instead of depth=0 and surface=1. The same defect occurs in both coordinate axes;
even the wet pool's normal tilted toward the dry rock.

`RaftSimWetSurfaceInterpolation.h` now provides a shared point reconstruction.
In a mixed wet/dry footprint, positive-depth donors define a weighted wet stage.
Only dry bed elevations ABOVE that stage are capped when interpolating the
surface; lower dry terrain retains its original wetting-front contribution.
The resulting surface intersects the unchanged bilinear bed, giving nonnegative
point depth. Its normal differentiates that same surface. Entirely positive
footprints keep the previous interpolation and normal convention, including
arbitrarily thin positive films. Exactly zero depth, not a new threshold,
identifies an absent water surface. The existing presentation wet threshold is
unchanged. Current samples are retained; dry flags govern whether support exists.

This point reconstruction changes no FV state, bed geometry, roughness, volume,
solver clock, physical time step, source file or research solver. Exact aligned
window transfers remain bit-exact. The legacy fractional-grid transfer explicitly
retains its old raw bilinear depth/current and float conversion, rather than
feeding the new clipped point depth back into conserved solver state. Both live
gameplay sampling and the immutable presentation atlas use the correction.

## Native evidence, including failures retained

- Original native run 59860: exit 1, the new `WaterDryRockSampling` test fails.
  Report: `unreal/Saved/RaftSimValidation/dry-rock-before-v1-20260914/index.json`.
- First correction build 49086 failed on a local variable name collision; fixed.
- First wider run 34099: 14 pass / 1 fail. Zeroing sampled current in thin cells
  broke the existing real-atlas field-preservation gate. That behavior was removed;
  the gate and its tolerance were not changed. Historical report remains at
  `unreal/Saved/RaftSimValidation/dry-rock-after-v1-20260914/index.json`.
- Final build 48982: exit 0, 15.30 seconds. Final native run 49348: exit 0,
  **15 succeeded, zero warnings/failures/not-run**, 5.022164 seconds test duration.
  Report: `unreal/Saved/RaftSimValidation/dry-rock-after-v2-20260914/index.json`.

The final set includes the new live/atlas dry-rock test, analytic presentation,
crop boundaries, exact overlap, real shared atlases, coupled crest support,
shoreline geometry/compact upload/opposite-dry fan/exact and moving caches/fine
crest, completed GPU contact, career catalog and progression migration. New
controls cover the lower dry wetting front, untouched thin positive films,
independently differenced normals, unchanged sampled volume/time, and fractional
transfer retaining raw depth. Existing real-atlas state/evolution checks pass.
The unchanged Python shape analyzer's 12 tests and frame-CSV auditor's 8 tests
also pass; scoped `git diff --check` passes. The public sampling comment was
updated after the final build; no runtime or test code changed after that build.

Fixture preparation: run `physics/scripts/prepare_cartesian_runtime_fixture.py`,
then `prepare_cartesian_atlas_fixture.py`, then
`physics/scripts/prepare_dry_rock_sampling_fixture.py`. The last creates a new
`tmp/cartesian-dry-rock-fixture-v1` and refuses overwrite. These are analytic
fixtures, not surveyed river geometry or a substitute for river acceptance.

Built SHA256 identities:

- Reconstruction header: `4e85b8dcca91c728fc7cb92253659eadaa6df1dda435bf35617724ce648a747d`.
- Live-window cpp: `c00ecc641230b135d1f32ece4f671941feb62489e2b69f91754144fe8708d776`.
- Native test: `e8945cb6bfdc9c0a61599450bfd32f0afc83e1b41479d18c94347df5398db8f6`.
- Water DLL: `cf4a326823b1d7484d873b5de36da9a9a29be8d8d621654c2f1a2212ea5c71c2`.

## Actual playable scene: contact agrees, appearance still fails

Game 48549 completed exit 0 in the ordinary full-reach South Fork scenario at
station 8330, 1280x720. It did not enable a research solver or change materials.
Actual carrier contact at sequence 96 has 2,017 wet probes, 3 raw-dry probes,
zero unavailable probes, and maximum support/carrier error 4.767933e-5 cm.
942 points contain detail. Same-sequence GPU comparison passes 4,226 queries,
maximum RGBA error 5.960464e-8 against the unchanged 1e-6 gate. The dry probes
are not counted as wet contact evidence.

Reports: `tmp/south-fork-dry-rock-motion-{contact,detail,shape}-v1-20260914.json`.
The separate shape capture at sequence 121 contains 21,598 nearby triangles;
gradient decomposition closes to 1.798648e-12. Its fully wet 30–60 degree subset
still has source slope 0.620811, target-minus-source 0.087484, and submitted-base
minus-target 0.126004 on 913 triangles / 68.71875 m2. These are different epochs
and trajectories from older captures, not a controlled improvement comparison.
The dominant steep source geometry remains; the dry-rock fix does not explain
or repair all of those faces.

The complete local recording `unreal/Saved/VideoCaptures/RaftSim_20260914-115913.mp4`
decodes 191 encoded frames from 50 engine source frames over 6.373 seconds.
Encoding may repeat frames; its 30 Hz timestamps are NOT gameplay FPS evidence.
The unmodified extracted one-second frame was visually inspected:
[actual game frame](detail-motion/south-fork-dry-rock-motion-v1-20260914_01s.png).
Broad smooth green faces, bulky rock forms and blurred froth remain. **Visual
acceptance fails.** Full decoding/image-change measurements are not calibrated
breaking-wave dynamics or a continuous-motion visual acceptance claim.

## Ordinary performance still fails 30 FPS

Separate game 4734 completed exit 0 without screenshot/contact/shape exports.
Strict CSV/footer/water-scope audit passes all 300 rows, warm interval 120–250
inclusive. Target remains 30 FPS. Measured **11.435670 FPS**, mean frame
87.445685 ms, p95 **104.3914 ms**, versus the 33.333333 ms budget. The expanded
cook continued running; this is a shared-host, short Development/editor-hosted
capture, not an isolated causal speed comparison or packaged traversal.

CSV SHA256: `435cc54508d5714ae4086c322eb6960d89984f04984eee0910746fc1489f2422`.
Report: `tmp/south-fork-dry-rock-performance-v1-20260914.json`.

## Cook and remaining work

Live handle 84168 advanced beyond 9530 seconds. COMPLETE 9500 / local 2000
passes BOTH state and artificial-bank audits. All 86,720 artificial-bank cells
are exactly dry; maximum step conservation residual is 1.222035e-8 m3. It is
still unsettled: approximately 103.708334 m3/s out versus 45.306955 m3/s in.
Next COMPLETE 9600 is local 4000 in the recovered output and needs both audits.
The 417/422 research source guards remain unchanged. No broken research history
was restarted or promoted.

Continue the main source geometry/evolved-stage and jointly compatible
mass/pressure work; the steep fully wet faces remain unresolved. Then complete
Colorado, Pacuare, Futaleufu and the remaining water/crew/normalization/regression/
release scope. Troublemaker remains inside South Fork, never a menu scenario.
Neither this corrected shoreline sampler nor its native passes closes those gates.
