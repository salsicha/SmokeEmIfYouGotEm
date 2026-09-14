# Captured thin-state diagnostic — September 13

Follow-up: [moving-history accuracy and exact-product performance](normal-river-moving-history-performance.md).
Two live moves now complete, but full-history accuracy still fails. Exact
multiplication is34.49% cheaper in the measured active GPU graph; neither this
nor the retained-remainder pass qualifies normal playable water.

This is failure localization, not solver or scene acceptance. Desktop remains
30 FPS / p95 33.333 ms. Ordinary gameplay remains18.899245FPS/p9570.33ms.
The CPU correction and isolated FP64 proof below are followed by an integer
implementation in the diagnostic total-depth step. Normal water is unchanged;
the original transaction, retained remainder and extreme-pressure regressions now pass. Full
history, real-time capacity and normal playable integration are still open.

## Latest: enforced physical residual and actual retained remainder pass

Both actual RK2 stages now pass their same-stage geometry into the true-residual
check. The ORIGINAL unweighted2e-5 residual gate remains mandatory; an additional
sqrt(depth)-weighted2e-5 gate catches errors hidden by huge algebraic values in
thin cells. Original pole bits0/1 and new physical pole bits2/3 all reject the
transaction. This is a necessary additional check, not proof of arbitrary force
accuracy; independent state/force comparisons remain required.

Physical norms use normalized mantissas and integer exponents BEFORE multiplying
sqrt(depth) by RHS/residual. This avoids losing weighted products below the
minimum subnormal or overflowing products of large finite inputs. Negative
subnormal/nonfinite depth rejects. The raw check and its original eight fixtures
are unchanged. Nine added cases test raw-pass/physical-fail, raw-fail/physical-pass,
weighted underflow/overflow, zero RHS, dry geometry and invalid geometry. Normal
RK2 adds four small reduction passes per stage; warm cost is NOT qualified.

Build58404 exits0 in22.43s, final interval-capture build19484 exits0 in14.92s.
Native98695 exits0:124 clean tests, zero warnings/failures/not-run,34.49199295s
automation duration. `tmp/south-fork-physical-residual-native-v1-20260913/index.json`.
This run also tests the ten-case source-inclusive pressure fixture v3, SHA256
`ed779101dece6dbe460fd0595fe692d49062def9c14e64c3b2b1b0816498d5e1`.
Single-trial capture/independent analysis `tmp/south-fork-physical-residual-
{capture,analysis}-v1-20260913.json` still accepts and passes both stages.
Its binary is bit-identical to the previous accepted capture, SHA256
`5667023e7f7c62891d533a6b1e1e643bd5d6d115b9b3ac2d89d5bc2494dd69d1`.

New v2 interval input appends the ACTUAL432/37 trial/accepted counters,
diagnostics[0,5,8,0] and512-face cumulative ledger to the unchanged captured
state/clock/boundary payload. `tmp/south-fork-retained-interval-input-v1-20260913.bin`
SHA256 `fc82d6caccc6af486dc724476032bb42e0fe3d082be7157b1964b898736bb231`.
Source remains the original plateau-owner capture, SHA256
`a7d46be2e00dda5289df06614716fad8dcdb4baf54b58bf74df119338ff74e5d`.
Two eight-slot graphs retain all five GPU records across graph lifetimes,
preserving the4096 total limit and original proposed step; no source-interior,
counter, clock or ledger reset. Native28876 exits0, one clean diagnostic test,
1.009274244s automation duration (NOT a frame/solver cost benchmark).

The continuation completes after FIVE additional trials, all accepted:
summary[437,42,1,1], diagnostics[0,0,0,1], progress
[7.600000381469727,1.4901161193847656e-8,0,0]. The two-word committed time is
EXACTLY the original observed end7.600000396370888s. No invalid output cells.
Capture `tmp/south-fork-retained-interval-capture-v1-20260913.bin` SHA256
`0861e2d3514081e853ec49d02e065483df85e5a32c352c2f4a43c27573339782`.

Independent `audit_captured_owner_interval.py` verifies source/input hashes AND
repacked payload equality, counter bounds, record layouts, clock/completion,
state validity and retained ledger. Its double control starts from the actual
captured interior, uses the ORIGINAL observed exterior bracket, and independently
chooses three admissible RK2 steps for the0.018899115912333286s remainder.
`tmp/south-fork-retained-interval-analysis-v1-20260913.json` passes the unchanged
1e-4 absolute/2e-5 component-relative state gates: maxerror1.486208486e-6,
relative[4.676515846e-8,4.927686091e-8,4.902525666e-8]. Water inventory change
-0.315624266914715m3, outward ledger delta0.315620537000111m3, reported float
balance-3.729914604e-6m3; foam remains zero. The float balance is reported under
the existing policy, not repaired or declared a new conservation acceptance.
56 focused Python checks pass in2.71s, including13 new interval-audit and12 new
interval-export cases. This remainder proof does NOT requalify the prior
full-history error0.00743069265, moving-owner queue capacity, warm GPU cost,
nonzero-foam history, visual quality or30FPS. Next: fresh complete moving-owner
history/accuracy and separately measured capacity/cost before playable promotion.

