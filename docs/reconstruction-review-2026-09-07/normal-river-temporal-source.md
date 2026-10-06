# Actual face observations and temporal GPU boundary source — September 13

Progress toward the normal solver owner, not scene acceptance. The old relative
eta/q evolution still drives ordinary South Fork play. Desktop remains30FPS with
p9533.333ms, hitch66.667ms, unchanged quality, timestep/CFL, tolerances and budgets.
Troublemaker remains a rapid within South Fork, not a separate menu scenario.

## Source and temporal integration

Normal moving-window source acquisition now independently samples512 exterior
face-normal velocities at actual face positions, a quarter metre from adjacent
half-metre cell centres. These are additional live native field queries, not
velocities inferred from ghost-centre momentum. World-basis mapping is the same
metric east/north convention as the existing source. All four face mappings are
tested. The previous67x67 coarse samples and all interior interpolation stay intact.

`GetLiveFieldTimeSeconds` exposes the actual native solver's double clock. Source
`SampleSeconds` now uses that clock; it previously carried component elapsed time.
Sampling verifies that the native clock did not change while acquiring the paired
packet. Legacy detail elapsed time is NOT silently reinterpreted as native time.

The render-thread source owner uploads a sixth buffer for face velocities and
retains the preceding ghost state/bed/face observations only when origin, static
bed and increasing native time form a valid bracket. Moved windows, equal or
regressed clocks, and changed bed do not become fake temporal pairs. The future
evolution owner must obtain valid observations and handle these transitions.
No evolving interior state is overwritten by refreshed source data.

`RaftSimSampleTemporalBoundaryGPU` samples the explicit compensated Progress.xy
plus the actual TrialInfo.y at RK stage2. It linearly interpolates the conserved
ghost state and independent face velocity. Face acceleration is the secant of
those observations: this is a declared piecewise-linear approximation, not a
measured instantaneous derivative or transparent/radiation boundary condition.
Endpoints copy exactly, immutable bed is checked exactly, and invalid dimensions,
times, data or extrapolation are rejected. No clamping, artificial wet threshold,
state repair, CPU readback or extra time advance is introduced in the provider.
The bounded step's existing error handling receives invalid boundary data on a
failed sample and rejects that transaction.

Normal CPU acquisition adds512 queries per source refresh. GPU source ownership
adds2048 bytes for the current face observations plus12288 bytes for preceding
ghost/bed/face buffers when a bracket exists. A preceding immutable CPU source
packet is also retained. No cost or memory acceptance is inferred from these sizes.

## Verification

Initial build34144 succeeds176.42s; two pre-existing D6 damping float-conversion
warnings are retained. Build49883 succeeds16.56s with the new tests. The opt-in
audit build83942 failed on an unbraced logging macro; fixed in8010 (15.53s).
Final replay-input capture build79114 succeeds14.99s.

Focused run86641 exits0:2tests,0warnings/errors/unrun,0.158665s.
`tmp/south-fork-temporal-boundary-focused-v1-20260913/index.json`:

- Fourteen GPU sampling cases compare against double CPU interpolation, including
  large compensated clocks, actual second-stage dt, exact endpoints, tiny positive
  depths, dry states, bad time/state/bed/face values and six bad host descriptors.
- A real SSP-RK2 trial requests a second stage beyond the bracket. It rejects,
  retains state/time, emits zero boundary inventory and proposes half dt. The retry
  samples the same origin time plus the actual shorter dt and accepts, changing
  foam from0.25 to0.250732422. No retry time or state is invented.
- The real source uploader's six buffers are checked exactly. Its retained pair
  feeds the temporal shader directly; moved crops and duplicate times invalidate
  pairing. Face trace and secant acceleration match the independent expected values.

Final full targeted D3D12 run23859 exits0:79passes,0automation warnings/failures/
unrun,18.18298531s. All five existing pressure/transport/step/exterior fixtures
are supplied. `tmp/south-fork-temporal-boundary-native-v1-20260913/index.json`.
Prior248 CPU tests remain historical; no broad CPU solver rerun is claimed here.
Scoped source whitespace checks pass; no whole-worktree release pass is claimed.

## Actual playable observations and paired surface

Audit profile58839 and uninstrumented profile6560 both exit0; both verified cook
suspend/resume pairs return0. No cook restart. Map, water material and save hashes
remain unchanged. Startup experimental editor Python/SDK messages are retained;
they are not counted as clean whole-engine logs or hidden as test acceptance.

