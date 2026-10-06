# Cartesian two-dimensional shoreline — September 12

Status at September 12, 13:24 UTC: implementation integrated into the Cartesian
carrier; 30 native/D3D12 regressions pass, including actual raster membership.
This does not promote the normal FullReach map or accept its visuals,
hydraulic settling, boulder/support shore agreement, or frame cost.

## Exact cache and reflected-winding correction — 13:24 UTC

The renderer now owns reusable vertex/index/cell-lookup arrays and an exact
topology cache. Source XY, wet/availability masks and every active shoreline
crossing must match exactly; otherwise topology rebuilds immediately. Height,
normal, foam, UV and tangent changes still update the drawn vertices every
frame. Unchanged topology does not upload indices. No quantization, tolerance,
decimation or frozen hydraulic geometry was introduced. Twelve state changes
compare all drawn attributes, indices and cell offsets against a fresh build;
invalid inputs preserve the preceding valid mesh and cache.

The first actual scene-depth test exposed a real defect missed by the earlier
CPU-area and proxy-identity tests: reflected geographic water was invisible
from above. An independent stock-engine cube rendered 1,936 expected pixels;
the water rendered zero above and 1,936 underneath. Its source-row winding had
flipped under the geographic Y reflection. `Build` now emits clockwise Unreal
front faces from each triangle's actual XY cross product. All 128 rotated/
reflected wet/dry cell configurations additionally assert upward-facing winding.

Fresh D3D12 report:
`unreal/Saved/RaftSimValidation/south-fork-shoreline-winding-v1-20260912/index.json`:
**30 successes, zero failures/warnings/unrun**. For both Y orientations, actual
rendered water pixel counts are **1936 / 0 / 1692 / 1692 / 1936** for full wet,
dry-out, dry island, cached height change and full re-wet. The island center
has no water depth; the height change moves depth from 1000 to 990 cm. Both
underside captures correctly have zero water pixels. One proxy is retained.
This proves opaque diagnostic raster geometry, not the final water material,
froth, animated river appearance or hardware ray tracing (project RT is off).
Failed pre-fix reports `south-fork-shoreline-cache-v1-20260912` and
`south-fork-shoreline-raster-control-v1-20260912` remain available.

Latest same-size 225 x 225 / 224 m / 1 m diagnostic: fresh clipping median
**5.718 ms**, p95 **14.527 ms**; exact cached updates median **3.067 ms**, p95
**4.239 ms**, one rebuild and 31 reuses. The earlier cache run measured
2.699/3.716 ms. Allocation reuse accounts for part of the fresh-build improvement
over the historical 11.608/24.809 ms. These are non-isolated CPU substep
measurements while the flow cook runs; full GPU vertex uploads, production
subdivision, actual frame cost and material motion still require acceptance.

Normal playable entry remains South Fork's FullReach map. Its new Cartesian
terrain/33.334 km route/water configuration is not installed yet, so this fix
must not be described as a completed visible upgrade to that menu entry.

Actual-game regression report
`unreal/Saved/RaftSimValidation/south-fork-shoreline-winding-gameplay-20260912/index.json`
has two successes (crew commands and scoring/save), zero test failures/warnings/
unrun, and a clean process exit. It uses an ephemeral profile. The game startup
log still contains installed UE experimental plugin Python errors for missing
`AgentSkill` and `PythonTestRunner`; this is not a clean release-log acceptance.
At 13:27 UTC, normal FullReach map and real profile hashes were rechecked and
match the unchanged hashes below. Scoped diff whitespace checks pass.

## Implementation

`RaftSimWaterShoreline` clips each Cartesian cell against actual available
wet/dry samples. Shared horizontal and vertical edge nodes keep storage below
three original grids and make neighboring cells share identical waterlines.
Dry islands remain holes; opposite wet corners form disconnected polygons.
Unknown source corners exclude the cell rather than extending into unavailable
terrain. All-dry cells emit no triangles.

The boundary against a rising dry bed intersects the wet sample's free surface
with the sampled bed slope. An advancing wet/dry front whose dry bed is below
that surface uses the shared half-cell face: an explicit finite-volume
presentation convention, not a fabricated dry-cell water level or bathymetry.
Wet water height/current/optical channels are retained at shore intersections;
dry reference heights cannot pull the sheet up onto the bank.

`URaftSimShorelineMeshComponent` retains one scene proxy and fixed RHI buffer
capacity. Vertex data and the active index prefix update in place. The raster
draw and ray-tracing geometry use only active triangles; empty water stays
empty without clearing/recreating the section. Ray-tracing geometry rebuilds
follow the existing procedural-mesh approach; this is not yet cost-accepted.
The component has no collision/navigation/raft-physics authority.

