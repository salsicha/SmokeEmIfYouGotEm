# Queued live nonlinear evolution — September 13, 2026

The preceding turn made progress on GPU interval handoff. The live source
uploader still retained only its most recent two observations; that cannot own
a slower evolving solver, because refreshing it replaces an unconsumed bracket.

`FRaftSimNonlinearEvolutionGPU` now owns a bounded immutable observation FIFO,
one active GPU boundary bracket and retained state/progress/summary/diagnostics/
cumulative accepted boundary inventory. It initializes from the first native
total-depth packet exactly once. Later interior mean fields are never resets.
Nonblocking readbacks confirm interval completion before retiring its first
endpoint; pending/rejected trials retain their remainder and bracket. There are
no production GPU waits. Grid/bed/world-face changes, stale time/revision and
queue overflow are explicit failures, not skipped inputs or implicit reseeds.
Moving-window transfer remains required before playable promotion.

The explicit `-RaftSimNonlinearEvolutionAudit=<fresh.json>` path feeds the owner
from normal South Fork's actual immutable live observations. It requests four
intervals, captures the resulting state/ledger/clock and bounded source stream,
and records failure without altering the displayed/contact solver. This is an
integration diagnostic, not the final normal-game mode or an FPS benchmark.

Initial build85866 failed on an audit JSON shared-pointer conversion; corrected
build66645 succeeds15.65s. Native64141 exits0:90 clean passes in21.063320s.
The owner test proves exact retained state through two intervals even when later
mean interior depths change from1 to3 to7; one-slot and four-slot dispatches
consume the same four accepted steps. Queue overflow, stale/reordered time,
changed window/bed and invalid depth are rejected without overwriting inputs.

## Live failure preserved, not hidden by a clock tolerance

Normal-map diagnostic35718 exits0 and resumes cook32144 successfully. Its
`tmp/south-fork-live-nonlinear-owner-v1-20260913.json` records an exact-endpoint
failure after3 graphs/10 accepted trials in the first observed interval.
Requested native times.06666667014360428 to.13333334028720856s; GPU remaining0
but committed time.133333345875144s overshoots by5.58793544769287e-9s. Repeated
float remaining-duration subtraction loses precision even though the accepted
clock itself is compensated. The owner refuses to retire that bracket.

Independent CPU replay at the captured GPU instant completes and matches state
within existing gates (max1.873476815e-6, relative max9.668208e-8), but this does
NOT turn the clock failure into a pass. GPU float water balance is-5.60104e-6m3.
Report `tmp/south-fork-nonlinear-owner-comparison-v1-20260913.json` retains both
facts. Source SHA256
`e2cfa90612d1d97eed935c576d1ab79f2e71eeb8f9a68f2f6f438c836fb7da06`.

The owner now supplies an immutable, exactly represented interval endpoint to
the step/advance path. Remaining duration is recomputed from that endpoint and
the accepted compensated clock. A proposed dt rounds down when necessary; its
residual remains physical time for another accepted step. No endpoint snap,
state/velocity clamp, discarded time, tolerance increase, timestep or pressure
budget relaxation. The optional old duration-only comparison path is retained.
Build93377 succeeds55.81s. The native-clock regression uses the actual
4*(float1/60) interval duration. Build93427 succeeds54.50s; native67747 exits0
with90 clean passes in22.645365s. Native-clock cases consume16 accepted steps
across two intervals with exact end.20000001043081284s, identical retained state
for one-slot and four-slot graphs.

## Corrected actual owner completes; local state parity still fails

Fresh normal-map diagnostic31114 exits0 and resumes the same cook successfully.
`tmp/south-fork-live-nonlinear-owner-v2-20260913.json` completes four intervals,
40 accepted trials/10 graphs from.06666667014360428 to.40000002086162567s.
Final progress(.40000003576278687,-1.4901161193847656e-8,0,0) is the exact
observation endpoint, summary(16,16,1,1), diagnostics(0,0,0,1). There are four
retained observations, including the consumed endpoint and three future ones;
latest source.7333333715796471s means.3333333507180214s of queued physical time.
No sustained capacity/FPS acceptance follows from this bounded run.
Source SHA256
`35eedc2005511114fa4e9e726957ddcae02fa1488763020f9b5eb23cda527543`.

Independent CPU replay54262 exits0 with a FAILED state-gate report:
`tmp/south-fork-nonlinear-owner-comparison-v2-20260913.json`. CPU completes
the same four brackets with9+9+9+17 steps/0 retries, never resetting interiors.
Relative h/hu/hv errors3.857501e-6/1.199578e-6/5.852776e-6 pass2e-5, but local
absolute error8.712636947e-4 exceeds the unchanged1e-4 gate. Seven cells exceed
that absolute gate. Worst is(y77,x72), transverse momentum: GPU.002048645634
versus CPU.002919909329, with depths.019725579768/.019615134352m.
The nearby(y77..78,x71..73) shallow-bank cluster contains most large differences;
maximum h error4.249112e-4m, hu error3.977310e-4m2/s. Cause is not yet isolated.
GPU water change-1.624115689m3 plus cumulative outward1.624133640m3 leaves
1.795115e-5m3 float-storage balance. No repair or conservation-pass substitution.

Thus the clock defect is fixed and real queued evolution is demonstrated, but
the new solver is NOT accepted for normal display/contact. Next capture
per-interval/per-stage states at the shallow-bank cluster and separate transport,
pressure and front-classification divergence on identical inputs. Do not weaken
the local gate or infer its cause from global norms. Complete actual moving-
window source/face exchange, capacity and foam/shared-surface qualification too.

Final Raft DLL SHA256
`a1cd113c90cdee21c57b01d14ff1e3fafd5037b5facf3ebba706c70807c2d4ce`.
WaterDetail DLL SHA256
`8ea68a8d5ec1fc8c6403a38a691f43153e5108af58ec20e3f171d6cb80c5ad61`.
Step shader SHA256
`8306e975615babf69a7e2c1d1c5a676e1cb75f38ce93162bdde5e9d2a785cbbf`.

Twenty-one Python tests pass in0.74s, covering independent retained multi-
observation replay, partial failure instants, immutable sources, no reset,
unsupported foam and invalid observation ownership. No actual-source foam is
invented: captured packets contain0 transported foam.

Normal material, map and save hashes remainE0C961...,DB3080...,181D1E....
The last ordinary non-diagnostic gameplay measurement remains18.899245FPS,
p9570.33ms (FAIL30). This turn does not accept visuals, terrain, rapid shape,
crew or the unfinished moving-window/foam/render-contact solver integration.
Remaining river reviews, normalization, release checks and final commit stay
in scope; Troublemaker remains a rapid within South Fork, not a menu scenario.

Expanded cook84534/PID32144 passes BOTH5200s/local24000 state and artificial-
bank audits. All5,382,400 cells finite and86,720 artificial-face cells exactly
dry; outlet117.824758481 versus inlet45.306954547m3/s means STILL SETTLING.
Runtime600s remains unchanged; next5300/local26000 requires both audits after
the complete marker. Same cook, no restart.
