# Fixed water coverage on the geographic Troublemaker review

2026-09-09 local / 2026-09-10 UTC. South Fork remains incomplete; no production
map promotion, photoreal acceptance, or final commit.

## Cause and implementation

The previous north-up overhead exposed downstream rock groups because the sole
carrier was a raft-following 240 by 96 m lattice with a 36 m station-edge fade.
The native reconstructed hydraulic grid is 271 by 161 samples at 1 m spacing,
covering station -135..135 and lateral -80..80 m. It is a fixed bounded rapid,
not a streamed reach. Its visible coverage should not travel with the raft.

Added opt-in `bFixedCurvedGrid` and center station to the existing carrier. Other
maps keep their prior raft-following behavior. The geographic review now uses
a fixed center of zero, length 270 m, width 162 m, and zero station-edge feather.
The 1.5 m spacing remains unchanged: 19,729 vertices / 38,880 triangles versus
the previous 10,465 vertices. No second water plane, physics-grid enlargement,
terrain edits, hydraulic-source edits, or shoreline wetness override.
The exact outer station row still has zero alpha; the simulated-domain ends
remain straight. This bounded result is not the continuous full South Fork run.

`unreal/Scripts/stage_south_fork_fixed_surface_review.py` verifies the input map
hash, makes a recoverable backup, changes only those carrier properties, saves,
and verifies the coordinate-map and hydraulic-manifest hashes are unchanged.
See `fixed-surface-scene/staging.json`. The backup is
`tmp/south-fork-geographic-before-fixed-surface/SouthForkRegisteredRockPlayable.umap`.
The stage process returned 1 despite writing its verified report and saved map;
its log has no Error/Traceback. Subsequent actual engine loads confirm the saved
map and properties. Do not call the staging exit itself a clean test pass.

Updated review map SHA256:
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
The original non-geographic review remains unchanged at
`81f31bec7ba8683e3a7479f17333419b6d32eeB277de5630f098d41fdf705ad7`.

## Actual coverage/traversal checks

The added `-RaftSimSurveyFullSurfaceReview` checks fixed bounds and actual mesh
section data at four stationary locations: (-60,-9), (0,3), (60,2), (100,20).
Initial v1/v2 checks incorrectly required visible water *inside the passing
raft*. They failed 38/40 samples, even with source depths above 2 m. Inspection
confirmed the intentional `ComputeRaftHullSurfaceExclusion` multiplier.
Those failed reports remain preserved, not relabeled as passes.

The corrected check requires continuous pre-hull coverage at every location,
and separately compares actual submitted alpha with that pre-hull value times
the exact last-submitted hull pose, within one 8-bit color quantization step.
It does not ignore low-alpha samples, force water into the boat, or loosen
collision/route/outlet gates.

Actual `engine-fixed-surface-traversal-v3/index.json`: one test passed with one
warning, zero failed/not-run. Runtime report:
`unreal/Saved/Automation/SouthForkGuidedTraversal_20260910_060747.json`.

- 64.866 s, outlet reached, 607 wet samples.
- All 2,428 fixed-location checks passed; minimum pre-hull alpha 1.0.
- 57 probes affected by the intentional hull mask; maximum submitted-alpha
  error 0.001607 (below 1/255).
- One carrier and coupled hydraulic scale throughout.
- No missing/grounded tube queries; minimum tube clearance 29.636 cm.
- Maximum guided-route error 4.923 m: passes the existing 5 m gate narrowly,
  not a robust steering-margin claim.
- Existing `r.MotionVectorSimulation` render-thread CVar warning remains.

All 13 requested traversal images exist. Actual old/new overheads inspected:
`unreal/Saved/Screenshots/troublemaker_geographic_overhead_20260910_000.png` and
`unreal/Saved/Screenshots/troublemaker_fixed_surface_overhead_20260910_000.png`.
The latter now covers the downstream/upper-left rock groups instead of draining
before them. Also inspected the 1280x960 warmed capture
`troublemaker_fixed_surface_warm_20260910_000.png` in the same directory.
These are actual engine images, not generated illustrations.

## Performance evidence and limitations

Initial 360-frame interval included screenshot readback and a 0.54 s hitch;
it is not a clean warmed measurement. A separate run used engine frame-scheduled
`StartFPSChart` at frame 360 and `StopFPSChart` at 1080, after the frame-163
screenshot. Log: `tmp/south-fork-fixed-surface-warm-profile.log`.

720 frames / 11.54 s: 62.39 average FPS; average game thread 16.00 ms,
render thread 8.03 ms, GPU 5.27 ms; zero chart-classified hitches. Ryzen 7 5800H /
RTX 3060 Laptop GPU. Output screenshot is actually 1280x960 with a 1280x720
letterboxed view; scalability resolution quality is 60%, other categories 2.
The FPS chart's configured 2560x1440 metadata is stale and must not be cited as
the actual rendered resolution. Full-grid solver logged roughly 8.7 ms average;
initial carrier refresh was 6.633 ms (not a sustained refresh mean).

This is a short, static overhead, offscreen editor-executable game run of a
small gray-terrain review. It neither measures the cost delta in a controlled
A/B nor establishes production full-scene FPS. Both game-mode capture logs
contain unrelated EditorToolset/ToolsetRegistry Python startup errors and the
render-thread CVar warning; no error-free release claim. Game-mode captures
landed in Local/UnrealEngine/5.8/Saved and were copied unchanged into project
Saved/Screenshots for retention.

## Next

Keep the fixed extent, but do not promote this rough scene. Coarse rock-face
connections, overly smooth water and broad foam patches still fail the user's
footage reference. Next validate the larger source-aligned hole/turn sequence
and consistent physical crest/returning roller, then integrate the local fluid
layer in the corrected geographic frame. The old 21 m liquid fixture has not
been reflected and does not cover the rapid's recovered rock groups. Full-run
performance, source/bed uncertainties, later rivers, crew and release work all
remain in the active queue. All processes from this pass are terminal.
