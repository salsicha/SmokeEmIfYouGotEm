# Regional boundary coordinates and pressure metric

September 10, 2026. Progress toward full-rapid integration, not completed South
Fork water. The preceding contact-reader pass was progress. Production maps,
source terrain and the full objective remain unchanged; no commit.

## Runtime changes

Boundary face selection and outlet pressure no longer assume one 21 m square,
64 equal columns per side, or a fixed origin at (0,0,350) cm. A shared per-table
layout decoder supplies separate X/Y half-widths, XYZ cell sizes, physical cell
counts, computational extents, canonical origin and variable face-row offsets.
World queries subtract the canonical centre; pressure-grid queries use centred
XY and absolute datum Z. The geographic reflection is applied once.

The compatible divergence, pressure operator and pressure gradient now read the
same profile XYZ metric. Pressure centre and neighbour stage queries derive
their coordinates from computational extents and floor, replacing hard-coded
1115.625 cm offsets and the fixed 350 cm elevation. Inflow vector addressing
also uses the actual side lengths rather than a fixed 260-row offset.

`RaftSimLiquidBoundaryProfile.h` validates legacy scalar/vector and rectangular
v3 profiles. It checks finite data, horizontal orthonormal axes, integer counts,
cell/extent consistency, explicit face/vector offsets and normal-velocity
agreement. Rectangular uploads have a per-table ABI marker (negative header
height); disk profiles remain unchanged. The existing 2,000,000 reconstruction
cell limit and the wide-stencil X-coloring constraint are enforced.

**The fixed-fixture installer deliberately still refuses v3.** Loading a new
profile alone does not allocate the correct native grid or install matching
sources/particles. The existing max-axis resolution path cannot represent an
arbitrary anisotropic XYZ request. Bounded explicit allocation, region
selection and conserved state/exchange are still required. No resource cap was
raised and the whole rapid was not substituted with disconnected fixtures.

## Verification

- 190 liquid Python tests pass; editor builds succeed.
- [Four headless editor tests](engine-liquid-boundary-layout/index.json) pass
  cleanly: rectangular/legacy decoder, outlet shader substitution, geographic
  frame and contact encoding. The rectangular test uses distinct 50/75/33.33 cm
  cell sizes and a nonzero rotated-frame origin, rejects incorrect equal-side
  offsets and confirms the prepared whole-domain profile cannot bypass caps.
- First actual GPU run, `liquid-boundary-layout-regression`, failed compilation
  because an outer stage-axis declaration duplicated the new helper's local
  name. The failure is retained. Renamed the caller's canonical axes and rebuilt.
- [Corrected actual replay](liquid-boundary-layout-regression-v2/capture.json)
  completes 720 requested steps / 12 seconds with RHI validation. This is the
  existing 21 m regression patch, **not a rectangular/full-rapid GPU test**.
- [Clock](liquid-boundary-layout-regression-v2/clock_audit.json),
  [stage order](liquid-boundary-layout-regression-v2/stage_order_audit.json),
  [live surface](liquid-boundary-layout-regression-v2/live_audit.json),
  [affine transfer](liquid-boundary-layout-regression-v2/affine_audit.json), and
  [foam transport](liquid-boundary-layout-regression-v2/current_foam_audit.json)
  checks pass under existing tolerances. 759 reconstruction callbacks, 714
  positive-clock simulation updates and 45 render-only callbacks. All 30 motion
  frames are distinct. Live position max error 1.878e-6 m; affine max error
  3.541e-6 per second versus the unchanged 0.001 tolerance.
- No engine error lines in the corrected replay. The existing Niagara SimCache
  volume warning remains; captured GPU buffers, not SimCache volume replay,
  supply the audits. The 84.33 s blocking capture duration is not FPS evidence.
- [Secondary audit](liquid-boundary-layout-regression-v2/secondary_audit.json)
  confirms sampled terrain clearance, not exhaustive trajectories. At the final
  snapshot all 24,025 spray samples are outside the rendered liquid and all
  13,754 bubbles inside; foam absolute-distance p95 is 0.932901 cm. The audit's
  broader visibility/surface-coupling acceptance fields remain false; they are
  not overridden or represented as a pass.

Viewed `terrain_0720.png`: the isolated water is still a glossy, corrugated/lumpy
block with exposed boundary walls, not realistic returning whitewater. No visual
acceptance. The geographic saved-map SHA remains
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
All build/editor/audit sessions are terminal. Scoped diff whitespace check passes.

## Next

Implement explicit bounded native XYZ allocation and matching regional
source/initial-state installation, with shared conservative exchange rather
than independent restarts at internal faces. Then join one visible surface to
the full source-aligned rapid and raft, and verify actual GPU v2 contacts/v3
boundaries, whole-rapid motion, references and performance. Later river, crew,
normalization and release work remains queued behind South Fork acceptance.
