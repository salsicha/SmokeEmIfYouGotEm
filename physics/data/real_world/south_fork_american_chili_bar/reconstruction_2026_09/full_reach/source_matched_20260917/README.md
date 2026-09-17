# Sources used by the normal South Fork reconstruction, September 17

These are byte-exact archives of the geometry used by the newly saved normal
FullReach map, not a new survey or a claim of physical acceptance.

| Archived file | Original local artifact | SHA-256 |
| --- | --- | --- |
| `registered_mesh_source.npz` | `tmp/troublemaker-control-ablation-v1-20260916/registered_mesh_source.npz` | `8edf8a7fbfb675a22ac6736db600a3300f018f1c9037b1c0674bc1c376cfcca7` |
| `bed_revision_manifest.json` | `tmp/troublemaker-control-ablation-v1-20260916/manifest.json` | `982f4a9374ea0cd23cb5d0c151354aaf40dc367ef551303a1461a76a0c512741` |
| `original_return_rock_cap.npz` | `tmp/troublemaker-source-connected-landward-v1-20260915/original_return_rock_cap.npz` | `78f77b67c64dc98094522ad2a8362edd0bfeab422816c90dc668e2cc5dd2baeb` |

`rock_cap_manifest.json` is also archived without rewriting its historical
paths, hashes, or acceptance flags. Original captured returns remain at
`../../troublemaker/classified_lidar_returns.npz` relative to this directory
(see the full repository path inside that manifest). Their SHA-256 is
`7f0a5d903a3914c830916390820cbf99260d7cb2f2cf667c57f2a1faa1c47cfe`.
The original registered ground is retained in the sibling `composite_terrain`
directory; it has not been overwritten.

The bed revision removes the old inferred shelf/plunge from 2,132 authority-2
vertices. Captured vertices, registered XY, topology and the rapid seam remain
unchanged. The remaining shore-distance depth prior is **inferred, uncalibrated
bathymetry**. Rock faces between exposed source points and the landward flanks
also contain documented inference. Do not label them measured underwater rock.

The historical manifests correctly describe their original experimental state.
Normal-play installation is recorded separately in
`docs/reconstruction-review-2026-09-07/source-matched-installed-receipt.json`.
The 4950-second flow was cooked against this geometry, not transferred from the
old bed. Its complete runtime dependency closure is versioned under
`physics/data/runtime_bundles/south_fork_source_matched_v2`.
Settled flow, calibrated rapid identity, convincing breaking/froth, full contact,
sustained 30 FPS and release acceptance remain unproven.
