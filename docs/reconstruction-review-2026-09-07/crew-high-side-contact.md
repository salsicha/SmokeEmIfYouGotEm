# High-side foot-contact trial — September 23

Status: **rejected for normal play**, not crew or South Fork acceptance.
Latest follow-through: [prepared grounded stances](crew-prepared-stances.md)
removes measured full searches from the short command capture, while retaining
setup cost and the unresolved whole-body/transition/performance gates.
Update: the subsequent staggered v3 resolves the scoped sole-support failures
below, but remains opt-in pending normal command motion, transition and cost.
The ordinary rest/stroke/brace fit remains enabled. The unqualified high-side
branch requires `-RaftSimReviewHighSideContact`; it is not a delivered scene
improvement. No captured geometry, terrain, collision, installed4950 hydraulic
fields or nonlinear enablement changed. Colorado/Pacuare/Futaleufu remain queued.

## Actual failures and bounded correction

The authored high-side shifts hips28cm and feet14cm toward the command. The
candidate uses paired floor support for the opposite seat, and searches for a
full tube-crest footprint on the commanded side. Both legs retain their rest
segment lengths. A supported but unreachable candidate is rejected. Full boot
bounding footprints retain a4cm support-height span limit; no floor plane or
one-corner tube fallback is invented. Action changes invalidate the stance.

v1 searched only inward from a seat positioned on the tube's inner shoulder.
All five outboard crew/action combinations failed; independent actual tread
measurements include39.93cm penetration in authored fallback. Native report
`tmp/crew-high-side-native-v1-20260923/index.json`:3 passed,1 failed. Engine
exit0 did not mean test success. Session86508 is terminal.

v2 searches both inward and outward up to48cm, without relaxing the support or
reach criteria. The two middle-seat outboard poses now solve. Both bow-seat
outboard poses and the starboard guide still fail (27 native assertions, initial
pose plus eight motion samples for each of three combinations). Report
`tmp/crew-high-side-native-v2-20260923/index.json`:3 passed,1 failed.
Editor v2 build succeeds in34.65s. Test/capture session75480 is terminal exit0.

Independent v2 source-tread audit retains all50 boot/action records against
15,064 actual uploaded solid triangles. All samples have a solid below them;
this does NOT mean nonpenetration. The six unsolved high-side boots still have
negative minimum clearance, worst−39.93cm. The two newly solved middle-seat
pairs have minimum clearances0.10–1.14cm and maximum gaps no larger than2.97cm.
These limited passes are not grounds to promote the partially failing solver.
Report: `tmp/crew-high-side-tread-v2-20260923/report.json`.

## Capture correction and limitations

The v1 six PNGs are byte-identical stale captures, not six accepted views.
They are preserved. The diagnostic now yields actual editor frames between
pose/camera changes, scene capture and export, rejects duplicate image hashes,
has a120-second callback bound, and records completion/error. Launch it via
`-ExecCmds="py <absolute script>"`, not `-ExecutePythonScript` (which exits before
callbacks finish). v2 completes six distinct images; the starboard rear view
was inspected and shows unresolved crew/hull intersections. A posed editor
fixture does not establish animation, normal-game motion, collision or cost.
Four independent projection regressions pass; initial restricted dependency
access failed, then the same tests passed with dependency read access.

The normal-scene capture helper now supports `-StartupHighSide` exclusively
with `-StartupRenderReplay`, rejects simultaneous paddle/high-side input, and
confirms actual command issuance from the engine log. The command goes through
the normal `IssueCrewCommand(HighSide)` route. New high-side guards and existing
paddle guards pass. This helper capability has not yet been exercised in a
normal-game high-side recording; request flags alone are not execution proof.

## Next bounded work

Do not rerun the unchanged v1/v2 failures. Resolve a reachable, fully supported
stance for bow curvature and the guide, including boot orientation if needed,
then rerun the opt-in native gate and independent actual tread measurements.
Keep the full high-side assertions enabled for that trial. Do not enlarge the
support-gap limits to obtain a pass. Transition motion, normal command-side
stability, garment/limb collision and isolated cost need qualification before
normal promotion. Existing normal p95 around40ms still fails33.333333ms.

## Default-exclusion rebuild