## Previous: dynamically normalized CG and depth-root coefficients pass

Both single-workgroup and distributed (split/fused) GPU CG now maintain
residual/search vectors in a moving power-of-two scale and accumulate the
solution in original RHS units. Integer scale exponents do not themselves
underflow. After a scale change rho, the search recurrence uses
`p_new = z_new + rho*(rz_new/rz_old)*p_old`; this is the same CG equation in
different units. The misleading initial-global-residual early exit is removed;
exact zero may stop early, otherwise the EXISTING40-iteration budget is used.
No matrix, physical forcing, timestep, acceptance tolerance or depth is changed.
Distributed reductions retain separate read/write storage and explicit shared
memory barriers. Added storage at128x128 is512B group exponents plus32B control.

The CPU reference now uses the same arithmetic scaling policy, independently
validated against explicitly assembled442x442 dense matrices. Old extreme
fixtures and failed results remain preserved. New eight-case fixture
`tmp/south-fork-range-pressure-fixtures-v2-20260913.bin` SHA256
`1cdd27c67c4f03afc94002f594f4047fa8067bc5d39ad8fb124464fbcad1d2fa` has direct
force agreement within float32 fixture rounding (about1.2e-7); see dense-v3
report. The double dynamic recurrence agrees with dense forces within3.6e-15;
the float32 arithmetic prototype is within6.6e-7. Those prototypes alone are
not native GPU qualification. The original huge-finite-RHS regression exposed
a norm-reporting overflow, fixed by normalizing before squaring; it passes.

Native16119 (range-cg-native-v2) originally had123 passes/one pressure failure:
2^-130 and2^-126 cases passed, but minimum2^-149 still had force error0.04426.
The remaining defect was taking square roots of already-rounded face fractions.
Shared edge coefficients now evaluate `h*sqrt(h*other)/(h+other)/dx` through
normalized mantissas and integer exponents, avoiding premature ratio/root loss.
Equal depths retain the exact half-weight branch and W/transpose-W coefficients
are identical in pressure reconstruction and solver preparation.

Build10474 exits0 in13.95s. An initial shader launch61807 failed compilation
because an identifier conflicted with Unreal's `half` macro; renamed without
changing arithmetic. Final native86921 exits0 with124 clean passes, zero
warnings/failures/not-run,95.402946472s automation duration:
`tmp/south-fork-range-cg-native-v3-20260913/index.json`. All three extreme cases
now pass in BOTH split and fused modes, force errors
1.1920929e-6/9.53674316e-7/7.15255737e-7; pressure errors below1.863e-6.
Negative-subnormal depth still rejects. The scale helper passes16,672 independent
exact-rational cases bit-for-bit (fixture SHA256
`80852b82fa9fc14ac71651b9adce254a4105b9caab440b57c940d373736b83ab`).
Unchanged original seven pressure fixtures, including both source captures,
also pass separately in native92880 with original prescribed boundaries.
That run is one clean pass in1.514129639s; the final combined Python suite
passes125 checks in15.24s (session85606 exits0).

Actual `tmp/south-fork-range-cg-analysis-v2-20260913.json` still accepts the
retained stalled trial [0,0,0,1], with no invalid candidate/classifier cells.
Both independent pressure stages pass; max force errors3.700472075e-5 and
3.127228767e-5, RHS relative errors below2.232e-6. True residuals are
2.322378708e-7/2.240889411e-7. The added sqrt(h)-weighted audit also passes,
2.380451165e-7/2.307516330e-7. This additional physical-residual check is
currently an AUDIT, not yet an enforced runtime GPU acceptance gate.
Capture SHA256 `5667023e7f7c62891d533a6b1e1e643bd5d6d115b9b3ac2d89d5bc2494dd69d1`.

Current hashes: portable arithmetic
`ae18b0e97c93e31693a6eea448f5aa1cec51394929a30f0b4cf122d11c1a54dc`;
acceleration shader `5f447d1d7e1923435f0c78ac9c75e45a5858248f664dcb28800d41682f7b9d14`;
shared pressure math `e731d9e7099e8229515d9f684645ba09d2223299e921fa7fee68efaf78fee3ae`;
CPU range recurrence `55b3a99c6ed00e5711952f5f2528904316e58ae6e52ac5170eaeaf9c0e8a7bc4`.
Prepared ten-case fixture-v3 includes the original source snapshot and records
the new reference-module hash; SHA256
`ed779101dece6dbe460fd0595fe692d49062def9c14e64c3b2b1b0816498d5e1`.
It is prepared for subsequent tests, not claimed tested by the runs above.

Next: enforce a meaningful additional runtime physical-residual check, then
repeat the full retained interval and original live history/capacity before
normal promotion. Profile warm GPU cost separately: these automation durations
are NOT30FPS or solver-cost measurements. Normal visuals and gameplay are
unchanged. Cook74818/PID41820 remains live beyond6261.5s; complete6300/local6000
requires both state and artificial-bank audits.

