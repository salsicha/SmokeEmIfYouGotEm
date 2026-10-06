# South Fork discharge-bed runtime: independent follow-through

September 26, 2026. The owning session completed the 600 s cook, imported
190 changed terrain meshes and rebound the normal FullReach water actor.
This follow-through reads those saved assets and the new packageable v3 data
bundle without launching another engine, recooking, or modifying their work.
It is supporting validation, not a separate playable delivery or acceptance.

## Numerical and saved-asset checks

The [receipt](south-fork-discharge-runtime-audit.json) records the exact bundle
hash. `audit_south_fork_discharge_runtime.py` independently verifies:

- All 799 bundled runtime windows retain all 82,329,759 captured-mask cell
  occurrences and all 699,560 protected/registered bed cell occurrences.
  Only owners 1 and 4 are eligible for changed inferred geometry.
- All 841 atlas tiles (5,382,400 bed cells) exactly match the completed cook's
  input beds and grid origins. Bundled h/u/v bytes match its 600 s snapshot.
- The saved normal map, water actor and run-manager hashes match the bundle's
  scene binding inventory. All 190 imported terrain package hashes still
  match the owning session's completed import receipts.
- The bundle's dependency closure is internally verified. This does not prove
  that a packaged executable has been built, staged or run with this revision.

Two mutation tests reject edits to any protected owner, captured-mask changes,
and nonfinite runtime beds. These supplement the preceding six tile-audit tests.
The import receipts contain the owning session's collision probes; this audit
checks their saved package hashes, **not fresh collision traces**.

## Independent review of existing engine captures

Reviewed the owning session's actual FullReach raft-camera screenshots in
`unreal/Saved/Screenshots/`: `sfs2_1320_000.png`, `sfs2_1320_001.png`,
`sfs2_11520_001.png`, and `sfs2_25870_001.png`.

At 1.32 km, foam and camera-relative scenery differ between the two frames;
the channel shows broad foam streaks over a comparatively smooth surface.
At 11.52 km and 25.87 km, the inspected views show continuous water meeting
the banks, without an obvious open water-mesh gap in those single views.
They still lack convincing resolved breaking crests or individual boulder
controls. Smooth broad banks remain visibly simplified. These are visual
observations only, not quantitative shoreline-stability or motion acceptance.

The 11.52 km log explicitly launches the FullReach map with
`-RaftSimWaterReviewStation=11520` and a two-frame raft capture command.
Thus these views use the real game scene/data, but **do not verify the normal
Boot/menu launch path**. No FPS conclusion is drawn from the capture runs.

## Still required

Keep South Fork first in the queue. The 600 s state remains labelled
`settled_hydraulics=false`; preserved geometry and finite fields do not prove
hydraulic equilibrium. The owner is still inspecting the new playable state.
Normal-menu motion, collision/shoreline stability over time, convincing rapid
geometry and breaking water, and idle-host 20 FPS performance remain required.
No experimental solver was enabled by this audit.

Reproduce (use a fresh report path):

```powershell
python -B -m unittest discover -s physics/tests -p test_south_fork_discharge_runtime_audit.py -v
python -B physics/scripts/audit_south_fork_discharge_runtime.py --bundle physics/data/runtime_bundles/south_fork_discharge_bed_v3 --export tmp/discharge-bed-runtime-v1-20260926/export_audit.json --cook tmp/discharge-bed-20260926/cook_v1_full_out --imports tmp/discharge-bed-20260926/reimport_coarse_tiles.json tmp/discharge-bed-20260926/reimport_context_tiles.json --report tmp/NEW_UNIQUE_AUDIT/runtime.json
```