The final normal build excludes the failed trial explicitly; default native
tests check that only rest/stroke/brace claim a solved stance. With the review
flag, the same tests still require successful high-side contact, so the failed
trial's gate is not waived. Editor rebuild succeeds in14.43s and Game in122.12s
(`tmp/crew-high-side-exclusion-{editor,game}-v1-20260923.log`); session97113 is
terminal exit0. An unrelated pre-existing uninitialized `Current` warning in
`RaftSimDetailSourceFootprintTest.cpp` remains. Rebuilding this exclusion does
not constitute a new visual improvement or packaged-release acceptance.

Final default native report
`tmp/crew-high-side-exclusion-native-v1-20260923/index.json` confirms4 succeeded,
0 failed/warned/not-run/in-process; engine session15197 is terminal exit0.
This verifies the scoped default exclusion, NOT successful high-side contact.
No normal-game high-side movie or fresh cost measurement was run for this
rejected candidate. Final process inventory contains only original cook36692
(start2026-09-23T18:34:26.9266904Z); no engine/build job remains running.
The separate16150s hydraulic finite/dry-bank audit is recorded in
[the existing continuation record](cartesian-continuation-15000.md); its
outflow still exceeds inflow, so those fields were not promoted.

## Geometry-derived staggered stance — subsequent September23 pass

Exported the actual uploaded sections, production boot bounds/scales and
rendered rest-joint coordinates without saving any assets:
`tmp/crew-support-geometry-v1-20260923/geometry.json`. Export session78464 is
terminal exit1 despite writing the complete five-crew artifact and logging
`CREW_SUPPORT_GEOMETRY exported`; no engine/Python Error or traceback is present.
Do not describe that process as exit0. The JSON independently retains section
indices/points and all five pairs of boots and six rest joints per crew.

An exact triangle-query analyzer (20cm spatial bins, no height resampling)
searched along±80cm/lateral±60cm. Rigid paired translation has zero feasible
candidates at port bow and guide, while each foot independently has hundreds.
Nonoverlapping staggered pairs exist for all five crew under unchanged4cm
support span and1cm anatomical reach margin. Analysis requires an unrotated
exported raft explicitly; it is a placement hypothesis, not runtime acceptance.
Eight projection/query regressions pass, including bin boundaries, triangle
winding, highest-overlap selection and missing support. Retain both
`tmp/crew-support-stance-{v1,v2}-20260923.json` (source hash included).

The opt-in runtime v3 searches independent feet bounded to±64cm along and±48cm
lateral, then enforces left/right order,1cm boot-box separation and no more than
10cm foot-height difference. Rest/stroke/brace and opposing-seat floor fits
retain their path. No hull shape, physical mass or upper-body pose is changed.
Editor build15.60s; `tmp/crew-high-side-stagger-native-v3-20260923/index.json`
has4 succeeded,0 failed, total16.93s. Tread/capture session3719 is terminal exit0.

`tmp/crew-high-side-stagger-tread-v3-20260923/report.json` contains50 solved
boot poses,9,600 actual tread vertices,0 unsupported points,0 penetration;
per-boot minimum gap0.1074359–1.3527533cm, maximum tread gap3.5921189cm and
maximum body/boot anchor difference8.30e−14cm. Six distinct posed images finish;
port-front and starboard-rear views were inspected. This fixes the scoped
footprint search, not whole-body/garment collision or the awkward high-side
upper-body pose. It is not a normal-play motion or performance result.

Native binding timestamps show second-scale initial searches. An exact,
revision/relative-mesh-transform-keyed support-triangle index is being qualified
to remove repeated full-mesh scanning before normal command review. Its native
regression compares every returned floor/solid sample exactly to the original
scanner across broad-grid/vertex/bin-edge probes, moved-mesh and rebuilt-mesh
states. Do not promote on source-text tests or an unchanged v3 pose alone.

## Indexed runtime and actual normal-start check

Editor index build succeeds295.54s; all5 native suites pass in
`tmp/crew-support-index-native-v1-20260923/index.json`, session90347 terminal0.
7,570 grid/vertex/bin-edge queries×3 lifecycle states have exactly equal floor,
solid and missing-support results versus the original scanner. The geometry
index is retained only under the high-side review flag; no normal promotion.

`south-fork-high-side-stagger-index-v1-20260923` completes on the normal
FullReach/full_descent start, no teleport,4 solver lanes, confirmed high-side
command,24 stills and successful exact-cook suspend/resume. Movie
`unreal/Saved/VideoCaptures/RaftSim_20260923-164057.mp4`, SHA256
`556cce401f32683dcc046759fc62c055c6d96bd482bd6b4f075abadd8d2143d4`, fully
decodes468 frames over15.5667s,33 exact adjacent duplicates. Original3s/9s
frames show raft progression0.12→0.13km and changing water with crew holding
the command. Sixteen seconds without a direction flip is NOT a general
command-side stability test. The default camera hides much of the soles;
these images alone cannot verify tread support. Decoder report:
`tmp/crew-high-side-stagger-motion-v1-20260923/report.json`. Session19002 terminal0.

