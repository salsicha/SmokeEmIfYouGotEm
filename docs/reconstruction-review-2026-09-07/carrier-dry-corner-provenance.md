# Submitted water over a hydraulically dry bank corner

September28 UTC. Bounded diagnostic complete, not a visible game improvement.
South Fork remains first and unfinished. The normal solver, wet/support gates,
geometry, material and 450s v8 fields are unchanged. No performance or visual
acceptance, and no advancement to Colorado, Pacuare or Futaleufu.

## New evidence

The v17 dry contact discrepancy is reproduced at effectively the same XY in a
new rebuilt package. The contact observer now retains the actual triangle,
raw depth/bed/stage, and the four surrounding presentation-lattice vertices:
both cached clipping inputs and fresh samples from the same call. This avoids
comparing against the separate shape observer three seconds later. These
extra reads are opt-in, non-shipping observation only; no water step, mask,
support override, mesh edit or additional detail commit was added.

At world10.025614811980631s:

| Quantity | Measured value |
| --- | ---: |
| Probe world XY, cm |(-542931.4614427652,-361170.3368914142)|
| Submitted water above registered ground |33.0438692cm|
| Submitted water relative to sampled hydraulic bed |-18.0651396cm|
| Raw water depth |0m|
| Presentation cell extent |1m x 1m|
| Clipping and fresh corner wet flags |wet, wet, dry, wet|
| Largest cached-to-fresh corner depth change |0.000004827976m|
| Largest corner bed change |0m|
| Raw point bed minus bilinear fresh corner bed |-0.000006872916m|

The retained triangle reconstructs the observer's barycentric XY exactly. Its
water is therefore genuinely submitted above the registered ground while
below the hydraulic bed at that point. Making the raft-support sample wet
would conceal the inconsistency and is expressly NOT a fix.

The positive-depth corner stage, normalized by donor weights, is7.870065525m;
the bilinear corner bed is8.062277991m. Their difference is-0.192212467m,
consistent with a dry mixed-footprint reconstruction, despite the drawn
three-wet-corner polygon covering the point. Simple bilinear corner depth is
0.258834033m; it is NOT the actual mixed wet/dry sampler and must not be used
to replace its dry decision.

This localizes a spatial shoreline/bed inconsistency with unchanged wet masks
and negligible corner-source age difference. The current clipper connects
edge intersections with straight polygon segments; its later crest refinement
does not re-clip against the mixed-footprint interior. That is the repair
direction. The exported coarse samples are NOT an export of native conserved
cell values; they must not be relabeled as such or used to assert an exact
native-stencil reconstruction. Ground-versus-hydraulic-bed representation also
remains an explicit discrepancy, not a newly measured terrain feature.

## Validation and artifacts

One owner only: session18046 / wrapper35664, start06:40:41.6906614UTC,
terminal06:48:27.2654951UTC, exit0. No live owner remains. Recipe:
`tmp/capture-dry-carrier-provenance-20260928.ps1`; receipt:
`tmp/sf-dry-carrier-provenance-20260928-process.json`.

Game/editor build succeeds in133.84s. BuildCookRun completes in422.72s.
Isolated diagnostic stage: `tmp/south-fork-provenance-v18-20260928/Windows`.
Existing packages and all captured data are retained. Known MetaHuman missing
texture-dependency warnings remain release work. This stage is not a new
visually accepted release.

The packaged normal FullReach configuration runs at8310 with only the contact
observer and capture-series controls added; exit0, zero logged runtime errors.
This is not a fresh Boot/menu validation or frame-time benchmark. Contact
totals remain1,982wet,42dry,41ground-occluded,0ground-occluded-wet; wet support
maximum triangle error0.0000476514cm. Only one dry probe is above ground.

Contact: `tmp/sf-dry-carrier-provenance-20260928-contact.json`, SHA256
`0da3f8add95688587d99277f2c06b83211bf1656b7eaf9d0310e61afe55110d5`.
Analysis: `tmp/sf-dry-carrier-provenance-20260928-analysis-v2.json`.
The initial analysis is preserved too. The tracked parser
`physics/scripts/analyze_carrier_dry_provenance.py` rejects unavailable,
nonfinite, misordered, negative-depth, out-of-cell and mismatched-triangle
evidence. Its11 tests include the actual captured case; combined with the24
existing presentation guards,35 tests pass in1.51s. These are diagnostic and
source checks, not shoreline acceptance. Frozen inputs, including the user's
native test, were unchanged after the run.

## Next bounded implementation

Use the retained three-wet-corner case to develop a spatially consistent
shoreline cut, with native sampler/mesh tests for all wet patterns and both
world orientations. Preserve positive films and disconnected channels; do not
make raw-dry samples support a raft or discard whole boundary triangles to
hide the mismatch. Preserve shared-edge identity, crest history, collision
source provenance and continuity. Measure the actual cost before promoting a
refined boundary: both rapid p95 gates already fail the20FPS requirement.

Do not repeat this unchanged capture to rediscover the same point. The next
run should implement and validate a candidate repair, then integrate it into
normal play with motion/shoreline/collision/timing review. Breaking-water
appearance, full rapid reconstruction and the larger river queue remain open.
