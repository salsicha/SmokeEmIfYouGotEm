# Actual observed interval: CPU/GPU water evolution

September 13, 2026. This is a complete **single observed interval** replay, not
long-running stability, normal-play integration, breaking/froth realism or 30 FPS
acceptance. The previous [temporal source](normal-river-temporal-source.md)
captured actual normal South Fork inputs; this check evolves their interior
instead of only checking source interpolation.

## Input and independent control

`tmp/south-fork-live-temporal-audit-v1-20260913.json.inputs.json`, SHA256
`b3ee6cb3b8b1c209613c85c2c5d15a7fe5dbc321ddf1434df9e7749f8304b9b5`, contains
revisions 2/3, 128x128 cells at 0.5 m, common world origin (-5450,3566), paired
interior/exterior beds and 512 independently observed face-normal velocities.
Native times are 0.01666666753590107 and 0.033333335071802139 seconds. Both beds
must be identical, registration unchanged, and time/revision increasing.

`physics/scripts/audit_live_temporal_evolution.py` reads those actual arrays and
advances the entire 0.01666666753590107-second interval with the independent CPU
double SSP-RK2, second-order FV and rational-SGN pressure reference. Both stages
sample the observed exterior state and face trace, including its observed secant
acceleration. No extrapolation, interior reset to the second observation, bed
change, pressure gate relaxation, depth/velocity cap or mass repair is allowed.
This control explicitly rejects nonzero source foam because `bank.advance`
currently evolves three components; it does not silently discard observed foam.
The actual source observations have zero foam.

The v2 report is `tmp/south-fork-live-temporal-evolution-double-v2-20260913.json`.
It completes in three double-storage steps with zero rejections, maximum depth
3.235103131663428 m, maximum speed 7.063369568797199 m/s, worst relative pressure
residual 1.223564092450875e-7, maximum 40 iterations and 12 pressure solves. The
water inventory changes by -0.067961457677484 m3 with 0.067961457677331 m3 outward
accepted flux; balance error is -1.532801663373107e-13 m3. Maximum state-component
change is 0.4197397619650092. These are solver diagnostics, not river observations.

The reference fixture is `tmp/south-fork-live-temporal-evolution-v1-20260913.bin`,
SHA256 `d55b1c2825d81b8bf1b132a9afdaf0f492508624ef8642f540c31ef4bf91bd5e`.
It includes the actual first state/bed, both exterior states, exterior bed, both
independent face arrays and the final CPU control. The second observed interior
is not an expected answer. Version/magic, dimensions, byte counts, finite header
fields and exact file length are checked by the native reader.

## Actual D3D12 evolution

New `RaftSim.WaterDetail.TemporalEvolutionGPU` consumes the actual fixture with
`-RaftSimTemporalEvolutionFixture=<absolute binary path>`. It composes the real
temporal GPU provider, bounded total-depth advance, both nonlinear pressure
stages and cumulative accepted boundary ledger. The dispersion fraction is one:
this deliberately isolates nonbreaking evolution, not a production breaking
classifier or foam-generation model.

Four scheduled single-slot graphs versus one four-slot graph produce **bit-exact
state, compensated clock, summary, diagnostics and per-face inventory**. The
interval completes in two accepted GPU steps, no rejected steps, status complete,
boundary mode one, diagnostics 0/0/0/1, zero remaining time, final time
0.033333335071802139. The count differs from the CPU's three because float32
1/120 is exactly half this observed duration; double 1/120 leaves a tiny final
remainder. Neither implementation changes the requested interval to hide it.

Per-component CPU-relative L2 errors are 5.48161782132e-8, 5.18400528549e-8,
5.53103007097e-8 and zero foam. Maximum absolute state error is
9.53674316406e-7. Existing component gates (relative 2e-5, maximum absolute
1e-4), nonnegative/finite state and exact-zero foam remain unchanged. GPU water
inventory change is -0.0679636598491 m3, outward accepted inventory
0.0679614655175 m3 and float-storage balance residual -2.19433153513e-6 m3.
That last residual is reported, not repaired or represented as the CPU double
roundoff result. Stage-by-stage float-storage accounting remains future work.

Focused report: `tmp/south-fork-temporal-evolution-focused-v1-20260913/index.json`,
one pass, zero warnings/errors/unrun, 0.1902008951 s, session 15291 CLOSED0.
This automation duration includes CPU submission/readback and is **not** a GPU
component cost or FPS measurement.

## Isolated full-path GPU timing

