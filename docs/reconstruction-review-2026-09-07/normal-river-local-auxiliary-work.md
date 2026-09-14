# Local auxiliary energy transfer, with the stress defect retained

September 14, 2026. Previous goal turn: NO PROGRESS (only confirmed the existing
30 FPS target). This continuation adds and verifies a local energy-work identity
on the unchanged physical profiles. It does not promote a solver or scenario.

## What changed

`physics/scripts/rational_auxiliary_energy_work.py` differentiates the local
stationary realization of the SAME two-pole physical energy from
[the positive-energy derivation](normal-river-positive-primal-energy.md).
For q=p/sqrt(h), z=(I+beta Q)^-1 q, Q=W.T W+3 V.T V/4, each pole contributes

    e = alpha/2 * (|Wz|² + 3|Vz|²/4 + |q-z|²/beta).

Its time derivative uses the supplied physical h_t and p_t, including all
normalization and geometry derivatives. The auxiliary rate solves

    (I+beta Q) z_t = q_t - beta Q_t z

with the unchanged 40-CG budget and full operators. Let
`r = Qz - (q-z)/beta` be the finite-solve stationarity residual. Then

    e_t = alpha * [(q-z).q_t/beta + (Wz)(W_t z) + 3(Vz)(V_t z)/4]
          + auxiliary_exchange + alpha*r.z_t.

The base kinetic and gravity derivatives are included separately. No term is
dropped based on its size; residual work is returned explicitly.

The exchange uses the actual sparse W/V factor entries. Each directed stored
entry deposits `a[row]*A[row,column]*z_t[column]` into the row cell and its
negative into the column cell. Thus it reproduces the local adjoint identity
`a*(A z_t) - z_t*(A.T a)` and sums to zero on the periodic domain. There is no
cumulative integration, fitted total flux, uniform subtraction or projection.
Self entries and one-/two-cell periodic aliases are handled by the authoritative
factor assembly. This is a **local auxiliary graph transfer**, not yet a full
hydrodynamic energy flux. Geometry-coefficient derivative work and the
mass/momentum transport pairing still require their own compatible local split.

The derivation is specific to our reconstructed, depth-dependent Q. The
[SGN split-form paper by Ranocha and Ricchiuto](https://arxiv.org/html/2408.02665v3)
provides relevant background on discrete product rules and summation by parts;
its fixed-derivative split is not assumed to prove this reconstructed two-pole
scheme. No relaxation projection from that paper is used.

## Evidence on unchanged inputs

New unit suite: `tmp/rational-auxiliary-energy-work-controls-v1-20260914.xml`,
10 PASS in 1.37 s. Includes factor-adjoint equality cell by cell, singleton and
two-cell aliases, variable beds, independent central finite differences of each
cell's local energy density, input immutability and invalid-direction rejection.

Original-profile report:
`tmp/south-fork-rational-auxiliary-energy-work-v1-20260914.json`.
All eight original flat profiles, seeds 2200/2202/2204/2206 at 64 and 128 cells,
use their exact physical source momentum and the unchanged stress-stage rates.
Source/bed hashes and 37 implementation hashes are recorded; before/after
implementation and input checks pass. No smoothness-friendly replacement states.

- All eight local identity checks pass; worst error 7.18975188037924e-15.
- All eight final local density finite-difference checks pass; worst error
  5.357076560130736e-9 versus the explicit 1e-7 gate.
- Worst integrated auxiliary exchange magnitude: 2.6020852139652106e-17.
- Worst integrated stationarity residual work: 4.892020451690959e-15.
- Recovered original stress energy rates agree within 1.1102230246251565e-15.
- **All eight actual energy-conservation gates still fail**, with both signs.
  The smallest absolute defect is about 1.33e-4, vastly larger than residual work.

This rules out adding a missing conservative auxiliary exchange, or reducing
the pole residual alone, as a cure for the measured net defect. The new identity
exposes where such transfer belongs locally; it cannot cancel net production.

Selected integrated suite:
`tmp/rational-auxiliary-energy-integrated-controls-v1-20260914.xml`,
41 PASS / 25 FAIL in 42.89 s. This is a different, explicitly selected test set
from the earlier 67-PASS suite, not a whole-project regression result. It retains
all eight stress energy failures, thirteen original momentum/rest/reversal/
reflection failures and four original block-preconditioned accuracy failures.
No xfail or acceptance-threshold changes. Audit process 71029 and test process
71594 are terminal; original histories and cook are separate and remain live.

The complete prior 12-file control set plus the new local-work tests was then
rerun: `tmp/rational-auxiliary-energy-all-controls-v1-20260914.xml`,
**77 PASS / 25 FAIL in 52.15 s**, process 73931 terminal exit 1. The same 25
failures remain, with all 67 prior passing controls and the 10 new controls
passing. This is still a numerical research suite, not release acceptance.
Scoped changed-document `git diff --check` passes. The initial repository-wide
attempt could not finish because Git LFS could not write its `.git/lfs/tmp`
clean-filter scratch file; do not record that attempt as a full-worktree pass.

## Reference retry and live work

Read the computer-use skill and its required guidance/confirmation documents.
Fresh browser initialization for the bank-side video failed with
`failed to write kernel assets: The system cannot find the path specified.
(os error 3)`. Reset the browser session and retried the raft-view video: same
failure. Direct web retrieval of BOTH supplied links also returned cache misses.
No new player, frame or continuous motion was inspected. No remote-video
download or runtime/security modification was attempted.

All five original handles were directly polled live this continuation, with
no restart, suspension, source reset or history splice. The difference-scalar
history reached about 7,665 m/s in actual 2.17 mm water at cell [101,25], further
physical failure, not gameplay evidence. Both original observation provenance
sets were checked: 417 and 422 guarded source files, zero changes.
The cook passed native 9344.5/local26890 on the final direct live check; complete
9400/local28000 was not present on the earlier filesystem check. Latest
BOTH-audited checkpoint remains 9300.
Do not audit a partial snapshot or call unsettled outflow a steady solution.

## Next required implementation and full scope

Derive the hydrodynamic mass/momentum flux pairing that cancels the explicit
local work, including depth-dependent reconstruction derivatives. Test against
the unchanged local identities, original energy/momentum/reversal gates and
positive mass transport, then variable-bed/dry/open/full-history qualification.
Do not use a net-energy projection, a singular face correction, weaker gates,
a different wave model or a depth floor to obtain a pass.

No native or playable integration changed here. South Fork terrain, boulders,
collision, hydraulic geometry, crest/breaking/froth/contact and actual 30 FPS
acceptance remain open. Troublemaker remains an embedded South Fork rapid, never
a scenario-menu entry. Then Colorado, Pacuare, Futaleufu, remaining Chilko/
Zambezi reviews, crew, normalization, regressions, release and final commit remain
in the original order and scope. The full goal is not complete.
