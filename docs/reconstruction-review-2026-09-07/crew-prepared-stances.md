# Grounded stance preparation — September24 UTC

Continuation of [high-side contact](crew-high-side-contact.md). This is an
opt-in runtime improvement, not normal high-side promotion, crew realism or
South Fork acceptance. The previous goal turn made measured progress; this
turn addresses its remaining approximately41ms command-time foot search.

## Runtime change

The host retains three independent placements: seated/stroke/brace, high-side
port and high-side starboard. Seating setup prepares them after glute/seat
reconciliation. Preparation calls the same geometry/IK solver on local pose
copies; it never changes the current action, animation phase, rendered body or
boots. Each placement retains its own geometry revision, seat transform and
support heights. Reattachment and appearance changes discard all placements.
Reusing another action's placement does not skip current geometry/seat checks.
The existing local-repair/full-search fallback and support/reach/pair gates
remain intact. Preparation and high-side fitting remain review-flag-only.

Preparation moves real work into setup; it does not eliminate its cost. Initial
normal-run logs record100.2045ms across five crew; final instrumented logs
record105.9186ms (individual12.9834–33.0499ms). These occur at setup frame0,
before the captured gameplay interval. They are not hidden in warmed means.

## Engine verification

Editor build133.69s passes; five native suites pass in BOTH review and default
modes (6.3612895s and8.4749022s respectively), terminal session63763 exit0:

- `tmp/crew-prepared-stances-native-v1-20260924/index.json`
- `tmp/crew-prepared-stances-default-native-v1-20260924/index.json`

New assertions check preparation leaves the current action, actual pelvis
transform and both boots unchanged, and repeated starboard/port/idle switches
retain separate supported stances. Existing320 timed pose checks, body/boot
anchors, seat-transform invalidation, rigid paddle, vest and exact7,582-point
support-index×3 lifecycle checks remain. Native instant switching is NOT
continuous transition, swept collision or direction-flip motion acceptance.

The initial900-frame capture has maximum FitFeet3.5143ms and all9,000 attempts
solved. However, its full-search counter column is ABSENT and is unavailable,
not a measured zero. A16.58s Editor rebuild adds explicit zero accumulation;
the final capture below is the evidence for no full searches. Initial CSV:
`south-fork-prepared-stances-cost-v1-20260924`, SHA256
`19c888728005231784d8adf5a2dae435fc80f99b443b467409e0860bda419ba7`.
Initial frame report `tmp/crew-prepared-stances-frame-v1-20260924.json` records
mean30.4601264ms/p9540.0551ms/max46.29ms: FAIL33.333333ms.

## Final normal-start cost

`south-fork-prepared-stances-cost-v2-20260924` completes terminal0 in session22659.
FullReach/full_descent normal start,1280×720 D3D12,4 solver lanes, confirmed
high-side input; exact identified cook36692 suspension/resumption both0.
CSV timing mode confirms scope offset1. Across all900 captured rows:

- 9,000 attempted poses =9,000 solved;8,985 cache hits.
- Explicit `FullTubeSearches` column sums to0, not absent/missing.
- 60 support queries,15 geometry misses,0 seat misses;1 successful local repair.
- Full-capture FitFeet maximum3.5189ms; repair row0.3795ms with40 queries.

Warmed scope rows59–839:7,810 attempts/solves/cache hits, no queries/misses/
searches; FitFeet mean0.0385407ms/p950.0494ms/max0.1147ms. This is contact cost,
not elapsed frame cost. The matched elapsed rows60–840 have mean36.1141980ms,
p9543.4028ms/max68.132ms: **FAIL33.333333ms**. Sequential captures do not isolate
overall FPS gains. No cost is inferred from encoded video rate.

Frame report: `tmp/crew-prepared-stances-frame-v2-20260924.json`.
CSV SHA256 `df0bcc093470737f91f797d3ebbebe7b4fd8403077bd23e5ebbd3e193bf397f9`.

## Independent tread and visible motion

Because setup solves on an earlier hull shape, the prepared/live-repaired bow
stance differs from the prior command-time cold search. Do not claim identical
live feet from unchanged support gates. Fresh static engine audit
`tmp/crew-prepared-stances-tread-v1-20260924/report.json` completes terminal0
(session1794), with6 distinct images and50 solved boot/action measurements.
All9,600 actual tread points have solid support; no penetration. Per-boot minimum
gaps0.1074359–1.3527533cm; maximum tread gap3.5921189cm; body/boot target error
at most8.30e-14cm. No assets or levels saved. Front-port/rear-starboard images
were inspected: supported boots do not resolve awkward crouching, displaced
hips, garment shape or potential limb/hull intersections. This static report
does not establish tread support throughout deformed-hull transitions.

Separate normal-start motion `south-fork-prepared-stances-motion-v1-20260924`
is terminal0 (session90249), confirmed high-side command,24 stills and successful
exact-cook suspend/resume. Movie
`unreal/Saved/VideoCaptures/RaftSim_20260923-172819.mp4`, SHA256
`c768691813189820b37695ba207507e29a1c39c2aa1c82cd889f75c60cef64c4`, fully decodes
469 frames over15.6s,32 exact adjacent duplicates. Original3s/9s views show
0.12→0.13km raft progression and changing water while the crew holds high-side;
most soles remain occluded. Decoder:
`tmp/crew-prepared-stances-motion-v1-20260924/report.json`. This does not establish
continuous step trajectories or full-route shoreline/surface/collision acceptance.

## Next work and boundaries

Final ordinary-play check without the review flag or high-side command:
`south-fork-prepared-stances-default-cost-v1-20260924`, terminal0 session52197,
normal start and cook suspend/resume0. No preparation log events; all900 rows
have matching attempted/solved counts. Warm scope rows59–839 have7,810 attempts,
solves and cache hits,0 support queries; FitFeet mean0.0385830ms/p950.0498ms,
max0.0928ms. Overall elapsed mean36.2782407ms/p9543.6425ms/max71.0017ms still
FAILS33.333333ms. This verifies the ordinary shared-cache path, not an isolated
speedup or performance acceptance. Report
`tmp/crew-prepared-stances-default-frame-v1-20260924.json`; CSV SHA256
`a27c075dd00993435155d95ba012c9677022e6dbb27a5c2aea2c15593732c7b5`.

Final Game build118.28s succeeds (session13653 terminal0), log
`tmp/crew-prepared-stances-game-v2-20260924.log`. Engine captures use the normal
scenario in an editor-hosted game, not packaged-release acceptance. Both builds
retain the historical unrelated uninitialized-Current/compiler warnings; those
are not claimed fixed here.

The measured command-time full-search hitch is removed in these short runs;
unbounded deformation/seat relocation can still require the full fallback.
Next solve and validate whole-body high-side transitions in both directions,
including foot-lift trajectories and limb/hull clearance, before normal
promotion. Overall water-dominated performance remains separately unresolved.
Captured sources, hull/collision, physical crew mass, installed4950 fields and
nonlinear OFF are unchanged. Do not advance to Colorado/Pacuare/Futaleufu yet.
