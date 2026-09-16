# Sustained and rotating contact qualification

September 16, 2026 UTC. Continuation of the local passage improvement in
`861c732c8`; not full hull, all-scene, visual, or performance acceptance.

## Failures found beyond the first river replay

The new independent plane fixture advances the same six supports under gravity
for 600 fixed 1/120-second steps on each of a horizontal and inclined plane.
Every completed substep checks all support clearances (>= -10 micrometres),
complete time consumption (1e-12 s tolerance) and no contact-generated kinetic
energy (1e-8 J tolerance). Those gates have not been relaxed.

Initial run `tmp/swept-sustained-native-v1-20260915/index.json` retained two
failures: a non-closing rotating hit at step 54, and repeated impacts exhausting
the substep at step 47 on the incline. A nearby-contact manifold fixed the flat
case but not the incline (`v2`). Instantaneously tangent points can rotate back
into the ground, yielding a sequence of ever-smaller impacts. The revised
manifold also evaluates the impending endpoint contact Jacobian when that
endpoint would enter its plane. Its impulses remain dissipative in the current
world-axis diagonal inertia metric; no substep time is discarded and no pose
is lifted. This is a fixed-step contact approximation, not exact rotational CCD.

`v3` passes both 600-step cases with no measured kinetic-energy increase and
maximum consumed-time error 3.47e-18 seconds. Expanded `v4` also passes initial
angular velocity (2,-3,4) rad/s on both planes, but the actual engine-mesh fixture
fails at step 284: 0.055609456 mm penetration, followed by an initial-overlap
refusal. The actual-mesh clearance gate remains 10 micrometres. This prevented
the guarded playable replay from starting; engine exit zero alone is not a pass.

Subsequent face-time and overlap-plane refinements (`v5` through `v7`) also
failed and have been removed, together with temporary registry diagnostic
logging. The initial hypothesis of a false overlap report was wrong: an
independent ray confirmed real penetration during a partial substep. A second
diagnostic found engine sweep normals and contact points inconsistent with the
actual flat floor, not merely tiny time-of-impact roundoff.

The candidate now sweeps translating spheres against original collision-provider
triangles in double precision, testing faces, finite edges and vertices. A BVH
reorders triangle references without changing source geometry. The cache binds
asset, body setup, collision-source identity and component transform; unavailable
source triangles produce an explicit invalid-hit refusal, not invisible ground.
Configured collision LOD/sections are retained. Faces are two-sided, and returned
face indices identify provider triangles, not necessarily Chaos-cooked indices.

`v8` passes all 11 tests, including 600 steps on the actual mesh with minimum
clearance 7.0392226e-9 m. `v9` and final `v10` pass all 12 tests, adding analytical
face/edge/vertex cases and 96 transformed BVH queries checked against all source
triangles. Final native report:
`tmp/swept-sustained-native-v10-20260915/index.json`, SHA256
`04c1e697d9c8048fffd1769a668070193ea8742fb21ceaf2521275c43539b1ef`.
Zero warnings, failures or unrun cases. Final editor build passed.

## Playable replay is NOT accepted

The guarded South Fork replay completed and finalized its recording, but logged
81 rejection entries: `zero-time separating contact cannot advance`, between
02:04:08.000 and 02:04:08.881 UTC. These are log entries, not an independently
deduplicated count of simulation steps. Native fixture success does not override
this actual-map failure. Keep the candidate opt-in; resolve and regress this case
before default promotion.

The three source caches were ready: 803,842 terrain triangles (3,541.823 ms build),
3,214 triangles (4.709 ms), and the 6,404-triangle candidate rock (10.054 ms).
The large synchronous cache build is also an unresolved startup hitch.
Telemetry reached station 8392.323 at 32.119 s, 8421.166 at 52.062 s and
8433.688 at 72.070 s; passage is not contact acceptance. No visual or 30 FPS
acceptance is inferred from these samples or the encoded recording rate.

Replay log: `tmp/swept-manifold-playable-v1-20260915.log`, SHA256
`10aa227796c918c8c351b68605298f8909c87a6934148ef1808edb6b2b0d569e`.
Finalized video: `unreal/Saved/VideoCaptures/RaftSim_20260915-190414.mp4`,
732 source frames over 64.215 seconds; not visually reviewed for this checkpoint.
Full-hull coverage, packaged CPU triangle availability, memory/contact cost and
arbitrary live-editor geometry mutation remain unqualified.

The implementation moved from an inline public header to a private source
file, retaining the public callback/API. Default gameplay remains unchanged.

## Actual authored hull is not six isolated spheres

The production raft is project-owned authored art, not a measured capture.
Its generator uses a 160-point superellipse chamber centreline, diminished and
raised ends, two thwarts, and a separate inflated floor. Six buoyancy/support
spheres cannot be labeled full continuous coverage of that shape. Connecting
their old centres would also produce a different outline from the real asset.
Full-hull work must bind to the actual chamber/floor and deformation model.

Source bindings (unchanged):

- `unreal/Scripts/build_production_whitewater_raft.py`: SHA256
  `ddeb157fe76cc1e6734927d1e2712b5f6f40256c9fd68126dccb6dae819583ee`.
- Authored production FBX: `dc5db2e526493cc9328836b5eecd73ad41980259371366bcebf2d391bd623328`.
- `unreal/Content/RaftSim/Rafts/Production/SM_RaftSim_ProductionPaddleRaft.uasset`:
  `ad9ca38179d0bcacd2c315bb4cdb54cb97cc75e35636c453c199dfa50ab366bf`.

## Hydraulic continuation

The continuing landward cook was not restarted or given old-geometry water.
Local step 3000 / absolute 200 seconds completed. Independent audits
`tmp/south-fork-landward-200s-snapshot-v1-20260915.json` and
`tmp/south-fork-landward-200s-banks-v1-20260915.json` pass all 5,350,400 cells
and all 86,720 artificial bank-face cells remain exactly dry. Maximum depth
4.347480938 m, speed 12.111856477 m/s, step residual 1.3647665e-8 m3.
Net boundary flow is still about +25.2449 m3/s; this is NOT settling acceptance.
Local step 4000 / absolute 250 seconds also passed snapshot and bank audits:
`tmp/south-fork-landward-250s-snapshot-v1-20260915.json` and the corresponding
`south-fork-landward-250s-banks-v1-20260915.json`. Maximum depth 4.630367685 m,
speed 12.111907195 m/s, step residual 1.3647665e-8 m3; all artificial bank-face
cells dry. Not settled. Later checkpoints are not certified by this document.

Before this commit, all 464 protected source/material/actor hashes were checked
again and remain unchanged. Generated logs, reports, captures, build output and
local-review assets are already covered by `.gitignore`; none is staged.

All terrain/crest/froth visuals, 30 FPS, full-hull/default contact qualification,
13 physical regressions, remaining scenes in their requested order, crew,
normalization and release remain open. Troublemaker is a rapid in South Fork,
not a separate menu scenario.
