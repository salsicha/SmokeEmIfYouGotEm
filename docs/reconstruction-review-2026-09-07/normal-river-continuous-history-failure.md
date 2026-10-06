# Continuous history accuracy and startup correction — September14 UTC

Full original scope remains open. Desktop30FPS/p9533.333ms, physics120Hz and
all source, geometry, pressure, CFL, accuracy and visual-quality gates stay.
Previous goal turn made progress: persistent model identity and source-exact GPU
history replay were implemented/tested. This turn completes the independent
comparison, fixes a reproduced startup bug and strengthens resting-water checks.

## Complete independent history FAILS

CPU25447/PID3948 exits0 with a valid FAILED accuracy result:
`tmp/south-fork-continuous-owner-independent-history-v1-20260914.json` and
`.last-state.npy`. All72 original intervals and both moves complete from the
original initial state; no intermediate GPU resets or timestep substitutions.
GPU source `tmp/south-fork-continuous-owner-history-v2-20260914.json`, SHA256
`03978a0630ec7db6f29f966303bb586203ce8752468cedfef0ad67dd2096ae5e`,
retains all80 original observations exactly.

- Maximum state error0.02084749266270594;132 cells exceed1e-4.
- Component maxima[h,hu,hv]=[0.000223900583899,0.0187704108734,0.0208474926627].
- Relative errors[3.83569701305e-6,7.61598940401e-5,1.13006636602e-4].
- Worst final component y64/x69/hv: GPU-0.04771335422992706,
  independent CPU-0.026865861567221122.
- Window inventory discrepancy9.16293914e-6; GPU float water balance
  -0.000114672333297m3. Independent interval mass-balance errors stay between
  -6.66133815e-13 and9.69002656e-13m3.

The candidate has fewer failing cells than the binary control but a larger
worst discrepancy. Neither is accepted. The earlier locally continuous shoreline
comparison and clean component tests did not establish complete-history accuracy.
Do not promote this solver, quantize/reset the reference or relax1e-4/2e-5 gates.
The new failure is localized below; the replacement model is not yet qualified.

The stage recorder now reads the model from the captured history, checks it
against persisted mode bits, and uses it at both stages. Existing binary traces
remain default binary. It retains the mandatory final-state-byte-equality gate.
Build68705 succeeds in15.67s. Endpoint native66776 exits0, one pass WITH
descriptor-cache warning,28.53s:
`tmp/south-fork-continuous-owner-endpoint-native-v1-20260914/index.json`.
Trace prefix `tmp/south-fork-continuous-owner-endpoints-v1-20260914` captures
all72 interval starts while evolving all1080 trials/two moves. Final state is
byte-exact to the continuous owner history. Binary SHA256
`7ebfddbf0b9af325782caabcb43b4ded000a1c3ff5e32062ef4dbb26596b9a00`.
The CPU endpoint reader now also rejects mismatched trace/history model identity
and hashes the continuous reference helper;29 focused checks pass1.12s.

Independent checkpoint job54556/PID38316 is COMPLETE (exit0), original start exact.
Targets `tmp/south-fork-continuous-endpoint-history-v1-20260914.json` and
`tmp/south-fork-continuous-endpoint-cpu-v1-20260914.npz`. This intentionally
repeats the complete independent evolution to locate error growth and retain
reusable CPU states, not to reset the interior or replace the failed result.
Early completed comparisons through1.5333334133s have no cells over1e-4.
At the binary model's former first burst1.2666667327284813s, continuous history
error is now4.56072174693e-6 (zero failing cells), versus the former binary
0.00931952 burst. Thus the original diagnosed switch is removed in the actual
history, but a later error still fails final acceptance. Do not conflate the
remaining failure with proof that this specific correction had no effect.
First new endpoint failure is interval13,1.5333334133028984→1.666666753590107s:
error grows5.48327611e-6→0.000509075882236254, two failing cells, worsty100/x18/hu.
At1.8s it drops below1e-4 again. This is before either move and is not monotone
accumulation. Both-stage polynomial capture94954 is COMPLETE (exit0), one
descriptor-warning pass,28.63s. Retained-step and isolated-interval CPU diagnostics now
also validate/use the captured model;21 focused checks pass0.95s. These files
were not imported by the checkpoint history while it ran; its implementation was unchanged.

