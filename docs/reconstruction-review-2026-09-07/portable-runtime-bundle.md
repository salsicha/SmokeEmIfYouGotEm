# Portable saved South Fork runtime data

Verified 2026-09-16. This change packages the existing saved South Fork scene's
runtime dependencies; it does not promote the experimental landward rock/water
candidate or establish visual, physical, packaged-execution, or 30 FPS acceptance.
Troublemaker remains a rapid within South Fork, not a menu scenario.

## Delivery

`physics/data/runtime_bundles/south_fork_saved_scene_v1` contains the exact
dependency closure of the native saved-scene bindings: 2,405 payloads totaling
916,906,778 bytes (803 JSON documents and 1,602 NumPy arrays). The existing 600 s
water state, route, terrain fields, and actor bindings are unchanged. Every file
is content-addressed and tracked with Git LFS. The bundle manifest SHA-256 is
`73736ed3459fcbd72e5a9d583d221346662cd03fe137b6d7c2290ff0c421daa9`.

Build rules check the payload hashes, sizes, and saved map/actor identities, then
stage the files under `RaftSimRuntimeData` beside the executable. Legacy logical
paths are preserved inside that tree; their bytes no longer depend on a local
developer `tmp` directory. Inputs participate in build-cache invalidation.
Missing LFS objects or changed scene bindings fail the build rather than silently
shipping a mismatched bundle. Regenerate the verified bundle when those bindings
intentionally change.

The generator validates all inputs before creating a fresh output directory.
Its verifier checks the exact transitive closure, canonical paths, duplicate
destinations, payload identities, and actual staged files without source fallback.
Builds, logs, caches, packages, and temporary audits remain covered by the existing
`.gitignore`; required runtime payloads must not be ignored.

## Verification and limits

- 113 focused Python tests PASS, covering runtime bundles, release fixtures,
  collision configuration, source retention, rock caps, and shading pairs.
- Unreal Development build reports `Succeeded`; all 2,405 payloads were copied.
  The first rules attempt failed on a missing rules-assembly reference and was
  corrected to use `EpicGames.Core.JsonObject`.
- The subsequent `-SkipBuild` run still rewrote target metadata. The real build
  then rebuilt three modules and relinked the game. Both unchanged-output wrapper
  guards correctly failed; neither wrapper is represented as an exit-zero audit.
- Staged-tree audit PASS: all 2,405 files / 916,906,778 bytes match exactly.
  Report SHA-256:
  `199c21fa1b80b4808ef25d1fdcfe467d3e85c683974e218f2b97e5085cd2434e`.
- Fresh native editor-process comparison loads absolute staged paths first:
  2,001 route queries and 2,601 initial-water queries (689 wet) match source data
  exactly. No solver steps or asset saves. Native report SHA-256:
  `c67dd49aea5189ec70d1ad9683da25e40a6b97ac465df0ef0d41d66cdd0f13fa`.
- Rebuilt executable SHA-256:
  `308ea189c9e56f9ded53481accefddf32c0e9e18fd150eca1c4c8928613849aa`;
  target receipt SHA-256:
  `7c21a33677521da69e67d67e31b69b077f14d66e701966ffe9d759a0bcf973dd`.

Audit outputs remain local under `tmp/south-fork-runtime-bundle-*-v1-20260916.json`.
The reusable native check is `unreal/Scripts/verify_south_fork_runtime_bundle.py`.
The full package cook was still running when this increment was committed.
Next: verify the final archive's executable and staged closure, run the non-editor
444-ground-source audit, then actual playable contact, motion, and performance
checks. Editor initial-field equality is not packaged gameplay acceptance.