## Previous: actual pressure step accepts; extreme-pressure tests remain failing

Pressure/acceleration now share represented-range depth weights and W
coefficients. Validation preserves positive subnormals and rejects negative
subnormal depth; recovered velocity, square-root normalization, weight rates,
depth-factored forcing, pressure gradient/reconstruction and final conservative
forces use the tested portable arithmetic where these values were being lost.
The solver recurrence,40-iteration limit, CFL, residual and acceptance gates
are unchanged. Existing graph-local pressure references are exposed for
diagnostic capture only, including actual prescribed boundary traces.

Build9858 exits0 in55.89s; additional capture/invalid-test build82922 exits0
in15.36s.101 focused Python pressure, provenance, boundary and30FPS checks pass
in7.30s; five fixture checks pass again after preserving the original lake/
zero-fraction test independently. New reference fixtures add three explicit
positive depths (2^-149,2^-130,2^-126), not dry-cell substitutions.

Actual `tmp/south-fork-range-pressure-analysis-v1-20260913.json`:

- Transaction ACCEPTS `[0,0,0,1]`, dt1.5894572769070692e-8. Compensated progress
  becomes [7.581101417541504,-1.2118837844354857e-7,.01889909990131855,
  .008333333767950535]. Candidate has zero invalid cells; this is one trial,
  not proof the remaining interval or full live history completes.
- Both transport/classifier stages still pass. Each actual pressure stage has
  zero pressure/solver error flags,40/25 iterations. Independent pressure on
  the actual captured state/rate/graph/slope/fraction/boundary trace passes:
  maximum force error1.7692823947e-5/1.6402947881e-5; relative errors for all
  RHS/correction/pressure/force fields below2.235e-6; true GPU residuals
  2.1245010e-7/2.1577357e-7.
- Stage1 thin-cell force [6.513149782975426e-39,4.056085029659005e-39]
  survives and matches the independent [6.51314920206292e-39,
  4.056086160221074e-39]. No flooring or replacement state is used.

Native57320 is TERMINAL exit1:123 clean passes and ONE FAILED pressure test,
zero warnings/not-run,104.965797424s automation duration. Report
`tmp/south-fork-range-pressure-native-v1-20260913/index.json`. The new extreme
cases5/6/7 have pressure force errors8.57786226/8.57041073/8.57067037 in the
legacy reduction path despite small global residuals; fused mode also fails.
Do not report this as a green suite. Separate34877 exits0, one clean pressure
test in1.521968722s using the UNCHANGED original seven fixtures (including both
captured source cases) and original prescribed-boundary fixtures. This does
not erase or supersede the new failures.

Independent bounded dense diagnostic
`tmp/south-fork-range-pressure-dense-v1-20260913.json` shows the CPU iterative
oracle itself is underconverged in those extreme cases. The explicitly
assembled442x442 matrices are exactly symmetric. The largest RHS is1.7473e20;
direct-solve global residuals are tiny, but forces differ from iterative CPU
fixtures by4.146600424/4.144875852/4.144875860 (dense maximum force about2.7491).
This explains why a small globally normalized residual alone cannot establish
physically useful pressure accuracy. Dense solves are diagnostic only and do
not replace the runtime algorithm or authorize changing the iteration budget.
Next: strengthen represented-range solver conditioning/error qualification
and independently validate the reference before regenerating fixtures. Keep
old artifacts and gates; do not accept either old oracle or GPU force merely
because their global norms are small. Then repeat interval/full-history,
capacity, warm cost and normal playable/visual integration.

Fixture SHA256 `65bec83d72ed430296f8757e71709ee40c5346d61209061fb429e3775621a489`.
Actual capture SHA256 `069ca29d49db8b16416e2a0296981870d50ce864134204af0a67f1918fadb27f`.
Shared math SHA256 `547eed102679877c89f78b84e683d5d7baf1f59c727af4ecad55bbd855a44949`.
Pressure shader SHA256 `5246481305510cbeec96b57726f2c18cbfba36231f7288ad46c9ee48783eea34`.
Acceleration SHA256 `af4ebf783df0b278835c8b76e42290609e0842d11214a2e09aefe3ef86b6c3a1`.
Cook74818/PID41820 remains live. BOTH6200/local4000 snapshot audits pass:
5,382,400 finite cells,86,720 exactly dry artificial-bank cells; still settling.
Next complete6300/local6000 needs both audits. No source promotion,30FPS
acceptance or gameplay visual change is claimed by this diagnostic work.

## Previous: actual breaking classification passes both stages

The classifier now uses represented-bit wetness/sign checks, normalized
subnormal depth logarithms and tested integer arithmetic for rate roots, depth
ratios and band radius. Cancellation-prone surface jumps use the same exact
four-term dyadic difference; physical thresholds and flat-front connectivity
are unchanged. Each stage caches both axis jumps once in an8-byte/cell buffer
(128KiB at128x128), avoiding repeated exact arithmetic in front scans. The
independent CPU reference also uses exact rational cancellation fallback.