## Localized amplification: non-self-monotone, stiff reconstruction

The subsequent target-only turn revalidated ten existing30FPS checks, but did
not advance the wider goal. This continuation makes new progress: both6800s
cook audits, single-depth derivative evidence and local hydro stability probes.
No runtime model, timestep, source or acceptance threshold was changed.

Completed endpoint archive SHA256:
`d101ec9afcc491cde48d9c37e2a3321a23e98c7740083e74e65ac10bc0a8a934`.
It retains72 independently evolved checkpoints and the same failed final error.
Native trace `tmp/south-fork-continuous-first-divergence-v1-20260914.json/.bin`
records16 trials of interval13, both stages and raw/scaled polynomials, while
replaying all1080 trials/two moves to the exact final owner state. Trace SHA256
`4f5558394c68819e2e6ffd14edc74c414c725443f9e9e483767c6925e24c1fa8`;
binary SHA256 `8b5728546d1e915933bee4b554c7605e3d54257a4fd4165c2198c4b6e71eb9e5`.

Completed independent diagnostic controls (not default-dt history gates):

- `tmp/south-fork-continuous-first-full-control-v1-20260914.json` carries the
  independently evolved interval-start state through16 recorded trial durations.
  Final error0.000508457366195203 reproduces the endpoint burst. Trial10 has
  Euler error2.78161139894e-5 but second-stage hydro error0.035250706315;
  final error0.00011871437908. Trial13 second hydro error0.471043394586.
  Both-stage breaking fractions stay close, all second-stage graphs agree.
- `tmp/south-fork-continuous-first-same-input-v1-20260914.json` starts EACH
  diagnostic trial from its GPU input: maximum final error8.00964473413e-7.
- `tmp/south-fork-continuous-first-interval-isolation-v1-20260914.json` starts
  one diagnostic interval from its GPU input and uses default CPU timesteps:
  final error2.76925272267e-5,17 steps/no rejects. These explicit local resets
  isolate sensitivity; they do NOT repair or qualify independent history.

`tmp/south-fork-continuous-polynomial-response-v1-20260914.json` interpolates
between the actual trial10 second-stage CPU/GPU states for diagnosis only.
Hydro rates vary smoothly but steeply. At neighbor y100/x19, depth changes
0.047752756153→0.047762561589m; raw owning-plus depth is only0.0006074472m.
Its reduced/owning limiter factor changes0.2014181201→0.2445966631 and changes
the neighboring wet transport face substantially. Final reduced-plus depth is
zero on BOTH inputs, not a different breaking graph.

New single-depth probe
`tmp/south-fork-continuous-depth-derivative-v1-20260914.json`
changes ONLY h at y100/x19, leaving all other depths, momenta and bed fixed.
Central differences at1e-6,5e-7,2.5e-7m agree:

- Raw owning depth derivatives are[minus,plus]=[2,0].
- Limiter derivative is2880.9087145 per meter.
- Scaled owning derivatives are[137.02274946,-135.02274946].
- Neighbor y100/x18 hu-rate derivative is approximately-2314.2904.

This is a direct local counterexample to self-monotonicity: adding average
water makes one owning reconstructed face much shallower. Continuity alone
does not prevent amplification.

Hydro-only frozen-patch central-difference matrices are preserved in
`tmp/south-fork-continuous-hydro-jacobian-r1-v1-20260914.json` and
`tmp/south-fork-continuous-hydro-jacobian-r2-v1-20260914.json`.
Native-capture source and CPU-archive hashes bind each report. Radius1 at
relative perturbation1e-5 yields a most negative eigenvalue-1283.7147145/s;
radius2 at5e-6 yields-1283.7180162/s. Frozen-linearized SSP-RK2 amplification
of that decaying mode is47.52 at recorded dt0.008333333768s,9.96 at half dt,
1.90 at quarter dt; all decaying modes are below1 at eighth dt. This is strong
local stiffness evidence, NOT a complete coupled hydro/pressure stability proof:
the surrounding patch is held fixed and real nonlinear RK stages differ.
No smaller timestep was installed or accepted as a performance solution.

