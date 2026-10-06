# Two-axis water surface and disjoint river geometry — September 12

This is integration prerequisite progress, not full-river visual acceptance.
South Fork remains the scenario. Troublemaker remains a rapid within it, with
no standalone menu entry. No normal FullReach map or user save changed here.

## Visible carrier movement

The normal `ARaftSimWaterSurfaceActor` construction/recenter path now uses both
east and north coordinates when the adapter explicitly binds Cartesian water.
Station/lateral rivers retain their previous zero-lateral-center behavior.
The Cartesian carrier stays on an inward-rounded presentation lattice inside
the complete coordinate domain; bounds account for the actual rounded vertex
count, not just nominal dimensions. Fixed Cartesian carriers have an explicit
north-center property. These are render-window changes, not terrain deformation
or substitutions for downstream gameplay progress.

Both texture-origin components update. Existing material authoring already
reconstructs UVs with the origin's RG components; the current-normal shader also
uses `Origin.xy`, so no material graph mutation was necessary for this change.

Signed XY shifts move wetness, smoothed foam, crest lift, shoreline height,
bank elevation/probe state, film culling and smoothed flow with their original
cells. Incoming cells receive explicit fresh state. Mid-blend rendered positions,
normals, colors, flow and wake data use the same XY overlap mapping. Advected
foam retains its previous coordinate origin until the next transport update;
that update now records the new north origin as well as east.

`RaftSim.M4.CartesianSurfaceGrid` exercises actual production construction,
recenter and rendered-history carry methods in an isolated native world bound
to the real full-river coordinate map. It checks north-only, west-only and
diagonal moves, a large jump, texture-origin bucket crossings, incoming cells,
subthreshold motion and domain-edge clamping. This does not replace in-game
render/motion/performance inspection. Compilation/test outcome is recorded below.

## Source-exact disjoint geometry

Initial audit of 799 disjoint 80 by 80 cores found 1,054 internal shared faces,
1,088 exterior faces, and 36 wet exterior faces (343 captured wet cells, 336
positive-depth cells). Most were tiny interior coverage gaps, not physical
river entrances/exits. Evidence:
`hydraulic_regions_context/disjoint_core_boundary_audit.json`, SHA256
`73ba297f0d34791756b4f83d69fe5d9be7ef8cdc03a6b8cae8f9285baf0d2762`.

Added 27 complete cores from existing, hash-verified 321 by 321 source packets.
The original 799 cores are unchanged. No interpolation, missing-terrain fill,
bed adjustment or new measured-bathymetry claim was used. This closes every
interior wet exterior face in one iteration. The resulting 826 cores contain
5,286,400 cells, including 1,632,290 captured wet cells.

`coupled_geometry/manifest.json` SHA256:
`a0ec94752314422506d55acdde736d0bc3c4abcfc4952d42b66534fe5c387a76`.
Independent on-disk audit compares all four fields in every core to its exact
source slice, verifies all 799 source packet hashes and every output core hash,
and independently recomputes the wet exterior faces. PASS: all 5,113,600 original
and 172,800 added context cells are exact.
`coupled_geometry/source_exact_audit.json` SHA256:
`d00a791cee143f7c2718c7a2ebe99bfc7cc4f78436a39071b742169141dd0129`.

Only four wet exterior faces remain:

| Core | Face | Nearest route endpoint | Captured wet cells |
| --- | --- | --- | ---: |
| core_0000 | west | downstream, station 33,334.146 m | 45 |
| core_0001 | west | downstream, station 33,334.146 m | 57 |
| core_0825 | east | upstream, station 0 m | 65 |
| core_0825 | north | upstream, station 0 m | 14 |

These lie about 264–293 m beyond the nearest route endpoint. Classification is
geometric evidence, not a prescribed discharge, valid settled stage or measured
boundary velocity. The two upstream faces must not each independently receive
the entire river discharge. Whole-domain physical boundary treatment, initial
velocity preparation, conservative cooking and settling remain required.

Reproducible scripts: `audit_south_fork_disjoint_cores.py`,
`prepare_south_fork_coupled_geometry.py`, and
`verify_south_fork_coupled_geometry.py`. All completed with exit 0. Generated
geometry manifests deliberately retain `hydraulic_state_solved=false` and
`normal_map_integrated=false`.

## Build and test ledger

The previous native ABI rebuild (session 43455/PID 27180) finished successfully:
172 actions, exit 0, 1,938.63 seconds. Retained log:
`unreal/Saved/Logs/south-fork-coupled-native-build-20260912.log`.
The verified solver archive remains SHA256 `e69772d2...` from the coupling pass.

Follow-up surface build completed: 31 actions, exit 0, 161.18 seconds. Retained
log: `unreal/Saved/Logs/south-fork-cartesian-surface-build-20260912.log`.
Two pre-existing double-to-float C4305 warnings remain in
`RaftSimD6ChaosMeasuredRunner.cpp` at its damping literals. This is not a clean
release-warning gate. No solver archive change was made during the surface pass.

At 08:41:48 UTC the following report records SIXTEEN PASS, ZERO failures,
ZERO test errors/warnings and no unrun tests:
`unreal/Saved/RaftSimValidation/south-fork-cartesian-surface-v1-20260912/index.json`.
Log: `unreal/Saved/Logs/south-fork-cartesian-surface-v1-20260912.log`.
Combined build/test session 36226 is terminal exit 0. The surface test checks
641 exact overlap vertices through actual production methods, with correct
XY visual history and texture-phase behavior. Other checks cover solver window
state transfer, real streaming controller, source selection, global progress,
catalog/migration, spray carrier, crest localization/scale, texture precision
and water field encoding/continuity. Tests use an ephemeral profile and NullRHI;
they are not a visual realism or performance measurement. Standard engine
Toolsets/platform/NullRHI startup diagnostics remain separate from test results.

The additional actual-game test-tank run completed at 08:43:36 UTC, session
61885 terminal exit 0. Report
`unreal/Saved/RaftSimValidation/south-fork-cartesian-gameplay-20260912/index.json`
records TWO PASS / ZERO errors or warnings: crew response (6.51 seconds) and
run scoring/saving (28.18 seconds including map setup). This checks actual
game-world commands, motion and score progression under the rebuilt runtime,
not full-river visuals or production frame cost.

At 08:44 UTC all owned build/test/preparation jobs are terminal; no editor or
UBT process remains. Normal map SHA256 remains
`e77da92b73bf0a2c566fe69ee8a0ef7115d26182bb2f91648582aa1197ce13a0`;
user save remains `181d1e570485d1ec3139aec4e1d9b56d0a420fd107ce5a94218368324207f5b1`.
Python syntax checks and scoped diff whitespace checks pass. Free disk space
4,478,861,312 bytes. No files deleted and no commit made. The overall goal
remains active and incomplete.

Next playable delivery: physically appropriate full-river flow on the exact
disjoint cores, source-window export/runtime boundary profiles, coherent normal
FullReach terrain/material/global-progress/start/section/finish migration, and
actual game visuals, movement and timing. Crest-generation assumptions about
downstream X also need review against Cartesian flow direction; carrier XY
movement alone does not establish correct breaking waves or convincing froth.
