# Code Review Remediation Plan

This plan addresses the four findings from the July 15, 2026 project review. It is written to be executed by an agent with no prior context. Read the whole plan before starting any phase. Phases are ordered by dependency and risk; do not reorder Phase 0.

## Context you need before touching anything

- This repo is a whitewater rafting simulator: `physics/` is a Python research/validation harness (`raftsim` package, run tests with `cd physics && uv run pytest -q`), `unreal/` is a UE 5.8 project whose substance is editor tooling, and the two sides communicate only through committed JSON report locks (e.g. `physics/reports/milestone20/report_set_lock.json`).
- The project's core convention is an **honest, evidence-first audit trail**: every change to validation behavior must be recorded in the relevant plan doc under `docs/`, and gates/manifests are hash-locked. Preserve this convention in everything below. Never make a gate pass by weakening what it records; make it pass by making its record truthful.
- The working tree may contain in-flight, uncommitted photoreal iteration work (at review time: cypress v42 artifacts and edits to `RaftSimEditorModule.cpp`). **Do not revert, clobber, or commit anyone else's in-flight changes.** If the tree is dirty when you start, treat those files as read-only context and confirm with the owner before any step that would rewrite them.
- Expected baseline test state at review time: 536 tests, **522 passed / 11 failed / 3 skipped** (~4 min). The 11 failures are snapshot/manifest tests that fail *because* the tree is mid-iteration (5 in `tests/test_milestone20.py` + `tests/test_milestone21.py` about locked manifests, 6 in `tests/test_photoreal_environment_assets.py` for cypress v37–v42). One numeric drift also exists: `tests/test_photoreal_environment_assets.py:5704` expects `mean_absolute_channel_delta` between 35 and 45 but gets 55.6.

## Execution log

### 2026-07-15 Phase 0 baseline

- Started from clean commit `630921253fa85b89af743b736e1d841cfc0cc253`.
- `cd physics && uv run pytest -q` accounts for 537 tests: **529 passed / 5 failed / 3 skipped in 131.81 seconds**. The five failures are stale generated/locked manifests in one Milestone 20 and four Milestone 21 tests. The six review-time cypress failures and numeric drift no longer reproduce.
- The exact command result, failure list, skip list, and interpretation are preserved in `physics/reports/code_review_remediation/phase0_baseline_2026-07-15.txt`.
- `physics/uv.lock` was absent before the run and `uv` generated it as an untracked file. Commit-versus-ignore remains an explicit owner choice; committing is recommended for reproducible builds.
- `outputs/videos/raftsim_2d_seed3.mp4` remains a tracked 9.5 MB LFS object despite `outputs/` being ignored. Removing it from the index remains owner-gated.
- This 529/5/3 result is the no-regression baseline for every later phase.

### 2026-07-15 Owner decisions (unblocks Phase 0 step 3)

- **`physics/uv.lock`: commit it.** Owner chose reproducible builds; add the file to git as-is (do not regenerate it first).
- **`outputs/videos/raftsim_2d_seed3.mp4`: removal approved.** Run `git rm --cached outputs/videos/raftsim_2d_seed3.mp4` so the `outputs/` ignore rule holds; the local file stays on disk and history keeps the old LFS blob.
- With these two items resolved, Phase 0 is complete. **Proceed directly into Finding 1, Steps 1.1–1.2 — no further owner input is required until the Step 1.3 decision memo.** Do not stop again for anything except the owner gates explicitly named in this plan (Step 1.3, LFS pruning in 3.1, policy sign-off in 3.2, and the Finding 4 memo).
- Phase 0 post-check: `cd physics && uv run pytest -q` remained at **529 passed / 5 failed / 3 skipped in 123.93 seconds**. There is no regression from the recorded baseline.

### 2026-07-15 Finding 1 Step 1.1

- Added an opt-in `disable_fixture_calibrations` configuration path through the Python runner and C++ CLI. Default calibrated behavior is unchanged.
- Added fixture-kind invariance coverage and a report generator that rejects any row not explicitly manifest-recorded as uncalibrated.
- Ran the frozen 40-row Milestone 16 GeoClaw/C++ matrix from commit `accfaeeef1b88baf9c33a024c00023cdfa9c80c4`. The uncalibrated solver passes **6 of 40** rows and fails **34 of 40**.
- Committed evidence lives in `physics/reports/solver_truth_baseline/uncalibrated_baseline.{json,md}`; the full per-row error norms and solver binary hash are preserved there.
- Step 1.2 must now relabel calibrated comparison rows as reference playback and remove playback rows from the solver-parity approval count.
- Post-check: the full suite reports **531 passed / 5 failed / 3 skipped in 124.64 seconds**. The two added passes are the new truth-baseline tests; the five failures and three skips are identical to Phase 0, so there is no regression.

### 2026-07-15 Finding 1 Step 1.2

