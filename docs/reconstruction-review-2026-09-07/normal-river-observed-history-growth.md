# Observe original-history growth without changing the water evolution

September14,2026. Previous turn was progress: both native fusion candidates were
shown slower, correctness/range controls completed and both8100s cook audits
passed. The next priority is the original reconstructed-history velocity growth,
not claiming faster GPU dispatches or a completed playable scene.

## Original jobs remain live and unchanged

Directly polled handles59896,95666,83142 this turn: all return live session IDs.
Main59896 last accepted0.534898806672s, speed123.950038m/s,48 accepted and48
rejected trials in interval5. The full9.066667139530182s/two-move request remains
unproved. Diagnostic95666 is separate and cannot replace or splice the requested
history. River continuation83142 remains live, observed8140s; latest BOTH8100s
audits passed but settling remains unaccepted. Next COMPLETE8200/local4000 BOTH.

Main accepted maxima by completed interval:7.284m/s at0.133333s,8.244 at0.2s,
12.031 at0.266667s,20.979 at0.333333s,30.280 at0.466667s. Interval5 subsequently
exceeds120m/s. Increasing accepted speed and shrinking CFL steps are concerning;
good mass balance and pressure residuals alone do not prove physical stability.

## A separately labeled observation-only full replay

Added `physics/scripts/observe_reconstructed_history.py`. It calls the EXISTING
requested_replay from the FIRST original source, through every original bracket
and both owner moves to the same requested endpoint. No shorter endpoint, restart,
state replacement, modified trial budget, new boundary, CFL change or velocity cap.
It never attaches to or alters the original live processes.

Its scoped wrappers return the exact original rate/pressure results and call the
original accepted-step callback. They log four fastest cells, depth, momentum,
pressure contribution, partial-time velocity derivative and CFL bound. Trial
state/rate/pressure snapshots are saved at speed doublings, separately labeled
from accepted-state snapshots saved on crossing0.1s observation bins. Snapshots
never shorten steps or feed back into evolution. Full inputs, captured original
log prefix and script hashes are recorded; later source changes invalidate the
final comparison. Preserve ALL files named in its `implementation_hashes` while
this run is live (the current guard includes all pre-existing script files).

Optional exact endpoint/shared coefficient construction is enabled in this
separate run, using the previously full-rate-bit-verified implementations. No
polynomial preconditioner switch: the original block solver remains in use.
Every original accepted-step diagnostic available in its captured log prefix is
compared exactly (excluding wall time). A mismatch raises an error, not a repair.
The prefix contained124 accepted steps; passing five does NOT prove all124 or
the full history. Original target/source/request checks remain in requested_replay.

Observer tests: initial run had a Windows temporary archive-handle cleanup error,
fixed in the test by closing the NPZ handle. Three tests now pass0.124s: unchanged
objects/callbacks, retained tiny wet cells, and binding restoration on exceptions.

Session97152 is LIVE, output
`tmp/south-fork-observed-reconstructed-history-v1-20260914`.
First seven accepted steps match original diagnostics through0.125000003477s.
All417 recorded script hashes rechecked unchanged;97152 directly re-polled LIVE.
The first captured COMPLETE rate has SHA256
`3cb142f3dc4ede1c6cb9ff92bfb31d86117de9a8429f4293f22495f83c07ee80`,
identical to the independently audited original full-rate output. Original
source SHA remains0114ce46…; first archive `trial-000000.npz` SHA
`a175f7f8c1f2ee7c3cf3ecaa9d89b8572bc7ff46266511ca9c0cffddf99d6a4a`.

## Findings that narrow the investigation, not a claimed cause

Original boundary inputs at observation indices0,1,5,6 have maximum exterior
speed5.4048–5.4069m/s and maximum normal speed4.2464–4.2467m/s. The live-growth
bracket5 spans0.466666691005–0.600000031292s; its maximum prescribed face
acceleration is0.005599558061m/s2. There is no120m/s supplied velocity spike in
that bracket. This does not exclude a boundary-closure/coupling instability.

The original first-stage pressure acceleration reaches1.781084667e8m/s2 in cell
[76,72], depth1.147990774e-12m. However, its mass rate is0.00867845m/s and the
pressure-force/entering-mass-rate vector is only[-0.0167994,0.0165187]m/s.
Dividing force by nearly zero existing depth is NOT proof of large accepted
velocity when the cell is filling. Do not add a depth floor based on this number.
The first accepted states' fastest cells are ordinary wet flow cells, not yet
the later high-speed region. Its location is still being captured.

