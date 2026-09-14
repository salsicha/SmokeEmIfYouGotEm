# Exact-flat breaking-front continuity — September 13, 2026

This follows [post-handoff accuracy isolation](normal-river-postmove-throughput.md).
The previous turn made progress: tested endpoint observations and the5600s
state/artificial-bank audits. This turn locates and corrects a concrete front
partition defect. Full gameplay acceptance remains unproven.

## Error onset on the same captured source

CPU history97458 exits0. `tmp/south-fork-recorded-state-history-v1-20260913.json`
contains17 exact-time/origin comparisons against independently recorded GPU
stage inputs, with no interior resets and unchanged default CPU timesteps.
Source SHA256 remains
`d783ecd5d8cb48972ad3262c61a17dcdef9868fd766cb7dbf89e96bf17dcc0bf`.
The actual handoff3.933333538s passes: maximum4.967095637e-5. Some later
single-cell errors transiently exceed1e-4; the broad late failure is localized
between6.066666983s (maximum4.427939857e-5, zero failing cells) and6.200000323s
(maximum0.002505139630,78 failing cells). Final6.333333664s remains a fail.

An isolated CPU control initialized from the exact GPU state at interval48's
start independently reproduces maximum0.002503290851/78 failing cells at its
end. Report `tmp/south-fork-isolated-interval48-v1-20260913.json`. This reset is
ONLY diagnostic, never normal evolution or a replacement acceptance result.

Every independently restarted one-step control is accurate to1.194e-6 or better.
Keeping the CPU control between the16 recorded physical steps exposes the
switch at trial9/begin6.141666986979544s: input error3.221053326e-6,
first-stage dispersion-fraction error1.0, Euler error0.007985763805 and final
error0.003938242151. The same-dt control deliberately uses recorded float dt;
it is not the full-history default-dt gate. Reports and retained CPU states:

- `tmp/south-fork-interval48-steps-v1-20260913.json`
- `tmp/south-fork-interval48-retained-steps-v1-20260913.json`
- `tmp/south-fork-interval48-retained-states-v1-20260913.npz`
- `tmp/south-fork-interval48-front-switch-v1-20260913.json`

## Concrete defect and correction

At x32/y37 the represented GPU free-surface jump is exactly0; independent
CPU evolution gives-7.101483845e-8m. Adjacent jumps are both negative.
The old strict-sign detector splits the GPU front at that flat face, selecting
peak y38/depth1.693166971m instead of y35/depth1.227572013m. Both select
trough y71/depth0.60529065m and steepest face y63. The spurious peak changes
band width and flips y56–58/x32 between dispersive and fully hydrostatic.

CPU and GPU now bridge exactly flat connected internal faces only when their
neighboring nonzero slopes have the SAME direction. A plateau is not an
extremum. Opposing signs, dry/disconnected edges and all-flat components stay
separate. No epsilon, smoothing, depth/velocity clipping, threshold change,
time discard or tolerance relaxation is introduced. Actual nonzero slopes,
however small, keep their sign. Python and GPU implement the scan independently.

The physical criteria and7.5-depth-difference band follow the already selected
[Filippini et al., section6](https://www.math.u-bordeaux.fr/~mricchiu/GN1D.pdf).
Plateau treatment is our discrete raster correction, not a newly claimed
validated2D formulation from that paper.

The corrected independent detector on the two preserved trial9 inputs lowers
fraction difference1.0 to3.380646149e-6, with zero switched cells and matching
69 fronts/908 breaking cells. `tmp/south-fork-plateau-front-switch-v1-20260913.json`.
All51 focused Python tests pass. Fresh fixtures add connected plateaus,
periodic translation, axis transpose and the actual failing128x128 stage.
Fixture `tmp/south-fork-plateau-breaking-fixtures-v1-20260913.bin` SHA256
`f25a2efc4242a223c35f2b369935752fe7ba194e646ae194be479da1bdf8cab7`.
Full native regression41724 exits0 against ALL original fixtures:122 clean
passes, zero warnings/failures,32.281806946s. Additional native69889 exits0:
one clean test covering20 cases, including four plateau/translation/transpose
cases (fraction error0) and the actual failing stage (fraction error3.9935112e-6,
69/69 fronts and1532/1532 truncated runs). Original fixture checks were not
removed to accommodate the added cases.
Corrected shader SHA256:
`b81e5a8a4864d324039b4dead3801b256054db7bdba9ff4cd9ce97d057bc646b`.
Fresh actual moving-owner capture25924 exits0, suspension/resume both0.
With16 slots/two requested moves, the actual owner AGAIN fails queue capacity
after57 completed intervals and one move. It retains all time and16 observations.
Completed native time7.466667056s, actual state time7.581101280s,
remaining0.0188991148s and next proposed step1.589457277e-8s. Latest source
9.466667160s;888 accepted trials in completed intervals,142 graphs/70 run-ahead.
Output `tmp/south-fork-plateau-owner-v1-20260913.json`, SHA256
`a7d46be2e00dda5289df06614716fad8dcdb4baf54b58bf74df119338ff74e5d`.
Independent CPU20724 completed with a FAILED accuracy gate; report
`tmp/south-fork-plateau-comparison-v1-20260913.json`.
Maximum state error0.0074306920349256345; relative component errors
[3.150166259852569e-6,3.460174764242242e-5,8.402016170207015e-5].
The plateau correction is not sufficient for qualification. A subsequent
[captured-state diagnostic](normal-river-thin-state.md) isolates a separate
Euler-stage numerical failure and reference face cancellation.

Diagnostic frame report `tmp/south-fork-plateau-frame-v1-20260913.json` measures
8.733419651FPS over rows60–240 and fails30FPS. Capture/serialization is included;
this does not replace ordinary gameplay's18.899245FPS/p9570.33ms failure.
The fresh screenshot was inspected: normal displayed water still has broad,
merged white patches and rounded crests, with blocky foliage/basic crew. The
corrected solver is diagnostic-only; no visible-wave integration is claimed.

The unnecessary earlier gap capture32992 exits0 and reproduces the old failing
state exactly (36 trials/150,996,672 bytes), but has one descriptor-cache
warning. It is not a clean native pass; it did not locate the final defect.

## Remaining acceptance

Fresh actual moving-owner comparison, sustained capacity and30FPS are required
after the correction. Normal display/contact integration and convincing
breaking/froth remain open, as do terrain, crew, later rivers and release work.
The5800/local36000 complete snapshot passes both audits but is still settling.
Next5900/local38000 requires a complete snapshot before both audits.

Reference-video retry: the computer-use skill's supported initialization and
the browser fallback both fail with missing kernel-assets path (os error3).
Direct fetches of ZEG1kvjNI30 and2XTbOCNDcZQ return cache misses. Neither video
was played or used as new visual evidence.
