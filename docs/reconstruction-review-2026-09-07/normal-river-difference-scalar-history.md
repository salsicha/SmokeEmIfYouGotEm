# Scalar-advection derivative candidate — September 14

The preceding goal turn was verified progress: one clock connection was saved
in the normal South Fork water parent, audited after reload, tested on the GPU,
and inspected in actual gameplay. That capture still fails wave/froth appearance.
This turn does not change that playable parent or enable a research solver.

## Why this candidate, and what it does not establish

`kinematic_forcing` uses `geometry.scalar_gradient` for u·grad(u), u·grad(Du),
and u·grad(Eu). The original method reuses the pressure action G=-D.T.
Its previously measured constant-field defect on a fully wet variable bed is
not appropriate for an ordinary scalar derivative. Pressure compatibility alone
does not prove that this is a consistent ordinary gradient.

New isolated `difference_scalar_gradient_reference.py` retains the original
off-diagonal coefficients but multiplies scalar differences. Algebraically it
is G(f)−f G(1), evaluated directly without cancellation of two complete actions.
Constants are annihilated exactly. The pressure traction, D/E, geometry tangent,
wet/dry support, original FV/RK, rational two-pole40CG solve, CFL and residual
gates remain unchanged. This changes nonlinear forcing; it is NOT a bit-exact
optimization or a claim of equivalent pressure physics.

Six focused tests PASS0.520s: constants/uniform advection, row-sum algebra,
second-order manufactured smooth derivative refinement, byte-identical pressure
action and D/E, directional dry support without changing zero depths, and
exception-safe restoration. These do not establish boundary derivative closure,
energy consistency, finite-amplitude wet/dry evolution or physical acceptance.
No depth floor, velocity cap, dropped source, source reset or relaxed gate.

## Complete original-source rate comparison

`audit_difference_scalar_rate.py`, session27164 TERMINAL exit0. Source SHA
`0114ce4611375f4e169e077d36747754306b867e67fa44bf7858ca5566f6bf10`.
Original complete rate is byte-identical to retained observer trial000000:
`3cb142f3dc4ede1c6cb9ff92bfb31d86117de9a8429f4293f22495f83c07ee80`.
Candidate complete rate SHA:
`421cd623e01b6b41ad8a72f6c6d6d3a2166cbd11629eb9523029b1d72e5272b0`.
Mass rate and CFL0.010949196145979424s are exactly unchanged. Candidate pressure
residuals4.99648944e-8/2.89774897e-16, both40iterations;8entering dry cells use
the original directional limit. Maximum momentum-rate change3.452888294 at
cell[69,118], h0.262239993m. This is not uniformly reduced forcing or proof that
the later high-speed behavior is fixed. Timings29.459/28.985s are individual
shared-load CPU observations, NOT a performance gain or native budget result.

Report `tmp/south-fork-difference-scalar-rate-v1-20260914.json`, SHA
`76b21f19eef439b554d1a82aa7d65675ae0e2d975857522a4e78862c7f8e0348`.
Retained complete original/candidate arrays same-stem.npz SHA
`6da75e78ad976b21ed9b4abb2c379e5830bad9762b4027f97667860329c57e66`.

## Separate full requested history running

`replay_difference_scalar_history.py`, session41566 LIVE. Output
`tmp/south-fork-difference-scalar-history-v1-20260914`. Original source/start
0.0666666701436s, original requested endpoint9.06666713953s and BOTH ownership
moves, including the same-instant final move. No old failure-time truncation.
The existing observer only logs/snapshots; it does not shorten steps. Initial
snapshot complete rate independently matches the candidate audit hash above.
First accepted step0.0750000034769s, speed6.93071118m/s, no rejections, mass
residual−2.52242671e-13m3. Full completion, physical/native/cost/contact/playable
qualification remain UNPROVEN. Do not replace the original run with this result.
Direct poll41566 remains LIVE; latest third accepted step0.091666670144s,
speed6.844832866m/s, no rejections. All422 guarded candidate scripts rehashed
unchanged. Original cook now8258s, still no complete8300 checkpoint yet.

Original59896/95666/97152/83142 were directly polled LIVE this turn and are
untouched. All417 original observer script hashes rechecked unchanged. Candidate
also guards its own pre-existing script list: do not edit those dependencies
while it is running. Added files are separate research controls, not runtime.
Cook latest8244s; BOTH complete8200 audits remain the latest qualified checkpoint
checks, still UNSETTLED. Next COMPLETE8300/local6000 requires BOTH audits.

## Reference and capture limitations

Video retry used the computer-use skill's initialization path, then the browser
fallback. Both returned `failed to write kernel assets: ... path specified.
(os error 3)`. Both original YouTube web fetches returned cache misses. No new
footage was viewed or downloaded. The skill did not cause a project mutation.

Rechecked the last normal-game capture CSV: it is ZERO BYTES. Gameplay exited at
151frames before the requested300frame CSV finalized. That file contains no
usable timing evidence, not a short valid benchmark. Retained PNGs and movie
remain valid visual artifacts. The last valid18.899245FPS/p9570.33ms result still
fails the30FPS target. Broad froth and sheet-like crest are open; the previously
rejected rectangular sharpened-grid material must not be silently reinstated.

Next: inspect candidate full-history behavior versus the intact original and
advance physical pressure/wet-boundary qualification, then native integration
on the shared playable surface. Whole-river terrain/flow integration, accurate
rapid shape, breaking/froth/contact/30FPS, crew and later rivers, normalization,
release checks and final commit remain open.