Build 23201 succeeded in 14.44 s after adding optional actual GPU timestamps to
the test. `-RaftSimTemporalEvolutionTiming` repeats the identical observed
interval eight times, two slots per graph. Graph 0 completes both physical
steps; graph 1 is a terminal continuation. Both graphs retain all five records,
and each repeated result must be bit-exact with the untimed four-slot result.
Timestamps surround boundary sampling, both RK stages, nonlinear pressure,
commit and boundary ledger; upload/readback are outside the bracket. These are
GPU command intervals, not isolated arithmetic throughput or scene FPS; command
submission stalls can be inside a timestamp bracket.

`unreal/Scripts/profile_nonlinear_acceleration.ps1` now accepts this test and its
explicit fixture, with the same owned-process identity checks and finally-resume
contract. Session 99688 CLOSED0: one native pass, no warnings/failures/unrun,
0.4652009904 s total automation duration. Report:
`unreal/Saved/RaftSimValidation/south-fork-temporal-evolution-timing-v1-20260913`.
The matching `-process.json` verifies PID 32144, start
`2026-09-13T10:55:07.5804942Z`, suspend 0, resume 0, no timeout, editor exit 0.
No build or CPU replay was active during this timing run.

All eight timestamp samples are retained, in milliseconds:

| Sample | Two active steps | Two terminal slots |
| --- | ---: | ---: |
| 0 | 32.876 | 17.520 |
| 1 | 32.867 | 17.532 |
| 2 | 17.686 | 2.992 |
| 3 | 5.006 | 2.980 |
| 4 | 5.005 | 2.988 |
| 5 | 4.994 | 2.970 |
| 6 | 5.005 | 2.992 |
| 7 | 5.001 | 2.994 |

The last five active samples are near 5 ms, but the first samples cannot be
discarded to assert a capacity pass. The cause of their larger intervals is not
isolated. Eight samples in an editor component test do not establish sustained
30 FPS, a warm-up policy, full-scene cost or the separate 1.6 ms FV budget. The
terminal slots still schedule solver work, as the existing advance contract
explicitly says; their roughly 3 ms later-sample cost is avoidable overhead to
address, not valid physical simulation time.

## Regression and scope

Build 99541 succeeded in 15.35 s. CPU session 15253 CLOSED0: **261 passed in
39.08 s** across the previous 18 files plus 13 new observation/interval tests.
The tests cover registration, fixed beds, times, independent face values,
out-of-bracket refusal, foam refusal, complete interval ownership, no interior
reset, failure preservation and binary layout/overwrite refusal.

Native session 64738 CLOSED0: **80 passed**, zero warnings/failures/unrun, total
18.6929836273 s, report `tmp/south-fork-temporal-evolution-native-v1-20260913`.
This suite now requires **six** reference flags: the previous nonlinear pressure,
prescribed pressure, transport, step and exterior fixtures, plus the actual
temporal evolution fixture above.

Final optional-timing binary also passes the full suite: session 92246 CLOSED0,
`tmp/south-fork-temporal-evolution-native-v2-20260913/index.json`, **80 passed**,
zero warnings/failures/unrun, 18.7634754181 s. Timings above are not inferred from
either broad regression run.

Final timing-test source SHA256:
`c8a5468f83de3c9c672531df19ebd1cd3dce0d338c56811e05377c009f9fbeee`.
Final WaterDetail DLL:
`b16aae45aa6bc618399c5674e0a6b730e178e15a075e40d20682e9815a9dc936`.
Replay script:
`b68a6de85b5b3a5e1f4bcb9f947db4c2872d01196c654e851aeb6034381f1782`.
Scoped whitespace checks and the modified profiling script's PowerShell parse
pass. No full dirty-worktree release check or commit is claimed.

Normal gameplay and its costly CPU mesh/crest path are unchanged. The latest
ordinary gameplay result remains **20.877573 FPS / p95 56.8497 ms**, not a fresh
measurement or a 30 FPS pass. Its native source/detail clock mismatch remains.
The protected map, transmission material and save hashes match the preceding
record. No video was accessed, no new motion/terrain/crew acceptance is claimed,
and runtime river data remains the earlier 600-second state. The full task and
scene sequence remain active.

Next: reduce inactive-slot work and establish sustained full-path GPU capacity,
then resolve native/source/detail clock
ownership and persistent interval queues without extrapolation, dropped physical
time, lower-quality geometry or weakened numerical limits. Continue outgoing
wave and long-time nonlinear qualification, evolved wet/breaking/froth, actual
shared render/contact publication and normal 30 FPS traversal acceptance.
