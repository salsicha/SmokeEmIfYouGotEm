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
- Any LFS pruning was explicitly approved by the owner and logged (what was pruned, with what retention settings) in the plan doc.

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
