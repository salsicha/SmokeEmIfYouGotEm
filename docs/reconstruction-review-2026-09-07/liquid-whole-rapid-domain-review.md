# Whole-rapid source domain and native boundary preparation

September 10, 2026. The preceding geographic-adapter pass was **progress**:
code changes plus actual GPU evidence. This continuation extends preparation
beyond the isolated hole, but does not yet activate whole-rapid 3D simulation.
South Fork and the complete queue remain incomplete.

## Coverage and preserved geometry

The previous 21 m liquid window contains no authority-3 recovered-rock vertices
and does not cover the obstacle/turn sequence. A source-aligned rectangle was
selected around all four previously reviewed rock regions: local Cartesian
station faces **-112.5 to 132.5 m**, lateral faces **-40.5 to 40.5 m**.
This is a 245 x 81 m preparation domain, centred at station 10 m. Station is a
Cartesian source coordinate, not independently measured channel chainage.

`build_south_fork_liquid_window.py` now accepts separate length/width and centre,
and clips exact source triangles to a rectangular collision patch. Its default
20 m square remains supported. Boundary sampling uses the appropriate separate
face lengths, rejects incomplete cells and does not clamp queries into source
coverage. The terrain remains fixed; selecting an origin does not relocate it.

The prepared package is `tmp/south-fork-whole-rapid-liquid-native-20260910`:

- 172,538 top triangles, 182,198 closed-solid triangles; artificial side/bottom
  closure remains labelled as numerical support, not survey data.
- Maximum top-centroid disagreement against the original exact triangle sampler:
  **5.8212e-12 m**, below the unchanged 1e-7 m threshold.
- **All 4,226 recovered-rock vertices** are inside the physical bounds.
- The independent aerial coverage check finds **100% of each of the four
  interpreted search-region polygons** inside the bounds. Region coverage does
  not verify named-rock identities or unseen submerged surfaces.
- Original mesh SHA256:
  `4b0dfeac342607c118e91b2182fced676b4fc0c9ea08c2ff70e2166818255d40`.
- Prepared solid SHA256:
  `9e7ac3a743d53844d3dd66c5598014bbfa38b182532c10750c701297ee0b4cf0`.

Rendered and inspected the [coverage overlay](troublemaker-whole-rapid-coverage/coverage.png)
on the existing July 21, 2022 NAIP image. Its label explicitly says prepared
domain, not active GPU or game capture. Numeric coverage and source hashes are
in [coverage.json](troublemaker-whole-rapid-coverage/coverage.json).

## Native flow, not interpolated shoreline leakage

`audit_south_fork_liquid_flux.py` now accepts arbitrary rectangular control-volume
faces. It requires exact native finite-volume face alignment and rejects
out-of-grid or rounded-to-a-different-face requests. The default old 21 m audit
remains supported.

The actual native solver's one-microsecond step over this complete domain gives:

| Quantity | m³/s |
| --- | ---: |
| Net native inflow | 0.1129338672 |
| Independently measured storage derivative | 0.1129344904 |
| Absolute disagreement | 0.0000006232 |

The unchanged conservation gate is 0.001 m³/s. This is numerical consistency,
not calibration to measured river discharge. See
[native audit](liquid-whole-rapid-native-flux/report.json).

The first prepared package, retained at
`tmp/south-fork-whole-rapid-liquid-20260910`, reports two dry-face conflicts.
Interpolated momentum suggested outgoing flow at station 93.25 and 93.75 m,
lateral 40.5 m, despite the exact bed being 4.9 and 6.3 cm above the interpolated
stage. The actual native face flux at the corresponding cells is zero.

The selected preparation takes **native finite-volume flux**, not interpolated
momentum, for boundary discharge. It apportions each native face only to its own
overlapping wet subfaces. A nonzero native flux without wet support still fails
with zero unresolved tolerance; no water is created to make a check pass.
Original interpolated values/conflicts are retained in each affected row.

Final prepared boundary totals: inflow **47.0068051382 m³/s**, outflow
**46.8938712710 m³/s**, zero dry-face conflicts. These totals refer to numerical
exchange through this rectangle, not measured total river flow. The native
source geometry, hydraulic manifest, raw face file and audit hashes are checked.
The native and initial interpolated packages have identical collision-solid
hashes: this correction changes boundary preparation, not the captured terrain.

## Tests and remaining implementation

17 focused unit tests pass: 12 clipping/sampling/remap tests, 2 native face-index
tests, and 3 source-rebase regressions. Cases include non-square volume, nonzero
centre, both horizontal flux components, invalid bounds, missing wet support,
and preservation of the legacy square. Scoped `git diff --check` passes.
All preparation/audit processes are terminal; no engine was launched this pass.

**Not yet implemented:** whole-domain or bounded tiled/moving GPU coupling,
native-face source/initial/contact profile generalization downstream of this
preparation, one continuous rendered surface at fluid/carrier joins, and raft
support/flow consistency through those joins. Existing runtime material/grid/
source code still assumes the small 68 x 68 x 24 fixture in several places;
do not point it at this package and infer success from an actor loading.

An all-at-once uniform full-rapid 3D grid may exceed the frame-time budget.
Choose and measure the bounded runtime layout using this complete coverage and
native exchange, rather than dropping obstacles from the requirement or calling
an offscreen capture wall time an FPS result. Then inspect the hole, wakes,
right/left passage and continuous shoreline in actual engine motion against the
reference, keeping uncertain bathymetry/discharge labelled as inference.

No production promotion, completed-scene claim or commit. The geographic map
hash remains `36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