- Added `parity_mode: solver | reference_playback` and manifest-derived `parity_evidence` to every v1 Milestone 16 comparison row. Missing fixture-scoped audit flags are rejected instead of guessed.
- Regenerated the calibrated C++ matrix after adding the missing finite-volume bed-step hydrostatic-source audit flag. The honest headline is **6 of 40 passing solver-parity rows, 34 of 40 reference-playback rows, and 40 of 40 raw calibrated threshold checks passing**.
- Regenerated the full C++ gate, GeoClaw-to-Unreal readiness package, and Milestone 20 report-set lock through their generators. All three are blocked, and the lock keeps live custom water disabled while preserving telemetry/frozen-playback use.
- Updated the governing water, readiness, Unreal, authority, and TODO documents so playback is no longer presented as solver approval. Step 1.3 is the next owner gate.
- Post-check: the full suite reports **539 passed / 2 failed / 3 skipped in 131.17 seconds**. The remaining failures are the pre-existing production-foundation plugin-list snapshot drift and Colorado rowing-route generator drift; neither is part of the water parity path. The honest-gate tests and regenerated downstream locks pass.

### 2026-07-15 Finding 1 Step 1.3

- Added `docs/water-solver-strategy-decision.md` with the measured 6/40 uncalibrated solver result, the 34/40 playback count, explicit Option A and Option B contracts, implementation sequences, risks, and gate consequences.
- The memo recommends Option B because flow-dependent rapid features, stitched geometry, real-world South Fork behavior, and raft/crew coupling require trustworthy fields beyond the six simple passing rows.
- Owner selected **Option B** on July 15, 2026. Subsequent solver splitting and implementation must preserve the analytic/GeoClaw regression gates and move toward a genuine well-balanced finite-volume core; live custom-water stepping remains disabled until those gates pass.
- Post-check: the full suite remains **539 passed / 2 failed / 3 skipped in 129.86 seconds**, with only the same production-foundation and Colorado generator snapshot drift recorded in Step 1.2.

### 2026-07-15 Finding 4 Strategy Review

- Added a deterministic miner and tests for all **47** locked Futaleufu cypress reviews (v1-v43 plus four v20.x branches). The committed report records zero promotions, gate-era counts, dates, normalized outcomes, and comparable green/silhouette/luminance evidence without modifying source reviews or captures.
- Added `docs/futaleufu-canopy-strategy-review.md`. It compares in-repo procedural work, dedicated vegetation middleware, licensed libraries, and a hybrid path against rights, ecology, Unreal integration, and the existing gates.
- Recommended a bounded hybrid pilot, froze V44 pending the source/ecology decision, and added six-cycle, metric-improvement, family-expansion, rights, and five-iteration stop-loss rules.
- Post-check: the full suite reports **542 passed / 2 failed / 3 skipped in 133.77 seconds**. The three new miner tests pass; only the same production-foundation and Colorado generator snapshot drift remains.

### 2026-07-15 Finding 3 Step 3.1 Audit and Proposal

- Confirmed hosted LFS endpoints on GitHub `origin` and the GitLab mirror. The active LFS/prune remote is GitHub `origin`.
- The current local audit is **8.6 GB `.git/lfs`, 3.7 GB `.git/objects`, and 28 GB working tree**. This differs from the plan's earlier 291 GB LFS snapshot; no undocumented cleanup is inferred. Current tracked LFS has 961 files and approximately 8.86 GiB of payload.
- Forty-nine tracked `.umap` files account for approximately 6.37 GiB; 21 generated `EnvironmentPreviews` files account for approximately 6.36 GiB and have been touched by 169 commits.
- Added `docs/generated-artifact-retention-policy.md` with keep/regenerate/evidence classes, exact Unreal regeneration commands, a conservative dry-run-first local retention proposal, hosted-retention separation, and explicit owner gates.
- No prune, LFS configuration change, untracking, ignore change, server deletion, or history rewrite was performed.
- Post-check: the full suite remains **542 passed / 2 failed / 3 skipped in 132.60 seconds**, with only the two previously recorded snapshot-drift failures.

### 2026-07-15 Finding 2 Step 2.1 Source Map

- Added `raftsim.editor_source_layout` so tests inspect the complete `RaftSimEditor/Private/**/*.cpp` source set instead of coupling implementation checks to `RaftSimEditorModule.cpp`.
- Updated all four directly coupled test files before moving C++ code. The geospatial manifest's function provenance remains on the current file until that function moves.
- Added a generated editor-source inventory with **6 implementation files, 46,915 lines, 34 unique registered console commands, 18 automation flags, and all six river build paths**. The report and tests become the split-completeness guard.
- Post-check: the full suite reports **544 passed / 2 failed / 3 skipped in 130.49 seconds**. The two source-layout tests pass and only the same production-foundation and Colorado generator snapshot drift remains.

### 2026-07-15 Finding 2 Step 2.1 Tool UI Extraction

- Extracted the editor tool subsystem from `RaftSimEditorModule.cpp` into `Private/Tools/RaftSimEditorTools.cpp`: menu/tab registration, tool descriptors and panels, validation actions, reviewed DataAsset creation, and screenshot evidence capture now compile as an independent translation unit.
- Kept module startup, console-command ownership, and shutdown in the module file so command lifetimes remain unchanged. Environment generation, foliage/PVE, captures, and river directors remain in the monolith and are still open work.
- Regenerated the editor-source inventory: **7 implementation files, 47,087 lines, 34 unique registered console commands, 18 automation flags, and all six river build paths**. The extra aggregate lines are translation-unit include scaffolding; the module file itself fell from 46,188 to 44,830 lines.
- Verification: the focused Python source-layout suite passes **13/13**, and the UE 5.8 `SmokeEmIfYouGotEmEditor Mac Development` target compiled and linked both editor translation units successfully.

