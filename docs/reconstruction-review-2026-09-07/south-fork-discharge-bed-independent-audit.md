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
