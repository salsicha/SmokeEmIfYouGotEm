# Source-current wave coupling and nonlinear verification — September 12

Status: isolated strain correction REJECTED for ordinary gameplay after a real
shallow-bank failure despite64 passing native tests. It is now gated behind
`bExperimentalMeanStrain=false` / explicit `-RaftSimMeanStrainReview`; restoration
passes64 native tests and the actual-game checks below. Nonlinear breaking/overturning and convincing froth
remain unfinished. Desktop target30 FPS and all existing tolerances unchanged.

## Why the large crests still look wrong

`FPhysicalCrestEnvelope` still makes an asymmetric Gaussian main crest, fixed
negative toe and two positive tails. Its parameters follow hydraulic-site
records, but this is not a time-evolved nonlinear breaking profile. GPU detail
adds small waves; finite-depth pressure corrected their propagation but did not
turn that large prescribed shape into a breaking wave. Neither sharper foam
masking nor an arbitrary larger noise amplitude closes this gap.

## Physical formulation and current implementation

Let H,U be the authoritative mean, h=H+eta, and q=h*(u-U) the relative momentum.
For constant H,U the full hydrostatic relative flux in direction j is:

    mass: U_j*eta + q_j
    momentum_i: U_j*q_i + q_j*q_i/h + delta_ij*g*(H*eta + eta^2/2)

