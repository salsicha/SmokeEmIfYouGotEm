# Regional terrain and shared/exterior boundaries — 2026-09-10

South Fork remains incomplete. This pass prepares all twelve terrain pages and
shared/exterior boundary mappings and adds matching engine support. It does not
activate regional water, solve shared pressure, transfer live particles, or
establish photorealism/performance. No production map or asset was promoted.
The preceding user-facing status turn was no implementation progress; this pass
changes the implementation and yields new full-data evidence.

## Implementation and discoveries

`physics/scripts/liquid_region_geometry.py` constructs a distinct
`raftsim.regional_liquid_boundary.v1` contract, never a legacy tank boundary:

- All 1,304 parent exterior bed/stage/normal-speed and velocity rows are sliced
  unchanged and owned once. No interpolation or flux refitting at regional cuts.
- All 5,960 shared halo XY columns point directly to the unique neighboring
  physical owner, including diagonal neighbors. They contain no reservoir
  stage/velocity defaults and cannot act as native particle emitters.
- All 2,704 exterior halo XY columns map to their exact full-parent computational
  addresses. Corners do not arbitrarily select a new forcing face.
- Canonical station/lateral/up indices are explicit. The engine helper reflects
  Y at both ends for positive-scale Niagara addressing. Cell metrics, frames,
  particle volume and limits remain unchanged.

`RaftSimLiquidRegionalBoundary.h` independently builds these mappings from the
validated regional states and parent boundary. It rechecks complete physical
ownership and rejects missing neighbors, wrong frames/metrics/normal vectors.
Its internal faces have empty forcing arrays. This is a read-only runtime data
builder, not an installed pressure/transport pass. Pressure iterations must
coordinate across the interfaces; copying the previous frame's halo is not
sufficient. Particle-to-grid contributions and particle ownership also require
conservative coordination.

The old full contact table lacked the extra nominal neighboring quad needed at
an outer corner. Its original 522x338 quads were extended to 524x340 using the
original registered mesh, preserving the old triangles exactly. This adds
contact support, not new/moved terrain. All 356,320 extended triangles were
independently rechecked against that source mesh. Regional pages remain below
the unchanged 256x256-quad DI limit (maximum axis 152 quads).

A second actual-data failure exposed a rounding distinction: rebasing a page's
float32 origin could change the first triangle selected at a nominal quad edge.
One probe differed by 0.00006103515625 cm despite identical triangles and quad
origins. Rather than loosen parity, `raftsim.registered_liquid_contact.v3` retains
the original query anchor and adds a signed integer global-quad offset header.
The floor/addressing calculation now stays identical between pages.

The engine decoder, primary/pressure terrain query and secondary swept query
support this per-table ABI: negative uploaded columns mean relative XY, negative
uploaded rows additionally mean the third anchor-offset header. Disk dimensions
remain positive. Legacy v1/v2 tables remain supported. No mutable global encoding
flag is introduced. Explicit regional world-frame installation in all consumers
is still required; the old geographic fixture's translation must not leak in.

The declared page support is the computational XY cell-center AABB plus 50 cm
in ENU, with all neighboring 3x3 nominal-query candidates retained. This is NOT
a verified bound on all possible live particle sweeps. An active runtime must
enforce/extend required support, not clamp escaping queries.

## Authoritative data and verification

Prepared geometry directory:
`tmp/south-fork-liquid-regional-geometry-v4-20260910`

Geometry manifest SHA256:
`1ce01f3615bd92e6508b296a3285ace3fbf779ddf2fff90e1fa2ac1f6221cf9f`

Extended contact SHA256:
`45a4ee1a3c93c219720cb18f68dd6271b21802eb2289bebd92465c817a57b1e7`

Original mesh remains:
`4b0dfeac342607c118e91b2182fced676b4fc0c9ea08c2ff70e2166818255d40`

Independent `liquid-regional-geometry-source-audit.json` verifies:

- All twelve regions; all exterior rows once; all 8,664 halo columns exactly once
  per destination and pointing to the correct canonical cells.
- All 719,335 initial particle contact queries bitwise identical to the ORIGINAL
  pre-extension contact table, not merely the new extended table.
- 88,044 computational XY center queries and 98,304 independent support probes
  finite and bitwise identical to extended-parent queries.
- Original anchor/triangle bytes unchanged; every extended triangle agrees with
  the original registered source. Submerged bed remains an inferred prior, not
  surveyed bathymetry or identified rapid geometry.

203 liquid Python unit tests pass. Added coverage for missing/duplicate/fake
reservoir interfaces, diagonal owner addressing, exact exterior reassembly,
missing contact support, and nested anchored pages at float32 edge neighbors.
Scoped git whitespace check passes.

Editor builds 6420 and 46226 succeeded. Actual D3D12/RHI-validation report
`engine-liquid-regional-geometry-v1/index.json`: four successful tests, zero
failures, 33.813 s. `LiquidRegionalState` logged one unrelated Google connectivity
timeout warning; the other three have no warnings. Tests are:

- LiquidContactEncoding: legacy and anchored ABI, invalid-offset/cap checks.
- LiquidFixtureTerrainGridFrameTransfer: fourteen existing compiled coupling
  variants, including the changed shared query HLSL.
- LiquidRegionalGeometry: all twelve actual pages decoded, engine halo/face
  mappings compared elementwise with prepared data; missing neighbor rejected.
- LiquidRegionalState: full seed/owner identity, exact startup configuration,
  compiled source-fed/empty-source/tail examples.

Actual twelve-second old geographic fixture replay:
`liquid-regional-contact-regression`, log alongside it. Clock/stage/live/affine/
current-surface-foam audits pass: 757 callbacks, 714 positive-clock steps,
43 render-only callbacks, 30 distinct decoded motion images, 57,242 primary
particles and 55,982 supported. Maximum position error 1.849964e-6 m and affine
error 4.705097e-6 /s. No engine errors. Blocking capture took 87.582 s, NOT FPS.
53,634 secondary particles are reported; their full trajectory audit was not
rerun. Viewed `terrain_0720.png` still shows a glossy/lumpy isolated block with
exposed vertical edges: visually rejected, not a realistic roller. This is a
legacy v1-table replay, not actual regional/v3 contacts or wet partial-X coverage.

Retained failed preparation attempts: initial directory failed insufficient
source support; v2 failed NumPy integer JSON serialization; v3 failed exact
query parity. Fixed in v4, no acceptance gate relaxed. All process handles are
terminal: preparation87296, builds6420/46226, engine33990, replay4424, audit2120.

Saved geographic map SHA unchanged:
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.

## Next work toward the actual scene

Wire the regional contract into a coordinated live solve, not twelve independent
tanks: explicit per-component frame/contact/boundary installation; pressure
exchange within projection iterations and conservative grid/particle handoff;
isolated per-region GPU clock/foam histories and physical-volume reconstruction.
Verify actual regional birth, v3 contact and wet partial-X behavior. Join the
visible surface and raft support without duplicate edges, then validate the
whole rapid's hole/wakes/turns against footage and profile a playable scene.
South Fork remains active before Colorado, Pacuare, Futaleufu and the rest of
the full queue. No commit or goal completion in this pass.