### 2026-07-15 Finding 2 Step 2.1 Procedural Vegetation Extraction

- Extracted the reflected PVE graph configuration, cypress palette/atlas baking, async beech/cypress evaluation, structural review-map authoring, and evidence reporting into `Private/Foliage/RaftSimEditorProceduralVegetation.cpp`.
- Added `RaftSimEditorFoliageInternal.h` as the private boundary for shared environment-preview types and the small set of mesh, material, capture, and asset helpers required by PVE. The bridge keeps defaults and call behavior unchanged and avoids copying implementation into the new translation unit.
- Regenerated the inventory at **8 implementation files, 47,663 lines, 34 commands, 18 flags, and all six river paths**. `RaftSimEditorModule.cpp` is down to 36,964 lines; the extracted 8,442-line PVE implementation still requires an internal functional split before the god-file acceptance criterion is complete.
- Verification: the focused source-layout and photoreal asset contracts pass, and UE 5.8 independently compiled `RaftSimEditorModule.cpp` plus `RaftSimEditorProceduralVegetation.cpp` and linked the editor module.

### 2026-07-15 Finding 2 Step 2.1 PVE Functional Split

- Split the extracted subsystem into graph/palette authoring (`RaftSimEditorProceduralVegetation.cpp`, 2,154 lines), atlas baking (`RaftSimEditorPveAtlas.cpp`, 1,684 lines), and async evaluation (`RaftSimEditorPveEvaluation.cpp`, 4,898 lines) behind `RaftSimEditorPveAuthoringInternal.h`.
- The evaluation file's long completion function is now a documented frozen-legacy exception: only lifecycle fixes belong there; new graph, material, atlas, capture, or report behavior must be added to focused modules. The same function-owned-module policy now applies to Python milestone coordinators in `docs/raftsim-tools-workflow.md`.
- Verification: UE 5.8 independently compiled the authoring, atlas, and evaluation translation units and linked `libUnrealEditor-RaftSimEditor.dylib` successfully.

### 2026-07-15 Finding 2 Step 2.1 Production Foundation Lock Repair

- Added `raftsim.unreal_production_foundation` and a CLI generator that preserve authored foundation policy while deriving engine association and enabled plugin order from the current `.uproject`.
- Regenerated `production_foundation.json` to include `ProceduralVegetationEditor`, `ImpostorBaker`, and `ProceduralMeshComponent`. Updated the module assertion to keep `RaftSimEditor` explicitly outside runtime/production domain boundaries.
- Verification: all **20 Milestone 20 tests pass**; the former production-foundation stale-lock failure is closed.

### 2026-07-15 Baseline Colorado Generator Contract Repair

- Reclassified the Milestone 21 Colorado builder as the route/source seed it actually is. The committed source manifest has later official gauge, 3DEP, NAIP, NHD, release, access, and review attachments; regenerating the old seed over it would discard reviewed provenance.
- Replaced byte equality with a monotonic compatibility contract: route identity, endpoints, segments, flow bands, policies, and status remain exact; flow presets remain byte-equivalent; source IDs, fetch IDs, and artifact paths cannot disappear; confidence cannot regress; control semantics/telemetry remain stable while Unreal input-axis bindings may advance.
- Verification: all **35 Milestone 21 tests pass**; the former Colorado stale-generator failure is closed without rewriting newer source data.

### 2026-07-16 LFS and Generated-Map Retention Decision

- Owner decision: do not prune Git LFS and keep versioning generated preview/candidate maps.
- Closed Finding 3.1 without running an LFS dry run or prune, changing retention configuration, untracking maps, adding ignore rules, deleting hosted objects, or rewriting history.
- Updated `docs/generated-artifact-retention-policy.md` to retain the audit as a growth baseline while recording that its prior prune/untracking recommendation was rejected.

### 2026-07-16 Finding 2 Step 2.1 Module-Lifecycle Boundary

- Reduced `RaftSimEditorModule.cpp` from 36,964 to 1,035 lines. It now owns module startup/shutdown, the 34 console-command registrations, command handlers, and `IMPLEMENT_MODULE` only.
- Moved the existing environment implementation without behavioral edits into `Private/Environment/RaftSimEditorEnvironmentLegacy.cpp`. This is an explicitly temporary mechanical boundary, not completion of Step 2.1: materials, geometry, captures, landscape generation, and river-specific directors must still leave the 36,090-line legacy translation unit in focused slices.
- Fixed a unity-build collision exposed by the refreshed Unreal makefile by giving PVE authoring, atlas, and evaluation translation units unique private log categories. Emitted log behavior is unchanged.
- Verification: the regenerated inventory preserves all 34 commands, 18 startup flags, and six river paths; the 22 focused source-layout/Milestone 20 tests pass; UE 5.8 compiles and links `SmokeEmIfYouGotEmEditor Mac Development` successfully.

