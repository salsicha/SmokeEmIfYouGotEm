# Changelog

All notable changes to this project are recorded here, newest first. Versioning is semver; the current line is pre-1.0 development driven by [docs/release-1.0-plan.md](docs/release-1.0-plan.md).

## [Unreleased]

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
