# Transport on the original curved wetting front

September 18, 2026. The preceding commit-only turn was no goal progress: it
confirmed a clean tree. This continuation implements a missing force component,
not a visible water update. The nonlinear runtime remains OFF.

## Physical change

The fixed-wet-support auxiliary transport assumes a horizontal local water level,
so its within-triangle spatial derivative uses `grad(h) = -grad(b)`. That identity
does not hold on the quadratic dry-front profile. In particular, uniform depth
on a sloping bed has `grad(h) = 0`, not a bed-parallel depth gradient. Reusing the
hydrostatic connection would generate a spurious force term there.

`subcell_front_auxiliary_transport.py` constructs the existing original
`FrontPressureGeometry` and supplies four exact auxiliary operators:

- Shared-face factor transport, integrating the actual first, second and third
  depth moments rather than substituting powers of a mean depth.
- The within-source spatial connection using the actual depth gradient.
- Paired difference-velocity transport using the same shared mass coefficient.
- The physical-time factor commutator, including both the actual profile rate
  and the changing shared divergence operator.

For the unchanged vertical factor `F(w) = h D(w) - 1.5 grad(b).w`, the spatial
connection has coefficient

    k = -3/4 grad(b) [u . integral(h grad(h))].
    C(w) = k D(w) - D^T(k.w).

The depth-gradient moment is evaluated as `integral_boundary(h^2 n)/2` on the
original polygon. This retains the original source edge normals without rounded
unit normals. Interior faces use one coefficient with opposite ownership.
Reflecting exterior faces carry no advective exchange, but they MUST remain in
the spatial gradient identity. A wall condition does not set that gradient to
zero. The source audit independently verifies the same moment by exact volume
integration of the original quadratic profile.

All geometry and operators remain in the original rational quadratic field;
positive fragments below floating-point export range survive. Dry owners have
no velocity unknown. Original source elevations, pressure geometry, two-pole
constants, solver budgets and all existing acceptance gates are unchanged.

These operators are necessary transport pieces, NOT a completed conservative
mass/momentum law. They do not resolve unequal incident depth profiles, bed-slope
junctions, open boundaries, changing owner topology or a finite time step.
Their exact skew-work identities are not evidence that those missing pieces
are correct. The reflected pressure test domain is not an open-river simulation.

The factor transport and time commutator also have direct momentum ledgers.
Shared-face contributions debit/credit the two owners exactly; source-slope
terms and reflecting-wall terms are assembled explicitly from their original
coefficients. Neither is defined as the difference from the final operator.
The independent operator actions and ledger reconstructions agree exactly,
and a flat front produces exactly zero bed terms.

## Verification

Final focused controls: 19 PASS, 9.49 s, including independent line/volume quadrature,
direct factor-time work, exact skew adjoints, winding/hanging vertices,
constant-depth/nonflat-bed negative control, explicit dry-owner rejection and
positive subfloat face moments. Direct local ledgers and wholly dry geometry
also pass. Report: `tmp/front-auxiliary-controls-v2-20260918.xml`, SHA256
`9cf329e05c1740bef7cdbb9c2b07bf40c4a4baf23dd6f294e8c43c1ce2652213`.

The source audit uses the qualified flux-extended original predictor, not its
earlier report without boundary rates. It takes physical owner velocities from
the original integrated momenta and volumes. The rotated velocity is explicitly
an adjoint probe, not a replacement source state. Historical audit/preparation
tools are allowed only through their existing full Git revisions and recorded
hashes; loaded physics and captured inputs must match current bytes. Initial
attempts with an earlier report and incomplete historical-tool arguments rejected
without creating an acceptance report.

All 11 supported original cases pass the final operator AND direct force-ledger
checks. The two unsupported records (indices 2 and 7) remain present and untested.
Report: `tmp/south-fork-front-auxiliary-transport-v2-20260918.json`, SHA256
`baec97febb736baae163bc4ae9e009fc54f20225d4646951804e12a6babcf4cc`.
A separate reload independently reconstructs all 22 serialized local ledgers
from their face/bed/wall records and rechecks all 625 current source/implementation
hashes. No source water, protected implementation or acceptance flag changed.