### 2026-07-16 Finding 2 Step 2.1 Environment Decomposition

- Removed the temporary 36,090-line environment legacy translation unit. The implementation now lives in 23 focused files covering catalog/configuration, materials, surface sampling, mesh primitives, canopy geometry/review, terrain, water/banks, atmosphere/foliage, near-field lighting, captures, landscape foliage/geometry/build, automation, and Zambezi/Futaleufu directors.
- Added `RaftSimEditorEnvironmentInternal.h` as the 2,109-line private contract for the shared types, enums, constants, and function declarations previously hidden by one anonymous namespace. `RaftSimEditorModule.cpp` remains a 1,035-line lifecycle/registration/handler file.
- Added a source-layout guard that fails if the module exceeds 1,500 lines, the removed legacy file returns, the private contract exceeds 3,000 lines, or any implementation exceeds 3,000 lines except the already documented 4,900-line frozen PVE evaluation lifecycle.
- Updated the source inventory to include private headers and regenerated it at **36 files, 50,491 lines, 34 commands, 18 flags, and six river paths**. Regenerated the Pacuare preview-centerline provenance through its generator so `GetPreviewRiverCenterY` points to `RaftSimEditorSurfaceSampling.cpp`.
- Verification: UE 5.8 independently compiled all 23 new translation units and linked the editor target; the 123 focused editor/geospatial/Milestone 20/photoreal tests pass.

### 2026-07-16 Finding 2 Step 2.2 Reference-Profile Externalization

- Moved the eight retained dam-break and reduced bed-step GeoClaw playback arrays out of `solver.cpp` into the versioned `physics/data/calibration/milestone18_column_geoclaw_profiles.json` calibration artifact.
- Added a strict schema/shape loader and explicit `calibration_only_not_solver_parity` provenance. This changes storage only: playback enablement, interpolation, bounded response, and emitted manifest fields remain unchanged.
- Verification: the native C++ targets compile, and fresh dam-break finite-volume, dam-break reduced, and bed-step reduced runs reproduce the pre-change manifest and frame SHA-256 hashes byte for byte.

### 2026-07-16 Finding 2 Step 2.2 Solver Decomposition

- Replaced the 38,573-line `solver.cpp` translation unit with focused runtime, numerics/playback, diagnostics, output, and eleven ordered constriction-correction translation units. Shared private types/declarations and fixture constants now live in bounded internal headers.
- Kept every solver source/header/output fragment below 3,000 lines and added a source-layout regression guard. The large manifest writer remains one public I/O concern but is physically bounded into include fragments and 100-insertion stream statements so AppleClang no longer reports stack exhaustion while compiling it.
- This is a mechanical Option B prerequisite, not a new parity claim: the uncalibrated result remains 6 of 40 genuine solver rows, retained playback remains calibration-only, and live custom-water stepping remains blocked.
- Verification: all native C++ targets compile without warnings, focused C++ solver tests pass, and all pre-split dam-break/bed-step playback manifest and frame hashes remain byte-identical.

### 2026-07-16 Finding 3 Step 3.2 Current-Review Dependency Boundary

- Adopted the versioned-generator retirement policy in the photoreal production plan: governed review evidence remains, while superseded generators, one-off drivers, exports, and version-specific snapshots leave the live tree after the successor review locks.
- Extracted the six constants/metrics still needed by V43 into `futaleufu_cypress_review_metrics.py`; the current locked driver no longer imports V32, V37, V40, or V41 scripts. This removes the historical driver chain before oldest-first deletion begins.

### 2026-07-16 Finding 3 Step 3.2 V9 Retirement

- Retired the superseded V9 texture generator, generate/review drivers, and two V9-specific snapshots after confirming later locked reviews no longer execute them.
- Preserved all V9 review JSON, source reports, capture hashes, and contact-sheet evidence under `docs/environment-captures/`; git history remains the implementation archive.

### 2026-07-16 Finding 3 Step 3.2 V10 Retirement

- Retired the superseded V10 texture generator, generate driver, and two V10-specific snapshots. Later historical evidence checks read the committed V10 manifest by path and no longer import executable V10 code.
- Preserved the V10 review/source/capture evidence unchanged; only implementation and version-specific snapshots left the live tree.

### 2026-07-16 Finding 3 Step 3.2 V18 Retirement

- Retired the superseded V18 generator, generate/compare drivers, and V18-specific snapshot. No later live code imports that version.
- Preserved the V18 twig-hierarchy review, source report, captures, and contact-sheet evidence unchanged.

### 2026-07-16 Finding 3 Step 3.2 V19 Retirement

- Retired the superseded V19 generator, compare driver, and V19-specific snapshot after confirming zero downstream executable imports.
- Preserved the V19 scale-leaf hierarchy review, source report, captures, and contact-sheet evidence unchanged.

### 2026-07-16 Finding 3 Step 3.2 V21 Retirement

