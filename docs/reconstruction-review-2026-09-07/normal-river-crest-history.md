# Exact-coordinate crest-history reuse — September 12

Status: integrated,63 native tests pass; ordinary gameplay19.625346 FPS still
fails30. Not performance or visual acceptance.
The desktop target remains30 FPS with unchanged quality, physics timestep,
contact/geometry tolerances and solver/memory gates.

## Evidence and implementation

The preceding default finite-depth profile measured20.043179 FPS, p9558.8251ms.
Water actor CPU mean36.591ms versus GPU16.164ms identifies significant CPU work;
these overlapping/nested scopes must not be summed. A fresh instrumented
baseline (session16622) exits0 and safely resumes identified cook29104.
CSV `south-fork-crest-normal-baseline-v1-20260912.csv` is preserved; warmed
rows100–250 average19.235450 FPS. Stage logs for engine frames100–250 (a different
index domain, not asserted to be the same CSV interval) show vertex/history work
averaging6.4154ms on70 geometry-reuse calls and4.7459ms on81 rebuild calls;
normal work averages1.7061/1.5466ms respectively. This directs the next change
to temporal-history lookup rather than normal reconstruction.

`FRaftSimCrestHistory` caches exact XY-to-index ownership, not heights. It compares
every current midpoint XY. Stable coordinates use dense previous-value indices;
changed coordinates use the old coordinate-map lookup, then rebuild ownership.
Duplicate coordinates deliberately use the last previous writer, including
boundary-zero values, as the original `TMap::Add` loop did. Every target, blend
and corrected vertex height is recomputed on every call. Source vertices remain
untouched. No cadence, density, tolerances, crest dimensions, foam or GPU detail
physics are changed. `-RaftSimMappedCrestHistory` disables the dense branch for
same-binary comparison. Keys are bounded to the current midpoint set; capacity
can retain the peak window allocation, not accumulate old windows.

The independent native fixture compares against the original serial map loop
over36 frames with duplicates, different per-duplicate targets/boundary flags,
translation/reordering, growth/shrink, changing source-prefix sizes, reset,
empty midpoint sets and alpha0/1/intermediate. Exact positions/corrections and
untouched attributes are required; there is no loosened numeric tolerance.

Build48405 succeeds in157.98 seconds. The only warnings are existing D6 damping
double-to-float conversions. Native4167 exits0; the actual JSON report records
63 successes,0 warnings/failures/unrun in16.1832 seconds. The new test covers
694,534 vertices and25 dense-path calls, all exactly matching the serial loop.
Report: `unreal/Saved/RaftSimValidation/south-fork-crest-history-regressions-v1-20260912/index.json`.
Raft DLL SHA256 `3aad3636cd74a188ad89b219b15bc3384ba7485882c470c54c2b687a6de7819e`;
main `4b9065ec3a73d64dc646457b2df1781f7c1e1ea7e759a005d9b0a2d5b6795f00`.
WaterDetail remains ef1d7f74… and Water f992dec3…; map remains db3080cc….

## Actual gameplay and performance

Instrumented candidate7843 exits0 and resumes the cook. Engine frames100–250
contain52 reuse/99 rebuild calls versus baseline70/81. Reuse vertex/history
mean falls6.4154 to3.2817ms; rebuild mean is4.8399ms versus4.7459ms. This is
evidence of cheaper stable-coordinate work, NOT overall FPS improvement.
The candidate's CSV rows100–250 average17.776312 FPS versus19.235450 baseline;
more geometry refreshes and differing trajectories prevent sole-cause attribution.
All evidence remains preserved in `tmp/south-fork-crest-history-performance-v1-20260912.json`
and the baseline report. Neither run meets30 FPS.

Fresh ordinary-play20171 (no stage logging/review flags) exits0, safely resumes
cook29104, and records19.625346 FPS, frame p9574.679ms, GPU mean16.13ms. This
also does NOT establish an overall improvement over the previous20.043179 FPS
capture. Metadata correctly records30, with1280x720/D3D12/Development unchanged.
Report: `tmp/south-fork-crest-history-default-performance-v1-20260912.json`;
CSV SHA256 `a1b60b01cdf2783453967bfb5f3791bd264ee7cd916018be942343a42a7a80b7`.
69 of151 warmed rows use the dense history branch. Ordinary final PDE backlog
6.235ms;653 paired commits/1 hold, maximum queue age0.4s includes startup and
screenshot, not warmed latency acceptance. Both profile PNGs were inspected:
large rounded crests and broad soft/merged whitewater remain visibly unfinished.
Map db3080cc…, primary material26aa5029… and saved game181d1e57… rehash unchanged.

Current-build actual-game45220 exits0 and produces8 PNGs;000/007 were inspected.
No continuous playback is claimed. Paired sequence100 has2,021 wet contact
points,959 with nonzero detail (maximum7.02113cm). Maximum independent support/
carrier error4.756047474e-5cm;4,226-query GPU payload error5.960464478e-8 passes
on the same sequence. No dry/unavailable contacts. Actual submitted crest audit
samples1,550,016 points, maximum target error0.600685767cm within unchanged2cm,
fine tracking0.000253439cm and source change0. Source transport UV3/bulk UV1
errors are both0 over50,625 source vertices. These are NOT calibrated momentum,
full traversal, render-latency, breaking-wave or froth acceptance.
Reports: `tmp/south-fork-crest-history-{contact,gpu,crest,transport}-v1-20260912.json`
(crest mesh additionally ends `.cartesian-mesh.json`). Images:
`unreal/Saved/Screenshots/south-fork-crest-history-v1-20260912_000.png` through007.
Cook29104 remains live at local11800/time2590s;2500 remains the last independently
audited snapshot,2600/local12000 next. Runtime600s data has not been promoted.

## Reference access

A fresh browser attempt for John Elkins video `ZEG1kvjNI30` again fails before
navigation: `failed to write kernel assets ... (os error 3)`. Direct retrieval
of that link and Qweniden `2XTbOCNDcZQ` both returns cache misses. Neither video
was newly viewed. The larger smooth macro-crest and soft/merged froth problems
remain unaccepted; this CPU optimization is not a substitute for their physical
and visual reconstruction or for the full remaining river/crew/release scope.
