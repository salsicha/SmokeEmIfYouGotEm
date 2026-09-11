# Secondary terrain contact and end-of-step phase review

September 9, 2026. South Fork remains incomplete; this is an isolated, unsaved
liquid review, not a promoted playable scene. Captured terrain is unchanged;
submerged bed, discharge and rapid identity retain their existing uncertainties.

## Implemented changes

`RaftSimSecondaryTerrainSweep.h` checks the entire straight secondary-particle
step against the same packed registered heightfield triangles used by primary
water. It clips the segment against each triangle's XY half-spaces and evaluates
linear vertical clearance at the clipped interval endpoints. This detects thin
ridges between the previous five samples. The secondary visual particle expires
on contact; primary water is not deleted or altered. This does not simulate a
droplet rebounding, splitting or spreading after impact, or an overhanging solid.

The sweep checks both endpoints against the **physical** 21 m domain, excluding
the 22.3125 m computational halo. Bounds come from `grid_boundary_profile.json`,
not the legacy 20 m clipping bounds in the window manifest. Invalid steps or
more than 256 candidate quads expire the visual particle instead of silently
truncating the search. No particle position is projected to conceal penetration.

`RaftSimLiquidSecondarySurface::EndpointPrediction` reclassifies the integrated
endpoint, using midpoint/RK2 backtracking through current grid velocity to the
previous completed surface. Foam thickness and emission gain are unchanged.
This fixes the old pre-integration phase label but **does not provide the current
reconstructed surface**. Telemetry now explicitly labels this predicted distance.
The existing column layout remains compatible with retained captures.

Both changes are opt-in (`RaftSimLiquidSecondaryExactContact` and
`RaftSimLiquidSecondaryEndpointPrediction`). The capture verifies their markers
in the actual compiled GPU shader, rather than merely inspecting graph text.

## Actual engine evidence

The final candidate also enables the existing control-centred window, pure PIC
affine transfer, shared surface cache and live reconstruction/foam pipeline.

| Capture | Secondary bed penetrations / domain escapes at captured times | Paused spray inside current rendered surface | Paused foam absolute surface distance p95 |
| --- | --- | --- | --- |
| `liquid-secondary-exact-sweep-12s` (before physical-bound fix, no endpoint prediction) | 0 / 20 (at frame 240) | 2,004 / 10,659 (18.8%) | 7.66 cm |
| `liquid-secondary-endpoint-phase-12s` | 0 / 0 | 1,211 / 10,115 (12.0%) | 5.82 cm |
| `liquid-secondary-endpoint-phase-60s` | 0 / 0 | 1,290 / 10,544 (12.2%) | 4.96 cm |

These are separate stochastic GPU runs, not identical trajectories or a controlled
estimate of the prediction's causal effect. Surface classification still fails.
The earlier affine 60 s run had 1,354 / 10,746 spray particles inside the surface;
the new long-run result is not a substantial resolution of that mismatch.

The 60 s run completes 3,630 reconstruction updates and 30 distinct motion frames.
Secondary counts at frames 6/30/60/240/480/3600 are 0/46/197/9976/29441/30157.
All recorded secondary positions/velocities are finite and every recorded
particle has an exact bed probe. Paused particle state is identical. The audit's
`sampled_secondary_contact_verified` is true; full contact/visual/physical
acceptance stays false. Independent continuous-segment reference tests cover
thin ridges, inclined triangles, initially penetrating particles and invalid data,
but sampled engine probes are not exhaustive GPU trajectory verification.

At 60 s there are 69,907 primary particles: no reported bed penetrations in
69,831 in-domain exact probes, no missing in-domain probes, finite state. The
remaining 76 primary particles lie outside the physical domain pending the
existing source/outlet lifecycle; this is not full primary-boundary acceptance.
Actual affine-gradient replay error is 2.9983e-6/s. Active foam coverage error is
0.00048828125, with source/history errors below 4.7e-6 and exact paused coverage.
These checks pass unchanged tolerances.

### Performance

`liquid-secondary-endpoint-phase-benchmark/benchmark_audit.json` verifies 480
uninterrupted editor-fixture frame intervals: mean **26.416 ms**, p95 **28.343 ms**,
max **29.672 ms**. The earlier affine candidate measured mean 25.928 / p95
27.904 ms. The approximately 0.49 ms difference is a separate-run observation,
not an isolated GPU attribution. Reconstruction GPU mean is 5.319 ms (density
4.567, distance 0.581, foam/copy/cache 0.171); this excludes Niagara simulation.
No packaged-game or full-scene performance acceptance is claimed.

## Visual comparison

Compared the actual `liquid-secondary-endpoint-phase-60s/motion_020.png` with the
user's real whitewater reference (`codex-clipboard-d8abf384-5a0e-44a3-8de0-1baee54963ed.png`).
The reference has dark green troughs, irregular thin breaking sheets, piled white
crests and fine spray. The candidate has visible froth and splashing, but still
reads as a cyan/glossy slab with rounded bead-like fragments and similar-sized
ridges. Its exposed rectangular window faces remain diagnostic boundaries, not
a continuous playable shoreline. Camera/light/scale are not registered to the
reference; no pixel-match or calibrated wave-height claim is made.

## Regression results and retained failures

- 149 numerical liquid tests pass, including two new fail-closed audit tests.
- Editor C++ build succeeds.
- `engine-liquid-secondary-exact-endpoint` initially has 13 passes / 1 failure:
  the older test compared deliberately recentered source arrays to the old
  window's coordinates. No executing shader assertion failed.
- The test now compares every selected native-profile position and velocity
  exactly, while separately snapshotting and asserting the saved source arrays
  are unchanged. The non-recentred test still requires baseline equality.
- `engine-liquid-secondary-exact-endpoint-profile` passes all 14 engine tests;
  one has an unrelated HTTP connectivity warning. New assertions verify the
  executing exact sweep, physical bounds and endpoint-prediction shader paths.
- Failed captures/reports are retained. A successful command exit alone is not
  acceptance: Unreal's first failed suite also exited with status zero.
- Saved contact-system, registered playable-map and project SHA256 hashes match
  the previous checkpoint. No production asset promotion or commit.

## Next required work

1. Replace the approximate surface timing with an explicitly ordered pipeline:
   primary integration -> current reconstruction -> secondary phase/integration
   -> rendering. Current `GetOnPostRenderEvent` reconstruction is too late for
   that step's secondary update. The local UE 5.8 source exposes DI `PostStage`
   / `PreStage` hooks and stage source/destination buffers; a dedicated owned DI
   can be investigated without patching the engine. Verify actual stage ordering,
   pause behavior, resource lifetimes and cost before switching the pipeline.
   No such integration has been implemented or validated yet. Do not hide the
   remaining mismatch with opacity or claim backtracking is exact reconstruction.
2. Recheck source/exit accounting, physical hole/crest shape and optics against
   real references. The bed and nominal discharge remain uncalibrated.
3. Integrate into the single playable water surface, verify shore/raft/boulder
   behavior and whole-scene performance, and complete South Fork acceptance.
4. Continue Colorado -> Pacuare -> Futaleufu and all remaining queued work;
   diagnostic test success does not shorten the goal.
