# Shared registered-triangle fluid contact

September 8. **Terrain penetration is corrected in the sampled bounded GPU
runs; the scene remains incomplete.** Sustained inflow accumulates, motion slows,
and the material/presentation is not realistic. No production promotion or commit.

Boundary correction: both historical captures below used Back=false and
Down=true. Full compiled binding tracing subsequently showed these mean closed
negative Y and open lower Z. Their sampled contact measurements stand, but
they are not correctly configured open-river flow tests. Fresh runs use
Back=true and Down=false; see `liquid-boundary-bindings.md`.

## Implementation

`build_south_fork_liquid_contact.py` packs original registered mesh triangles
into a float3 array, retaining XY, diagonals and heights. It selects a world-axis
40m patch containing the rotated21m fluid window and query support, not a new
smoothed height raster. There are12482 triangles. Two header vectors identify
nominal grid origin, spacing and quad dimensions; each quad then stores six
vertices in world centimetres. The registered submerged bed remains inferred,
and named rapid identity remains unverified.

The float32 bounded3x3 nominal-quad search agrees with the reference sampler at
all77085 seed locations: maximum height error0.0006495027cm. An additional30000
off-seed test positions pass a0.01cm tolerance. Outside coverage returns invalid,
not a clamped or filled height. This is a heightfield representation: it does
not model overhangs or moving geometry.

Generated triangle_contact_profile.json SHA256:
46c331b495c55f368c20e38481abe6f9925d541c48928f8c59567c89ddc1c738.

RaftSimRegisteredTerrainQuery.h supplies **one shared HLSL query** for:

- The privately copied Grid3D_ComputeBoundary pressure classification, replacing
  its mesh-distance-field query.
- Private swept particle contact, replacing its coarse mesh-distance-field
  query. Query result is signed vertical clearance, not Euclidean SDF distance.
  Contact raises Z above the actual triangle top plus2cm and removes inward
  normal momentum; it does not delete water or clamp speed. The existing8cm
  trajectory substeps remain, bounded at32 steps.

The new exact-triangles variant retains wet initialization, correct lateral
boundary axes, corrected P2G frame conversion and complete neighbor gather.
Only the transient review system is changed. The baseline saved assets remain
unchanged. The active GPU shader contains RegisteredTriangleBoundary and the
same array query in particle projection, with the vertical-clearance response.

## Actual GPU verification

Build84207 exit0, capture76771 exit0:
liquid-terrain-exact-triangles-readback / CaptureLiquidTerrainExactTriangles.log.
At0.1,0.5,1,4,8 and12s there are **zero particles more than1mm below the exact
bed and zero invalid terrain queries**. The previous filled-state run reached
2439 particles more than one cell below bed at12s.

At12s:77399live,29940 initial-state survivors and47459 inlet-source survivors;
60 outside-domain particles at readback (escape retirement runs separately).
Median speed37.3cm/s, maximum596.6cm/s. A spatial analysis bin contains6598
particles. Inlet crowding remains, despite corrected contact.

The capture script now separates actual simulation duration from its frozen
presentation-control timeline; -RaftSimLiquidTerrainSteps accepts720..3600.
Capture74248 exit0:
liquid-terrain-exact-triangles-60s / CaptureLiquidTerrainExactTriangles60s.log.
It completed3600 actual1/60s steps, confirmed by captured metadata and engine
age, then performed fixed-camera controls. Wall time350.16s includes editor
rendering and blocking readbacks: **not a gameplay frame-time measurement**.

At60s:

- 164079live, zero detected bed penetration, zero invalid query normals.
- 49 outside the fixture domain at readback.
- Median speed9.73cm/s, p95speed116.24cm/s, maximum580.58cm/s.
- Upstream quarter118774particles; mean downstream velocity7.84cm/s.
- Centre quarter23075particles; mean downstream velocity2.40cm/s.
- Downstream quarter5672particles; mean downstream velocity1.52cm/s.
- The most populated analysis bin contains84109particles. These are fixed
  floor(local_position/32.8125cm) bins, not a GPU NeighborQuery occupancy read.

Both12s and60s opacity-one images were inspected. Water still looks pale,
smooth, patchy and incomplete. The long run establishes the next failure rather
than scene acceptance: fluid accumulates instead of maintaining river discharge.
SimCache emits its existing RenderTargetVolume caching warning; the reports
inspect actual particles and live captures, not baked replay of that volume.

## Tests, provenance and next action

Build44322 exit0. Thirteen focused Python liquid tests pass (1.301s). Expanded
engine regression70956 exit0, engine-liquid-exact-triangles/index.json:
eight clean passes,0warnings/failures,12.66s. The transfer test constructs all
five variants and checks the shared query in the compiled GPU program, along
with initial-state, boundary, ownership and source invariants. These tests do
not assert photographic quality, volume balance, raft coupling or performance.

Saved contact/map/project hashes remain eefde251... /81f31bec... /01b95fff...
(complete values in liquid-grid-frame-transfer.md). No saved package changes.

Next implement actual inflow boundary conditions and outgoing-volume accounting.
Continuous particle spawning alone is not imposing the prescribed grid flux;
arbitrarily pruning the crowded particles or restoring the truncated gather
would hide mass/momentum rather than repair the coupling. The stock open border
is two cells of EMPTY classification. Inspect its pressure/velocity treatment
and place the native numerical faces consistently, including any required grid
halo. Preserve the wet initial state and this shared exact terrain query.
After sustained flow, real optical/animation, raft and performance acceptance
remain required; the full ordered scene queue remains active.