Build82181 exits0 in29.94s. Native20037 exits0:124 clean tests, zero warnings,
failures or not-run,33.553119659s total automation duration. This includes37
synthetic classifier cases (18 added minimum-subnormal/near-normal cases in
both orientations), original RK2 checks and six rejected invalid-input cases,
including negative minimum-subnormal depth. All24 focused Python reference/
captured-comparison checks pass in4.44s. These are correctness tests, not FPS
or isolated warm GPU-cost measurements.

Fresh report `tmp/south-fork-range-breaking-native-v1-20260913/index.json` and
actual analysis `tmp/south-fork-range-breaking-analysis-v1-20260913.json` show:

- Both actual stages have zero invalid fractions. Independently classifying
  the captured geometry, hydro rate and wet graph gives exactly79 fronts,
  1514 boundary-truncated runs and zero subcell fronts in each stage.
- Maximum fraction error is3.6954879760742188e-6 in both stages, below the
  unchanged2e-5 gate. Maximum surface-jump error is2.3374741431325674e-7.
  The CPU classification does not substitute the GPU surface jumps.
- Both transport flags remain zero and maximum hydro error is5.621579200e-5.
- The transaction STILL rejects with `[0,1,0,0]`: pressure/acceleration has its
  own uncorrected represented-depth validation/arithmetic. Output is bit-exact
  to input, committed clock/remaining time are unchanged and retry dt halves.

Fixture SHA256 `35a2ad1ad53fd8a9045b0f873cca7fc340a9d77f095cade7d429733061df7fd5`.
Capture SHA256 `590c6abc0fd7a54b59999b10256f397eee96d01bddb1de58e11747507047aa6d`.
Classifier shader SHA256 `13516e228b7e64101b62332bdd428ca543a4f0206d3239ce3b4e727df5160589`.
CPU classifier SHA256 `7d05565ae6384a6be91f3dcf194de2e03ca77ed3f7ee0d3d0fe7957850959c33`.
Input/source provenance remains the retained stalled trial recorded below.
Next: pressure and acceleration validation, weights, square-root normalization
and forces, without bypassing rejection or residual/accuracy gates. Then
repeat actual transaction, full-history/capacity and warm cost checks before
playable promotion. Normal visuals remain unchanged and unaccepted. The live
cook74818/PID41820 reached6156.5s;6200s/local4000 needs both complete audits.

## Previous: captured subnormal flux survives both transport stages

Transport now carries the corrected face depth through its velocity recovery,
wave speed, opposing flux products/subtraction, foam donor selection and flux,
divergence, bed source and explicit exterior reduction/ledger. Opposing products
still round symmetrically before subtraction, preserving exact rest. Ordinary
stored face depth is refined with the same exact MC polynomial when cancellation
requires it; slope/flattening rules and the physical state are unchanged.
These scalar operations currently reuse the general integer affine accumulator.
Their cold compilation/PSO and warm runtime costs need separate qualification.

The added integer square root normalizes the represented input and computes a
24-bit restoring root with an exact remainder. It does not flush subnormal input
or require FP64/native64-bit integers. Build16546 exits0 in14.08s. Native76357
passes16,672 square-root cases bit-exactly, one clean test,0.849886119s including
overhead. Fixture `tmp/south-fork-portable-sqrt-fixtures-v1-20260913.bin` SHA256:
`87ebe9a3f7df7dc44cc807c17ae7295627662585a556be0e8d2ec426a5d28dab`.
68 focused Python arithmetic, provenance and30FPS checks pass in3.31s;26
arithmetic/capture checks pass again after adding classifier-output diagnostics.

Integrated native84310 exits0 with124 clean passes (123 regressions plus actual
capture), zero warnings/failures/not-run. Report
`tmp/south-fork-range-flux-transport-native-v1-20260913/index.json` records
165.114105225s total, including101.223197937s for the cold captured trial and
33.995010376s for the first advance fixture. Shader compilation also exceeded
the compiler's time-reporting threshold. These are NOT isolated GPU/frame-time
measurements; do not report them as either30FPS acceptance or a measured warm
GPU cost. This implementation requires cost profiling/optimization before use.

Actual `tmp/south-fork-range-flux-transport-analysis-v2-20260913.json` confirms:

- Stage1 y79/x88 mass rate is now-5.169473552282724e-38 instead of zero;
  independent reference is-5.169473904368632e-38. Both momentum components also
  survive: [-4.4722469635934595e-37,-1.2007558384983639e-39] versus reference
  [-4.472247247051072e-37,-1.2007622568790478e-39].
- Maximum same-input hydro rate error across either stage is5.621579200e-5.
  This is a bounded operator comparison, not full live-history qualification.
