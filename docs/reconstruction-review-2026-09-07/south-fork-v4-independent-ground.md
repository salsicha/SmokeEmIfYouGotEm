# South Fork v4: independent source-ground comparison

September 27, 2026. Supporting validation of the already-recorded packaged
11,520 m rapid snapshot, not a new playable delivery, game run or acceptance.

The [paired contact check](south-fork-v4-paired-contact-pending.md) established
agreement between water support and the submitted water triangles, but its
ground heights still came from the engine's collision query. This follow-up
independently reconstructs ground height from the hash-verified archived v2
render/collision terrain triangles at **all 2,044 recorded probe locations**.
It does not simply reuse the collision heights or sample a bilinear bed raster.

## Result

- All 2,044 probes have source-triangle coverage; no survivor-only selection.
- Maximum source versus recorded collision difference: **0.000701296 cm**,
  below the predefined 0.002 cm numerical comparison tolerance.
- Wet/dry classifications agree at every probe without a classification
  tolerance. Both ground-occluded probes remain dry; no buried wet support.
- All intersected source faces belong to `coarse_0768_6016`. Four coarse and
  six context tiles intersect the conservative query bounds; the other nine
  contribute no containing triangles. Missing source coverage would fail.

| Probe index (zero-based) | Archived source face | Source ground cm | Water below source ground cm |
| --- | --- | --- | --- |
| 377 | 28109 | -246.712364030 | 0.232963957 |
| 2038 | 21299 | -84.958897771 | 8.069747662 |

These are archived triangle indices, **not claimed native collision face IDs**.
The numerical match does not independently identify every collider in the
packaged scene or establish that no coincident alternative collider exists.
The underwater bed remains inferred; this is not measured bathymetry evidence.
Swept hull contact, longer shoreline stability, visual/rapid reconstruction,
settled discharge and the existing busy-rapid 20 FPS failure remain open.

## Reproduction and safeguards

`physics/scripts/audit_tiled_ground_contact.py` merges each original tile
manifest with its explicitly named v2 replacements, verifies manifest and
selected NPZ hashes, preserves vertex/triangle counts and actor metadata,
converts local centimetres through float32 as in the export/import path, and
applies the documented actor translation and reflected Y scale. Independent
double-precision barycentric queries use the **original triangle diagonals**;
holes and missing coverage are not filled. Highest containing source triangles
are selected. No coordinates are snapped, geometry changed or captures rerun.

Run with the existing `south-fork-v4-paired-contact/contact.json`, and both
`coarse/manifest.json` and `context1024/manifest.json` under
`physics/data/real_world/south_fork_american_chili_bar/reconstruction_2026_09/full_reach/discharge_bed_v2_20260926/render_tiles/`,
using repeated `--replacement-manifest` arguments and a fresh `--report` path.

Twelve regression tests pass, covering triangle rather than bilinear heights,
holes, outside queries, reflected transforms, reversed winding, highest overlap,
vertical faces, malformed indices/observations, missing coverage, numerical
tolerance, exact wet/dry classification and a hashed-manifest fixture that
rejects source corruption. Test command:

```text
python -B -m unittest discover -s physics/scripts -p test_tiled_ground_contact.py
```

Final full report (ignored generated output):
`tmp/sf-v4-rapid11520-independent-ground-final-20260927.json`, SHA256
`2997c07dc0a04cd4ebd54b781dfddd8d01bea0fa0bbf96f8c697c335573b1e12`.
It includes every probe's independent height and source face, selected tile
hashes and all input manifest identities; no new duplicate source archive.
Auditor SHA256:
`11c0edf03edf8821d947d9a3daf17bedb354f5fea29d6f92bb1c7addb008621d`.
Input contact SHA256:
`8480495a2e9665f455b2c211dcfd0bbdda8267187990c697119ba0964ac52abb`.

No engine/game/cook was started. The v4 executable remains SHA256
`12d71f2830633d51d9b8851e9b4524b58fd74be33176d331092e6fd76433e523`.
Captured data, map, cooked fields and gameplay source are unchanged. South Fork
is still first unfinished. Do not repeat this unchanged numerical comparison
as a substitute for resolving physical geometry or runtime performance.
