# Shared Cartesian runtime state — September 12

The native runtime can now load the full-river shared flow dataset and gather
source-exact moving windows. This is an implemented and tested runtime path,
not merely an export plan. The201s data used here is transient diagnostic data;
the normal FullReach map is still unchanged and no scene/visual/performance or
settled-hydraulics acceptance is claimed. Troublemaker stays off-menu.

## Data path and fail-closed behavior

`FRaftSimLiveWaterWindow::CreateFromCookedFields` accepts an optional band-level
`shared_cartesian_state` manifest path and SHA256 within the existing cooked-
fields schema. It requires explicit Cartesian coupled configuration and rejects
survey replay, hydraulic-crux recentering and mixed dense h/u/v/wet sources.
Dense legacy inputs continue through the existing path.

The shared manifest schema is `raftsim.cartesian_state_atlas.v1`: float64
bed/h/u/v tile-row arrays, tile origins, grid spacing, vertical datum, dry
tolerance and explicit physical exterior faces. Loader checks actual array
bytes/hashes/dtypes/shapes, all finite bounded h/u/v cells, one disjoint integer
lattice, source grid/datum/tolerance agreement and exact per-packet bed equality.
Two source ghost layers are copied unchanged for the live MUSCL crop.

One thread-safe immutable dataset cache is keyed by absolute manifest path and
digest. It avoids rereading and rehashing the full river on each handoff. A
failed replacement never evicts the prior verified dataset. This is a bounded
single-dataset cache, not799 duplicated snapshots. The cache does not imply
frame-cost acceptance; actual scene timings remain required.

Availability explicitly distinguishes solved cells, captured-dry outside
context and unavailable captured water. Crop plus ghost footprint cannot reach
unavailable cells. The loader independently checks that every *artificial*
exterior bank face is exactly dry; it does not trust a generic passed flag.
Adjacent exterior cells at a wet *physical* inlet/outlet are also unavailable,
even when the capture labels them dry: internal-crop ghost data must not replace
the physical boundary with invented dry water. Fractional/duplicate tiles,
terrain mismatch, bad masks/digests, float32 shared state, nonfinite cells,
wet artificial banks and incompatible runtime configuration all fail closed.

## Export and complete source-coverage evidence

`physics/scripts/export_cartesian_runtime_atlas.py` exports exact terrain packets
and shared metadata while referencing immutable completed h/u/v snapshots. The
source arrays remain float64; no precision reduction or fabricated solved water
was used to save disk. Runtime release packaging must stage these exact external
dependencies explicitly, not every acquisition or cook frame.

Diagnostic export `tmp/south-fork-runtime-atlas-201s-v1-20260912`:

- 799 source packets and832 solved tiles;41,832,878 intersecting bed samples
  verified exactly against the source packets.
- Atlas manifest SHA256
  `5ac1c903b1c5d72a419db4effe0ea9d90181b84311d3026108ca0dccd7b3b2f1`.
- `export_audit.json`, SHA256
  `680eb17e64ab459a5d225ab11becc419473db371f940b79ba8f21b4ea4d8bd4a`.
- Shared h/u/v refer to the complete201s frame in
  `tmp/south-fork-expanded-checkpoint-pilot-v1-20260912/frame_000020`.

Important: the exporter's original `streaming_manifest.json` was a candidate,
not final coverage evidence. The extra physical-exterior check found two newly
unavailable cells in one allowed rectangle for region_0002. Added
`physics/scripts/audit_cartesian_runtime_source_coverage.py` to audit the union
of every continuous center rectangle's full crop+ghost footprint. Its optional
repair recomputes admissible centers from actual availability and then checks
ALL406,823 original captured wet-domain positions, without shortening windows
or dropping failed positions.