- Both transport diagnostic buffers are zero. Input/second-stage breaking
  classification has0/16384 invalid fraction cells respectively. The classifier
  still uses float wetness/graph checks which treat the subnormal cell as dry;
  its invalid fraction is passed to pressure validation and causes rejection.
- Transaction diagnostics remain `[0,1,0,0]`. No rejected state is published;
  output is bit-exact to input and no committed time is consumed.

Capture SHA256 `e346a0f1eac606f17e035c5839196376cb59e01ff9fdaae61f86ad4bdf8f9b24`.
Portable helper SHA256 `821f44af14f270edbed6a2923d485a053fe27de78b712c46c6fe88ff43444d25`;
transport shader SHA256 `09f59cae84194ce5d3c93d43e022c00d355ba06e643d2e71afe6c63f89daf295`.
Next: preserve represented wetness, rate thresholds and depth ratios through
breaking classification, then pressure/acceleration validity, weights, root
normalization and force calculation. Preserve rejection/accuracy/CFL gates.
Warm cost, full live history/capacity and normal visual/gameplay integration
remain open. Full-river6100s now passes both snapshot audits and is unsettled;
continuation74818/PID41820 remains live toward8000s.

## Previous: exact hydrostatic cancellation removes the false inflow

`RaftSimExactHydrostatic.ush` represents the finite FP32 depth/bed MC
polynomials as10 integer limbs with quantum2^-160. This preserves the full
polynomial through bed-offset subtraction and hydrostatic reduction, rounding
only the final face depths. No FP64, native64-bit integer, physical cutoff,
depth floor or state repair is introduced. A conservative64eps local arithmetic
scale selects the exact fallback for cancellation-prone faces; it does not
select wetness. Exact positivity remains available even if a positive face is
smaller than the final FP32 storage quantum.

The actual transport now retains one explicit per-axis flattening mask
(4bytes/cell) from the original raw face decision. This avoids inferring that
decision from a rounded zero slope. Raw MC wetness uses represented positive
depth. Closed-boundary direction and first/second-order handling are retained.
Ordinary face velocity, flux products/divergence and exterior reduction still
need represented-range work; do not infer those are fixed by the new helper.

Build62515 exits0 in14.25s. Independent rational fixtures include constant films
across bed datums, strictly positive faces rounding to zero, random finite
stencils and both actual captured stages with all four flattening combinations.
Native4320 passes4301 cases/34408 output comparisons bit-exactly, one clean test,
0.866009712s including overhead. Fixture
`tmp/south-fork-exact-hydrostatic-fixtures-v1-20260913.bin` SHA256:
`c6a03c6bfe2889facc72999af297d0e22521ef73b61a540c3836ef48d7283314`.
An initial Python assertion incorrectly expected a nonzero reconstructed bed
offset on a flat bed; the assertion was corrected to the independent rational
result, without changing the shader or fixture.67 focused Python checks pass
in2.49s, including the exact-positive/rounded-zero and exact-blocked cases.

Integrated native23103 exits0:123 regressions plus actual capture,124 clean
passes, zero warnings/failures/not-run,32.804458618s. That suite duration is
NOT a frame-time or solver-cost measurement. Report:
`tmp/south-fork-exact-face-transport-native-v1-20260913/index.json`.
Actual analysis `tmp/south-fork-exact-face-transport-analysis-v1-20260913.json`:

- The old spuriously positive stage1 mass rate2.771265983e-18 at y79/x88 is
  gone. Stage0 mass rate is now-5.167702311e-38 versus reference-5.169474465e-38,
  instead of approximately twice the expected outflow.
- Stage1 at that cell is now zero, NOT the required-5.169473904e-38: ordinary
  face velocity/products/divergence still flush the represented subnormal.
- Both stages at the other inspected thin cell y109/x113 now have the expected
  mass rate to float rounding, removing the previous doubled outflow.
- Both transport diagnostic buffers are zero, but the transaction still
  rejects with `[0,1,0,0]`. Output state remains bit-exact to input; committed
  time and the unconsumed interval are unchanged. Pressure rejection is retained.

Capture SHA256 `6709b501333ba504cee0557a76523bc9ed87fb0e9d4f501cdd45fe2c9cd2f2cb`.
Exact helper SHA256 `08f639830d5fa689ee3d6a8defa4298a1c3aee8bbdbe6b4f8bf015b4f439f1ab`;
transport shader SHA256 `419ec2d84236b6a24b0397af78e5396b5cabe101b5e53a186de8533da7d303bf`.
Next: preserve the corrected faces through velocity/flux/pressure consumers,
then repeat full live-history accuracy, capacity, cost and actual visual checks.
No normal promotion,30FPS claim or full-history requalification.
Continuation74818/PID41820 remains live; last observed local1040/native6052s,
next COMPLETE local2000/6100s needs both independent snapshot audits.

## Previous: transport velocity restored, pressure rejection remains

