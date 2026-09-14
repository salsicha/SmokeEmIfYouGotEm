# Native CG sustained-load timing and exact CPU construction profile

September 14, 2026, 08:47 UTC. All 960 resident GPU solves preserve every
solution/diagnostic bit of the audited original problem. Sustained captured
slot-major samples are about 3.5 ms PER POLE, not a production water-budget or
30 FPS pass. No native geometry, evolved history or gameplay promotion.

## Clock telemetry explains why isolated timing was insufficient

Added host submission/completion UTC brackets around graph execution and GPU
idle wait. The bracket includes CPU/RHI/readback overhead and is not pure GPU
duration. Added a fresh-output wrapper which starts a hidden read-only NVIDIA
sampler at 100 ms intervals, runs both reconstructed GPU tests, retains a five
second tail, and stops ONLY its own sampler handle. It does not change clocks,
power settings, the cook, or either original CPU replay.

The ordinary paired-layout telemetry run completed: build3858 exit0/15.97s,
wrapper55866 exit0, engine31224 and sampler41948 both gone. Both tests pass;
all60 full solves have exact repeated bits. Final six outputs independently
match the original PASSED factored-operator audit's referenced binary after
verifying its hash. The raw CSV has369 complete rows and one partial trailing
row; complete rows cover all60 host windows. The incomplete row is retained,
not repaired, and occurs after the test.

Captured CSR samples122-127ms coincide with inside-window P8/405MHz memory
samples. Later CSR55-57ms windows include P5/810MHz memory. Slot-major samples
range21.8-47.6ms in that intermittent run. CPU reference/layout/checking work
leaves roughly130-250ms gaps between captured graph submissions. This is
evidence of low-clock/intermittent conditions, not proof that clocks alone
explain every timing fluctuation. A nearest sample outside a window is NOT an
inside-window observation; utilization counters also lag the instantaneous work.

## Resident solve batches

New explicit `-RaftSimReconstructedCGResidentBurst` queues16 independent complete
solves per graph using one immutable uploaded input. Each solve initializes its
own scratch, keeps the original FP64 coefficients/order and all40CG iterations,
and has its own outer GPU timestamps. Every intermediate solution/diagnostic is
copied to an archive buffer and ultimately read back, preventing RDG from
culling earlier solves. Copies lie outside individual-solve timestamps; the
whole-graph timing includes them. No CPU reference or readback separates the16
solves. These independent benchmark initializations are NOT evolving-water
resets. The binary's timing field is the last resident solve, not16 solves.

Combined with ten alternating CSR/slot-major repeats over six original cases,
this executes960 complete solves. The first two solves of each batch are marked
warmup, as are the first two layout repeats (one per layout). All samples remain
in the report. The following summary includes56 post-warmup solves per pole/
layout; p95 is the nearest-rank empirical percentile, not a frame-time p95.

| Original South Fork pole/layout | Min ms | Median ms | p95 ms | Max ms | Mean ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Larger, CSR |6.519|7.586|8.161|8.201|7.682946|
| Larger, slot-major |3.268|3.5745|3.738|3.761|3.564482|
| Smaller, CSR |6.645|7.5015|7.952|7.996|7.521250|
| Smaller, slot-major |3.265|3.565|3.716|3.742|3.541732|

Build27904 exit0/17.50s; wrapper45218 exit0, engine1724 exit0, sampler31904
stopped. Both automation tests pass. All960 archived solutions/diagnostics are
bit-exact; all60 final-per-batch comparisons pass and match their first CSR
result. All six retained GPU AND native CPU outputs and diagnostics independently
match the original independently audited parallel binary bit-for-bit.

Resident telemetry has441 complete rows plus one partial trailing row, with
coverage through every host window. Captured inside-window observations now
show P0/P3, memory6001/7001MHz, SM1365-1987MHz, temperature46-50C. Two of the20
captured host windows contain no telemetry sample. Host brackets include graph
submission overhead; telemetry is not synchronized to individual inner solves.
Graphs still have CPU gaps BETWEEN batches and the original background jobs
remain active. This establishes a much more representative sustained component
sample, NOT continuous playable rendering, a power-state guarantee, or acceptance.

Two poles together still cost about7.1ms before geometry/RHS assembly, return
coupling, evolution, contacts or rendering. The original1.6ms component gate is
not met. Desktop30FPS/33.333ms p95 is the whole-frame target; it does not relax
120Hz physics, fidelity, CFL, residual or component gates. Latest playable
capture remains18.899245FPS/p9570.33ms FAIL.

## CPU construction profile