- Retired V21 before V20 under the policy's active-dependency exception: the V21 generator directly imported and invoked V20, so removing V20 first would have broken the retained executable path.
- Removed the V21 texture generator, compound-branchlet compare driver, and two V21-specific snapshots. Preserved the V21 manifest, source report, review JSON, captures, and contact-sheet evidence unchanged; V22 may continue reading that governed evidence as its historical baseline.
- Verification: `import raftsim` succeeds, no Python source imports the deleted generator, and the full suite reports **542 passed / 3 skipped**. The pass count changed only by the two intentionally retired V21 snapshots.

### 2026-07-16 Finding 3 Step 3.2 V20 Family Retirement

- After V21's removal eliminated the last live dependency, retired the V20 texture generator, the V20/V20.1-V20.4 compare drivers, and the five corresponding executable snapshots as one locked experiment family.
- Preserved every V20-family manifest, source report, review JSON, capture, and contact sheet. Later historical drivers that still import V20 metric helpers are superseded and are removed in the following driver-cleanup slice; the current V43 driver remains independent.
- Verification: `import raftsim` succeeds, no Python source imports the deleted V20 generator, and the full suite reports **537 passed / 3 skipped**. The pass count changed only by the five intentionally retired V20-family snapshots.

### 2026-07-16 Finding 3 Step 3.2 Historical Driver Retirement

- Removed the superseded V17 and V22-V42 comparison graph plus the V1-V8/V14/V15 review launchers. V43 is the sole live locked comparison driver and depends only on the stable current-review metrics module; the unversioned source generator remains available for current asset generation.
- Added a retention guard that rejects any returning historical driver or versioned texture generator and requires all 47 governed cypress review JSONs to remain present and nonempty. No report, review, capture, contact sheet, manifest, or map was removed.
- Verification: the retention guard passes **3/3**, `import raftsim` succeeds, and the full suite reports **539 passed / 3 skipped**. The two-test increase is exactly the new executable-surface and evidence-presence guards.

### 2026-07-16 Finding 3 Step 3.3 Snapshot Suite Split

- Deleted 36 executable snapshots for rejected V1-V42 cypress iterations while retaining the two source/current invariants, the current V43 gate, and all 47 governed review JSONs. This is the intentional collection/runtime reduction required by the retirement policy; the reviews, not live tests, preserve historical outcomes.
- Replaced the 11,943-line residual monolith with ten per-concern test files and a non-collected shared support module. The largest test file is 1,900 lines; a layout guard rejects reintroduction of the monolith, a file at or above 2,000 lines, or a missing concern split.
- Verification: the focused split/retention suite passes **49/49** and the full suite reports **504 passed / 3 skipped in 138.61 seconds**. Relative to the preceding 539-pass run, the count changes only by deleting 36 historical snapshots and adding one layout guard; current V43 and shared behavior remain green.

### 2026-07-16 Finding 2 Final Unity-Build Boundary

- A clean UE 5.8 acceptance build exposed private helper-name collisions when UBT regrouped the decomposed editor sources into unity translation units; prior independent/incremental builds did not exercise that grouping.
- Set `bUseUnity = false` for `RaftSimEditor` and locked it in the source-layout test. The module's 36 focused implementation files now have an explicit build boundary matching their private namespaces instead of depending on adaptive-unity grouping.
- Verification: the focused source-layout suite passes **3/3**, and the invalidated UE 5.8 `SmokeEmIfYouGotEmEditor Mac Development` target compiles and links successfully.

## Phase 0 — Baseline and guardrails (do first, ~30 min)

1. Run `cd physics && uv run pytest -q` and save the output. Your job in later phases is to never make this baseline worse except where a phase explicitly says which tests will change and why.
2. Record `git status --short` and treat every already-modified/untracked file as off-limits unless a phase names it.
3. Quick hygiene fixes (small, safe, do them now):
   - `physics/uv.lock` exists on disk but is untracked and not gitignored. Ask the owner: commit it (recommended, for reproducible builds) or add to `.gitignore`. Do whichever they choose.
   - `outputs/videos/raftsim_2d_seed3.mp4` is tracked in git (LFS) even though `outputs/` is gitignored — it was force-added before the ignore rule. Propose `git rm --cached` for it; get owner approval first since removal edits history going forward.

---

## Finding 1 — The C++ water solver is overfit to its validation fixtures

### Problem

`physics/cpp/src/solver.cpp` (38,469 lines) contains ~251 fixture-scoped `apply_*` correction functions and ~2,046 `constexpr double k…` tuning constants. The main step function (`ReducedShallowWaterSolver::step_reduced`, around line 30027) checks `*_geoclaw_profile_enabled(scenario_, config_)` and, for fixtures with stored profiles, **skips the dynamics entirely and replays recorded GeoClaw reference data** (embedded arrays such as `kDamBreakGeoclawProfileDepthT3`; also a generic catalog at `physics/data/calibration/milestone18_fixture_geoclaw_profile_catalog.json`). `step_finite_volume_once` similarly branches on `scenario_.fixture_kind`.