The next actual replay uses integer-normalized division with an exact integer
remainder and nearest/even rounding.17,159 rational/special-value cases pass
bit-exactly on the GPU (native67160, one clean pass,0.219782799s). The fixture
`tmp/south-fork-portable-division-fixtures-v1-20260913.bin` SHA256 is
`080ec03c1b2746137cb688ec4c63b522c5effdcbbef5a31c45a1f417fd74e5e0`.
No input depth cutoff, altered physical rule or hardware FP64 dependency.

Transport phase0 now uses represented-state validity and this division for
interior velocity, and the same validity rule for exterior state. The existing
velocity scratch buffer is exposed only for optional diagnostic readback.
Build93990 succeeds in47.84s. Native74585 exits0:123 original regressions plus
the actual capture,124 clean passes, zero warnings/failures/not-run,25.486892700s.
64 focused Python arithmetic/provenance/30FPS checks pass in2.16s.

Actual `tmp/south-fork-portable-transport-analysis-v1-20260913.json` shows:

- Both transport stages now report zero diagnostic errors and nonzero CFL.
- Stage1 y79/x88 velocity is4.396468162536621m/s, the correctly rounded value
  for the actual subnormal depth (CPU ratio4.396468209799314).
- Transaction diagnostics are `[0,1,0,0]`: downstream pressure-path rejection
  remains. Output is bit-exact to input; no committed time is consumed.
- Transport diagnostic validity is NOT accuracy acceptance. Stage1 thin-cell
  mass rate is spuriously positive2.7712659831088437e-18 instead of the exact-
  reference negative5.169473904368632e-38. Hydrostatic cancellation and remaining
  float wetness/face/flux consumers still require correction. Do not remove
  downstream rejection and promote this partial implementation.

Capture SHA256 `462986dd236372e3e4ca101c678db43dfd79fcc77e4b435299711995ba48593c`.
Portable helper SHA256 `53110fc58cbebff1d68b553a3d6b8aa90715a1060230d8f802c33c924532fa4a`;
transport shader SHA256 `f2cfcdb64d789698f2e90eb6e0d21cf23913eb53ba7d73e1ca8eef8021a09b77`.
Full-history accuracy, normal integration, real-time cost and visuals remain open.
Separately, full-river continuation74818/PID41820 is now live from the verified
6000s checkpoint toward8000s; pilot and actual frame-zero fidelity checks pass.
See `full-river-expanded-checkpoint.md` for current process and audit authority.

Reference-video retry at this revision: both original YouTube watch URLs return
web cache misses. Computer-use skill initialization and the supported browser
entry point both fail before page access with `failed to write kernel assets:
The system cannot find the path specified. (os error 3)`. No footage was viewed.

## Previous: portable step arithmetic, actual replay still rejected

`RaftSimPortableFloat.ush` evaluates Euler and RK2 with an 18-limb 32-bit
integer accumulator and one exact nearest/even FP32 rounding. This needs no
FP64, 64-bit integer support, compiler denorm flag, depth floor or state repair.
RK2 halves the final exact sum, avoiding intermediate half-rounding. Bit-based
validity preserves positive subnormal depth while still rejecting negative
depth/foam, nonfinite values, dry momentum and overflowing velocity. Actual
execution is qualified on Windows D3D12 SM6 only; other backends remain open.
The previous FP64 helper is now an explicitly requested diagnostic control,
not a required production shader permutation on non-D3D platforms.

Independent rational fixtures pass with zero exact-result errors: 4133 Euler
cases (native49054), 8229 RK2 cases (69554), and 8250 validity cases (28135).
Reports are in `tmp/south-fork-portable-float-euler-native-v2-20260913`,
`tmp/south-fork-portable-float-rk2-native-v1-20260913`, and
`tmp/south-fork-portable-validity-native-v1-20260913` respectively.
Fresh full native60293, `tmp/south-fork-portable-step-native-v2-20260913/index.json`,
exits0: 123 passes, zero warnings/failures/not-run,25.264530182s. This includes
the latest validity integration.54 focused Python checks pass in2.02s.

Actual preserved-input capture74008 exits0 with one clean diagnostic pass,
but its transaction is REJECTED. At y79/x88 Euler depth is now the correct
`0x007fffff`,1.1754942106924411e-38. Step invalid-state flag8 clears, giving
diagnostics `[0,5,0,0]`; second transport still flags `[1,0,0,0]` because it
does not yet preserve/recognize this range. Output state is bit-exact to input,
the committed clock and remaining interval are unchanged, and the next retry
step is halved. Rejection is not bypassed. Candidate storage is not an accepted
solution. Stage1 accuracy comparison is intentionally omitted because an
invalid transport stage suppresses reconstruction; earlier21.8243 output
difference is therefore not a valid operator accuracy measurement.

Capture `tmp/south-fork-portable-step-capture-v2-20260913.bin` SHA256:
`11ddd52fbd874118966605553e0a3f2fe0a7a3823d2daffd8fd23d370cd39c01`.
Analysis `tmp/south-fork-portable-step-analysis-v3-20260913.json` additionally
checks FP32 velocity range and bit-exact preservation including signed zero.
Portable helper SHA256:
`20563e49e9d4007223637002b8c76c5ce2b69544b05fc68736ccf787895c5710`.
TotalDepthStep shader SHA256:
`70bac1ecc125bad95af627206b89bac24baf95b16225b9ac85e433ee6dc998e0`.