The initial 67-module physical suite passes 846 tests and retains the same 13
failures (859 total, 307.45 s). That run used the initial 14-control component;
the final version adds five direct-ledger/dry tests. The final-code rerun completes
with **851 PASS / 13 unchanged FAIL**, 864 tests in 297.05 s. Both runs have the
same pre-existing JUnit metadata warning. XML comparison confirms exactly the
same failure identities as the preceding 845-test suite, with no new failure.
Final report: `tmp/front-auxiliary-full-suite-v2-20260918.xml`, SHA256
`864292a94c97ec90d63a48bd0b09f561476fd06ba1c426394f2e9a4f6410bfee`.
The 13 retained failures are four donor-mass energy controls, eight nonlinear
paired-stress energy controls and one exact storage/face representation control.
They are not xfailed, removed, relaxed or replaced by the new operator tests.

## Playable performance investigation

The existing normal-scene timing switch was used in a fresh controlled capture:
`south-fork-refresh-investigation-v1-20260918`. The game exited 0 without timeout.
The identified cook was suspended and resumed successfully; its CPU time stayed
28210.25 s during that interval. No graphics, geometry or physics settings changed.
CSV SHA256: `93b73237e8d894e2eb23bef852237885c70f17d603f28c2715f343de8444b92f`.

The initially unaccounted refresh time belongs to existing shore/wake, base
vertex, detection and core-publication work. It did not reveal a new dominant
refresh bottleneck. Earlier rejected base-vertex and incremental-history trials
were not repeated or promoted. Instrumented capture is not FPS qualification.
The latest ordinary p95 remains 41.7264 ms, FAILING the unchanged 30 FPS gate.
No new reference-video, rendered-motion, terrain or froth acceptance is claimed.

## Hydraulic continuation

Both state and artificial-bank audits pass at 7500, 7550, 7600 and 7650 seconds.
Every snapshot has 5,382,400 cells and all 86,720 artificial-bank face cells are
exactly dry. Maximum step mass residual remains 1.4194163622249789e-8 m3.

At 7600 s, maximum depth is 3.814709221403207 m and maximum speed is
5.34799591821559 m/s. Outflow is 105.18397699882731 m3/s against inflow
45.30695454719997 m3/s: still NOT settled. Installed 4950 s water is unchanged.
The 7600 s depth-array SHA256 is
`0b13e3b120f4a492479f2e22eebc0ed11eca74789ea4ca5239914a03cd47477f`.
Reports are `tmp/control-ablation-{7500,7550,7600}s-{state,banks}-v1-20260918.json`.
At 7650 s the same checks pass, with maximum depth 3.814333880862681 m,
speed 5.348518614677382 m/s and outflow 107.54468491711939 m3/s, still NOT settled.
Reports: `tmp/control-ablation-7650s-{state,banks}-v1-20260918.json`;
depth SHA256 `02ea69f5d49562d1a634ff31a9fb39486b743edc6bf56bb2bee095e866fa2216`.

The subsequent queued-river follow-up verified the SAME cook handle live at
7707 s/local10140, then completed both 7700 s/local10000 audits after checking
the completion marker. All 5,382,400 cells pass; all 86,720 artificial-bank
face cells remain exactly dry. Maximum depth is 3.813751164992087 m, speed
5.348983956669725 m/s, and maximum step mass residual remains
1.4194163622249789e-8 m3. Outflow 102.74726920680162 m3/s still exceeds inflow
45.30695454719997 m3/s: NOT settled, no new runtime installation or scene
acceptance. Reports: `tmp/control-ablation-7700s-{state,banks}-v1-20260918.json`;
depth SHA256 `fa0c22c41b0b4a95b10ab06854e0a275d72ead3b1e2e88f0ce82f0f479d1950f`.
Next complete 7750 s/local11000 requires both audits; no process was restarted.

## Remaining delivery

Next couple actual profile transport, conservative mass and physical momentum,
using these direct local force ledgers with interactions/topology changes before
native integration. The new operator still shares ONE depth profile; differing
incident fronts and source slopes need their actual joint interface law.
No runtime switch is enabled by this research component.
South Fork remains the normal playable scenario; Troublemaker remains its rapid,
not a menu entry. Breaking/froth/contact/terrain and 30 FPS acceptance, then
Colorado -> Pacuare -> Futaleufu, Chilko/Zambezi reviews, crew, normalization,
the retained physical regressions and release work all remain OPEN.
