# South Fork candidate bed: independent tile audit

September 26, 2026. Supporting numerical validation only; no new playable
delivery or river acceptance is claimed here. The other session's hydraulic
cook and in-place Unreal terrain reimport were active throughout this audit.
Neither process was duplicated or interrupted, and no engine asset was edited.

The independent audit checks all 441 source/replacement tile pairs, not only
the changed subset, against candidate bed manifest
`f01abf14fed25bb8586eb5512f76a74f5aaa9d5c3eb3115e46b3adf7943d4c6b`.
The [machine receipt](south-fork-discharge-bed-tile-audit.json) records the
candidate and source hashes. The candidate remains inferred bathymetry at an
authored discharge, not a measured underwater survey.

| Check | Result |
| --- | --- |
| Coarse tiles | 390 checked; 188 replacements; 4,074,847 vertex occurrences |
| Context tiles | 51 checked; 2 replacements; 227,070 vertex occurrences |
| Grid mapping | Coarse row/column offset `(0,71)`; context `(0,0)` |
| Dry grid vertices | 3,832,673 bit-identical to the previous prior |
| Protected rapid rectangle | 27,010 grid vertices bit-identical |
| Changed finite grid vertices | 379,199 |
| Source nodata footprint | 33,596,317 nodata values retained bit-identically |
| Maximum absolute height change | Coarse 2.200 m; context 3.520 m |

All tile XY, triangle arrays, grid indices, actor transforms and retained
source metadata match the originals. Every revised Z equals its exact indexed
candidate grid height; unchanged tiles also match that grid. Shared indexed
vertices therefore retain equal heights across tile boundaries. File hashes,
replacement membership and declared change counts match. Rendered shoreline
stability and triangle-interior hydraulic sampling still need engine/cook
validation; equal vertex heights alone are not that validation.

The first diagnostic incorrectly required the entire rectangular bed array to
be finite. It rejected existing source nodata outside the retained terrain
footprint. The corrected audit requires identical finite coverage and nodata
bits, while requiring all actual tile vertices to be finite. No input or
acceptance threshold was changed to accommodate new missing coverage.

Six mutation tests pass: shifted-grid mapping; wrong candidate height; changed
XY/topology/index; wrong offset; dry/protected edits; and newly introduced
nodata. Reproduce with:

```powershell
python -B -m unittest discover -s physics/tests -p test_south_fork_discharge_bed_tile_audit.py -v
python -B physics/scripts/audit_south_fork_discharge_bed_tiles.py physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/discharge_bed_20260926/render_tiles --report tmp/NEW_UNIQUE_AUDIT/tile-consistency.json
```

Remaining gates: finish the owning session's import/cook; verify saved engine
mesh/collision readback and field/bed consistency; inspect actual normal-scene
animation, shorelines and surface continuity; rebuild/test the normal launch
with motion and idle-host performance at the user's 20 FPS target. This audit
does not authorize enabling the known-broken experimental solver or advancing
to Colorado.

## V2 follow-through — September26 15:54 UTC heartbeat

The owning session is now smoothing its inferred along-route depth transitions
and continuing the hydraulic state over that revised bed. Its v2 hydraulic cook
and in-place coarse-terrain import were active; neither was duplicated or
interrupted. This is a new-candidate consistency check, not a repeat of v1's
resolved staging diagnostics or a new playable acceptance claim.

The same independent full-tile audit **passes** against v2 bed manifest
`c637966b3b70e1f28847bb339d8eecad91772066d1806f4c0e309a0271b8a1c5`.
The [v2 receipt](south-fork-discharge-bed-v2-tile-audit.json) covers all441 tiles
(188 coarse and2 context replacements),4,301,917 vertex occurrences and384,982
changed grid vertices. All3,832,673 dry vertices,27,010 protected rapid vertices,
33,596,317 nodata values, source XY/topology/indices and actor metadata remain
unchanged. Revised/unchanged tile heights agree exactly with their indexed v2
bed; coarse/context offsets remain(0,71)/(0,0). Max changes relative to the
original prior are2.199996948m coarse and2.293281555m context.

A separate hash-checked v1/v2 array comparison gives maximum bed lowering
0.6294708251953125m. The existing inner backdrop's recorded1.5m minimum clearance
therefore retains a conservative **0.8705291748046875m source-vertex clearance**
against v2. This bound relies on the prior backdrop clearance receipt; it is
not a fresh rendered-triangle, collision or shoreline acceptance test. Compared
bed hashes are v1`4b7b8b3b16ede96ee6745f1eed27af83a1dca80767bf8718c45d325ebf96e51d`
and v2`a47fbebd0ee05c1a6eee9951229aa64cc70672ef38772728614f72ad18e0dc50`;
backdrop source mesh hash is`4dc6183c0d07adc095e96b916e0cab9df8dc89480cabc61d23b5414bc11dfe8c`.

Do not substitute this check for the forthcoming v2 cooked-field/bed audit,
saved engine collision readback, normal-scene motion and isolated20FPS run.
The v3 native staged-data receipt describes the preceding delivery, not these
in-progress v2 geometry/water changes. Rebuild and stage the final matching
dependencies together once the owning session completes its integration.
