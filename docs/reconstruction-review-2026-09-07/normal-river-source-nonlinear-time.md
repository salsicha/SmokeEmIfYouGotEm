# Full nonlinear source-metric time candidate

The [finer source comparison](normal-river-source-pressure-conditioning.md) is
complete. Two 64-grid profiles now distinguish the full curvature model from
the omitted-force control with the original pressure and force/energy gates.
This new work advances that full rate in time on complete, unchanged wet support.
It does not supply wetting transitions, open river boundaries or native gameplay.

## Time method and rejection rules

`subcell_nonlinear_time_stage.py` implements the three-stage, sixth-order
Gauss collocation tableau. Every internal stage reconstructs the current
original-source volumes and physical momenta, then evaluates the full nonlinear
mass/pressure/metric/transport/curvature rate. Geometry, source slopes, source
IDs and the original pressure matrix are retained. There is no frozen-water
time advance or substitution of canonical momentum for physical momentum.

The nonlinear fixed-point solve allows at most 40 sweeps and requires an
absolute collocation residual <=1e-12. Every pressure solve inside each stage
still has its original 40-CG budget. **These are additional outer solves and
are not a claim of meeting any native solver or frame-time budget.**

The Gauss method is not exactly energy preserving for general nonlinear
Hamiltonians. Endpoint full energy is measured, not projected. A step rejects
if its absolute full-energy change, mass error, independent local/global
momentum-impulse error or positive-energy contraction error exceeds 1e-10.
Each impulse is assembled by time quadrature of the actual face/bed/wall
ledger, not inferred from the final momentum difference. Histories also check
cumulative original mass, full energy and local momentum budgets.

Every internal and final state must remain inside its original source topology
interval and satisfy the full rate's support gates. Failure returns no advanced
state for that step; there is no clipping, rescaling, retry, timestep adjustment
or positive-water deletion. The caller's original state remains unchanged.

The nondispersive energy is also recorded separately. Its earlier two-energy
nonincrease check is **not claimed as passed** when the nondispersive component
increases. The full nonlinear Hamiltonian includes additional metric kinetic
energy, so these two quantities can exchange energy. The existing nondispersive
front/energy regressions are not redirected, waived or removed by this method.
Overall time/topology/open/native/gameplay acceptance remains false.

## Completed original South Fork one-step control

The original 600-second atlas channel block [6,6], 16 pools, is unchanged as the
initial state. It retains the same 302 same-region terrain-curvature edges and
uses the default local/source-block pressure solves, not the periodic FFT option.
Boundaries are explicitly reflecting test walls, **not the natural open river**.
Its terrain authority is 2/5: inferred submerged prior/flank, not captured
bathymetry.

One step of 0.00833333333333333 seconds completes in seven collocation sweeps:

- Collocation residual: 3.3217872896784684e-13.
- Full-energy change: 1.4779288903810084e-12, from 962.3603713589893.
- Mass error: zero; local momentum-impulse error: 9.957312752106873e-16.
- Total momentum-impulse error: 1.2212453270876722e-15.
- Maximum pressure residual: 5.055379705864902e-16.
- Maximum endpoint speed: 3.193559833051056 m/s.
- Nondispersive-energy change: +0.6961326019969647. Its old both-energy
  nonincrease control is explicitly **false**; this is not broad acceptance.

Report: `tmp/south-fork-nonlinear-time-channel-v1-20260914.json`, SHA256
`25da4ce9d5cbe306b21912471b60078d812d2d1cf4a1727181515877cd615fc2`.
All 540 recorded hashes matched at completion, before the additional contraction
and history-reporting controls. This is one closed nonlinear step, not a river
trajectory or timestep-convergence measurement.

## Retained actual rock-bank rejection

The same request on original block [12,8] rejects with "Complete original wet
support required; source activation is unresolved" before any time state is
returned. It retains the original water and mixed authority 3/4/5 (exposed rock,
interpolation and inferred flank), not wholly measured submerged geometry.
Report: `tmp/south-fork-nonlinear-time-bank-v1-20260914.json`, SHA256
`8a9c237c64a33cd749f65a59cb72e7a472ab416465bc962a657e44147a81a275`.
All 540 recorded hashes matched. This failure remains an active integration
requirement, not an artificial reflecting boundary substituted at the wet front.

## Completed twelve-step history

The same channel run completed all 12 fixed steps / 0.1 seconds. It used seven
collocation sweeps per step and retained all original full-metric budgets:

- Maximum absolute cumulative full-energy change: 4.786215868080035e-11;
  final change 4.3428372009657323e-11.
- Maximum cumulative local momentum-impulse error: 3.2612801348363973e-15.
- Maximum cumulative mass error: 2.220446049250313e-15.
- Maximum sampled endpoint speed: 3.3947421806427145 m/s; final 3.39153717973394.
- Nondispersive energy increased by 11.012032535655067. Its old both-energy
  nonincrease check remains false throughout; this is not broad acceptance.

Report: `tmp/south-fork-nonlinear-time-channel-12-v1-20260914.json`, SHA256
`30cb45548653b236265d3f42372e28d3c19f1547b784205bf05cf505cd34e49c`.
All 540 recorded hashes matched at completion. Session 46485 / PID 34068 is
terminal, exit 0. The history precedes the geometry-identity optimization below;
only a one-step evolving-state A/B was rerun after that optimization.

## Exact geometry identity and regression checks

Profiling found 15,104 source-face constructions in one original channel rate
audit. Full-extent restrictions now reuse the existing read-only geometry;
exactly equal rational face segments need no repeated interpolation to verify
equality. Proper subintervals and unequal/segmented neighbors still use the
original exact routines. No water, pressure, depth or wet-state result is cached.

The same audit now constructs 1,536 faces. One instrumented comparison reduced
the force-stage time from 7.595 to 4.044 seconds (whole program 9.335 to 5.782).
This is reference Python profiling, **not a native/frame-time acceptance test**.
All non-hash fields of the original force/provenance report are identical.
Optimized report: `tmp/source-nonlinear-force-profile-v2-20260915.json`, SHA256
`b5a0eac83e9f0984766b5376fba791db229574d352a4af39f0d8d05067664637`.

An actual one-step A/B also has binary64-byte-identical final volumes and physical
momenta, identical force/provenance fields and every prior time diagnostic.
Report: `tmp/south-fork-nonlinear-time-channel-identity-v1-20260915.json`, SHA256
`b396155a7a350596a770429f5267e99023b2f3150a518915e24d812f119c91b1`;
540 hashes match. The final rock-bank path still rejects unresolved activation:
`tmp/south-fork-nonlinear-time-bank-identity-v1-20260915.json`, SHA256
`7990e2d8bf7791f0a35fbfed101a9ceb873f17c2ae4fb653084a4d08b582a4f2`.

Fourteen time tests pass, including independent collocation identities, rest,
constant flow, moving/consecutive steps, independent finite impulse assembly,
input preservation, oversized-step rejection, and work/contraction errors
rejected without projection. With source-face controls, 32 tests pass in
`tmp/source-time-face-identity-unit-v1-20260915.xml`. The final broader suite
completed with **368 passes and one retained original geometry failure**, in
`tmp/source-time-face-identity-suite-v1-20260915.xml`. The earlier 365-pass suite
and all retained legacy energy failures are not erased or waived. All 464
protected scene/source/capture/actor hashes remain unchanged.

All numerical jobs for this work are terminal. Next: temporal convergence/longer histories,
derive and couple the unresolved wet/front work, then actual open-flow and
native shared-surface integration. No engine motion or 30 FPS improvement is
claimed. Later rivers, all-scene water, crew, normalization and release remain open.
