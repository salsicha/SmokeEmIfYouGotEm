# Consistent hydrostatic polynomials — September 13, 2026

The longer live-window mismatch exposed a second reconstruction defect. The
GPU fix passes the original native suite plus two actual failing-stage inputs.
This is operator verification, not normal-water promotion or scene acceptance.

## Reproduce before changing the solver

The fixed-window prefix of `tmp/south-fork-live-window-owner-v2-20260913.json`
(SHA256 `49da97748ab0aca18d97ac38e0b486f660e9a74e92aa4cf8c3ac9224b5a58ec4`)
was replayed for all 224 trials to 1.9333334341645241 seconds. Bounded early and
late stage captures both reproduce the original live final state bit-exactly.
Only the captured time range changes; evolution still starts at the first source.
The final partial interval interpolates the actual full observed bracket.

Early operator report `tmp/south-fork-early-operators-v1-20260913.json` finds
maximum transport error 0.004878012786821265. Late report
`tmp/south-fork-late-operators-v1-20260913.json` finds 2.23173944850341 at
interval 11, trial 7, second stage, y89/x42/hu. Independent pressure on the
recorded GPU transport/graph/fraction differs by at most about 2.1e-5 in the
late capture. This does not establish pressure as the cause of the large error.

Ordinary float32/float64 emulation found no local flattening disagreement with
exact rational arithmetic. It did not emulate the GPU's previously compensated
depth polynomial, so it could not rule out a GPU-specific inconsistency.

The optional `-RaftSimRecordedPolynomials` diagnostic exposes existing raw/final
slope buffers without new solver allocations. Schema v2 appends four float4
arrays per stage; its 64-record limit retains the original bounded memory scope.
The v1 reader/layout remains supported and tested. Native capture 5186 exits 0,
still reproducing the old live final state exactly. It captures four trials
starting at 1.2500000651925802 seconds, with both stages per trial.

- Trace metadata: `tmp/south-fork-polynomial-stages-v1-20260913.json`, SHA256
  `e103ba8fedc9a79740c0707a36e7b5b558e7516997ffc3742dcec4d3e601594d`.
- Binary SHA256: `1601f28cadd864fa6fd631e74a0088b996e6df6a302d15ac7237bf5923317a7d`.
- Exact-arithmetic/local GPU report:
  `tmp/south-fork-gpu-polynomial-proof-v1-20260913.json`, record1/stage1.

## Defect and correction

At y90/x42, in the y direction, depth is 0.20644843578338623 m and bed is
6.972808837890625 m. Exact represented-input MC depth slope is
-0.24292628653347492; the stored high word is -0.24292628467082977. The
hydrostatically reduced positive face is exactly zero. The old GPU retains
the nonzero polynomial, including velocity slope -0.8371763229370117, instead
of flattening it. Its neighbor's hu transport rate is 0.4250612258911133,
versus independent CPU 2.6568006743945234.

The earlier depth correction retained the low word through cancellation, but
the bed offset still used rounded depth/free-surface slopes. Mixing those two
polynomials creates a spuriously positive blocked face. The corrected shader
uses compensated MC depth and free-surface slopes consistently for depth,
bed offsets, bed jump and hydrostatic reduction. Final face values are rounded
only after the cancellation. No conserved average, geometry, source, physical
time, depth floor, limiter policy or acceptance tolerance is changed.

## Verification so far

Build20416 succeeds in63.16s; final build85744 succeeds in13.86s. Native35473
exits0: 102 clean tests, zero warnings/failures,25.300985s. This includes
the original exterior cases and two full128x128 recorded stage states with
independently computed CPU exterior transport. New fixture:
`tmp/south-fork-polynomial-exterior-fixtures-v1-20260913.bin`, SHA256
`d965fd0ba33e90f6699edfb6c3a3a2c31e1aaaa00af1913c8667952f7355a935`.
The fixture manifest preserves trace/binary/live-source hashes; no source is
rewritten. Existing operator gates remain relative2e-5, absolute1e-3.

| Recorded stage | GPU/CPU maximum rate error | Relative rate error |
| --- | ---: | ---: |
| First | 0.0000712871552 | 0.00000730857937 |
| Second (previously2.23173945) | 0.0000523328781 | 0.00000728912672 |

Physical bed slopes match exactly; maximum boundary flux differences are
7.62939453e-6 and1.14440918e-5. All54 Python reconstruction, capture-layout,
exact-arithmetic and exterior conservation checks pass in6.27s. The independent
CPU solver was not altered. Six additional exporter rejection checks bring the
final focused Python result to60 passes in4.82s.

