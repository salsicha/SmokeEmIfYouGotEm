# Gameplay export coverage audit — September 12

Heartbeat progress at10:01UTC, not a delivered scene update. The existing river
cook is still live (session63136/PID36216,step2730 /136.5simseconds). No duplicate
cook, map edit, solver replacement, source deletion or new Unreal build occurred.
The preceding flow-frame build and all22 checks remain terminal/passing.

Added `physics/scripts/audit_south_fork_gameplay_export_coverage.py`. It verifies
the source/core manifest relationship and ALL799 packet/826 core hashes, builds
exact core-to-packet slice mappings, and compares the original float64 bed at
every modeled intersection. Native source selection's active-source preference
and three-cell margin are replayed over every retained route and +/-12m probe.
The optional full original-water-domain check reads the retained2m raster and
tests the entire224m crop plus two ghost layers against unmodeled captured wet
cells; it does not replace the broader requirement with a centerline-only check.

Reports retained:

- `tmp/south-fork-gameplay-export-coverage-20260912.json`,SHA256
  `e05c19f4e82e8f0cf2391f367c2f73a1b65b30bdf4f4ca698f588f3c93793b13`.
- Extended `tmp/south-fork-gameplay-export-coverage-v2-20260912.json`,SHA256
  `03e397b7cf5158fa7efcd02c93f228121c07a09acdd3a5573f552687a048c25f`.
  Both audit processes are terminal exit0 (sessions82180,30793); successful
  execution does NOT mean complete source-state coverage.

## Evidence that changes export design

All41,594,716 modeled packet-cell intersections have exactly matching source bed.
All52,689 route/side crop+ghost probes have captured-wet state coverage. However,
the complete799 source packets contain21,518 unique captured-wet cells outside
the modeled tile union (58,412 appearances across overlapping packets). Full
packet coverage is therefore FALSE. Do not fill these with dry water/zero flow
and silently call them solved.

The broader406,823 original wet-domain probes include3,822 centered crop+ghost
footprints reaching those unmodeled captured-wet cells. The first recorded
failures reach the west exterior of the downstream domain: e.g.probeUTM
(669833,4293401) reaches unmodeled captured-wet cell(669719,4293364) at114m
Chebyshev distance. This is a physical-domain-boundary/crop issue, not a missing
terrain-data claim. Only the first20 failures are recorded; do not assume every
failure is downstream without inspecting the rest.

Next distinguish endpoint cases from any interior failures. Verify a boundary-
aware crop center, physical-edge handling or additional *solved* context while
preserving the full playable footprint. A raft can remain inside a crop without
being its exact center near a physical end. Do not shrink the footprint, loosen
the ghost requirement, mask out failed probes, or move the physical river merely
to pass. The main route passes already, but that does not prove all wet-domain
positions or every full source packet is valid.

## Storage/runtime implication

The retained packet bed is float64,notfloat32. Naively duplicating bed+h+u+v as
float64 for all82,329,759 packet cells plus masks costs about2.717GB, before the
remaining five127MB native snapshots. With current free space that would fall
below the cook's512MiB reserve. Do not delete captured sources or reduce precision
to hide this design problem.

Prefer one hash-verified shared native h/u/v tile atlas (about127MB), with the
audited per-packet slice index and exact source bed. The loader should cache the
immutable shared snapshot and gather only its required source window; avoid
rehashing/reloading127MB on every handoff. This is a proposed next implementation,
not existing runtime support. Preserve an explicit unavailable-state mask and
fail closed if a requested crop/ghost reaches unmodeled captured water. An
off-route source packet may contain such cells even when the actual route crop
does not. Packaging must stage the exact shared dependencies, not every cook
snapshot or captured acquisition.

The100s snapshot remains transient, not accepted flow. Export/index correctness
can be tested with it, but normal promotion still requires settling/section
discharge, remaining boulder/baseline Cartesian paths, coherent FullReach scene
integration, actual motion/visual/cost checks and the rest of the active goal.

## September 12 10:24 UTC: endpoint placement implemented and verified

The complete v3 audit classifies all3,822 original centered-crop failures:
1,382 beyond the upstream route endpoint,2,440 beyond the downstream endpoint,
zero beside the retained route. This supersedes the first20-only classification
above, not the captured-water or physics acceptance requirements.

- `tmp/south-fork-gameplay-export-coverage-v3-20260912.json`, SHA256
  `335cd3a376bf474f63a89315eaefe9dfd4964ed9f8721cf66160ed56c1fdb148`.
- Full failed probes `tmp/south-fork-gameplay-export-coverage-v3-20260912.failed-probes.npz`,
  SHA256 `f701ee181f805a610c838640146d39ae0cfd1f6d48bcbecfaacaaef6d085cc3f`.