Next: correct represented-range transport/pressure consumers and complete
hydrostatic cancellation, then repeat the actual transaction and full live
history accuracy/capacity tests. Neither the known0.007430692651 history error,
runtime cost nor visual/gameplay integration is resolved by these unit passes.
The full-river cook84534 is terminal exit0 at6000s; both snapshot audits pass
but settling is false. No cook is currently running; PID32144 is retired.

## Independent comparison and actual stall

`tmp/south-fork-plateau-comparison-v1-20260913.json` completed: accuracy FAIL,
maximum error0.0074306920349256345, relative momentum errors3.460175e-5 and
8.402016e-5. CPU completes the final0.114434224s interval in14 steps with no
rejections. The captured GPU active interval has432 attempts,37 accepted and
395 rejected. Queue exhaustion is not solely a throughput issue.

`export_captured_owner_trial.py` exports the actual evolved128x128 state,
retained two-word clock and observed boundary bracket, not source interiors.
Input `tmp/south-fork-stalled-trial-input-v1-20260913.bin` SHA256:
`5c1b62d4f34486db5fc29d22b1938b456584143a7da6ca519c8c7b1cf2b59bed`.
Source `tmp/south-fork-plateau-owner-v1-20260913.json` SHA256:
`a7d46be2e00dda5289df06614716fad8dcdb4baf54b58bf74df119338ff74e5d`.

Native `RaftSim.Diagnostics.CapturedOwnerTrial` captures existing graph-local
Euler/candidate states and operators. Build succeeded; native64254 completed
with1 clean capture pass, zero warnings/failures. The transaction itself is
explicitly REJECTED. Capture success does not mean numerical acceptance.
Output `tmp/south-fork-stalled-trial-v1-20260913.bin` SHA256:
`3f617146fda316d28fe2d7be1d1760131a081dd1330bdbe5134b5fabd94ed8c1`.

Analysis `tmp/south-fork-stalled-trial-analysis-v1-20260913.json` reproduces
flags[0,5,8,0] at actual time7.5811012804585545s and dt1.589457277e-8s.
The sole invalid Euler cell is y79/x88:

- Input h1.1754943508222875e-38, hu5.168023488631841e-38, hv0.
- First GPU rate [-1.0336046977263681e-37,-4.544210029657536e-37,0].
- Euler h0, hu5.168022928112455e-38, hv0: depth disappears while momentum remains.
- Rejection leaves output exactly equal to input and retains unconsumed time.

This is consistent with first-stage underflow at the smallest normal float32
depth. The separate zero-rate minimum-normal native integration cases both
pass with exact state preservation; that test rules out the initial hypothesis
that RK2 averaging alone necessarily destroys unchanged minimum-normal state.
No speculative averaging change was applied.

## Independent reference also needs a correction

`tmp/south-fork-stalled-exact-faces-v1-20260913.json` evaluates represented
inputs using exact rational arithmetic. Neighbor y79/x87's east final face
should have depth1.1754943508222875e-38; the current double operator gives
1.2828313986166379e-18 through cancellation. Its raw exact face is zero and
the existing partial-face flattening rule applies. The CPU's apparent inflow
must therefore not be used as a trusted target for a GPU patch. The actual GPU
face polynomial has not yet been captured for this specific stalled state.

Next: independently validate range-safe reconstruction and integration, then
rerun full live accuracy/capacity checks. Do not clip tiny cells, add a depth
floor, repair momentum, discard time, or relax gates. Normal display/contact,
breaking/froth, terrain, crew and the rest of the project remain unaccepted.

Focused Python verification:25 tests pass in1.63s, covering desktop runtime
budgets,30FPS CSV checks, captured-state export, integration fixtures and exact
polynomial diagnostics. Full production regression and fresh playable-scene
qualification are not implied by these diagnostic tests.

## Exact reference correction and preserved GPU polynomial capture

`adaptive_hydrostatic_precision.py` now reevaluates cancellation-prone CPU
polynomial faces using exact rational arithmetic on represented input values.
A local floating-point error scale selects arithmetic precision only; it is
not a depth/wetness threshold. Corrected raw faces feed the same one-pass
partial-face decision, and final faces use its explicit flattening mask.
Momentum reconstruction receives the same corrected depth faces. No conserved
state, boundary input, timestep or physical criterion is changed.

Both orientations of the actual y79/x87 stencil reproduce the exact final
depth2^-126. A fresh full-state local diagnostic
`tmp/south-fork-stalled-exact-faces-corrected-v1-20260913.json` agrees with the
independent rational oracle on all eight inspected directed faces. The spurious
CPU inflow disappears: y79/x88 mass rate becomes-5.169474465103799e-38.
This is still different from the GPU rate, not an accuracy pass.