Use **`streaming_manifest_verified.json`**, SHA256
`e46b260653f94e819c23c80bc3aaf17f4e6dc81d610c23d5bf3cfd183769ffe8`.
It retains799 source identities and797 continuous-center rectangles. Only
region_0002 needed repair. All406,823 water positions remain covered:403,001
unchanged centers,3,822 shifted,maximum shift102m,minimum raft interior margin10m
versus the8m requirement. All windows retain224m extent. A separate fresh audit
of the repaired file passes with no invalid rectangles, including181 physical
wet exterior cells and10 additionally unavailable packet-cell appearances:
`runtime_source_coverage_verified_audit.json`, SHA256
`561ed14559b46855cc6a3545274e838aff6dc2826c4fc073e22f5c609bd10d23`.

For future snapshots, export to a fresh location, then run the coverage auditor
with `--repair` to a fresh verified streaming manifest and independently audit
that result with `--streaming-manifest`. Do not reuse an earlier snapshot's
center exclusions without checking current physical-edge wetness. Avoid
duplicating all packet bed/mask files for every later snapshot; they can be
shared by exact hash once exporter dependency reuse is implemented.

## Native and actual-game verification

`prepare_cartesian_atlas_fixture.py` supplies analytic positive/negative cases.
The first test run caught a fixture writer bug: JSON digest calculated before
Windows newline conversion. Corrected it to hash the actual written file.
The failed report is retained; no runtime hash check was bypassed.

`RaftSim.M3.SharedCartesianAtlas` verifies:

- Four-tile shared loading exactly matches an independently prepared dense
  source,96 source ghost cells and10 further live solver steps.
- A different source packet reuses the verified shared dataset. All malformed
  and unavailable-state cases reject, and failed loads preserve the cache.
- Real832-tile South Fork data:151,875 cells across3 full224m windows match
  independently exported dense references and3 live steps bit-exact. The
  dataset loads only once across these packets.

`RaftSim.Survey.CartesianWaterRegions` also reads the actual verified streaming
manifest. All3,822 endpoint probes and52,689 unshifted route/side selections pass
using the repaired, physical-exterior-safe catalog.

Builds all terminal exit0:

- 20705:38 actions,242.44s,`south-fork-shared-atlas-build-20260912.log`.
- 12865:4 actions,18.26s,real-river test addition.
- 54423:5 actions,20.48s,physical-exterior guard.
- 26800:4 actions,18.58s,actual verified-catalog checks.

The two pre-existing C4305 damping literal warnings remain in the first broader
build. No compiler gate was relaxed.

Offscreen real D3D12 session76552 terminal exit0 at11:06:33:
`unreal/Saved/RaftSimValidation/south-fork-shared-atlas-v3-20260912/index.json`,
21 PASS,0 test errors/warnings. Includes shared loader, full source selection,
current-oriented crest/support/foam, GPU shared relief, exact overlap transfer,
streaming actor, menu/migration and legacy water regressions.

Actual-game session19371 terminal exit0 at11:08:18:
`unreal/Saved/RaftSimValidation/south-fork-shared-atlas-gameplay-20260912/index.json`,
2 clean PASS (crew responds to commands; run scoring/saves). Both tests use an
ephemeral profile. Actual normal map hash remains e77da92b... and real user save
181d1e57..., unchanged. Source tests are not a replacement for whole-scene
terrain/collision/route/surface/spray/motion/cost acceptance.

## Current next work

The live continuation's300s frame exposes14 wet cells on two new artificial
faces (core_0682 south,core_0683 west),maximum0.504105m. Its former repaired edges
are no longer affected. This snapshot cannot be used as a dry-exterior runtime
atlas. It was extended by one more source-exact tile using the verified
checkpoint workflow; the301s pilot has no wet artificial bank faces and preserves
all5,324,800 prior cells exactly. Current continuation session48811/PID8116
runs from300s to600s with833 tiles. See the latest process entry in
[Expanded checkpoint](full-river-expanded-checkpoint.md).

Next finish remaining Cartesian boulder-height/baseline paths and coherent
normal FullReach terrain/route/collision/water integration. Inspect later solve
snapshots for bank coverage, settling and section Q; do not call a transient
frame accepted steady water. Later rivers, crew realism, normalization, release
checks and final commit remain part of the unchanged active goal.
