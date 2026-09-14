# Unscaled reconstruction through persistent ownership — September 14 UTC

Previous goal turn made progress: original-MC CPU and GPU transport controls
passed the local failure interval and physical/transport checks. This turn
carries the same opt-in model through the complete retained-state path, without
promoting it into playable water. The full remaining project scope is unchanged.

## Implemented identity and stage integration

- Both SSP-RK2 transport evaluations now receive the fixed unscaled choice.
  Pressure/breaking and accepted-only foam/state/time/inventory remain unchanged.
- Bounded advance and next-interval admission retain/check an explicit model
  bit2, alongside boundary bit0 and continuous-model bit1. Valid open modes are
  binary1, continuous3 and unscaled5. Both numerical-model bits at once are
  rejected before work; they are not aliases for a valid model.
- The moving-window owner fixes both model flags at construction, rejects the
  invalid combination and preserves identity during move-before-first-step,
  later interval/move transitions and asynchronous completion polling.
- Recorded-owner replay has explicit `-RaftSimUnscaledShorelineTest`; original
  packet observations and original endpoint remain mandatory. Binary control
  still requires final-state byte equality. A different model's new trajectory
  requires independent same-model CPU qualification, not comparison with old
  binary output as an accuracy oracle.
- Stage capture reads/checks mode5 and forwards it to both stages. Independent
  history/step readers accept unscaled only with matching captured/persisted
  identity; missing, stale or combined mode bits fail.

Default flags remain false. No normal playable caller selects unscaled. Frame
presentation/contact still requires model-aware qualification before this path
can be promoted; this work does not reinterpret legacy frame validation.

## Verification so far

Build64309 completes successfully in64.86s.
`tmp/south-fork-unscaled-step-fixtures-v1-20260914.bin` uses distinct fixture v3,
SHA256 `68b98b742da9cf0c4bb93543bf6e5a74580b880ad7bcc44d1b020cc438deff2a`.
It covers both pressure/transport stages, conserved foam, exact dry/lake and
minimum-normal states; v1/v2 default/continuous fixtures are unchanged.

Native82495 completes38 CLEAN tests, zero warnings/failures,13.87145s:
`tmp/south-fork-unscaled-owner-components-native-v1-20260914/index.json/.log`.
This includes all six ordered switches between three models during pending and
completed evolution, all six switches between intervals, rejection latching,
original state/time/counters/inventory retention, bounded advance and moving-
window stress configurations. Initial move passes all three models with one
move, one interval and two accepted steps, exact uniform final state.

Python2237 completes95 tests in35.53s: physical reconstruction, both-stage foam/
state conservation, exact rough lakes, original-input isolation, immutable model
provenance/history, and unchanged30FPS budget checks. Earlier50-test run passes
5.39s; these suites overlap and must not be added as unique test counts.

## Original history qualification FAILS

Native11493 finishes FAILED after50.04464s, using the ORIGINAL captured packets from
`tmp/south-fork-qualified-range-owner-v1-20260914.json`, not a shortened segment
or a reset from an intermediate GPU state. Output target:
`tmp/south-fork-unscaled-owner-history-v1-20260914.json`; report:
`tmp/south-fork-unscaled-owner-history-native-v1-20260914/index.json/.log`.
The log contains a descriptor-cache warning. After19 completed intervals and303
accepted steps in those intervals, interval19 stalls at2.325785777831797s.
Its summary is[2077,1038,2,5], diagnostics[0,4,16,0], remaining0.007547677028924227s.
Second-stage CFL rejection is followed by a retry below the unchanged1e-9s gate.
The retained state is physically invalid: cell y22/x102 has depth0.030830143m,
hu732839.4375, hv2364794 and speed80,302,682.362m/s. This is not merely a velocity
division in a vanishing-depth cell. Do not reset/repair it, relax the gate, or
run the completed-history accuracy CLI as if it reached the original endpoint.

The failure-capture diagnostic now has explicit `-RaftSimRecordedRetainedFailure`.
It retains the original right source endpoint (not a shortened interval ending
at the stalled clock), replays from the original start, and requires exact failed
state bytes, clock, interval trial/accepted counts and all four diagnostic words.
The source failure is labelled separately from diagnostic replay completion.
Build99759 passes in15.34s. Capture73689/v1 correctly fails its unchanged64-record
memory budget at2.299696s; that incomplete artifact is retained and unqualified.
Capture4495/v2 narrows ONLY the readback window to2.2666667849–2.28s and completes
with one descriptor warning. It retains22 two-stage polynomial records and
reproduces the original failed state, clock, counters and flags exactly after
all2438 trials from the original start. No physics steps or observations are
sampled out. Capture/source reports:
`tmp/south-fork-unscaled-prestall-stages-v2-20260914.json/.bin`, with trace SHA256
`4ce817d4ef871d3c74b04edcada53b9f91792d24e59b7c397cbf63f41e8a3375` and binary SHA256
`efc8f6b78961c7a68d7571b1b0ef6f1b8b45d9b997918d1861a5e631b449b27a`.