Fourteen diagnostic unit tests pass0.45s, including unchanged inputs/operator
restoration, actual raw/scaled capture, depth-only perturbations, derivative
controls and local matrix validation. New native builds are not needed because
this continuation changes only Python diagnostics/documentation.
Combined reconstruction, trace-model/history, resting-lake fixture and desktop
budget suite1180 completes61 tests in27.02s, no failures. All diagnostics are
terminal; only the separately verified river cook remains live.

Next: replace the survival-ratio reconstruction with a mathematically bounded
response, checking self-monotonicity and its CFL implications before a native
port/full-history replay. Do not just add a denominator epsilon or flatten more
cells. Fixed geometry, exact rough/dry lakes, arbitrarily thin continuous films,
conservation, second-order waves and current accuracy gates remain required.
The published convex-depth approach provides conditions for self-monotonicity,
including bed variation independent of water and a bounded blend derivative;
it is NOT the project's current survival-ratio rule. Its sufficient blend bound
also excludes simply inserting the current uniform-grid MC endpoint coefficient1.
See [Skevington, theorem4.1](https://arxiv.org/html/2106.11273v1).
Any candidate must satisfy the project's stronger exact-lake checks separately.

## Reproduced and fixed move-before-first-step failure

New `NonlinearEvolutionOwnerGPU.InitialMove` reproduces failure in BOTH models:
native16819 exits1, report
`tmp/south-fork-initial-move-repro-native-v1-20260914/index.json`.
The initial move correctly transfers state but then refuses the first interval:
status2/bit64, one move, zero intervals/accepted trials. The initializer had set
accepted-step diagnostic1 while its accepted counter was0. Initializing that
diagnostic to0 accurately records that moving a packet accepts no physical step.
No admission check, clock, state, counter or source is weakened/reset.

After correction, native34420 exits0, two clean tests in1.37s:
`tmp/south-fork-initial-move-rough-lake-native-v1-20260914/index.json`.
Both initial-move models now complete one move, one interval and two accepted
steps, retaining the exact expected uniform water state.

## Stronger exact resting-water qualification

Added eight exactly FP32-represented rough-bed lakes: closed/periodic,
fully wet/emergent islands, datum0/1024m. All cases have exactly constant wet
free surface and zero momentum. Both independent CPU models give exactly zero
transport/pressure force; seven fixture tests pass0.88s.
Fixture `tmp/south-fork-continuous-rough-lake-fixtures-v1-20260914.bin`, SHA256
`a89d0ee193b8779f44e8df75a1cb7813f7b8ddda01d3a1974b2145d88a31132f`,
includes the original eight synthetic cases, eight rough lakes and both actual
first-failure stage crops (18 cases total). GPU34420 returns EXACT zero rates
and pressure forces for all eight rough lakes. The transport test now requires
exact native zero for every zero-rate reference case, not just indices0/1.
This strengthens the check; it does not explain or erase the history failure.

Full native startup regression74994 exits0:126 clean, one passing WITH
descriptor-cache warning, zero failures,64.50s. Report
`tmp/south-fork-startup-default-native-v1-20260914/index.json`.
Binary full-history control remains final-state-byte-exact to original; retained
isolated capture SHA256 remains
`5667023e7f7c62891d533a6b1e1e643bd5d6d115b9b3ac2d89d5bc2494dd69d1`.
Broader Python75828 passes82 tests32.90s. No playable visual or performance pass.

Cook74818/PID41820 remains live, freshly observed past6840.5s. Both6800s/local16000 audits pass,
still unsettled; next COMPLETE6900s/local18000 needs both audits. No source
promotion/restart. Reference video access remains unavailable from the prior
turn's supported web/browser attempts; no new footage inspected in this turn.