Added separate `audit_reconstructed_scalar_consistency.py`. The research
kinematic forcing uses `geometry.scalar_gradient`, which is the pressure action
with zero bottom pressure. A physical derivative annihilates a constant scalar;
an integrated-pressure action on cut columns is not automatically that derivative.
Fully wet periodic flat controls annihilate constants exactly. A smooth sinusoidal
bed of amplitude0.2 yields constant-scalar/uniform-velocity advective defects
0.002859661543,0.000295957200,0.000035344609 for16,32,64 columns respectively.
The defect refines strongly but is not identically zero. Captured constant-field
extension through dry cells has maximum2.666666667; this extension is an operator
diagnostic, NOT a physical velocity assigned to dry cells.

Two diagnostic tests pass0.428s. Audit70931 TERMINAL exit0; report
`tmp/south-fork-reconstructed-scalar-consistency-v1-20260914.json` verifies original
state/bed bytes and explicitly records `replay_growth_cause_established=false`.
These checks expose a distinction missing from pure adjoint/material-identity
tests; they do not prove the source of growth or qualify a replacement operator.

## Next action and full scope

Inspect observer97152's first speed-doubling trial and corresponding accepted
cell trajectories as they arrive. Compare mass/momentum transport and pressure
contributions at those SAME cells; do not infer cause from a global derivative
maximum. Verify all matching original accepted diagnostics and source hashes.
Independently investigate scalar derivative consistency before changing the
pressure/kinematic model; retain original true-residual and physical wave tests.

Native geometry/rates, full evolved ownership, outgoing wave/foam return, terrain,
collision/raft contact, convincing breaking/froth/crew, playable30FPS and all later
rivers/release/final commit remain OPEN. No new gameplay capture or integration
acceptance this turn. Reference footage remains unavailable from the last retry.
# First speed-doubling trial: kinetic bookkeeping, September14

Observer97152 retained rate58/trial-clock0.283333347241s at peak14.076554408m/s.
Archive `tmp/south-fork-observed-reconstructed-history-v1-20260914/trial-000004.npz`,
SHA `d3db17031d237e5e4249aa917148a817d50ca1e81e64b5cb2dd0f54d30f7cfda`.
Independent read-only `audit_observed_kinetic_bookkeeping.py` verifies archive
hash and observed cells, then uses K=|m|2/(2h), K_t=u·m_t−|u|2 h_t/2.
Three analytic/read-only/dry-and-tiny-depth tests PASS0.216s. Report
`tmp/south-fork-observed-first-doubling-kinetic-v1-20260914.json`.

Fastest cell[100,21] has h9.7245mm, h_t−0.3721014m/s, K0.9634517,
K_t−21.7699456, pressure work+26.3392865 and remaining rate−48.1092321.
All FOUR fastest cells have NEGATIVE instantaneous kinetic rate despite
positive pressure work and increasing speed. Quantities are per horizontal area,
with constant water density omitted. The remaining rate includes transport,
gravity and other original terms; it must NOT be labelled numerical dissipation.
This is not accepted-state total mechanical energy or a boundary energy balance.
Pressure-majority velocity growth therefore is NOT evidence by itself of kinetic
energy blow-up. No solver correction, wetness floor, cap or changed gate follows.

At last explicit accepted state0.291666681s, peak14.544724m/s; original-step
diagnostics remain exact. All417 original observer script hashes checked unchanged.
Original main59896 independently reached0.548778026s/103.524226m/s, down from its
earlier peak but still unqualified; full9.066667s and both moves remain open.

## Second speed-doubling trial — September 14

Read-only audit of trial127/clock0.374183780140s, archive `trial-000006.npz`,
SHA `b214027016fd42b964c091d40e052b83e9c3e342f711323f6dd31e2a5d7d58d8`,
independently matches the original observer's retained cells and full arrays.
Report `tmp/south-fork-observed-second-doubling-kinetic-v1-20260914.json`.
Fastest[100,20]: depth0.428948mm, speed28.330339m/s, mass rate−0.0204103,
kinetic rate−13.7712373, pressure work+0.000312477. All four fastest cells
have negative local instantaneous kinetic rate, as in the first doubling.
This excludes neither transport/boundary energy issues nor later instability;
it does not support interpreting the speed spike alone as local energy growth.
No simulation state, floor, cap, timestep, residual gate or operator was changed.