181 focused Python tests pass in21.72s, including the new captured-stencil,
2^-300, exact-oracle, transpose, periodic, constant-ghost, datum-invariance and
conservation tests, plus existing nonlinear pressure, breaking, integration,
live-moving-owner and temporal/exterior-boundary regressions.
Reference-producing manifests now include the new arithmetic dependency hash.
At this revision the new module SHA256 is
`ed2a65a906b62ebc9b7ef25698472b1cdfbf4a02f8271b5d6f5ae0c630f907ac`;
`total_depth_bank_replay.py` SHA256 is
`f98f7f441bdae7098bfad4b42601674b2135ccd1991b3b7139e8a915484eb1a5`.

Build99855 completes successfully in15.17s. Native17673 exits0 with1 clean
capture pass, no warnings/failures. It additionally captures the existing raw
and final polynomial buffers for both actual stages, without new normal-path
allocations. Output `tmp/south-fork-stalled-polynomials-v1-20260913.bin` SHA256:
`f7b09bce191da6bb8963cf9f1797797f97fc7f2585aa7b32d7f2b899505be979`.
The actual transaction remains rejected with the same invalid Euler cell.
Final x polynomials show the upstream y79/x87 cell flattened and y79/x88
retaining surface slope-0.0314788818359375; recovering the very small face
requires cancellation through the complete h/bed polynomial, not just h alone.

Full independent replay70729 completed exit0 against the unchanged plateau
live capture, target7.5811012804585545s. Report
`tmp/south-fork-plateau-exact-reference-comparison-v1-20260913.json` still FAILS:
maximum state error0.0074306926506331195, relative component errors
[3.150162631034972e-6,3.460175022635616e-5,8.402016366855397e-5].
The reference correction removes a real local defect but does not explain the
larger accumulated mismatch. Original reports remain unchanged.
At that checkpoint the full-river cook PID32144 was live at5900s. It has since
finished at6000s (see latest entry); this historical PID must not be reused.

The GPU arithmetic range problem remains open. The installed Unreal compiler
has no exposed denorm-preservation switch in the inspected argument path;
Microsoft documents the DXC command-line option separately in
[Denorm Mode](https://github.com/microsoft/DirectXShaderCompiler/wiki/Denorm-Mode).
No installed engine files were changed and no unsupported compiler flag was
injected. Normal solver promotion, real-time capacity,30FPS and visual acceptance
remain open.

## Bit-preserving GPU arithmetic foundation (not yet solver integration)

`RaftSimRepresentedFloat.ush` now provides explicit FP32 bit decode/encode and
an Euler multiply-add evaluated with an exact FP64 product plus a TwoSum
residual. Integer nearest/even rounding preserves represented subnormals and
avoids the double-rounding error of simply casting a double result to float.
It changes arithmetic precision, not the equation, state range or wet/dry rule.
It is currently used ONLY by the isolated actual-GPU regression, not the
production step or normal display. FP64 hardware support and full downstream
consumer correctness must be accounted for before production use.

The independent fixture generator rounds rational results directly to IEEE
binary32 using integer division/remainders. It includes the actual rejected
depth/momentum, minimum subnormals, normal/subnormal boundary ties, signed
roundtrips, overflow, cancellation, explicit double-rounding counterexamples
and4096 random finite triples. Fixture
`tmp/south-fork-represented-float-fixtures-v1-20260913.bin` contains4133 cases,
SHA256 `27d8574857532ad3e1a70296e85210b7a85a66352ae5a42f049d68404d44491e`.

Build77832 exits0,14.75s. Initial native46351 exits1 before testing because
`half` was mistakenly used as an HLSL variable name; renamed to `midpoint`.
Fresh native98817 exits0; report
`tmp/south-fork-represented-float-native-v2-20260913/index.json` has1 clean pass,
zero warnings/failures,0.084318101s including test overhead. All4133 Euler
results match exact rational references bit-for-bit, all roundtrips match;
ordinary FP32 arithmetic differs on25 cases. Specifically, actual cell y79/x88
expects0x007fffff: new arithmetic returns0x007fffff while ordinary arithmetic
returns0x00000000. This proves the isolated arithmetic defect is fixable in the
project without changing installed engine files. It is not a frame-time or
complete-step qualification.

Helper SHA256 `942328966e3c40ae7bcdc97bd8b3f7d60af902283c9447ed1676746e5604bd66`;
test shader SHA256 `cca5fdd1fe3ee926cf6efc1eaf06e41aa0f2febac7544b87e8105332e5dd6c53`.
10 exact-rounding Python tests pass;44 combined arithmetic, reconstruction,
captured-input and30FPS budget checks pass in1.29s.

Next: preserve these values through the actual transport/pressure/validity
consumers and full RK2 update, then repeat the captured transaction, full live
accuracy, sustained capacity and performance checks. Changing only Euler would
leave the next stage treating a valid subnormal as dry, so the isolated pass is
explicitly not solver integration or gameplay acceptance. The independent
full-history accuracy mismatch also remains open.