The docs record this honestly (see `docs/custom-cpp-engine-validation-plan.md`, especially the paragraph at line ~123 recording the 40-of-40 GeoClaw/C++ parity gate passing "with fixture-scoped GeoClaw-profile calibrations"), but the consequence is that the 40/40 parity gate is **circular**: it validated profile playback, not the solver. That gate was then used (same doc, line ~23) to "approve live Unreal custom water." Meanwhile the actual Unreal water adapter is still a placeholder returning constant depth 1.0 m (`unreal/Plugins/RaftSim/Source/RaftSimWater/Private/RaftSimWaterRuntimeAdapter.cpp:108-126`), so nothing has shipped on false pretenses yet — but the approval chain is unsound and must be corrected before Unreal water goes live.

### Step 1.1 — Measure the truth (no behavior changes)

Add a solver/config switch (e.g. `disable_fixture_calibrations`) that turns off every fixture-scoped calibration, profile replay, and `fixture_kind`-conditioned branch, leaving only the base reduced and finite-volume dynamics. Then rerun the milestone 16/18 GeoClaw/C++ comparison harness (entry points are under `physics/src/raftsim/` — see `dual_solver.py`, `comparison.py`, `milestone16.py`, `milestone18.py`; comparison evidence lives in `physics/reports/milestone16/geoclaw_cpp_comparisons.{json,md}`) with the switch on. Produce a report: for each of the 40 rows, does the *uncalibrated* solver pass, and what are the actual error norms? Commit this as a new report (e.g. `physics/reports/solver_truth_baseline/`) and summarize it in `docs/custom-cpp-engine-validation-plan.md`. Do not delete any calibration yet.

### Step 1.2 — Make the gate honest

Update the comparison gate and its documentation so calibrated rows are labeled as what they are (e.g. a per-row `parity_mode: "solver" | "reference_playback"` field), and the headline metric reports both counts (e.g. "solver-parity N of 40; playback-parity M of 40"). Update the approval language in `docs/custom-cpp-engine-validation-plan.md` and `docs/custom-water-runtime-baseline.md` so that "approve live Unreal custom water" is explicitly conditioned on **solver-parity** rows (or on a new re-scoped criterion the owner accepts), not on playback rows. The existing milestone tests assert on committed manifests, so regenerate the affected locks/manifests through their own generators — never hand-edit a locked JSON.

### Step 1.3 — Put the decision to the owner

Write a short decision memo (in the plan doc or as `docs/water-solver-strategy-decision.md`) laying out the two viable paths, with the Step 1.1 data attached:

- **Option A (re-scope):** accept the reduced solver as a *game-feel* water model; validation target becomes qualitative feature correctness + stability + budget, not GeoClaw parity. The fixture playback machinery gets deleted as dead weight; GeoClaw remains an offline design reference.
- **Option B (real solver):** implement a well-balanced finite-volume SWE core (HLL/HLLC or hydrostatic-reconstruction Godunov with proper wet/dry fronts — the pieces the current code approximates with per-fixture nudges) and re-run the gate honestly. Larger effort; the 40-row fixture set becomes a genuine regression suite.

**Do not implement either option without an explicit owner decision.** Stop after 1.1–1.3 and report.

### Acceptance criteria

- A committed uncalibrated-baseline report exists and is referenced from the validation plan doc.
- No document or gate any longer presents playback rows as solver parity.
- The physics test suite passes at least as well as the Phase 0 baseline (regenerated manifests may change which snapshot tests are locked — document every intentional diff).

---

## Finding 2 — God-files

### Problem