An input-only `RaftSim.ProfileHighSide` command now supports isolated900-frame
CSV runs; no screenshots/recording/camera changes or early quit. Helper
`-ProfileHighSide` rejects replay modes and confirms execution, separately from
`-StartupHighSide` motion capture. New guards and existing paddle guards pass;
command Editor rebuild24.75s. Native contact/index code is unchanged by that
command-only rebuild.

Cost capture `south-fork-high-side-cost-v1-20260923` is terminal0 (session41600),
normal start,1280×720 D3D12,4 lanes, exact cook suspend/resume0, confirmed input
and default CSV timing phase. Elapsed rows60–840 mean32.2805343ms/p9540.9841ms,
maximum46.5676ms: **FAIL33.333333ms**. This is neither a speedup claim nor
packaged/full-route acceptance. Report `tmp/crew-high-side-frame-v1-20260923.json`;
CSV SHA256 `ba22a7701e669672f44519981d549a426e1ba14383060c819ea291b84917e865`.

Associated scope rows59–839 have foot-fit mean0.1015402ms/p950.1195ms, support
query mean0.0634540ms/p950.0760ms (nested, do not add). Counters show6,248 cache
hits,1,562 geometry misses,0 seat misses and3,124 support queries: exactly8 hits,
2 geometry misses and4 queries per row. This contradicts settled contact reuse
for one crew member: the current invalidated-stance failure path does not
search again. Full-capture maximum foot-fit time is147.7744ms, so excluding
startup/command frames cannot establish hitch-free behavior. Next repair failed
stance recovery and add explicit attempted/solved pose counters; existing cache
counts alone do not prove every rendered high-side pose remained solved.

## Live invalidation recovery

The measured failed stance now invalidates its binding and searches again on
the current uploaded shape. This applies to the opt-in high-side path only;
ordinary qualified floor fitting is not broadened. Explicit `AttemptedPoses`
and `SolvedPoses` counters distinguish actual success from cache-hit intent.
Editor recovery build17.90s succeeds. The prior stagger/index Game build also
finished188.03s (session4097 terminal0), before this recovery edit.

Fresh input-only900-frame capture
`south-fork-high-side-recovery-cost-v1-20260923` completes (session51619 exit0),
with confirmed high-side command, normal start and exact cook suspend/resume0.
The bow binds at frame23, then rebinds at24 by1cm laterally as the live hull
changes. All900 CSV rows have equal attempted/solved counts. In associated
scope rows59–839, all7,810 attempted poses are solved with7,810 cache hits,
0 support queries,0 geometry/seat misses and0 further stance searches.
Foot-fit mean0.0384237ms/p950.0483ms/max0.0944ms for that warmed scope interval.
These explicit counters verify solve success, not full tread/limb collision.

Elapsed rows60–840 mean34.2910793ms/p9542.3535ms/max57.3905ms: still
**FAIL33.333333ms**. Do not claim an overall speedup from lower foot-fit cost;
this run is not an isolated AB comparison. Full-capture foot-fit maximum
136.8212ms remains a command/startup hitch. Report
`tmp/crew-high-side-recovery-frame-v1-20260923.json`, CSV SHA256
`c6a581b05b72365b33103194c5d6c4edaea80cd70913ea2d60800ec5f16a3db7`.

Next remove command-time cold searches (with geometry-aware precomputation or
another measured safe approach), warm-start invalidated placements and verify
full transition motion and contact on both directions. The original high-side
upper-body pose remains awkward and has not been certified against limb/hull
collision. Do not promote solely because pose counters now agree. Normal
promotion, packaged release, South Fork and later river acceptance remain open.

Final recovery native report
`tmp/crew-high-side-recovery-native-v1-20260923/index.json`:5 succeeded,
0 failed/not-run/in-process; session98949 terminal0. Final recovery Game build
33.14s succeeds, session28124 terminal0, log
`tmp/crew-high-side-recovery-game-v1-20260923.log`. Eight Python geometry-query
tests and both high-side/paddle PowerShell guard suites pass again. No final
recovery movie or packaged-game run is claimed; the live recovery evidence is
the isolated normal-start input/CSV run above. All engine/build/capture jobs
are terminal. Captured sources, installed4950 fields and nonlinear OFF remain
unchanged, and original cook36692 continues without duplication.

