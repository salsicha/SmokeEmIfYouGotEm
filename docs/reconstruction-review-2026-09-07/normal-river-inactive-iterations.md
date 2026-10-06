# Inactive pressure recurrence: exact results, less GPU work

September 13, 2026. This follows the actual-source
[temporal evolution replay](normal-river-temporal-evolution.md). It optimizes
the new bounded evolution path; it does not enable that path in normal gameplay
or establish realistic breaking/froth, long-time stability or 30 FPS.

## Change and invariants

Previously every bounded slot ran the pressure solver's 40 recurrence iterations
even when the interval was already complete, fatal or exhausted. The slot's
existing GPU status now also writes two indirect uint3 dispatch records:

- Active: all grid groups and one reduction group respectively.
- Inactive: zero groups. Both other dimensions are one; all six words are
  initialized by the same status pass that produces scratch progress.

The records pass through the existing total-depth trial and full nonlinear
pressure APIs to the distributed acceleration solver. Only the recurrence
dispatches use them. Preparation, initialization, final true-residual evaluation,
trial guards, state/clock selection and boundary inventory validation still run.
The optional arguments require exactly six 4-byte elements with indirect/vertex
usage and the distributed solver. The unchanged 40-iteration budget, full-grid
coupling, tolerances, timestep, CFL and physical equations remain intact.

`bCullInactiveIterations=false` retains the direct-dispatch comparison path in
the same binary. There is no CPU completion readback, guessed completion time,
interior reset or ignored invalid ledger. Bounded advance also validates grid,
cell size and exact state/bed descriptors before computing dispatch counts or
creating passes, including for closed/periodic calls.

An inactive pressure result is not promoted as a solved physical pressure field.
The inactive interval owner preserves its prior accepted records. A corrupted
completed boundary inventory still fails and cannot become a publishable frame.

## Exactness checks

The actual 128x128 South Fork temporal fixture is unchanged (SHA256
`d55b1c2825d81b8bf1b132a9afdaf0f492508624ef8642f540c31ef4bf91bd5e`).
The real observed interval still completes in two accepted GPU steps without
rejection. Split/batched and indirect/direct results match bit-for-bit in all
five records: state, compensated clock, summary, diagnostics and per-face
accepted inventory. Maximum difference from the independent CPU control remains
9.53674316406e-7, under the original gates.

Eight closed/periodic and thirteen open-boundary cases additionally compare the
direct and indirect paths, including initial/later failure, rejected retry,
budget exhaustion, zero interval, nonuniform advected foam, corrupt/overflowed
inventory and illegal boundary-mode changes. Every direct/indirect comparison
is exact. Invalid grids and wrong state/bed descriptors fail before callbacks.

Focused session 71423 CLOSED0, report
`tmp/south-fork-inactive-iterations-focused-v1-20260913/index.json`: three tests
pass in 3.1588311195 s, **one with a warning**, not three clean passes. The warning
in `TotalDepthBoundaryAdvanceGPU` is a D3D12 descriptor-cache fallback to a
context-local view heap under the enlarged one-command stress workload. No
descriptor budget was raised and no warning was suppressed. It is retained in
the report, not represented as release acceptance.

The standalone pressure test now checks both direct and indirect dispatch for
all sixteen cases in both fused and unfused distributed modes: 32 additional
raw solution/true-residual/diagnostic comparisons. These include 512x512,
one-dimensional, thin/dry, invalid-input, mixed-fraction and single-active-pole
cases. Four malformed indirect descriptor cases are also explicitly refused.

Full session 19355 CLOSED0 reproduced the same descriptor warning: 79 clean
passes plus one pass with warning, no failures/unrun, 18.7924442291 s. All 32
additional acceleration comparisons were exact. That report is retained as
`tmp/south-fork-inactive-iterations-native-v1-20260913`.

The boundary diagnostic now uses one unchanged case per normal automation
frame. A latent command owns the accumulated results and enforces distinct
`GFrameCounter` values; it does not force an RHI frame boundary, raise descriptor
budgets, suppress warnings, reduce dimensions/slots or remove assertions. Each
case still runs split indirect, batched indirect and batched direct controls;
the original host validation block still runs after the final case.

Final session **23918 CLOSED0**, report
`tmp/south-fork-inactive-iterations-native-v2-20260913/index.json`: **80 clean
passes**, zero warnings/failures/unrun, **19.4944076538 s**. The report proves all
thirteen cases ran on distinct consecutive editor frames 754 through 766. The
earlier monolithic stress warning is not erased or reclassified; the final
harness respects normal resource recycling while retaining the entire matrix.

## Isolated, paired timing

Initial separate-process controls are retained as
`unreal/Saved/RaftSimValidation/south-fork-inactive-iterations-{culled,direct}-v1-20260913`.
Sessions 51988/35395 both CLOSED0, one clean test each, cook suspend/resume zero.
Their active costs vary considerably, so they are not used to claim a sustained
speedup. Their WaterDetail DLL was
`1a452eed37269bc6f85ddea38f1df3efb4bf3735d04f599f9192994abfa996cf`.

