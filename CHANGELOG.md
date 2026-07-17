# Changelog

All notable changes to this project are recorded here, newest first. Versioning is semver; the current line is pre-1.0 development driven by [docs/release-1.0-plan.md](docs/release-1.0-plan.md).

## [Unreleased]

### Phase 0 — Governance reset, licensing, repo trim (July 17, 2026)

- Froze the superseded five-river execution plan and its external-review/DoD apparatus; `docs/release-1.0-plan.md` (revision 2) is the single top-level driver.
- Recorded the July 17 owner reversal of the July 16 no-prune retention decision in `docs/generated-artifact-retention-policy.md`; repo trim and history clean authorized.
- Retired the July 16–17 process-artifact machinery: ~230 review-form / recommendation / readiness / briefing / acceptance / work-order generator modules, their tests, generated JSON templates, and per-gate form docs. Product evidence (source pulls, audits, diagnostics, corridor data, review JSONs) is untouched; git history and the pre-rewrite archive retain everything deleted.
- Added `LICENSE` (MIT, code), `LICENSE-CONTENT.md` (CC BY 4.0, first-party content), `NOTICE.md`, `CREDITS.md`, root `README.md`, and this changelog.