- `unreal/Plugins/RaftSim/Source/RaftSimEditor/Private/RaftSimEditorModule.cpp`: **45,664 lines**, 83% of all plugin C++. Real, working procedural-environment tooling (landscape import, material authoring, GeometryScript meshes, foliage, scene captures, 40+ `RaftSim.*` console commands for six rivers) in one file, with a 1-line sibling `RaftSimEditorToolRegistry.cpp` and a 178-line header.
- `physics/cpp/src/solver.cpp`: 38,469 lines (see Finding 1 — its fate depends on the Option A/B decision, so **sequence solver splitting after Finding 1's decision**).
- `physics/src/raftsim/milestone18.py`: 9,297 lines / ~250 defs; `milestone16/19/20/21/22.py` similar in kind — code organized by milestone number rather than by function.

### Step 2.1 — Split RaftSimEditorModule.cpp (highest value, do this one)

Mechanical decomposition, no behavior change:

1. Map the file: enumerate the registered console commands and the per-river build paths (rivers: South Fork American, Colorado Grand Canyon, Pacuare, Zambezi Batoka, Futaleufú, Chilko).
2. Extract into cohesive `.cpp` files under the same module (e.g. `Landscape/`, `Materials/`, `Foliage/`, `Captures/`, `Commands/`, per-river directors), each with its own header; keep `RaftSimEditorModule.cpp` as module startup + command registration only.
3. **Critical coupling:** Python tests grep the editor source. `physics/tests/test_photoreal_environment_assets.py` (and possibly other test files) contain assertions of the form `assert implementation_token in editor_source` against this exact file path. Before moving code, run `grep -rn "RaftSimEditorModule" physics/tests physics/src` and update every such test to read from the new file layout (or better: a helper that concatenates the module's sources). Also `physics/tests/test_milestone20.py::test_unreal_production_foundation_matches_locked_project_and_modules` validates `unreal/Content/RaftSim/Production/production_foundation.json` against the project/module structure — regenerate that lock through its generator after the split.
4. Verify: the UE project must still compile (owner runs the editor build; you can at minimum verify with the UBT command the repo's docs/scripts use), and the physics suite must return to the Phase 0 baseline.

Split in several reviewable commits (one subsystem at a time), not one mega-commit.

### Step 2.2 — solver.cpp (after Finding 1 decision)

- If Option A: most of the file is deleted with the calibration machinery; split the remainder (core stepping, boundaries, feature forcing, IO) into `physics/cpp/src/` files by concern.
- If Option B: same split, plus move all embedded reference-profile arrays out of source into data files alongside the existing milestone18 catalog. Constraint: deterministic replay hashes recorded in the milestone manifests must not change for retained modes — verify via `physics/tests/test_cpp_water_solver.py` and the comparison harness.

### Step 2.3 — milestone*.py (low priority, policy only)

Do not mass-refactor. Adopt and document (in `docs/raftsim-tools-workflow.md` or CLAUDE-level guidance) a rule that new code goes in function-named modules, and milestone modules are frozen legacy. Optionally extract genuinely shared helpers when a future change touches them.

### Acceptance criteria

- No single source file in the touched areas exceeds ~3,000 lines (except frozen legacy explicitly exempted).
- All command names, behavior, and generated artifacts are byte-identical where the plan says "mechanical" (spot-check by regenerating one river's candidate maps and diffing manifests/hashes).
- Physics suite matches Phase 0 baseline; UE project compiles.

---

## Finding 3 — Repo weight and iteration exhaust

### Problem

- `.git/lfs` is **291 GB** (working tree 311 GB; `.git/objects` only 3.7 GB). Cause: multi-hundred-MB-to-GB generated corridor `.umap`s (largest: `L_ZambeziBatokaGorge_PhysicalCorridorCandidate.umap` 1.6 GB, Chilko 1.1 GB, Futaleufú 688 MB, Colorado 330 MB, South Fork 250 MB) regenerated dozens of times at ~38 commits/day — every regeneration is a new immortal LFS blob.
- Iteration exhaust kept as live code: 6 superseded versioned generators (`physics/src/raftsim/futaleufu_cordillera_cypress_v{9,10,18,19,20,21}_assets.py`), ~30 one-off `physics/src/raftsim/examples/compare_futaleufu_cordillera_cypress_v*.py` (v17–v42), `physics/reports/` at 113 MB / 3,743 tracked files (`milestone18/` alone 2,108 files).
- Test weight: `physics/tests/test_photoreal_environment_assets.py` is **15,687 lines / 93 tests / ~5,600 asserts** — about half of all test code — mostly asserting regenerated JSON equals committed JSON for every historical version including all rejected ones.

### Step 3.1 — LFS retention (requires owner approval; destructive)

**Owner decision, July 16, 2026:** keep versioning generated maps and do not prune Git LFS. This closes the decision step with no destructive action. The audit remains documentation only; no dry run, retention-setting change, untracking, ignore-rule change, hosted deletion, or history rewrite is authorized.

1. Check `git remote -v`. Determine whether the LFS store is purely local or hosted.
2. Propose to the owner: (a) run `git lfs prune` locally with a retention window (`lfs.fetchrecentrefsdays` / `lfs.pruneoffsetdays` tuned so recent history survives) to reclaim local disk; (b) if hosted, a matching server-side retention decision.
3. Bigger structural fix, also owner-gated: stop versioning volatile generated `.umap` candidates entirely. They are deterministically regenerable from tracked inputs via the `RaftSim.*` editor commands. Keep in git only: locked/promoted maps and the manifests/hashes needed to regenerate everything else; gitignore the volatile candidates the way `Environment/GeneratedLocalReview/PVEFutaleufu*` already is (`.gitignore:33-34`). Document the regeneration command per map in the plan docs so nothing becomes unreproducible.
4. **Never run history rewrites or prunes without explicit owner sign-off in this session.** Disk-space reclamation is not worth an evidence-trail hole.

### Step 3.2 — Retire superseded generators and one-off compare scripts

Adopt this policy (write it into `docs/photoreal-river-environment-production-plan.md`): when version N+1's review is locked, version N's generator module, its `examples/compare_*.py` driver, and its snapshot tests are deleted in the same commit — git history is the archive; the review JSONs and contact sheets under `docs/environment-captures/` remain (they are the evidence, and they're small relative to LFS maps). Then apply it retroactively:

1. `grep -rn "futaleufu_cordillera_cypress_v" physics/tests physics/src/raftsim/__init__.py` to map which versions' generators are still imported/tested.
2. Delete superseded versioned generator modules, their compare scripts, their `__init__.py` re-exports, and their tests together, oldest first, one version per commit. Keep the latest locked version plus any version the current in-flight iteration builds on.
3. After each removal, run the physics suite; only the deleted version's tests may disappear from the count.

### Step 3.3 — Split and slim the snapshot test monolith

Split `test_photoreal_environment_assets.py` into per-concern files (e.g. `test_photoreal_assets_current.py` for the active version + shared invariants, and per-river/per-species files as needed). With Step 3.2's policy, most historical per-version tests get deleted rather than moved. Target: no test file over ~2,000 lines; total suite time should drop noticeably from the ~4 min baseline.

### Acceptance criteria

- A written retention policy exists in the docs for both LFS maps and versioned generators.
- Superseded generators/compare scripts/tests removed; suite green (minus intentionally deleted tests); no remaining import of deleted modules (`uv run python -c "import raftsim"` still works).
- The owner decision to keep versioning maps and not prune is logged; no LFS pruning or tracking change was performed.

---

## Finding 4 — The tree-authoring loop needs a strategy review, not a v43

### Problem

The Cordilleran-cypress/coigue canopy effort is at **42 iterations with zero promotions**. Reviews live at `docs/environment-captures/photoreal_river_previews/landscape_candidates/futaleufu_cordillera_cypress_v*_review.json` (v1 → v42) and the narrative in `docs/zambezi-futaleufu-photoreal-goal.md`. The v42 "merged geometry upper bound" test shows the ceiling: even a 1.35M-vertex merged mesh reaches frontlit silhouette IoU 0.904 but fails backlit at 0.731. The project's own ecology contract (≥5 adult + 3 intermediate forms, mixed species, wind, LODs, measured desktop/VR performance) multiplies remaining cost by every species across two rivers. The quality gates are working; the *approach* (hand-rolled procedural vegetation authored in-repo) is what needs evaluation.

### Step 4.1 — Mine the loop's own data

From the 42 review JSONs plus git history, produce a small table: per version — date, what changed, which gate failed, key metric values (green-fraction early, silhouette-IoU/luminance later). Compute iterations-per-gate-class and the metric trend (is backlit IoU converging or plateaued?). This is a few hours of scripting against existing JSON; put the script in `physics/src/raftsim/examples/` per repo convention and the table in the memo below.

### Step 4.2 — Write the options memo

Create `docs/futaleufu-canopy-strategy-review.md` comparing, against the ecology contract and the review gates that already exist:

- **Continue in-repo procedural authoring** (status quo) — projected cost using the Step 4.1 trend.
- **Dedicated vegetation middleware** (SpeedTree for UE 5.8) — licensing cost/rights implications vs. the project's CC0/rights-review policy (`docs/free-and-ai-asset-policy.md`), expected quality on the failing gates (backlit crown transmission is exactly what such tools specialize in).
- **Licensed scanned/asset libraries** (e.g. Quixel/Fab ecosystem) — note the docs already record that Fab searches found no exact Nothofagus species; assess "ecology-reviewed analog" acceptability, which the goal doc currently treats as disqualifying (this is an owner-level criterion to confirm or relax).
- **Hybrid** — middleware/library for crown mass and distant strata, project-owned assets only for hero/near-bank specimens.

For each: rights compatibility, projected iterations to promotion, engine-integration risk (Nanite/Metal issues already documented in the goal doc), and what happens to the existing gate pipeline (it should be kept — it's the project's strength — only the asset *source* changes).

### Step 4.3 — Propose stop-loss rules

Recommend concrete loop guards for the owner to adopt, e.g.: a per-asset iteration budget (N more iterations), a required metric-improvement floor per iteration (e.g. backlit IoU +0.02 or the approach is declared plateaued), and a standing rule that every 10th iteration triggers a strategy checkpoint instead of another variant.

**Deliverable is the memo + data table only. No asset work, no new tree versions, no changes to the gate pipeline.** The owner decides.

### Acceptance criteria

- Memo committed with the mined per-version table, options compared against the project's own gates and rights policy, and explicit stop-loss recommendations.
- No changes to any capture, review JSON, or generator as part of this finding.

---

## Suggested execution order and sizing

| Order | Work | Size | Owner gate? |
|---|---|---|---|
| 0 | Phase 0 baseline + uv.lock + mp4 leak | hours | mp4 removal: yes |
| 1 | 1.1 truth measurement + 1.2 honest gate + 1.3 memo | days | 1.3 decision: yes |
| 2 | 4.1–4.3 canopy strategy memo | ~1 day | decision: yes |
| 3 | 3.1 LFS retention proposal | hours + owner call | yes (destructive) |
| 4 | 2.1 editor god-file split | days | no |
| 5 | 3.2–3.3 exhaust + test-monolith cleanup | 1–2 days | policy sign-off |
| 6 | 2.2 solver split | depends on Option A/B | follows 1.3 |

Items 1 and 2 are pure information-producing work and can run in parallel; they exist to put decisions in front of the owner early, because items 5 and 6 change shape depending on those decisions.

## Standing rules for whoever executes this

1. Run `cd physics && uv run pytest -q` before and after every phase; explain every diff from the Phase 0 baseline.
2. Never hand-edit a hash-locked manifest or review JSON — regenerate through its generator.
3. Never present calibrated/playback results as solver results anywhere (code, docs, commit messages).
4. Destructive actions (LFS prune, history rewrite, deleting tracked evidence) require explicit owner approval, every time.
5. Match the repo's documentation habit: every behavioral or policy change lands with a dated paragraph in the relevant `docs/*.md` plan.