The final paired benchmark declares four alternating warm-up intervals, then
eight pairs, alternating which path goes first. Each run repeats the same actual
source interval: graph 0 has two active steps, graph 1 two terminal slots. Every
warm-up and measured result must exactly match the original five-record result.
All earlier/cold samples remain recorded; this is a component warm-up policy,
not permission to discard cold frames from gameplay acceptance.

Paired session 73222 CLOSED0, report
`unreal/Saved/RaftSimValidation/south-fork-inactive-iterations-paired-v1-20260913`:
one clean native pass, 0.9681004882 s total automation duration. The process
record confirms PID 32144/start `2026-09-13T10:55:07.5804942Z`, suspend 0, resume 0,
no timeout, editor exit 0. No build or CPU replay overlapped the isolated run.

Actual GPU timestamp intervals, in milliseconds:

| Pair | Active direct | Active indirect | Terminal direct | Terminal indirect |
| --- | ---: | ---: | ---: | ---: |
| 0 | 14.594 | 14.621 | 8.844 | 2.698 |
| 1 | 14.577 | 14.601 | 8.870 | 2.681 |
| 2 | 12.599 | 14.593 | 7.472 | 2.688 |
| 3 | 11.965 | 11.969 | 7.467 | 2.257 |
| 4 | 11.947 | 11.963 | 7.461 | 2.269 |
| 5 | 11.946 | 7.582 | 6.913 | 1.327 |
| 6 | 7.575 | 7.581 | 4.397 | 1.317 |
| 7 | 7.574 | 7.588 | 4.396 | 1.322 |
| Mean | 11.597125 | 11.312250 | 6.977500 | 2.069875 |

Terminal cost is lower in **every pair**, with mean reduction about 70.3%.
Active comparable pairs are essentially unchanged; the changing timing level
and transitions in pairs 2/5 prevent claiming the small active mean difference
as a physical-solve speedup. GPU frequency/submission effects are not isolated.
The timestamp bracket includes boundary sampling, both RK stages, pressure,
commit and ledger; upload/readback are outside it, but GPU command starvation
may be inside it. These are not whole-frame or isolated arithmetic timings.
Remaining terminal preparation/validation and command-submission cost is not
removed. Neither 30 FPS nor the separate 1.6 ms FV budget is qualified here.

## Build, source and remaining scope

Builds 86677/42103/63621 succeeded in 49.97/42.93/15.04 s respectively. Paired-
timing WaterDetail DLL SHA256:
`56b2f944eca167efdc52edd61fb97bfd26f3638ebfd0291923e547a9fa1af132`.
Final harness-only build 63106 succeeds in 14.33 s; final WaterDetail DLL:
`0a1916c7844284956a615521c1620cbf63e64e622419a0bad7d0129b804458da`.
Acceleration implementation:
`8095e64f794e24e4eb4d9e9c16210856f86ad6086601169418fc29b5901e02b4`.
Bounded advance implementation:
`c703201a13e53a5c8385214e03b171fbe50adae37d0514b92b2ba3ae785d5497`.
Advance shader:
`2f6ef20c3da3d4b27beca53450b50fa6b7119b452a43040517265e2e5fa9230e`.
The pressure equations and acceleration shader were not changed.

Protected map, transmission material and save hashes remain unchanged. No CPU
solver code changed; the preceding 261-test CPU result is historical, not a new
run. Normal legacy evolution/render/contact ownership remains unchanged, as
does the most recent normal gameplay result, **20.877573 FPS / p95 56.8497 ms**.

The same background cook subsequently completed its 4300-second/local6000
snapshot. BOTH independent state and exterior-bank audits pass: 5,382,400 finite
cells, 86,720 exactly dry artificial-bank face cells, maximum depth 3.882450793 m,
speed 6.581974891 m/s, volume 2,880,186.57657297 m3. Outlet 97.216719762 versus
inlet 45.306954547 m3/s still shows settling, not integration readiness. See the
[checkpoint record](full-river-expanded-checkpoint.md). Continue the same job
toward 6000 seconds; the next complete4400/local8000 needs both audits.

No screenshot or scene/crew acceptance is claimed. A fresh reference-video retry
at approximately 12:30 UTC still fails: both supplied YouTube pages return cache
misses, and both desktop/computer-use initialization and the browser-only entry
point fail with "failed to write kernel assets: The system cannot find the path
specified. (os error 3)". No frames or motion were viewed. The computer-use skill
and mandatory guidance were read; no security settings or plugin configuration
were changed. A nonblocking request for directly attached reference clips was
sent, while code work continues.

Next: persistent common-clock native/source/detail ownership, without discarded
physical time or unknown-boundary extrapolation; qualify continued intervals,
outgoing-wave behavior, nonlinear stability, wet/breaking/froth and actual
single-surface presentation/contact in normal play. Reduce the existing costly
CPU crest/mesh path and qualify the full 30 FPS workload. The full scene sequence
and remaining release/commit goal are still active.
