# Detail wave transport and continuous capture

September7,2026 local time. South Fork registered-rock review only. Not scene
acceptance, geographic verification, production promotion or a performance pass.

## Change and preserved failures

The persistent GPU detail solver used first-order Rusanov transport for its
linear wave perturbations. New opt-in`-RaftSimSecondOrderDetailReview`, alongside
the existing registered-rock/detail/crest flags, retains the SAME128×128×0.5m
domain, forcing0.06m, damping, mean hydraulics, materials and physical amplitudes.
It reconstructs wave face values with a monotonized-central limiter and uses
two SSP-RK2 transport stages. Pressure forcing uses each stage's time. Exact
momentum damping and foam source/decay splitting occur once per full step.
Do not claim second-order accuracy for all split source physics or nonlinear
overturning fluid behavior: this remains a linear perturbation heightfield.

Method references: [Clawpack solver documentation](https://www.clawpack.org/v5.9.x/pyclaw/solvers.html)
describes higher-resolution spatial reconstruction with Runge–Kutta integration;
[Gkeyll's SSP formulas](https://gkeyll.readthedocs.io/en/latest/dev/ssp-rk.html)
give the two-stage convex combination used here. Gkeyll also cautions about RK2
for purely nondissipative operators; our operator retains limited Rusanov
dissipation. These references motivate the method, not validation of this code.

The first minmod trial reconstructed foam as well as waves. Its test failed:
foam centroid traveled1.99577488m instead of2m±0.002m. A monotonized-central
trial reduced wave error further but foam travel1.99624m still failed.
Reports`engine-detail-second-order` and`engine-detail-second-order-mc` remain.
No gate was relaxed. Foam SPATIAL flux now retains the existing first-order
upwind current transport; only the wave components receive face reconstruction.
This fixes wave attenuation, not foam-feature diffusion. No runtime reseeding,
state clipping, additional surface or greater wave amplitude was introduced.
Changing transport mode on a populated state is rejected until explicit reset.

Build49951:16actions36.70s exit0. GPU test process47926 exit0, final report
`engine-detail-second-order-wave/index.json`:13clean successes,0failures.
New actual-GPU fixture uses an analytic right-going wave at fixed grid/time:

- First-order RMS error0.00724448218m; final0.00106045297m (~85.4%lower).
- Final amplitude0.0178457759m from an initial~0.02m; no manufactured growth.
- Foam mass error−0.0000235453; mean travel2.00000013m at2m/s for1s.
- Full/split render-graph batch error0, including stage clocks.
- Uneven-depth rest error0, dry-state magnitude0, source/decay error0.00000208616.

Original transport/history/crest/resolve tests also pass. The two rejected trial
processes3004/72228 returned0 despite a failed automation report; process success
alone is not test success. No repeated unchanged tests counted as new progress.

Expanded final report `engine-detail-second-order-final/index.json`: 17 successes
(16 clean and one existing `r.MotionVectorSimulation` engine warning), zero
failures. Process57328 exited0 after the final build. Added a nonzero forcing
fixture: full/split dispatch error0, maximum height response0.0508176647m,
with dry cells remaining zero. This checks forcing stage clocks separately from
the unforced analytic-wave fixture; it is not a measurement of in-game crest
height. Registered-rock replay and three legacy rendering/data tests also ran.

## Continuous engine recordings

`RaftSim.CaptureSeries` now accepts`record`: start the existing WMF recorder at
the selected camera pose and finalize on normal teardown. Failure to start is
logged and aborts the capture instead of silently substituting still images.
Recipe:12swarmup,3screenshots10sapart, river_station_side, focusstation8/lateral0.
No raft teleport or paddling command. The raft continues drifting normally.
The final parser also requires all five explicit-pose arguments to be numeric,
so a longer list of named options cannot silently become a zero-valued pose.
That guard was compiled after the paired recordings; those recordings used the
eight-argument named-option recipe, not a separate nine-argument parser fixture.

Sequential process17469 completed both runs with exit0:

- Baseline: `unreal/Saved/VideoCaptures/RaftSim_20260907-184202.mp4`,
  696 actual captured source frames over23.830s;715 decoded encoded frames.
- Candidate: `unreal/Saved/VideoCaptures/RaftSim_20260907-184257.mp4`,
  696 source frames over23.855s;716 decoded frames.

Encoded timestamps are30Hz, NOT game FPS. The encoder can repeat captured
frames. First source recording also overlapped the local decoder-wheel download;
neither recording is a clean performance measurement.

Pinned PyAV16.0.1 was installed into ignored`tmp/water-motion-review-deps` (process
72552 exit0), not global dependencies. `analyze_detail_motion.py` decodes every
frame and saves unmodified frames at1/8/16/23s plus per-frame luma metrics.
Process44645 exit0; outputs under`detail-motion/`. Both streams have strictly
increasing timestamps; maximum presentation interval0.0333333s. Compression can
make repeated source frames differ, so decoded exact-duplicate counts do not
prove render cadence. Full-stream numerical analysis is NOT a claim that the
assistant visually watched every frame in real time.

Candidate8s/23s and baseline8s decoded images inspected. Foam remains broad,
smooth and sheet-like; spray still reads as detached small puffs. At23s the raft
has drifted into view. There is no demonstrated photographic improvement.
Foam-face mean spatial luma gradient is0.967849baseline vs0.968464candidate,
and mean adjacent-frame luma change1.059740 vs1.061996 (8-bit units). These
near-equal image metrics change the next action: further transport accuracy
alone is not the demonstrated route to fixing the visible face. They cannot
measure physical velocity, wave height, turbulence or realism.

## Clean performance and next action

Separate process43707 exit0, no recorder/decoder/build running:
`survey_performance_detail_second_order.json`. Same1280×720,87%,RTX3060Laptop,
Development offscreen,5swarmup/20smeasurement. Mean14.377541ms,p9519.499399ms,
GPUmean6.920129ms,solvermean8.970651ms,one34.775997mswallhitch. Prior crest-normal
baseline14.350345/19.443399ms. No speedup claimed; original16.667msframe and
1.6mssolver budgets still FAIL. Final detail backlog0.005910s, not a hidden
slow-motion presentation. This is not packaged-release qualification.

Keep this numerical option opt-in. Next examine aeration production/transport,
resolved height and spray coupling at the actual crux; do not keep adjusting
transport order or arbitrary amplitude to chase a picture. Geographic identity,
rock silhouettes, shared detail/raft support, robust traversal and CPU cost
remain required. The entire ordered river/crew/normalization/release/commit
queue stays active; no production map, material, native core archive or source
survey data changed in this pass.