The opt-in audit uses actual uploaded endpoint buffers and saves their exact CPU
source observations. It evaluates a diagnostic stage within the real bracket,
without driving the gameplay PDE or changing its state.
`tmp/south-fork-live-temporal-audit-v1-20260913.json` passes512faces:

- Revisions2/3,128x128 at0.5m, origin(-5450,3566)m.
- Native times0.01666666753590107 and0.033333335071802139s;
  evaluated stage0.025000001303851604s, actual supplied dt0.0041666668839752674s.
- Maximum state and trace absolute error2.384185791015625e-7;
  normalized error5.9009698066848191e-8, bed exact, all four error counters0.
- These are changing observations: max state change0.00014066696166992188 and
  face-velocity change0.00009472668170928955, not merely duplicated static inputs.

Replayable actual data:
`tmp/south-fork-live-temporal-audit-v1-20260913.json.inputs.json`, SHA256
`b3ee6cb3b8b1c209613c85c2c5d15a7fe5dbc321ddf1434df9e7749f8304b9b5`.
Both endpoint objects include native time, registration, packed h/hu/hv/foam,
bed, exterior state/bed and independent face velocities. These are live sampled
fields, not a new terrain survey. They enable subsequent CPU/GPU evolution replay.

Paired frame179:2021wet contact points,958affected by detail,0dry/unavailable;
max support error0.000047651849627072806cm, RMS0.000023905239281539196cm.
GPU4226queries: maxRGBAerror5.9604644775390625e-8, passed.
Reports: `tmp/south-fork-temporal-source-{contact,gpu}-v1-20260913.json`.
This is surface parity, not visual quality, traversal or latency acceptance.

## Performance and newly exposed clock-policy dependency

Uninstrumented CSV rows60–240,1280x720, current30FPS metadata:
20.8775729778FPS, p9556.8497ms: FAIL. Mean game-thread47.61979669ms,
GPU15.40511989ms. Inclusive surface tick34.51723315ms, crest update14.58238674ms,
native StepWater4.56875801ms. These scopes overlap/nest; do not sum them.
No causal regression/gain is inferred from differing trajectories and timing.
Report `tmp/south-fork-temporal-source-performance-v1-20260913.json`.
CSV SHA256 `7d1094a2c6fcde9a25aaa66dbc647586304824a31678c57d1df0f99b84d6bc47`.
Source preparation237updates averages2.693260ms; backlog0.004034s;
682paired commits,1hold,6exact window moves,0teleports.

The native/detail clocks cannot currently be treated as the same timeline:
default capture detail34.050002s versus latest native observation11.383333927s;
audit capture detail34.033335s versus native11.433333930s. Inspection of
`RaftSimPhysicsBridgeSubsystem::TickBridge`/`RunOneFixedWaterTick` establishes
the deliberate policy: fluid advances only on the first catch-up tick per render
frame; up to four raft ticks run and older wall-clock debt is discarded. That
policy was introduced to avoid a CPU catch-up spiral. It was NOT changed here.
Do not silently relabel timestamps, extrapolate sources, enlarge the physics step
or restore unlimited catch-up. A qualified common-clock owner and enough execution
capacity must resolve this before total-state gameplay promotion.

Current screenshot was inspected:
`unreal/Saved/Screenshots/south-fork-temporal-source-default-v1-20260913.png`, SHA256
`fb1325b8659d59c895f5d0e747fe6292ca35b06fae0c51fa78b689a9896bdbed`.
Broad smooth/glossy crests, blanket-like foam, unfinished vegetation/terrain/crew
remain visible. No video motion/reference match or realism acceptance is claimed.

## Next

The same long cook84534/PID32144 passes both4200s/local4000 state and bank audits:
all5,382,400 cells finite and86,720 artificial-face cells dry. Outflow97.379378196
versus inflow45.306954547m3/s is still unsettled. Live4202/local4040 verified after
both profile resumes;4300/local6000 is next. Playable source remains600s.

Replay the captured real temporal source through CPU/GPU total-state evolution;
resolve the bridge/detail/source clock policy and persistent window ownership;
qualify outgoing-wave boundary behavior, nonlinear stability, evolved wet/contact
eligibility and whole-water cost before promotion. Convincing breaking/froth,
terrain/rapid/boulder integration, later rivers, crew, release and final commit
remain active. Full goal is unchanged.