- `physics/scripts/prepare_south_fork_live_center_coverage.py` generates legal
  continuous-center rectangles from complete integer crop+ghost coverage. Four
  safe corners prove each continuous square; degenerate safe lines/points remain
  available. No water state is synthesized and the224m window is unchanged.
- `tmp/south-fork-live-center-coverage-20260912.json`, SHA256
  `e4fee0e1e090ae44127da2e4b286063516f8b08ce58c706d099e394a5b5490aa`:
  406,823 probes,403,001 unchanged centers,3,822 shifted, maximum shift102m,
  minimum raft interior margin10m (required8m),797 rectangles,4 explicitly
  unusable source identities retained without fallback.

Native `FRaftSimCartesianWaterRegions` now accepts explicit
`valid_live_center_bounds_m` and mandatory `minimum_raft_interior_margin_m`
for those sources. Selection prioritizes the least center displacement, then
active-source continuity and source margin. Empty rectangles cannot be selected.
Malformed/outside-source rectangles fail closed. The real streaming actor uses
the selected center, preserves overlap and clock, and avoids repeated reloads
when the raft moves but its legal center remains clamped. It also checks whether
the raft remains safely inside the previous crop before reusing it.

Build session87577 terminal exit0,9 actions,50.73s;
`unreal/Saved/Logs/south-fork-boundary-center-build-20260912.log`.
Offscreen D3D12 session73700 terminal exit0 at10:20:44:
`unreal/Saved/RaftSimValidation/south-fork-boundary-center-v1-20260912/index.json`,
20 PASS,0 test errors/warnings. The native selector checks every3,822 formerly
failed endpoint probe plus all52,689 unchanged route/side probes. The actual
streaming actor verifies off-center raft movement, no redundant reload, legal
center movement and real solver-state transfer. Menu/migration and current-
oriented crest/support/GPU regressions pass. Actual-game session69844 terminal
exit0 at10:22:10,2 clean PASS in
`unreal/Saved/RaftSimValidation/south-fork-boundary-center-gameplay-20260912/index.json`.
Both runs use ephemeral profiles. Normal FullReach map and real save hashes
remain e77da92b... and181d1e57..., unchanged. Troublemaker stays off-menu.

## New prerequisite: evolved wet state reaches artificial exterior banks

The crop rectangles prove coverage of captured-water positions, NOT absence of
flow into originally dry context. Added
`physics/scripts/audit_cartesian_exterior_banks.py` to inspect complete snapshots
without changing the running cook. It verifies scenario hashes/order/grid and
snapshot completion, excludes2,218 directed shared tile faces and distinguishes
the4 physical inlet/outlet faces from1,082 artificial exterior bank faces.

At100s,20 of86,560 bank-face cells are wet (all initially exactly dry), maximum
depth0.1794729805292834m.17 exceed1cm. Affected faces:
core_0104 south(13 cells),core_0293 east(4),core_0302 north(1),core_0365 east(1),
core_0666 north(1). These are NOT the route-end crop cases above.
Report `tmp/south-fork-coupled-flow-600s-v2-20260912/frame_002000_exterior_bank_audit.json`,
SHA256 `d8aef45b52e44432a5246e16afa1d56f7c9f3bd1ff20088a4ad879e73d45b067`.
Script exit0 means diagnostic execution succeeded; `all_artificial_banks_exactly_dry`
is FALSE. No tolerance was raised to hide the finding.

Therefore exporting unmodeled dry context as freely evolving dry cells would
remove a reflecting boundary that actually affects this cook. Do not claim
equivalent runtime coupling. Next resolve the artificial-domain boundary using
additional source-exact solved context and a verified state-preserving restart,
or explicitly preserve the actual boundary topology with justified physical
semantics. Merely zero-filling exterior cells, masking these probes or accepting
reflecting walls as real banks is not a fix. Inspect later completed snapshots
for the full affected set before final domain design. The same original cook
session63136/PID36216 remains live (191/600s at this checkpoint), useful as a
diagnostic but not promotable on the existing assumptions. Do not overwrite its
executable/output or duplicate the solve blindly. Shared-snapshot/index runtime
loading, settling/section checks and normal scene integration remain unfinished.

Superseded process/domain status at10:38UTC:
[Expanded checkpoint](full-river-expanded-checkpoint.md). Source-exact6-tile
extension and exact-state restart verified; original solve deliberately stopped
with outputs retained. New832-core continuation session54194/PID37312 runs from
the complete200s checkpoint to600s. Its one-second pilot has no wet artificial
bank faces. This is not a settling or normal-scene acceptance claim. Future
gameplay export mappings must include the added6 cores.