This follows from the [Saint-Venant conservation laws and characteristics](https://www.clawpack.org/riemann_book/html/Shallow_water.html).
The reference verifies equivalence to independently formed total-momentum fluxes
and eigenvalues u_j-sqrt(g*h),u_j,u_j+sqrt(g*h). It does not provide dispersion,
wet/dry transition, overturning or a froth closure.

For a mean that owns its own acceleration/bed balance, relative momentum must
also receive `-(q dot grad)U`. The eta*mean-acceleration term that appears when
transforming fluxes ALONE cancels against that background balance. An initial
audit v1 omitted this cancellation; its strain numbers are superseded by v2,
not silently overwritten. v3 uses neutral source-field labels that also apply
after the correction is integrated. Sources/friction beyond the assumed mean
balance require their own perturbation closure; no measured TKE is claimed.

The trial finite-depth shader added this linear strain coupling at
each RK stage, using current q and current prescribed velocity gradients.
Centered differences use wet neighbours; one-sided wet differences are used
at the fixed wet-domain edge, and isolated wet cells have zero inferred gradient.
Dry/absent cells are never sampled as zero-velocity fluid. Uniform currents are
unchanged. Height flux, foam flux/source, iteration count, time step, source head,
macro crest profile, materials and paired texture/contact path are unchanged.
The failed combination is now an explicit opt-in shader permutation, not enabled
by the finite-depth mode or ordinary South Fork FullReach. Mode changes on a
persistent simulation/remap are rejected. It is NOT the nonlinear q*q/h or eta^2
pressure integration yet. No arbitrary damping or height clamp hides the failure.

## Verification

Build7985 succeeds13.76s. Native57266 exits0 and actual report records64 successes,
0 warnings/failures/unrun. New GPU affine rotation/extension fixture checks128
interior points against analytic SSP-RK2: momentum error5.74271366e-9 m2/s,
height error0, foam bit-exact against the original branch. Existing phase,
pressure convergence, rest/dry, forced waves, remap and contact regressions pass.
Report: `unreal/Saved/RaftSimValidation/south-fork-mean-strain-regressions-v1-20260912/index.json`.
Shader SHA256 `506427bde988ebdc1668f9221345c102d04b487fed2594f22ede7d8dff975086`.
Raft/main/WaterDetail DLLs remain3aad3636…/4b9065ec…/ef1d7f74…; automation rebuilt.

37 Python tests pass, including6 new nonlinear-reference/input tests. The
constant-background simple-wave probe is EXPLICITLY authored, not surveyed:
H1.5m, amplitude0.45m, wavelength40m, current0.4m/s. At1.2s before characteristic
crossing, analytic maximum slope rises0.07068 to0.10495. Numerical mean height
error falls4.58270e-5m at200 cells to1.26649e-5m at400 cells, conserved-sum error
<1e-11. The reference rejects nonpositive depth and post-crossing analytic use;
state-aware CFL/retry never clips mass or advances a rejected interval's clock.
These are necessary numerical checks, not a replacement river scene.

Fresh pre-correction gameplay30753 exports three complete actual GPU snapshots
under `tmp/south-fork-finite-amplitude-input-v1-20260912/`. Input audit v2 records
11,198/11,827/11,825 wet cells, all positive total depths, but minimum total depth
reaches0.005217m and |eta|/H reaches1.42161 near shallow cells. Current-state
nonlinear signal CFL at120Hz is0.265–0.269, NOT a bound on future RK face states.
The omitted strain source reaches0.2668–0.3850 m2/s2 in these snapshots. This
rules out treating all cells as safely small-amplitude and then increasing
excitation blindly. Nonlinear production integration still needs state-aware
admissibility/CFL, variable-mean/bed consistency, retained finite-depth dispersion
and source-driven macro crest evolution; no amplitude clamps or weakened gates.

## Actual gameplay rejects the isolated strain change

Actual-game44198 exits0 and produces8 PNGs;000/007 were inspected. Both show a
spike near the shallow bank. Complete snapshots at10/15/20s show maximum raw
|eta|0.214575/0.470756/5.591992m. At20s,10 formerly wet cells have inferred total
depth<=0, minimum-0.465911m and maximum|eta|/H338.64256. This is a physical-model
failure, not acceptable breaking. Preserve all snapshots under
`tmp/south-fork-mean-strain-input-v1-20260912/` and their hash-bound v3 analysis
`tmp/south-fork-mean-strain-input-audit-v1-20260912.json` for nonlinear migration.

The10s paired contact/GPU audits still pass, demonstrating their deliberately
narrow scope: sequence141,2,021 wet contacts/956 detail-affected, support error
4.768161978e-5cm;4,226 GPU queries maxRGBA2.980232239e-8. The macro sampling audit
has1,550,160 points max0.600186518cm<2cm/sourcechange0;UV3/UV1 transport errors0.
None of those passes negates the subsequent invalid physical state. Reports use
`tmp/south-fork-mean-strain-{contact,gpu,crest,transport}-v1-20260912.json`.
Trial profile49193 finishes and safely resumes cook29104, but is not acceptable
performance evidence for a usable scene because this physics version is rejected.

NEXT: retain the analytic formulation tests, but integrate a coupled nonlinear
height/momentum/pressure treatment with state-aware CFL and admissibility,
including fixed wet-boundary/mean-flow consistency, before enabling this source.
Use the actual failed snapshots as a required replay/stress case. Do not enable
the isolated source simply because the affine GPU fixture passes.

Isolation build24372 succeeds71.64s; added mode-transition test build79296
succeeds12.96s. Final37 Python tests pass. Current shader is
`952243ae18cbbc568c67790d9d22a98c6f9f4c4f207dff5bf44dd15262740a49`,
Raft DLL `8a6480375ebb34bb47008c624ebe337bb1a8f004478506bcfe47e194372e7dd2`,
WaterDetail `615b55aa6fd1b969573e28cfebf429fe7a576c3e68655bdcab102c7ccd631a36`.
The experimental shader still has an analytic fixture; default mode explicitly
asserts false, and implicit enable through Advance or RemapWindow is rejected
before mutation. The finite-depth pressure correction remains enabled normally.

Final native55126 exits0 with64 successes,0 warnings/failures/unrun in
`unreal/Saved/RaftSimValidation/south-fork-strain-isolation-regressions-v1-20260912/index.json`.
Ordinary restored-game62514 exits0 without the experimental flag. All three raw
snapshots have0 nonpositive total-depth cells, minimum total depths0.009154/
0.009954/0.009750m and maximum|eta|0.121710/0.096173/0.163286m. Preserve under
`tmp/south-fork-strain-restored-input-v1-20260912/`; hash-bound audit is
`tmp/south-fork-strain-restored-input-audit-v1-20260912.json`. This is a bounded
restoration smoke check, not full nonlinear or long-duration acceptance.

The8 restored PNGs were produced;007 was inspected and the trial's bank spike
is absent. Broad rounded crests and soft merged whitewater remain unaccepted.
Pairedsequence115:2,021 contacts/959 nonzero detail, maxerror4.767604378e-5cm,
GPU4,226queries maxRGBA5.960464478e-8 passes. Macro1,549,944samples max target
error0.600502968cm<=2cm; fine tracking0.144331396cm, sourcechange0. Reports use
`tmp/south-fork-strain-restored-{contact,gpu,crest,transport}-v1-20260912.json`.
Map db3080cc…, primary material26aa5029… and save181d1e57… rehash unchanged.

Fresh restored ordinary-play profile6390 exits0 and safely resumes the cook.
Warmed CSV rows100–250:21.348655 FPS, p9554.2771ms, still FAIL30. Metadata30 and
1280x720 unchanged; CSV SHA256
`c109ad3bb1e9f33174c118b8d9b4fc1409046a62014886921327ac279e3a108f`.
Report: `tmp/south-fork-strain-restored-performance-v1-20260912.json`.
680 paired commits/1 hold, ordinary PDE backlog4.390ms; maximum queue age0.4s
still includes startup/screenshot and is not warmed render-latency acceptance.
Different trajectories/timing preclude calling the change from19.625346 FPS a
causal optimization gain. The stable physical equations are restored, not a
new nonlinear production model. Cook12920/time2646s remains live,2600 last both
audited,2700/local14000 next. No further engine process remains after the run.

## Actual-bank nonlinear replay: rejected, September 12

`physics/scripts/nonlinear_detail_replay.py` adds a research-only 2-D replay of
the captured mean/depth and eta/relative-momentum fields. It uses the independent
40-iteration finite-depth pressure stencil, MC reconstruction with positive face
depth slopes, nonlinear momentum and hydrostatic pressure, mean strain, and
SSP-RK2 stage rejection. Unsafe steps do not advance time or repair cell mass.
The mean and wet mask are frozen and forcing is absent; this is NOT an exact
replay of the moving engine and is NOT integrated into ordinary play.

The requested 5s replay from the real 15s `live_01` snapshot FAILS in both modes.
Fresh v2 diagnostics distinguish a timestep collapse from trial-budget exhaustion:

| Mode | Time reached | Accepted / rejected | Minimum total depth | Signed-volume error |
| --- | ---: | ---: | ---: | ---: |
| Nonlinear hybrid | 1.196926555s | 307 / 87 | 7.712366839e-7m | -7.216449660e-16m3 |
| Linear control with strain | 1.406881436s | 193 / 27 | 1.305480724e-11m | -1.665334537e-16m3 |

Both stop at an attempted timestep below1e-9s, before any negative depth is
accepted. Both drain cell(x61,y80), mean depth0.01787680015m. The nonlinear
last state already implies1455.29m/s total velocity, so positive depth and mass
conservation alone absolutely do not establish usable physical behavior.
Reports and last-admissible `.failed-state.npy` files are preserved under
`tmp/south-fork-{nonlinear,linear}-bank-replay-v2-20260912.*`. Earlier v1 reports
remain unchanged. Source metadata/flow/state hashes are recorded in each report.

A two-cell counterexample isolates a structural issue without strain or finite-
depth dispersion: H=(.02,1)m, eta=(-.02+epsilon,-.1)m, U=q=0. Dissipating the
eta jump sends water OUT of the nearly empty shallow cell even as epsilon tends
to zero. The flux is mass-conservative but does not preserve nonnegative total
depth across unequal bed levels. Smaller time steps or adding q*q/h cannot
repair that flux. The new failure-detector tests explicitly require rejection;
they are not physical acceptance tests.

Next work must reconcile total-depth face reconstruction and bed-source balance
with the mean-flow split and moving wet domain. A useful primary formulation is
[Audusse et al. (2004), equations2.9-2.16](https://publications.imp.fu-berlin.de/478/1/file_2004_siam.pdf):
reconstruct water depth above the higher interface bed and balance its pressure
with the bed source. Its lake-at-rest result does not justify freezing arbitrary
moving river means or establish our hybrid's nonlinear dispersive stability.
Do not port this rejected perturbation flux or enable isolated strain in play.

The focused Python suite now passes45 tests, including8 new replay tests
(pressure/dense-operator agreement, rest state, analytic convergence,
nearly-drained transport, and explicit exhaustion/failure detection). No new
Unreal build, gameplay capture, performance measurement, reference playback,
map/material/save mutation or production-water change occurred in this replay
work. The latest valid performance remains21.348655FPS/p9554.2771ms, FAIL30.
Cook29104 remains live at local13660/time2683s;2700/local14000 is next, not yet
audited. Runtime remains the audited600s state.

## Remaining scope

The2600s hydraulic snapshot passes both independent state and artificial-bank
audits; outlet93.38026 versus inlet45.30695m3/s still shows settling. Runtime600s
unchanged;2700/local14000 next. No new reference playback is claimed this turn.
Full terrain/boulder/collision traversal, physical breaking/froth,30 FPS,
Colorado then Pacuare then Futaleufu, Chilko/Zambezi, crew, normalization, release
qualification and final commit remain required. Goal remains active.
