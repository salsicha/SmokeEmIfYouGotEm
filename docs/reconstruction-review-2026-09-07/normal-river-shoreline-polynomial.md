# Cancellation-preserving shoreline reconstruction — September 13, 2026

The queued nonlinear owner's four-interval live comparison now passes the
unchanged local and relative state gates. This resolves the preceding bank-cell
defect, not normal playable-water, moving-window, foam, visual or 30 FPS acceptance.

## Reproduce and isolate the actual failure

The optional `RaftSim.Diagnostics.NonlinearRecordedStages` GPU diagnostic reads
the preserved live owner observations and captures both stages of each accepted
trial: state, transport, geometry, wet graph, breaking fraction and pressure force.
It retains evolved interiors across brackets and requires bit-exact final state
and exact clock equality with its source capture. No production blocking readback
was added. Json use is guarded by both automation and developer-tools macros,
matching the existing conditional module dependency.

Build90099 succeeds after adding the Json dependency. Diagnostic52060 passes:
40 trials / 80 stages reproduce the original live v2 final state bit-exactly.
Trace `tmp/south-fork-recorded-stages-v1-20260913.bin` SHA256
`70030d343ca854a3e37148a9fd5511d44695a28d2a23b6fc02624b26af73b9fe`.
Metadata SHA256 `12df068af15cf41f3cb624af46d6bccc462f4c84c05558b6ef4a0b2ec9d79ba7`.

Independent same-input analysis in `audit_recorded_stages.py` finds maximum
breaking-fraction error4.947186e-6 across all80 stages, below2e-5. At the failing
bank cluster, pressure-force discrepancies are only about2e-9 to6e-9, whereas
transport error reaches0.033111467. Reports preserve both operators rather than
attributing evolved-state differences to the classifier.

`diagnose_recorded_shoreline.py` isolates record18/stage0, y77/x72, y direction.
Represented depth is0.02226150967180729m. Ordinary FP32 MC slope rounds to exactly
twice that depth, producing a zero reconstructed face. Independent FP64 arithmetic
on the same represented inputs produces a genuinely positive1.112120812e-12m
face. The zero changes the polynomial-flattening decision. FP32 CPU transport
matches the GPU cluster within1.788139e-7; FP64 differs by0.033111467.
Report: `tmp/south-fork-shoreline-rounding-v1-20260913.json`.

## Correction and verification

The transport shader retains high/low words through MC depth differences and
face reconstruction. This recovers the small positive face algebraically; it
does not add a depth floor, clamp state, relax tolerances or discard physical
time. The bed, pressure solve and conserved state remain unchanged.

An actual7x7 crop of the recorded bank is appended as a closed-boundary operator
fixture. The original nine fixture payloads remain byte-identical. This fixture
is explicitly not a new live observation or a whole-interval reference.
`tmp/south-fork-shoreline-transport-fixtures-v1-20260913.bin` SHA256
`2fd2940fca1e7a560a55ab286e3c111e2f0d85a6dc82646ac1f8f71315637211`.

Native25737 exits0:90 clean passes in20.898073s, including the appended fixture.
Focused Python parser/owner/temporal/transport/30 FPS-budget suite:38 pass1.21s.
Final diagnostic-macro guard rebuild9483 succeeds16.56s.

Actual normal-map capture92434 exits0 and resumes the verified cook32144
successfully. `tmp/south-fork-live-nonlinear-owner-v3-20260913.json` completes
four intervals /40 accepted trials /10 graphs at exactly0.40000002086162567s.
Its source SHA256 is
`a19cc30262af89483a21b5ea0aed50eb828306d7ff2d2e32f090f3f53ce963f4`.
Independent CPU comparison82224 completes44 steps without retries; report
`tmp/south-fork-nonlinear-owner-comparison-v3-20260913.json` records:

- Maximum absolute state error3.635572405e-6, PASS1e-4 (previous8.712636947e-4 FAIL).
- Relative h/hu/hv errors1.123882e-7 /1.456605e-7 /2.031874e-7, PASS2e-5.
- GPU float inventory residual2.358791e-5m3, recorded without correction.
- CPU final state hash matches the prior comparison exactly:
  `21a3770cde7e6d21a31d35c1721fa9249c9f8e07dc325ed1e98945908502923d`.

Four observations remain retained. No sustained solver capacity is established.
Final-build diagnostic99739 passes1 focused test in1.502442s: corrected trace
v2 reproduces the new live capture bit-exactly over40 trials /80 stages.
Trace metadata SHA256
`84e683f890f579c8e444c0b7ad573c08d5c899f833b616d6a1c4308c975070a9`, binary SHA256
`ed4c4d863f45d15afc22bd205562d2a3425745d55234267f3a994f17ea4023ca`.
Independent operator audit46690 completes: maximum same-input transport error
falls from0.033111467 to9.914187e-5. Maximum pressure-force error is2.239597e-5
at y64/x26, while the original bank-cluster pressure error remains about4e-9.
Some stages still differ by one wet-graph cell. These operator observations are
not additional blanket pass claims; longer-time shoreline qualification remains
necessary even though the unchanged integrated state gates now pass.

Transport shader SHA256
`38916d9083b3dbe347c9b826050ca54e01c528cb33cc39b8495c6230846b7127`.
Final WaterDetail DLL SHA256
`9163de51aaa276ab75183a182973bd6dcdbf8d6f812f720c622bc69ef1b0c1cf`;
Raft DLL SHA256
`86fd2a58c02c9ff720da51f02d8eb0f4c238a3bbc7878bfa6426406d3a62d385`.
Saved normal froth material hash remains unchanged at
`e0c9613bc16125c0f991dc29c6421359cd0fbd6903ab0481657ed544bca55f2c`.

The normal display/contact solver remains unchanged; the new owner is still
diagnostic-only. Latest ordinary measurement remains18.899245FPS/p9570.33ms,
FAIL30. Do not treat this extra-work diagnostic capture as an ordinary benchmark.
Moving-window exchange, foam qualification, shared-surface promotion, visual
review and the remaining scenarios/crew/release work are unfinished.

Both supplied YouTube links were retried again and returned cache-miss access
errors. Neither reference video was viewed; reference-match claims remain invalid.
