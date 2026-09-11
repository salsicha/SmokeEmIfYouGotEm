# Project normalization — 2026-09-06

This is a scoped maintenance pass, not a geographic reconstruction or visual acceptance report. Existing uncommitted reconstruction, water, character, captured-data and evidence work was preserved. Nothing was committed or pushed.

## Scene ownership and removals

The [scene catalog](../../unreal/Config/scene_catalog.json) records eight shipping maps: startup, Guide School training, and the six selectable rivers. Two South Fork survey review maps remain development-only and are explicitly excluded from cooking, along with their candidate environment directory.

The standalone `L_Troublemaker.umap` was retired. The frontend already launches the Troublemaker challenge in `L_SouthForkAmerican_FullReach`. Before removal, an Unreal Asset Registry audit found no incoming package references; source, configuration and script references were checked separately. Zero asset references alone are not sufficient grounds for deletion.

Removed from the active project:

- The obsolete 2,159,213-byte Troublemaker prototype map, moved to recovery storage outside `Content`.
- Its one-off `bootstrap_troublemaker.py` wrapper and entry in the compact-river generator.
- Legacy-only branches in the live map tests. The six-river test list now includes the full South Fork map and fails explicitly for missing scenes.
- Four accidental tracked Git LFS hook copies under `dev/null/`. These were not the configured repository hooks.

Shared hydraulic inputs, historical review artifacts, captured terrain and active review scenes were not pruned. The map move reduces active content, not total disk usage: recovery copies intentionally remain.

## Normalization

- The frontend, cook list and live map test list are checked against the scene catalog.
- Troublemaker approach telemetry uses the full-reach map. No route geometry was promoted or rebuilt.
- Single-river bootstrap tooling requires a valid compact-river filter instead of silently rebuilding every map. Full-reach builders remain separate.
- Root and Unreal setup documentation now distinguish current functionality from historical claims. The former root narrative is preserved in [the history archive](../history/README-before-normalization.md); historical evidence tests reference that archive.
- `.editorconfig` establishes text conventions without a repository-wide rewrite of existing work.
- `/tmp/` and `/dev/null/` are ignored and prohibited by repository guards. Existing scratch data was not deleted.
- CTest now registers three native solver fixtures. CI uses `--no-tests=error`, so an empty test registry cannot appear successful.
- The generated editor-source inventory was refreshed from the current checkout (90 implementation files instead of the stale 69). This is a current source index, not a rewrite of historical review evidence.

## Verification

- Unreal Editor build: succeeded.
- Real-renderer automation: **2/2 passed**, `RaftSim.M6.CareerCatalog` and `RaftSim.P4.RiverMapLoads.L_SouthForkAmerican_FullReach`. South Fork passed with warnings: `M_GrassBermuda01_Foliage` lacks the instanced-static-mesh usage flag and falls back to the default material; `r.MotionVectorSimulation` is accessed from the render thread without its thread-safe flag; a moving-window handoff cold-started without overlap. These runtime/asset issues were not modified by this maintenance pass.
- Native CTest: **3/3 passed** (wet/dry shoreline, lake at rest, transcritical bump).
- New project-layout tests: **7/7 passed** in both focused Python runs.
- Layout, release-candidate and South Fork survey-sanity Python run: **24 passed, 3 failed**. The failures are unchanged macOS packaging fixture tests running on Windows: Unix executable permission bits do not behave as those fixtures require. Release validation was not weakened.
- Layout and historical Zambezi reference run: **18 passed, 5 failed**. Four historical hash checks mismatch current files and one source assertion expects the removed `PrimaryPacket` implementation. The first failing artifacts are the Zambezi scenario validation report, `test_editor_source_layout.py`, `RaftSimWaterSurfaceActor.cpp`, and `rapid_map_digitization.json`; this cleanup did not edit those files. Historical hashes were not rewritten to manufacture acceptance.
- The initial editor-source test run had **27 passed, 8 failed**: stale inventory, two existing oversized source files, and outdated water/foliage source or provenance assertions. The inventory was subsequently regenerated; the other failures need their own refactoring or evidence review, not relaxed acceptance checks.
- Final combined Python run: **63 passed, 15 failed** across the five suites above. The regenerated source-inventory check now passes. The remaining failures are the three Windows/macOS-fixture issues, five historical Zambezi checks and seven editor source/foliage/water checks described above.

These are focused maintenance checks, not a full test-suite, packaged-build, performance or photorealism certification. Other rivers were not visually re-reviewed during this pass. South Fork reconstruction remains unfinished.

Local verification evidence is in `tmp/project-cleanup/`: `asset_inventory.json`, `engine-tests/index.json`, `pytest-targeted.xml`, `pytest-reference-final.xml`, and `pytest-final.xml`. The renderer log is `unreal/Saved/Logs/ProjectCleanupRuntimeTests.log`.

## Recovery and remaining work

The original map is at `tmp/project-cleanup/retired/L_Troublemaker.umap`. Exact pre-cleanup copies of the selected files, including the deleted wrapper and hook artifacts, are under `tmp/project-cleanup/before/`, with SHA-256 values in `manifest.json` and the original worktree inventory in `status.porcelain`.

To recover a removed item, inspect its corresponding backup and restore only that exact path after checking for newer work. Restoring the legacy map alone does not restore its cook, generator or test entries. Do not bulk-restore the snapshot over ongoing changes.

No Git history, LFS objects, captured source data or active build/GIS dependencies were deleted. The deleted `dev/null/` hooks remain in Git's index until the cleanup deletions are staged; the repository guard will flag them in that intermediate state. Commit/staging was not part of this request.

## September 7 follow-up: cross-platform packaging fixtures

The three macOS-fixture failures on Windows are corrected in the tests, not in
the package validator. A targeted fixture stat shim supplies the Unix executable
bit that Windows chmod cannot set; POSIX hosts still use real file permissions.
A new negative test verifies rejection when that bit is absent. The release,
project-layout and survey-sanity suites now pass **28/28**. This is not a real
macOS package qualification, and the other historical/source-layout failures
remain separate. Evidence: `../reconstruction-review-2026-09-07/release-fixture-regressions.xml`.
