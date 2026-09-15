# Frozen gross-donor comparison

September 14, 2026. Research comparison only; native/gameplay water and the
30 FPS target remain unqualified.

The opt-in `coupled-gross-donor` history scheme retains both original Rusanov
donor rates instead of freezing only their net transfer. The same conservative
matrix advances volume and momentum; counterflow is not added again as a
separate velocity exchange. Existing defaults, direct pressure/bed forces,
matched dry-front force timing, and conservation/energy/range gates remain.

An independent two-region backward-Euler control with volumes [1, 2], gross
rates 4.3 and 4, and duration 3 gives first-region volume 0.9547738693467337.
The new scheme reproduces this and its momentum solution; the old net-directed
finite-step formulation gives 0.5263157894736844. Both retain the original
infinitesimal-rate controls. This distinguishes frozen linearizations, not
proof that either qualifies the full nonlinear model.

## Actual South Fork result

The exact-source, 20-step audit still accepts only 17 candidate steps (0.34 s),
ending with 420 regions. Step 18 rejects four zero solved volumes; three have
incoming transfers. No positive volume is deleted or repaired. The maximum
accepted-candidate speed is 5.806959739843251 m/s, with the last fastest region
holding only 8.833624880658447e-21 volume. Passing global budgets does not
qualify this local evolution. Conservative drying and force timing remain open.

Local report: `tmp/south-fork-gross-donor-history-v1-20260914.json`.
SHA-256: `fd704a2d2507ba8bbdc8c65c480e9398af1b0f3e39528cae4486ac9e76717c63`.
All 40 report source hashes match the committed implementation. All 464
protected source/capture/map/profile/actor hashes remain unchanged.

## Commit verification

- Focused geometry/subcell suite: 225 passed, 1 retained original float
  storage/face consistency failure (1.77635684e-15 discrepancy).
- Retained energy suites: 25 passed, 12 existing failures (8 nonlinear and
  4 legacy constant-velocity energy controls). No tests or tolerances waived.
- Test reports remain local under `tmp/subcell-gross-donor-commit-*-20260914.xml`.
- Existing `.gitignore` already excludes temporary reports, Unreal Saved,
  captures, caches, local environments and build outputs; no new rule needed.

No native solver switch, map/menu change, new visual qualification, or FPS
improvement is claimed by this commit.
