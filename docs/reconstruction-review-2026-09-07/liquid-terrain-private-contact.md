# Tagged-mesh contact implementation and instability evidence

September 8 continuation. Incomplete; no scene, material or system promoted.
The previous goal turn made progress. This turn implements an actual private
terrain query and changes the next action through GPU evidence, not acceptance.

## Implemented in the transient candidate

`RaftSim.LiquidTerrainMomentumReview private` retains the owned FLIP particle
update from the preceding experiment and adds a custom HLSL contact function.
It reads the existing User.Collide_Meshes DI through a typed parameter-map read.
That interface selects the explicit RaftSimLiquidTerrain tag. The stock global
Collision module is disabled in this variant; pressure, source arrays and escape
retirement are unchanged. Every active fluid graph is required to belong to the
transient system before it is edited. No engine/package content is saved.

The GPU call is GetClosestPointMeshDistanceFieldAccurate: signed distance,
normal validity, closest position/velocity and encoded-distance range. The
projection removes inward normal velocity without friction, using a2cm radius
and up to4 corrective queries. It now uses the actual Engine.DeltaTime input.
The later trajectory version starts from the previous particle position and
uses8cm travel steps (maximum32), sliding remaining travel along the contact
normal. Invalid negative-distance queries return to the preceding substep
position; they do not delete water. This bounded fallback is not proof of stable
physics, and proposed steps longer than256cm exceed that spatial sampling bound.

`-RaftSimLiquidTerrainPrivateContact` in the capture harness requires contact
mode, installs the transient variant and asserts its private identity. Runtime
readback exports query rows aligned with particle rows. Current columns are
distance_cm, normal_valid, normal_z, wall_speed_cm_s, proposed_step_cm.

## Actual results: not accepted

|Run at12s|Live|Below exact bed >one32.8125cm cell|Worst penetration cm|Outside|
|---|---:|---:|---:|---:|
|Private query, initial graph-copy warnings|54059|653|476.82|39|
|Private query after graph-copy fix|54888|467|479.70|18|
|Trajectory substeps|52746|977|545.13|87|
|Trajectory plus wall/step instrumentation|53572|1563|576.03|9|

Initial run2876: liquid-terrain-private-contact-readback. Corrected graph run
24933: liquid-terrain-private-query-audit. Trajectory47542:
liquid-terrain-private-swept-contact. Latest87302:
liquid-terrain-private-wall-audit. All processes exited0 and captures completed,
but the physical results fail. Independent runs vary; counts are not asserted
deterministic. None establishes calibrated mass conservation or performance.

In corrected-query run24933,52818 of54888 queried normals were valid. Invalid
queries can leave the engine normal output uninitialized; current telemetry
explicitly writes zero in that case. The corrected private-contact image was
inspected: patchy liquid remains concentrated at the inlet, not a realistic river.

The latest audit87302 rules out motion of the collision surface as the source of
the velocity explosion: all53572 reported wall speeds are zero. Mean proposed
particle step is2.73cm, but the maximum is3607.46cm in one1/60s update, and67
particles exceed the32x8cm spatial-substep budget.3463 query normals are invalid.
The fluid update is proposing physically unacceptable displacements. More
contact projection alone is not a demonstrated solution to that instability.

## Implementation failures retained

- First build rejected protected ReallocatePins. Public virtual
  AllocateDefaultPins works. Build53350 then failed linking unexported
  UNiagaraGraph::AddParameter; removed that optional helper. The existing typed
  User DI read compiles without it. Build2746 succeeds.
- Run86643 was launched against the preceding module after that failed build;
  its private-identity assertion stopped it. Folder
  liquid-terrain-private-contact-runtime is **invalid private-contact evidence**.
- Initial graph duplication called BreakAllPinLinks on copied, nonreciprocal
  links, producing ensures. It now clears only the new node's copied link arrays
  before making proper reciprocal connections. Builds78767/64525/91558 succeed;
  following captures show no graph-link ensures.
- Hardcoded1/60 query dt was replaced with the actual engine dt in build78767.
- No saved contact/map/project bytes changed: contacteefde251..., map81f31bec...,
  project01b95fff... match the preceding complete hashes. No commit.
- Final regression90429 exits0: engine-liquid-terrain-private-contact/index.json
  has7 clean passes,0 warnings/failures,7.77s. These cover the saved liquid
  fixtures/configuration, not acceptance of the transient contact physics.

## Next work

Stop treating small contact parameter changes as a route to acceptance. Audit
the particle/grid velocity transfer, pressure-step stability, particle crowding
at inlet cells and source momentum. Replace the inherited empty/flat tank startup
with the captured hydraulic field's wet volume and velocity, and verify real
incoming/outgoing volume. Assess PIC/FLIP mixing and timestep/CFL from actual
runtime values, not guesses. Preserve the existing photographic, raft-coupling,
exact-bed and performance gates. The original full queue remains unfinished.
