# Bank endpoint ray spacing — September28 UTC

Status: normal South Fork source correction and nine rendered native tests
complete. One v23 package owner is waiting for existing lossless old-stage
compression. NOT packaged delivery, visual acceptance or a20FPS pass yet.

## Reproduced defect

The v22 actual contact report
tmp/sf-v22-motion-20260928-contact.json, SHA256
bff4c53b8ad86c0003b40036862ae8c0e8e6aeb3a2e238e5e70ab0ff4dd2b74f,
retains a three-wet-corner point at world XY
(-542609.867033,-360212.234553)cm. Its source-cell coordinates are
(.9013296732491654,.12234552688732947); cached donor-weighted stage minus
unchanged bilinear bed is -0.044159120879m. This is not a positive film.

The shoreline algorithm correctly finds zero-depth roots on radial rays,
but previously interpolated the raw endpoint vectors to choose those rays.
One endpoint is only0.008275886505 cell lengths from the dry corner. Its
short radius biases nearly every ray toward the other, longer endpoint.
The final chord consequently spans from approximately(.342198,.107591)
to(1,.008276). Its midpoint has signed depth-0.079170749365m and the actual
submitted/refined triangle covers the retained raw-dry probe.

This is a spatial sampling defect, not evidence to change wet thresholds,
hydraulic bed, cached time, physical depth or the water solver.

## Correction and limits

RaftSimWaterBankContour::Point now interpolates normalized endpoint directions.
Each ray retains the same safeguarded cubic zero-depth root calculation;
shared edge endpoints,16 segments, wet masks, positive films, attributes,
temporal policies and physics remain unchanged. Explicit positive-length
normalization avoids a small-vector epsilon deleting a short endpoint.
The existing normal South Fork path consumes this helper; no opt-in is added.

The retained probe is outside the new generated triangles. On the retained
cell, an independent midpoint calculation still finds approximately-0.004796m
signed depth on another finite chord. This is a remaining error, NOT a relaxed
quality gate or a certificate of dry exclusion everywhere. The other v22
two-wet-corner failure is unchanged. Further conservative contour work is
required; do not declare the shoreline repaired as a whole.

## Verification and owners

Editor build123.29s succeeds. Native session64925/wrapper34480/native9828
completed10:02:41.9487101Z, exit0; nine tests pass with zero warnings, failures,
not-run/in-process tests and no runtime error/fatal entries.

New BankEndpointSpacing test uses the original captured triangle to reproduce
coverage, then the production builder to exclude that point under compact/
reserved storage, reflected Y and rotated coordinates. It verifies all new
nodes remain on the original zero-depth curve, unchanged16-segment count,
and ray invariance when endpoint lengths scale down to1e-12.
Existing CurvedHighBank, BreakingHeightKey/Cache, ShorelineCrestTargetCache,
SelectiveDetailEdges/Mode, ShorelineFineCrest and CrestHistory also pass.
These are geometry/cache regressions, not full river or visual acceptance.

Recipe: tmp/verify-bank-endpoint-spacing-v1-20260928.ps1.
Receipt: tmp/bank-endpoint-spacing-v1-20260928-process.json.
Native report: tmp/bank-endpoint-spacing-v1-20260928-native/index.json.
Seven frozen inputs unchanged, including protected user water-surface test
SHA256 d9abdd3643882d192e41af879eef023ed1e58f12a39d26698e42cb0f0773e8f3.
Initial recipe preflight accidentally included source files in its
must-not-exist list; corrected before any build launched.

Package session47138/wrapper40972 started10:03:15.7740713Z:
tmp/package-bank-endpoint-spacing-v23-20260928.ps1 and
tmp/bank-endpoint-spacing-v23-package-20260928.json.
It waits for exact compression owner34608, verifies every retained hash,
requires14GiB free and no competing native owner, then builds a fresh normal
v23 stage and checks staged closure and13 frozen source/payload inputs.
Do not launch a duplicate package or edit frozen source while this owner runs.

Compression session32261/wrapper34608 uses
tmp/compress-v4-to-v7-and-v20-staged-data-20260928.ps1; receipt
tmp/v4-to-v7-and-v20-staged-data-compression-v2-20260928.json.
Only old v4(September26),v5-v7(September27),v20(September28) runtime-data
copies/PDBs are eligible. Every file is hashed before/after; nothing deleted
or hardlinked. Current v21/v22 stages are untouched. Initial Windows
PowerShell5 enumeration stopped on a long path before modifying any file;
its failed receipt is retained. Same scope now runs under PowerShell7.

Original physical replay33152 remains live at index1 after index0 completed.
No replay physics module or captured input was edited; no duplicate replay.
After package completion, verify actual normal menu and rapid motion/contact
and inspect the new video. Isolated20FPS timing still requires the existing
replay to finish and pass full provenance/report checks. Keep flat foam,
weak breaking, two-wet-corner and finite-chord failures open. South Fork
remains first; no Colorado/Pacuare/Futaleufu advancement or push.