The actor's Cartesian branch uses this component for refresh, interpolation,
and recenter publication. It bypasses lateral-column bank retreat/reach/dry
collapse, probes shore terrain around two-dimensional wet boundaries, and does
not discard genuine source-backed channels via the legacy baseline flood fill.
The legacy non-Cartesian carrier is unchanged. Materials share the existing
configured dynamic water instance. Presentation anchors sample the actual
clipped triangle list, not the old source-lattice diagonal.

## Verification history

- Build v1 compiled the renderer/geometry/actor, but failed on mixed float and
  double constants in the new test's angle initializer. Build v2 passes.
- D3D12 report `south-fork-cartesian-shoreline-v1-20260912`: geometry and persistent
  proxy tests pass; actor test fails because its requested live crop extends
  beyond the deliberately small analytic source atlas. The loader correctly
  rejects missing captured-water state. No source extent or acceptance gate
  was weakened; the fixture now requests a physically in-bounds crop with the
  internal dry island and a larger source-backed presentation extent.
- Geometry test covers 128 cell-pattern/rotation/reflection combinations,
  water area, island exclusion, disconnected diagonals, exact bank crossing,
  advancing fronts, unknown coverage, and preserved linear optical/current data.
- Persistent-proxy test exercises thirty real RHI updates including dry-out,
  re-wet, and translation. Proxy identity remains unchanged; invalid indices
  are rejected without replacing valid state. This is not a rendered-film or
  hardware-ray-tracing visual acceptance test.
- Build v3 passes; D3D12 v2 reports 27 passes and one actor-test failure: the
  production 36 m edge feather covers the entire 20 m analytic fixture. The
  corrected test uses an actual `ARaftSimRiverWaterConfig`, both explicit carrier
  flags, and a two-meter fixture feather. Production's 36 m value is unchanged.
- Build v4 passes; D3D12 v3 exposes a genuine presentation-anchor mismatch:
  reconstruction through nominal grid/UV coordinates differs from the actual
  clipped geometry. Every one of the 25,636 tested triangle centroids is checked.
  It also exposes an inappropriate attempt to load a legacy band baseline for
  a Cartesian source atlas. These failures are retained in their reports.
- Fixed anchors to use actual triangle XY positions, keeping the same 1e-5 cm
  tolerance. Cartesian setup no longer loads the legacy band baseline. Build v5
  passes (7 actions, 54.88 s), with no new warnings.
- Final D3D12 report
  `unreal/Saved/RaftSimValidation/south-fork-cartesian-shoreline-v4-20260912/index.json`:
  **28 pass, zero failures/warnings/unrun**. All 25,636 actual clipped triangle
  centroids have valid anchors; maximum position error **5.14774001e-10 cm**.
  Dry-island anchors are rejected. Actual actor refresh/interpolation retains
  the same proxy, and the old uncut procedural core is hidden.

### Cost is NOT accepted

The pre-cache 225 x 225 / 224 m / 1 m pure-clipping diagnostic reported median
**11.608 ms**, p95 **24.809 ms**, 151,425 allocated vertices and 96,668 active
triangles. It ran with the continuing native flow cook on this machine and is
not an isolated full-frame benchmark. Even the median is too expensive to treat
as a finished per-frame path. Earlier v3 diagnostic was median 12.303 ms/p95
21.150 ms; replacing initializer-list index appends alone is not a sufficient
optimization. Preserve geometry and wet/dry correctness while removing redundant
per-frame topology construction/allocation; validate the actual production
subdivision/grid size, render uploads, and GPU/ray-tracing cost. The explicit
carrier configuration subdivides the small actor fixture to 121 x 121, so do
not assume the 225 x 225 diagnostic describes the normal production carrier.

Actual-game crew-command and scoring/save tests also pass: two successes, no
failures/warnings/unrun, using an ephemeral profile. Report:
`unreal/Saved/RaftSimValidation/south-fork-cartesian-shoreline-gameplay-20260912/index.json`.

Normal FullReach map SHA256 remains
`e77da92b73bf0a2c566fe69ee8a0ef7115d26182bb2f91648582aa1197ce13a0`;
real profile remains
`181d1e570485d1ec3139aec4e1d9b56d0a420fd107ce5a94218368324207f5b1`.

## Next requirements

Inspect actual rendered shoreline
motion and material behavior, including proxy/ray-tracing data and cost. Align
boulder eligibility/support lists and shore displacement before coherent normal
FullReach terrain/route/hydraulic promotion and common production crest settings.
The normal map still uses its old route/terrain/water. Keep Troublemaker out of
the scenario menu. See `full-river-expanded-checkpoint.md` for the CURRENT
836-core solve, session1541/PID31752, resuming exact 600 s state toward 1200 s.
The 600 s checkpoint has all artificial banks dry; settling is still unaccepted.
