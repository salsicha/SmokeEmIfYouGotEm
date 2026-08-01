# Changelog

All notable changes to this project are recorded here, newest first. Versioning is semver; the current line is pre-1.0 development driven by [docs/release-1.0-plan.md](docs/release-1.0-plan.md).

## [Unreleased]

### Native Linux build support (August 1, 2026)

- The UE editor and game targets now build and run on Linux (verified against a
  5.8.1 source engine): added the missing `<optional>`/`<array>` includes that
  broke the C++ solver under libstdc++, and `unreal/Scripts/build_solver_lib.sh`
  is now portable bash that compiles `libraftsim_water.a` with the engine's
  bundled clang/libc++ toolchain on Linux (a gcc/libstdc++ archive cannot link
  into UE there); RaftSimWater declares the engine zlib dependency the archive's
  `.npy` inflation needs.
- Added `unreal/Scripts/package_linux.sh` (BuildCookRun, `UE_ROOT` overridable).
- Stopped tracking `physics/cpp/build-ue/` (a macOS build cache and Mach-O
  archive were committed; the stale cache blocked configure and the Mach-O lib
  would shadow the per-host rebuild on other platforms).
- Declared `pillow` as a real runtime dependency of the physics package and
  moved pytest (plus matplotlib for the example-plot tests) into the default
  `uv` dev dependency group, so `uv run pytest -q` uses the locked environment
  on a fresh checkout instead of silently falling back to a PATH pytest.
- C3-window determinism tests now prove same-host determinism by double
  generation and compare committed packages at 1e-12 tolerance, since the
  Mac-generated artifacts differ by ~1 ulp under other libm/FMA
  implementations. Meat Grinder is the exception: its discrete channel-trace
  search amplifies ulp differences into a different traced path off the
  generating platform, so its committed-package comparison is a separate test
  marked xfail on non-macOS. Machine-local-evidence checks (GeoClaw CLI
  plumbing, m16 solver-output provenance) skip with a reason where their
  non-versioned prerequisites are absent.

### Game completion M3 — Full South Fork hydraulics (July 19, 2026)

- Cooked all 20 South Fork named rapids at 900, 1,600, and 3,000 cfs through the
  genuine first-party finite-volume solver; all 60 combinations pass finite-state,
  mass/volume, velocity, inflow/outflow, discharge-response, and 105 catalogued
  hydraulic-feature envelopes.
- Added flow-specific preferred lines, scout eddies, hazards, checkpoints, rescue zones,
  and outcome envelopes for every named rapid.
- Added a deterministic full-reach procedural transit seed, explicit inferred/not-for-
  navigation authority, and no-gap streaming coverage across the 49.1 km descent.
- Added state-preserving Unreal moving-water handoffs with global stationing, authored
  full-edge boundary forcing, transmissive crop edges, overlap depth/velocity transfer,
  continuous solver time, handoff telemetry, and non-overlap reset rejection.
- Added C++ replacement-state coverage, five hydraulic artifact tests, and two Unreal M3
  automation gates. The full physics/content suite passes 1,026 tests with 3 expected
  optional-dependency-path skips.

### Game completion M2 — Procedural geography completion (July 19, 2026)

- Added a deterministic full-reach South Fork geography generator that conditions all
  eight official 3DEP/NAIP windows along the adopted 49.1 km axis and fills missing
  bathymetry, banks, rapid controls, boulders, and shoreline detail.
- Added explicit source-authority, procedural-infill, uncertainty, material, and
  hydraulic-feature masks plus a seeded 115-boulder catalog. Generated content is
  permanently marked as inferred and not suitable for navigation.
- Added a 4 m canonical solver/collision/render grid and thirteen overlapping Unreal
  import tiles whose collision and render height hashes are identical.
- Added geography continuity, provenance, determinism, feature-coverage, and exact tile
  overlap automation. The focused suite passes 19/19 and the full physics/content suite
  passes 1,021 tests with 3 expected dependency-path skips.

### Game completion M1 — Flexible raft and rock contacts (July 19, 2026)

- Added runtime-authoritative rock actors and connected nearby world rocks to the D4
  flexible contact/wrap/pin/release solve.
- Exported D1-D4 per-segment visual state and made the procedural raft tubes and floor
  visibly compress, lose freeboard, indent around contacts, and recover after release.
- Regenerated all five runnable river maps with deterministic hydraulic-crux rock gardens
  and added automation for wrap deformation, stable topology, recovery, and serialized
  contact authority.
- Added an explicit wrap-test capture command and made latent gameplay tests select the
  newest PIE world/reset inherited motion when run after other tests.
- Published `docs/game-completion-plan.md` as the active milestone roadmap through 1.0.

### Phase 0 — Governance reset, licensing, repo trim (July 17, 2026)

- Froze the superseded five-river execution plan and its external-review/DoD apparatus; `docs/release-1.0-plan.md` (revision 2) is the single top-level driver.
- Recorded the July 17 owner reversal of the July 16 no-prune retention decision in `docs/generated-artifact-retention-policy.md`; repo trim and history clean authorized.
- Retired the July 16–17 process-artifact machinery: ~230 review-form / recommendation / readiness / briefing / acceptance / work-order generator modules, their tests, generated JSON templates, and per-gate form docs. Product evidence (source pulls, audits, diagnostics, corridor data, review JSONs) is untouched; git history and the pre-rewrite archive retain everything deleted.
- Added `LICENSE` (MIT, code), `LICENSE-CONTENT.md` (CC BY 4.0, first-party content), `NOTICE.md`, `CREDITS.md`, root `README.md`, and this changelog.

### Phase 1 (in progress) — Playable skeleton (July 17, 2026)

- South Fork A1 stationing adopted per plan §6: official Salmon Falls take-out anchor (station 49,077.7 m / 30.495 mi), all 20 named rapids re-stationed on the corrected axis, guide-review items converted to `pending_human_review`.
- First runtime gameplay code: `ARaftSimRaftActor` (multi-point tube buoyancy, drag, paddle impulses, 120 Hz self-integration), Enhanced Input bindings on `ARaftSimGuidePawn` (paddle/turn strokes, look, high-side, guide commands), `URaftSimMainMenuWidget`, `URaftSimSaveSubsystem`, `ARaftSimBootGameMode`.
- Generated runtime content via new headless bootstrap commands: 24 `IA_*` input actions + `IMC_RaftSimDefault` (KBM+gamepad), `L_RaftSimBoot` (fixes the broken GameDefaultMap), `L_RaftSimTestTank` (flat-water raft tank).
- CI (`.github/workflows/physics.yml`): physics suite, C++ solver build/tests, repo guards (`Scripts/check_repo_guards.py`). Packaging scripts for macOS/Windows under `unreal/Scripts/`.