`tmp/south-fork-unscaled-prestall-rates-v1-20260914.json` separates recorded
transport and pressure acceleration without a depth floor. At interval19/start,
y22/x102 has depth0.0299209673m and speed55.1461757m/s. Transport acceleration is
[-9.4594,-29.6614]m/s2 while nonlinear pressure adds[262.2946,889.5828]m/s2;
dispersion fraction1.0, graph bits3. Thus pressure directly drives the observed
growth there; this does not yet explain its onset or establish a stable remedy.

CPU80153 completes the independent SAME-INPUT operator check on all44 captured
stages: `tmp/south-fork-unscaled-prestall-operators-v1-20260914.json`.
Max absolute hydro discrepancy7.0687069e-5, pressure force discrepancy2.0343382e-5;
graphs match. Those discrepancies cannot explain pressure momentum rates of
order8–27 at the affected cell. This is not independent full-history qualification.
The operator-audit path now forwards captured model identity rather than silently
using default binary transport. Model forwarding/rejection tests cover all three
models. Combined recorded-layout/model/failure-rate checks pass33 in0.68s.
Original-start interval-endpoint capture72561 completes20 retained interval starts
and all2438 trials, again reproducing the failure exactly (one descriptor warning).
`tmp/south-fork-unscaled-prestall-endpoints-v1-20260914.json/.bin`; diagnostic
`tmp/south-fork-unscaled-endpoint-rates-v1-20260914.json`. At1.80000009s, y22/x102
has graph bits1, velocity[1.25945,7.30591]m/s and pressure acceleration
[-0.22133,-0.71565]m/s2. At1.93333343s, graph bits3, velocity[1.68278,8.82029]m/s
and pressure acceleration[5.76865,18.93387]m/s2. This brackets an earlier graph
reopening and force-growth interval; it is a correlation to investigate, not
proof that the physical face should be closed or that pressure may be disabled.
Expanded history/provenance/30FPS Python suite passes70 in1.67s (overlaps earlier
suites). Successful binary-history trace35922 completes all1080 trials and two
window moves at9.066667139530182s with byte-exact original final state (one
descriptor warning). The completed-history diagnostic path remains exact after
the retained-failure extension. Report/artifact prefix:
`tmp/south-fork-retained-failure-default-trace{,-native}-v1-20260914`.
The earlier1.8–1.933333434s two-stage polynomial capture29229 also completes:
16 trials retained, all2438 original trials replayed, exact failure, one descriptor
warning. `tmp/south-fork-unscaled-onset-stages-v1-20260914.json/.bin`, trace SHA256
`2cbfd26a98199bbbccd033d63e4d330f807e3de38aa5bbb6adf66b0aa1416723`, binary SHA256
`21fe59c3cb20eb383662a8e23d323491926b9624393944e863b0f08783bc2a38`.
`tmp/south-fork-unscaled-onset-rates-v1-20260914.json` identifies interval15/trial8:
begin1.8666667640209198s, dt0.008333333767950535s. At y22/x102 the positive-y
pressure edge opens between stages (bits1→3), while y pressure acceleration
changes-0.696983→12.780603m/s2. The following first stage remains open with
13.029727m/s2. Neighbor y23/x102 has positive mean depth6.4447403e-7m before
the transition, not a dry/invalid state. The later pressure growth persists.
NEXT isolate the pressure-graph/kinematic response on these actual stage inputs,
including its wetting-face limit, before deriving a stable conservative model.
Do not close the physical face, disable pressure, invent a depth threshold or
shrink the physics step to hide the failure. A root-cause/fix claim still needs
that analysis and full independent history/physical/cost gates.
All local diagnostics are now terminal; only the unchanged full-river cook is live.

Fresh default regression48416 passes126 CLEAN plus one descriptor-warning test,
zero failures,66.11s. `tmp/south-fork-unscaled-owner-default-native-v1-20260914`
is the report prefix. The binary original-history replay is byte-exact and the
retained capture SHA256 remains
`5667023e7f7c62891d533a6b1e1e643bd5d6d115b9b3ac2d89d5bc2494dd69d1`.
Focused recorded-layout/model/failure-rate Python checks pass29 in0.66s.

No playable visual/FPS acceptance or final commit. Desktop30FPS/p9533.333ms,
physics120Hz, production1.6ms solver and all accuracy/source/geometry gates remain.
The last valid gameplay18.899245FPS/p9570.33ms result still fails. Both YouTube
references were retried this continuation: web retrieval returned cache miss;
browser and computer-use fallback both failed kernel initialization with
`The system cannot find the path specified. (os error 3)`. No footage was newly
inspected or downloaded. This does not erase the earlier September9 sampled
review recorded in `troublemaker-reference-coverage-review.md`.

The unchanged cook74818/PID41820 has completed7000s/local20000. BOTH state and
artificial-bank audits pass:5,382,400 finite cells and86,720 exactly dry bank cells.
Outlet113.129839410 versus inlet45.306954547m3/s: settling is still unaccepted.
Next COMPLETE7100s/local22000 needs BOTH audits. No pause, restart or source
promotion here.