The second large late discrepancy (0.1758070064 at interval16/trial1/stage1,
1.8750000977888703s) also passes after the fix. Fixture
`tmp/south-fork-late-polynomial-exterior-fixtures-v1-20260913.bin`, SHA256
`76dd5f677cf742c03f169e99cafaba07bd906925025275d5f13662e2734b1622`, retains
both full recorded stages. Focused native81453 exits0, one clean test in0.101921s;
maximum rate errors6.03497028e-5/5.97238541e-5 and relative
9.41263758e-6/9.1713889e-6. Bed slopes are exact.

Shader SHA256: `634f5fc6fbca86d562ebe52212d71de61fb43ae4b0c7e7df40bc2af8211d326e`.
WaterDetail DLL: `82dfb69a9692fb766fff71162996c9cd5486e65fc7d072d085873ecfe35e2887`.
Raft DLL: `7aa5e8adfda9fbfc10045ca1c9971ecc9999dfa6914cf0484f3d7edb61c772a3`.

## Live first-handoff comparison now passes

Capture4984 exits0 and safely resumes the same cook (both suspension/resume
status0). `tmp/south-fork-compensated-owner-v1-20260913.json` has no owner
failure and completes its requested first move at3.9333335384726524s:
31 intervals,464 accepted steps,72 graphs,13 bounded run-ahead graphs.
The shift is[-16,+2] cells,14112 retained cells,2272 exposed cells, new origin
[-5458,3567]m. Eight observations remain queued, latest4.866666920483112s:
0.93333338201046s backlog. This is not sustained real-time capacity.

Independent CPU comparison64661 exits0. Report
`tmp/south-fork-compensated-comparison-v1-20260913.json` passes unchanged
absolute1e-4 and component-relative2e-5 state gates:

- Maximum state error5.2414382107457413e-5.
- Relative h/hu/hv errors4.011561070466881e-7,4.851224327571882e-7,
  8.316189598453945e-7.
- Window inventory maximum error7.503124820118501e-6.
- GPU float water-balance residual0.0004308843232365689m3.
- Live source SHA256 `e50c60b43d272b698bdecee2998d483be126417211625ecab4e2d3fa8cfe1d48`.

This ends immediately at the first handoff. Evolution after that move, repeated
moves and persistence of departed waves/foam in the outer solver remain to
qualify. A second-move capture is the next check; no normal promotion occurred.

The extended two-move attempt84558 has now exited0 with cook resume0, but the
actual owner report FAILS before its second move:
`tmp/south-fork-compensated-two-moves-owner-v1-20260913.json` reports
`Nonlinear observation queue full; unconsumed time retained, source not discarded`.
It completes48 intervals and one move; published interval time6.200000323355198s,
actual retained GPU state time6.3333336636424065s, latest source8.200000427663326s.
There are16 retained observations,123 submitted graphs,29 run-ahead graphs and
736 steps in completed intervals. No second move or sustained capacity pass.
The independent CPU comparison79125 now completes but fails the local state
gate: maximum0.002101234931135565,94 cells over1e-4, despite all component-relative
norms passing2e-5. See the [post-handoff follow-up](normal-river-postmove-throughput.md).
Retain this failure separately from the passing first-handoff result. Next address
bounded owner service capacity without discarding time or changing source/step
accuracy, then qualify repeated moves and shared playable presentation/contact.

Diagnostic frame audit `tmp/south-fork-compensated-frame-v1-20260913.json`
reports10.58439FPS,p9588.0686ms,maximum3401.2488ms, selected CSV rows60–240.
It includes opt-in owner/capture work and is not an ordinary gameplay benchmark
or an isolated shader-performance comparison. It fails30FPS regardless.
The fresh gameplay screenshot was inspected: broad merged whitewater, rounded
crests, blocky foliage and basic crew remain visibly unaccepted. The diagnostic
owner has not replaced the displayed/contact surface, so its numerical fix is
not presented as a visible water upgrade.

The new solver remains diagnostic-only. Ordinary gameplay
still has no30FPS or terrain/breaking/froth/crew visual acceptance; later rivers,
outer-domain wave/foam writeback, release checks and final commit remain open.
Both YouTube reference links were retried this turn and still return fetch cache
misses. The computer-use skill's supported runtime and the browser fallback both
also fail initialization with `failed to write kernel assets: The system cannot
find the path specified. (os error 3)`. Neither video has been viewed.