## Exact search pruning and local recovery — September24 UTC

The candidate triangle index now uses5cm bins instead of20cm; these bins only
select original triangles, never resample or simplify the support surface.
Tube searches reject horizontally unreachable candidates before querying
support: full3D reach cannot be smaller than its horizontal projection. The
unchanged full3D reach,15-point support,4cm span,foot ordering/height and boot
separation gates still decide acceptance. No new geometry or pose is authored.

The first normal-start900-frame command capture
`south-fork-high-side-prune-cost-v1-20260924` retains all solved poses and the
previous logged foot positions. Full-capture maximum foot-fit time39.9954ms
is lower than the prior136.8212ms observation, but still not hitch-free. The
subsequent live invalidation costs36.5786ms/7,262 support queries. Its overall
elapsed p9543.3062ms FAILS; report `tmp/crew-high-side-prune-frame-v1-20260924.json`,
CSV SHA256 `234aee8f1d84cb318470e450cded9b79fe48f2c0fedd9d507bd86122c7a9ece4`.
Editor build78.42s and all5 native suites pass; the exact index test now checks
7,582 points×3 lifecycle states, including additional signed5cm bin boundaries.

The final change first repairs an invalidated tube stance within2cm of each
prior foot. Only if that fails does it run the complete authored-origin search.
Both passes use identical support,reach and pair gates; nothing accepts stale
heights. Final Editor build16.03s succeeds. Final native report
`tmp/crew-support-local-repair-native-v1-20260924/index.json`:5 succeeded,
0 failed/not-run/in-process,6.015921s; session35282 terminal0. The later source
edit only indents this loop; no expression or control-flow change.

Final input-only capture `south-fork-high-side-local-repair-cost-v1-20260924`
is terminal0 (session6668), normal FullReach/full_descent start,1280×720 D3D12,
4 solver lanes, confirmed high-side input and exact cook suspend/resume0.
All900 rows have equal attempted/solved counts. The live bow repair now uses
20 queries and3.6468ms, with one explicit `LocalStanceRepairs` event; its logged
feet are the same (-32,-11,38.023)/(2,-7,40.795)cm as the prior full recovery.
Cold command fit still takes40.7643ms with10,194 queries;3,557 additional queries
are rejected as horizontally unreachable. This is NOT a hitch-free command.
Warmed scope rows59–839:7,810 attempted/solved/cache hits; zero queries,
geometry/seat misses or further searches; FitFeet mean0.0357712ms/p950.0454ms,
max0.0702ms. Overall elapsed rows60–840 mean32.6758234ms/p9542.0345ms,
max51.0535ms still FAIL33.333333ms. These sequential observations do not isolate
overall FPS gains; nested contact timings must not be added to frame timings.
Report: `tmp/crew-high-side-local-repair-frame-v1-20260924.json`.
CSV SHA256 `11e2f37281420fd612d78d62b43f1077e70b8f2b78f959949a1fb900b3eb296e`.

Separate normal-start motion capture
`south-fork-high-side-local-repair-motion-v1-20260924` completes24 stills with
confirmed high-side input and cook suspend/resume0 (session21352 terminal0).
Movie `unreal/Saved/VideoCaptures/RaftSim_20260923-171009.mp4`, SHA256
`d30f0e8d2ab3ce5f8a8dacc74eac403427ca94a6271c11c0385748dde52b8d68`, fully decodes
467 frames over15.533333s,35 exact adjacent duplicates. Unmodified3s/9s views
show0.12→0.13km progression, changing water and held high-side posture. Soles
remain mostly occluded; awkward upper-body pose, smooth water and coarse canopy
remain visible. This is not a fresh full-tread, direction-flip, transition or
limb/hull-collision qualification. Decoder report:
`tmp/crew-support-local-repair-motion-v1-20260924/report.json`.

Final Game build32.44s succeeds (session46091 terminal0), log
`tmp/crew-support-local-repair-game-v1-20260924.log`. Captures are editor-hosted
normal gameplay, not packaged-release acceptance. This increment improves the
opt-in contact candidate only; normal high-side promotion remains withheld.
Next remove the remaining cold command search with geometry-aware stance
preparation/reuse, then qualify both-direction transitions and whole-body fit.
No captured data,collision,hull,physical mass,4950 fields or nonlinear-OFF
state changes. South Fork and the full ordered queue remain unfinished.
