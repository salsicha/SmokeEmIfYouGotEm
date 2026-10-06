# Local signed crest intervals in normal South Fork

2026-09-18. The opt-in candidate from `101aa7ed7` has passed two independent
actual-input comparisons. Normal play now selects the tighter conservative
range; `-RaftSimReferenceCrestInterval` retains the original prepared range.
The unprepared/no-range reference switches still override this choice.
This saves profile evaluations, not triangles or physical updates. The
sampled height function, ordered mesh, shared contact surface, three refinement
levels, 0.5 cm selection and independent 2 cm interior gate remain unchanged.
Terrain, rock geometry, materials, foam density and timesteps are untouched.

## Exactness and component timing

The interval encloses each signed crest/toe/tail term, lateral/edge fade and
local/global cap. It retains the existing spatial index and roundoff margins,
adds explicit floating-point cushions and falls back to the original bound.
It is a local value interval, not a Hessian or approximate replacement height.

The native bound fixture checks 479,520 actual height samples across rotated,
mixed-cap, support-boundary and large-coordinate cases. The changing-input
selection fixture retains exact ordered parents, indices, ownership and XY;
its height calls fall from 65,337 to 65,128. Seven pre-promotion native tests
pass, including the existing independent interior/contact check. These finite
fixtures are evidence, not a formal exhaustive floating-point proof.

Two 300-frame actual FullReach captures at review station 8330 each contain
64 alternating changed-input comparisons after two warmups. The first uses
reference production, the second candidate production. All 128 pairs retain
exact parents, triangles, ownership and expanded XY, and match production
topology. Each candidate times the complete adaptive build, not a subset.
Both share the same immutable prepared sites; preparation is outside both
timers. They do not measure FPS or visual/physical realism.

| Capture / order | Reference mean ms | Interval mean ms |
| --- | ---: | ---: |
| A / reference first | 5.139387 | 4.884744 |
| A / interval first | 5.047540 | 4.791472 |
| B / reference first | 5.180449 | 4.958215 |
| B / interval first | 4.936362 | 4.733562 |

Raw reports: `tmp/south-fork-crest-interval-pair-{a,b}-v1-20260918-pairs.json`.
SHA256 A: `4d401cea81a0c7973c37a772326e93792c9e5b26bedc0053fb943d4f74a83ef9`.
SHA256 B: `2d149e0ea75ed92b95874728624eaf61f232b445fcfe93be1661b87ac6fe7da1`.
Strict summaries: `tmp/crest-interval-pair-{a,b}-review-v1-20260918.json`.

## Whole-frame result is still insufficient

Audit-free reference/interval/interval/reference runs use 1280x720 D3D12,
300 CSV rows and the preselected inclusive rows 60-240. Their frame p95 values
are **43.4283, 36.5798, 41.0295, 40.4931 ms**; average FPS are respectively
27.798919, 36.757246, 29.253796, 30.629607. All FAIL30's unchanged
33.333333 ms p95 budget. The second adjacent comparison is worse overall.
There is no repeatable whole-frame improvement claim: this change is retained
for the repeatable exact same-input component reduction, not FPS acceptance.
Report: `tmp/crest-interval-abba-review-v1-20260918.json`.

Each capture validates the exact identities of cook32728 and pressure audit21256,
suspends only those owned jobs and resumes the same retained handles in finally.
All six captures exit zero without timeout and resume successfully. The largest
observed residual CPU deltas across suspension are 0.125 seconds for the cook
and 0.015625 seconds for the pressure audit; do not call every interval zero.
Generated CSVs, recordings, reports and build artifacts remain ignored.

## Reference and remaining work

[Qweniden's Trouble Maker footage](https://www.youtube.com/watch?v=2XTbOCNDcZQ)
was accessible again through ordinary YouTube playback. Inspected views include
0:01 and samples in the 1:13-1:27 interval: angular exposed shelves, darker
troughs, broken white crests and downstream aerated streaks. This is sampled
visual observation, not full-video review, calibrated flow or measured bed
geometry. No remote video was downloaded. It does not justify treating the
current broad soft engine froth or simplified rock detail as accepted.

## Installed checks and fresh motion

Editor and standalone Development builds succeed in150.21s and314.51s.
Existing C4701/C4305 warnings remain; no warning fix is claimed.
106 focused Python checks PASS (`tmp/crest-interval-installed-python-v1-20260918.xml`).
Seven native D3D12 checks PASS, zero failures/not-run, including the fine-crest
fixture now wired through the default interval callback. In both geographic
orientations,110,448 independent interior samples have maximum error
0.49144486cm against the unchanged2cm gate; actual triangle anchors have
maximum error below1.31e-10cm. Native report:
`tmp/crest-interval-installed-native-v1-20260918/index.json`, SHA256
`0508f70f7d4818b6eeede0de5912d7573f989aefdf42d17dbe76ace3834dfb76`.
These scoped checks do not close the13 previously documented physical failures.
The same fine-crest fixture also passes under `-RaftSimReferenceCrestInterval`,
confirming the retained control path: `tmp/crest-interval-reference-native-v1-20260918/index.json`.

The final ordinary audit-free default capture averages35.365922FPS with
p9538.6731ms: **FAIL30**. Same1280x720D3D12,300rows, fixed60-240 interval.
Report:`tmp/crest-interval-installed-profile-review-v1-20260918.json`;
CSV SHA256:`04d478ddf4d41b46413da2045d987110da446d909278842996a6a51ab57e861a`.
This is neither packaged/sustained acceptance nor a controlled improvement
comparison against a differently evolving earlier trajectory.

Fresh normal-game motion records `tight_interval=1` without an opt-in flag.
Video:`unreal/Saved/VideoCaptures/RaftSim_20260917-210408.mp4`, SHA256
`d8d94e8942eeaa9e2735114b115a7321f960d02d333b8544cc481de05f011788`.
All474 encoded frames decode through15.766667s;41 adjacent frames are exact
duplicates. Encoded30fps is not measured game FPS. Decoder report:
`tmp/crest-interval-installed-decoded-v1-20260918/report.json`.
Inspected decoded3s/13s frames and startup PNG021 still show broad blurry
white patches, smooth green faces and tuft-like spray. No convincing-froth or
reference-match acceptance. Sparse inspected frames plus a complete decode
are not continuous visual tracking or a full-traversal review. Both recording
and final profile exit0, no timeout, same-handle job resumption succeeds.

The full ordered scene, physical breaking, froth, crew, regression and release
queue remains OPEN. Nonlinear runtime is OFF; Troublemaker remains a rapid
inside South Fork, never a menu scenario. Next physical work must complete the
conservative moving-front/force closure on the original two-pole model and
qualify actual crest breakup and advected froth, not hide them with density.
