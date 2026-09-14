# Native CG fusion experiments and separate range controls

September 14, 2026. Both fusion experiments preserve all actual-source solution
and diagnostic bits, but both are SLOWER than the separate schedule. Neither
is enabled by default or promoted into production. Desktop target remains
30 FPS; the original 1.6 ms/tick component gate and 120 Hz physics are unchanged.

## Actual-source comparisons

Original immutable six-case fixture SHA256:
`4e53b1bab29626585d3d017408d9043956fa61f5077cc55cd4087f1229a6feb4`.
Both experiments retain FP64, every coefficient and row accumulation order,
original initialization, all 40 CG iterations and the final direction diagnostic.
No approximation, precision reduction, state repair or weakened residual gate.

Direction fusion combines the direction update with the next sparse action,
using separate immutable input/output direction buffers. Its schedule has
286 compute dispatches instead of 325. Recomputing updated directions during
sparse loads did not improve measured cost. Build43760 and wrapper71788 ended
exit0; engine26132 exited and its dedicated sampler39860 stopped.

Reduction fusion combines phases4+5,7+8,9+10 into phases11,12,13. Every group
repeats the same small final reduction tree. Immutable partial/control ping-pong
buffers and 16-byte diagnostic snapshots preserve cross-group ordering and error
decisions. An explicit group barrier protects the final sum before shared scratch
is reused. This uses205 compute dispatches PLUS120 diagnostic-copy passes per
solve; the copies are inside solve timestamps. It also did not improve cost.
Build69934 passed; follow-up83463 fixed timing arrays/loops for all14 phases and
passed17.37s. Wrapper64076 ended exit0; engine36420 exited, sampler12100 stopped.

Each experiment runs ten alternating schedules on six actual-source cases,
16 independent initialized solves per graph, archiving EVERY solution and all
diagnostics. All960 outputs per experiment are bit-exact, all60 batch comparisons
pass, and both GPU automation tests succeed. Final six GPU AND CPU solutions and
diagnostics independently match the hash-verified original PASSED factored-operator
audit's native binary. Timing fields are excluded from bit comparisons.

Post-warmup results below contain56 samples per pole/variant (repeat>=2,
resident solve>=2). p95 is empirical nearest-rank solver duration, not frame p95.

| Experiment/pole | Separate median / p95 ms | Fused median / p95 ms |
| --- | ---: | ---: |
| Direction / larger |3.796 /4.159|3.9875 /4.656|
| Direction / smaller |3.903 /4.267|4.048 /4.672|
| Reduction / larger |3.9205 /4.112|4.1805 /4.667|
| Reduction / smaller |3.8565 /4.370|4.2205 /4.619|

Raw artifacts use labels `south-fork-reconstructed-cg-fused-direction-v1-20260914`
and `south-fork-reconstructed-cg-fused-reductions-v1-20260914`:
`tmp/LABEL-{native.bin,gpu.csv,process.json}`,
`unreal/Saved/RaftSimValidation/LABEL/index.json`, and
`unreal/Saved/Logs/LABEL.log`. Native hashes respectively:

- `d2d71bbe792b54b3ab8fcbc0d90ccd8db403998d417117a588bc6a0494e11401`.
- `5fc72bbbbeb054c9ef6b40fb246575a98828c233430bce56e5a5ca5b2dd6555b`.

Direction telemetry has846 complete rows; reduction telemetry442. Each retains
one incomplete trailing row after testing. Complete rows bracket all60 host
windows. Post-warmup captured inside-window observations: direction15 samples,
P0/P3, memory6001/7001MHz, SM1290–1980MHz,48–49C; reduction16 samples, P0/P3,
memory6001/7001MHz, SM1342–1785MHz,46–47C. No GPU settings or original jobs were
changed. These shared-load observations do not isolate a single hardware cause.

## Explicit synthetic controls

Added opt-in `RaftSimReconstructedCGControl=zero-rhs|identity-range`. These mutate
only in-memory test copies, never the immutable fixture. Logs explicitly label
SYNTHETIC; separate binary magic0x52534343 prevents the original factored-source
auditor from accepting them as actual-source output. Original output magic is
unchanged. Both original arithmetic tests still use the unmodified fixture.

Zero forcing uses the six original operators with exactly zero RHS. Identity
range uses identity operators with signed power-of-two/zero rows at exponents
-1074,-1022,-600,0,600,1000, including the smallest positive binary64 subnormal.
Expected GPU AND CPU solution bits, iteration count, active and zero flags are
checked explicitly, in addition to the unchanged residual checks. These simple
controls do NOT qualify a mixed-range physical operator or evolving shoreline.

Build82829 passed16.53s. Independent audit script
`physics/scripts/audit_reconstructed_cg_controls.py` checks every expected bit
and exact diagnostics with no tolerance. Six unit tests pass0.167s, including
rejection of lost subnormals, false zero termination, original-source magic,
incorrect shapes, truncation, trailing bytes and wrong control labels.

Zero-control wrapper39911 ended exit0, engine29088 exited, sampler7772 stopped.
Independent six-case audit passes: zero iterations, inactive, zero-RHS flag1,
GPU/CPU exactly positive zero. Output hash
`70dc5f619f364df434512aa2fc0109d040b4206202c0413fdb5e05367ebb328a`;
report `tmp/south-fork-reconstructed-cg-zero-control-audit-v1-20260914.json`.
Identity-range paired run26571 ended exit0; engine22060 exited, sampler19472
stopped. All six GPU/CPU expected solution bits match, exactly one iteration,
inactive and zero-RHS flag0, including exponent-1074. Native hash
`14bf02991b4fd59d8762145f7ef5ff382ba4b68288c26ba9663055383aa0d595`;
report `tmp/south-fork-reconstructed-cg-range-control-audit-v1-20260914.json`.
Both controls execute60 alternating baseline/reduction-fused solves, all repeated
bits exact and all checks pass. Both automation tests succeed in each run.
Direction fusion was not re-tested with these synthetic controls.

## Open scope

No native geometry/rate assembly, evolved original-start history, outer wave/foam
coupling, raft contact, gameplay image or 30 FPS acceptance follows from these
tests. The main original replay remains live; latest observed accepted time
0.531213540253s has speed109.68494m/s and42 rejected trials in its current
interval. This is a concerning growth trend, NOT stability acceptance. Preserve
its original dependencies and full9.066667139530182s/two-owner-move target.
The separate diagnostic prefix is not a replacement or spliceable history.
All16 recorded source dependencies for each live history were re-hashed and
remain unchanged. Both histories still lack terminal reports. Cook input and
executable hashes also still match the verified8000s continuation.

The complete8100s river checkpoint passed BOTH state and artificial-bank audits;
it remains unsettled (outflow103.3646 vs inflow45.3070m3/s), not a runtime source.
Next: diagnose the original-history velocity growth from retained evidence
and pursue native construction/evolution qualification. Do not keep treating
dispatch fusion as a demonstrated performance improvement. The unchanged separate
slot-major schedule remains faster in these comparisons but still over budget.
