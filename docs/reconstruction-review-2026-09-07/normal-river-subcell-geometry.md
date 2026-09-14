# South Fork fine geometry and conservative cell storage — September 14

The preceding turn committed the pending source/ground audit tools as
`9954b68d3`; that was progress, not scene acceptance. This turn establishes
which geometry representation disagrees with the ordinary game's ground and
implements an exact local storage primitive needed for conservative coupling.
No runtime, terrain asset, material, solver state, menu or quality gate changed.

## Same ground, different between-cell representation

The actual ordinary-game shape capture remains
`tmp/south-fork-dry-rock-motion-v1-20260914.json`, world time
13.021444722020533 seconds. The read-only saved-normal-map collision audit is
`unreal/Saved/RaftSimValidation/south-fork-carrier-ground-v2-20260914.json`.
It queried combined tagged ground, loading both captured rapid and join actors.
All 13,883 queries hit; no survivor-only or substituted-ground comparison.
The normal saved configuration still selects the verified 600-second atlas.

At the 2,827 source lattice points, bilinear source bed and actual collision
agree within 0.000794 cm. At 11,056 actually referenced submitted water vertices,
the same bed reconstruction has median/p95/max absolute error
0.297546 / 9.234226 / **58.949981 cm**. There are 105 below-ground submitted
points whose four source corners have the presentation wet flag. This is not
proof that all 105 are visible; ground may occlude them. It is also not evidence
that the captured terrain itself should be moved or reshaped.

The new exact-source comparison uses the registered mesh's **rapid-local**
east/north coordinates and relative elevation, not UTM coordinates passed
directly to that local sampler. An initial direct-UTM probe correctly failed
closed for all points; no clamp/fill was added. The verified composite manifest
provides the rapid origin and datum, and the normal coordinate map provides
world origin/Y sign/datum. Saved map, profile, meshes and all 455 actor packages
are rehashed against the collision audit before comparison.

Exact registered triangles match collision at all submitted points to
**0.000181773 cm maximum**, p95 0.000030550 cm. Thus the fine source and collision
agree in this footprint; coarse hydraulic interpolation loses intervening shape.
The coarse-diagonal shortcut is also ruled out: changing bilinear interpolation
to the captured lattice's triangles raises maximum error to **77.774841 cm**
and p95 to 10.301669 cm. Do not deploy that swap or raise the water mesh to hide
this mismatch. Quantiles here use NumPy's linear convention; the Unreal audit
uses nearest rank, explaining its slightly different p95 (9.234619 cm).

## Waiting for the cook does not eliminate the steep source faces

Fresh report `tmp/south-fork-carrier-600-vs9500-v2-20260914.json` verifies the
immutable bed is identical at compared cells and both completed-state audits
match the later snapshot. Within the exact 30 m focus, the common wet subset
contains 3,102 source triangles / 1,551 m2 / 1,755 distinct vertices. The median
late-minus-early depth is -0.738976 m, but source area at least 30 degrees only
changes from **34.5 to 32.0 m2**; captured current-game source area is 34.5 m2.
These are source triangles, not rendered triangles or a full-river convergence
gate. Off-grid/unavailable points remain excluded, not dry or invented water.
Settling remains necessary, but waiting alone does not explain away this shape.

## Implemented exact source-triangle storage, not yet a coupled solver

`physics/scripts/triangle_cell_storage.py` clips original registered triangles
to each Cartesian finite-volume footprint without moving source vertices or
changing their diagonal. Missing footprint coverage fails closed. It integrates
`max(stage - bed, 0)` exactly and returns positive-depth wet area. The latter is
the stage derivative except at a flat triangle's dry-level kink, where the
left derivative/zero wet area is returned. A monotone local inversion recovers
the stage for a specified cell volume, with exactly zero volume staying dry.

The upper-height branch is expanded into positive terms to avoid subtracting
large complementary volumes in shallow water over two equal low vertices.
The regression includes 1e-12 m stage and exact analytic volume, without a depth
floor. The independent clipped-polygon oracle initially counted a flat dry
triangle's geometric area as wet area (5 PASS / 1 FAIL). Its zero-depth semantic
error was corrected, without changing a physics acceptance gate. The final
combined run has **15 PASS**, process 85584, 0.310 seconds: seven new storage
tests, five original captured-registration tests and three source-epoch tests.
Controls include exact flat/ramp volumes, partial wetting, independent polygon
integration, derivatives, shifted datum, tiny volumes, moved source vertices,
unchanged topology, inverse residual and missing-coverage rejection.

The actual rapid audit integrates all 2,827 one-square-metre source-cell
footprints (2,545 have strictly positive captured volume; this is not the 2,397
presentation-wet-point count). Holding each existing center stage constant over
its fine footprint yields 3,274.172897 m3 against captured cell storage
3,250.406432 m3: +23.766465 m3 net, 45.185124 m3 sum of absolute local differences,
and up to **0.342137 m3 per cell**. This diagnostic includes dry-cell bed levels:
282 exactly zero-volume cells alone would gain 10.560614 m3 if those bed levels
were mistakenly interpreted as water surfaces across their fine footprints.
It is not an integral of the actual rendered surface or a measured gameplay
volume defect. It demonstrates why a bed-only/constant-stage reinterpretation
cannot be assumed conservative.

Local inversion recovers every requested cell volume to **2.664535e-15 m3**.
The largest positive-volume stage shift is 1.168713 m in a roughly 1e-6 m average
depth cell, not a metre-scale correction throughout the main wet river. These
stages are **not installed in gameplay**: cellwise storage does not by itself
supply compatible intercell discharge, pressure force, momentum/energy work,
wet-front evolution, shared render/contact sampling or 30 FPS implementation.
The original coupled research failures remain unresolved, not superseded.

Final full report: `tmp/south-fork-subcell-geometry-v2-20260914.json`.
The earlier report is retained. A compact [tracked summary and input hashes](south-fork-subcell-geometry-v2-20260914-summary.json)
preserves the evidence without committing generated cell records. Reproduce
with `unreal/Scripts/audit_south_fork_subcell_geometry.py CAPTURE GROUND_AUDIT
--report FRESH_PATH`; scripts require NumPy and the existing source modules.
Geometry provenance remains captured surface plus explicitly inferred submerged
bed/rock flanks. Exact agreement with that source is not measured bathymetry.

## Cook and remaining full scope

Handle 84168 was directly confirmed live beyond native 9641/local 4820. COMPLETE
9600/local 4000 passed BOTH state and artificial-bank audits: all 5,382,400 cells
finite, all 86,720 artificial-bank cells exactly dry, maximum step conservation
residual 1.222035e-8 m3. Flux remains unsettled: 103.345374 m3/s out versus
45.306955 m3/s in. Reports are `tmp/south-fork-expanded-9600s-{state,banks}-v1-20260914.json`.
Next COMPLETE 9700/local 6000 needs both audits. No restart or suspension.

Next: couple exact source-cell storage/geometry to compatible mass and pressure
transport, then shared contact and render clipping, while retaining dry/variable
bed/conservation/energy/refinement and original moving-source gates. Independently
continue the normal renderer/crest/solver performance work toward actual 30 FPS.
Latest actual game visual and performance evidence still FAILS; no engine
capture or speed improvement was produced this turn. Then Colorado, Pacuare,
Futaleufu in order; remaining Chilko/Zambezi water, crew fit/animation/realism,
normalization, regressions and release validation. Troublemaker remains a rapid
inside South Fork, never a standalone menu scenario. The full goal stays open.
