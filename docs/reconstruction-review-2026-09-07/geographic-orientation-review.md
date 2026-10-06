# South Fork geographic orientation correction

September 9–10 continuation. Previous pass was progress: reference inspection
and footprint registration established that the local liquid patch does not
cover the full obstacle sequence. This pass returns to the larger playable
reconstruction and fixes a separate geographic presentation error.

## Confirmed issue

The captured geometry/export and coordinate map used Unreal X=east, Y=north,
Z=up. An Unreal camera looking along +X sees +Y on its right, whereas true
geographic north is on the left of an east-facing observer. Consequently the
rendered geographic layout reverses left/right relative to real references.
This is not a shifted LiDAR origin or a reason to move measured boulders.

Actual overhead captures were made with the same physical focus and altitude:

- Before: `unreal/Saved/Screenshots/troublemaker_registered_overhead_20260910_000.png`
  (camera −1500, 500, 15000 cm; pitch −90°, yaw 90°).
- After: `unreal/Saved/Screenshots/troublemaker_geographic_overhead_20260910_000.png`
  (camera −1500, −500, 15000 cm; pitch −90°, yaw −90°).

Both are actual engine renders. The corrected overhead is north-up/east-right,
matching the NAIP orientation. The old north-up view was east-left. Three
frames were produced for each; the first corrected frame was inspected.
The visible downstream water still does not cover the entire overhead framing;
this requires a separate presentation-coverage check, not a claim of dry riverbed.
Game-mode capture logs contain unrelated experimental EditorToolset Python
startup errors (`AgentSkill` / `PythonTestRunner` missing), so these runs are
not claimed error-free. Rendering completed and each process exited.

## Implementation

- Coordinate maps may explicitly declare `world_y_sign: -1`. Source map points,
  solver station/lateral coordinates, spatial searches, bed elevations and flow
  arrays stay unchanged. Forward/inverse world positions, current vectors and
  surface normals apply the same Y reflection. Omitted sign preserves legacy
  behavior; invalid values fail closed.
- The water carrier reverses submitted triangle winding for reflected maps and
  corrects the sign of geometry-derived normals. Source refinement topology
  remains unchanged. No second water surface was added.
- `stage_south_fork_geographic_review.py` creates
  `/Game/RaftSim/Maps/Review/Geographic/SouthForkRegisteredRockPlayable` from the
  existing registered-rock map. Its ground actor uses scale (1,−1,1); raft and
  player-start positions/orientations are reflected consistently. The source
  mesh and hydraulic arrays are not rewritten. The separate folder keeps the
  established map classification while preserving the original asset.
- The new coordinate map is under the reconstruction's
  `troublemaker/geographic_engine_review` directory. It records the original
  coordinate-map hash and the explicit source/world conventions.

The original registered map remains SHA-256
`81f31bec7ba8683e3a7479f17333419b6d32eeb277de5630f098d41fdf705ad7`.
The source geometry remains
`4b0dfeac342607c118e91b2182fced676b4fc0c9ea08c2ff70e2166818255d40`.
See [staging evidence](geographic-scene/staging.json).

## Verification and retained failures

The editor builds succeeded. Initial synthetic-map regression failed because
its 100 m segment violated the existing 16 m corridor-edge spacing limit;
the fixture now uses 10 m segments, without changing that validation. The next
run failed because `+` in the expected-error matcher did not match the literal
diagnostic; the matcher was corrected, not the rejection behavior.
`engine-geographic-handedness-v3/index.json` reports **1 passed, 0 failed,
0 warnings**. It covers source/geographic-left orientation, forward/inverse
mapping, cached queries, legacy defaults, invalid-sign rejection, and actual
registered South Fork depth/stage/current/normal parity over three sampled
solver states. This is not a long-run fluid validation.

The first scene-staging attempt stopped before writing data or scenes because
the Unreal test report contains a UTF-8 BOM. After explicit UTF-8-sig decoding,
staging succeeded. **254 collision-height probes** against the reflected
captured terrain passed, maximum error **0.003866 cm**. The baseline map hash
remained unchanged. Retained logs record both attempts.

The new `RaftSim.Survey.SouthForkGeographicGuidedTraversal` checks matched
reflected ground and flow, then runs the existing source-matched route with
normal guide/crew paddle commands. It reports the full world package and world
Y sign to distinguish review variants sharing a map basename.

`engine-geographic-traversal/index.json`: **1 passed with warning, 0 failed**.
Warning: `r.MotionVectorSimulation` was used on the render thread without the
render-thread-safe flag. This was not suppressed and remains a rendering risk
to investigate; no project-source use was found in this pass.

Actual run: `unreal/Saved/Automation/SouthForkGuidedTraversal_20260910_051755.json`.

- Correct geographic world package; world Y sign −1.
- Duration 64.898 s; station −55.435 → 110.248 m; reached outlet.
- 604 wet samples, zero missing-ground queries, zero grounded samples.
- Minimum sampled tube clearance 31.416 cm; maximum guide-route error 3.246 m.
- One carrier/shared scale throughout; 8 maximum detected breaking sites.
- 13 station captures requested and produced. Frames 003, 005 and 009 inspected.

The traversal is not an obstacle-impact test: zero grounded samples cannot prove
every boulder collision response. The 254 static probes validate sampled terrain
collision heights only. These results do not establish real flow calibration,
photorealism, all-scene performance or exact rapid identity.

## Visual result and next work

The corrected geographic traversal still shows coarse, blocky rock connections,
overly smooth water and insufficient piled breaking crests compared with the
user's footage. Correct handedness is necessary but does not solve those issues.
Continue on this corrected larger review: verify the fixed-rock/turn sequence,
resolve the unrendered downstream water coverage, and improve consistent
hydraulic crest/roller geometry. Preserve measured returns and label inferred
rock sides/submerged bed. The earlier isolated liquid experiment remains separate;
do not enable its old unreflected source transforms in this map without migration.

No production scene replacement or commit. South Fork and the full ordered
completion queue remain active and incomplete.