Separate unmodified original captured-rate cProfile84378 completed exit0.
It records190,701,595 calls in92.535s including profiling overhead; do not compare
those durations directly with uninstrumented wall times. Main captured bank.rate
cost86.469s cumulative, with static geometry24.568s and nonlinear pressure61.759s.
Nested costs include tangent construction35.032s,209176 cut-pressure calls40.135s,
and two acceleration-system constructions19.803s. These overlap and must not be
added as independent totals. Fraction arithmetic and Decimal square roots are
substantial; CG is not the dominant original CPU cost.

NEXT isolated exact-endpoint cut evaluation experiment: simplify ONLY exactR=0
orR=H rational cases, retaining the full one-sided chain-rule tangent and every
input validation. All partial cuts stay on the original function. Compare full
original/candidate FV rate, CFL, operator/RHS, solutions, diagnostics and source
bits before considering any separately qualified replay. Do not edit or hot-
replace the dependencies of either ongoing original replay.

## Artifacts and identities

Paths are repository-relative below. Raw incomplete telemetry tails are retained.

- Ordinary telemetry prefix `tmp/south-fork-reconstructed-cg-telemetry-v1-20260914`:
  native SHA `3e40a75e9b621e6f6add6962ece2aaf72ea5b3ae21e6132579911538de3d8a10`;
  GPU CSV SHA `be257c26c27330b82fa887404f8c9e4323cbf15758dd85c4241f42654a078ef6`.
  `unreal/Saved/RaftSimValidation/south-fork-reconstructed-cg-telemetry-v1-20260914/index.json`
  SHA `cca9ec68b3b20e71ca0909b1054a4be26080ddcc1e9cc3313f5ddfa46dceb854`.
- Resident prefix `tmp/south-fork-reconstructed-cg-resident-telemetry-v1-20260914`:
  native SHA `4fe1a9aaed723185bb367a6e5635b886d6b554afee1d5243b1b22f00b436a160`;
  GPU CSV SHA `e976d44f6c83c3f5afd9ec26bce76615dd4b660ac7eb63cee58bcdb9fe5215f1`.
  `unreal/Saved/RaftSimValidation/south-fork-reconstructed-cg-resident-telemetry-v1-20260914/index.json`
  SHA `1a1f904c0e8caf74a26bec962c03b8396dc6d85049802fa14f5f9907a05f1c92`.
  Both prefixes also have process records; logs use the matching label.
- CPU `tmp/south-fork-reconstructed-cpu-construction-v1-20260914.pstats`
  SHA `8bb47bac4ac1b7851b3e707c4a0cea06e95452cea2358a0082bbaf8720c1e345`;
  `tmp/south-fork-reconstructed-cpu-profile-audit-v1-20260914.json`
  SHA `4d583fa138e37da8e48f0a2ab629d93a810180ed3ad1b0dea31aa7d708f80b97`.
- Current C++ test SHA `49d0cc413d79dc21bf49311ed545c73ad2ef8af280cc8a5c923c93d4f805d8dc`;
  telemetry wrapper SHA `6617fe1380c220045e3ea993c094bebbf46d29b0b7aa4239eff620d86c846133`.
  Shader unchanged from prior repeated-layout audit.

## Original ongoing work

BOTH7900/local38000 snapshot/bank audits pass. Reports
`tmp/south-fork-expanded-7900s-state-v1-20260914.json` and
`tmp/south-fork-expanded-7900s-banks-v1-20260914.json` verify5,382,400 finite
cells,86,720 exactly dry artificial-bank cells,1084 bank faces,2276 directed
shared faces, maxdepth3.809306536m, speed6.214802425m/s, volume2629573.173237m3,
driver volume error1.397e-9m3, maxstep residual1.574e-8m3. Depth SHA
`40b80568b6d5ffc37783a0b671cf747c13e42a700e43d1ea4d11e74b5852347a`.
Outflow104.453759914m3/s still exceeds inflow45.306954547m3/s: UNSETTLED.
Cook74818/PID41820 remains live, observed7927s. Next COMPLETE8000/local40000
requires BOTH audits and terminal/checkpoint review; do not treat it as settled.

MAIN59896 live, last accepted0.480332814253061s, maxspeed32.2308m/s and6 rejected
trials in the current interval. Full9.066667139530182s/two moves still unproved.
Diagnostic95666 remains a separate live old-failure-time prefix. Neither was
modified/restarted. Native geometry/rates/degenerate cases, evolved ownership,
outer wave/froth coupling, terrain/contact/playable integration, other rivers,
crew, release/regressions and final commit remain OPEN. No completed-goal claim.
