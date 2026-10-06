# Linked rapid calibration

This calibration uses the updated production raft and the `SEIYGECore`
submodule. The reference is the game's response to normal paddle, oar,
high-side and rescue commands, not a rapid's catalogue class.

## Current native result

The latest matching receipts cover all 37 planned trials: 30 reached their
endpoint, five recorded a stalled driver, and two Meat Grinder rock controls
were rejected because no eligible exposed physical rock was available.
Coverage is not 37 passes. All trial definitions match the committed plan;
no old route is substituted for a revised test. The compact observations and
binary/test provenance are in the companion `*-observations.json` and
`*-controls.json` reports.

| Requested calibration | Latest observed result | Limit |
|---|---|---|
| Lower Pinball reference slalom | Prepared: zero contact. First-only/late second: 5.02/6.02 contact-step seconds after clean first-rock passes. | All still arrive; clean navigation, not guaranteed capsize, distinguishes the routes. |
| Hance cross-current move | Nine timing/entry combinations; early steering from -8/-14 m makes both lanes. Absent steering from -20 m stalls. | The -14 m absent-steering alternative clears cleanly; no real-world class certification. |
| Meat Grinder / Troublemaker | Whole-rapid controls; localized Troublemaker impact and one actual high-side intervention followed by a successful exit. | Meat Grinder target geometry unavailable. No matched captured-rock pin/flip-prevention proof. |
| Terminator / Gulliver's linked moves | Prepared routes succeed. Terminator wrong-line stall recovers with normal Rest and steering; Gulliver's late steering recovers its line. | Matched input definitions are not bit-identical trajectories; Gulliver's first-only run still arrives after bank contact. |
| Continuous descents / rescue | All four requested sequences finish with one explicitly induced person recovered and no reset or remaining swimmer. | Controlled drills, not natural washout-frequency measurements. |

The actual-map eddy return/head/exit audit and Pinball's 60-second shared-water
audit completed. The new package builds and launches through Boot/menu, but
**fails the strict 20 FPS requirement** (48.16 ms mean, 58.48 ms p95,
113.72 ms maximum; 368/1,140 audited frames exceed 50 ms).
Packaged Pinball and Gulliver's completed their 60-second native audits and
first/middle/last image review. These direct diagnostic views are not full
packaged route or minimum-FPS acceptance. Compact receipts and hashes are in
`2026-10-05-linked-rapid-runtime-validation.json`.
Retained first-person steering screenshots are partly obscured by the guide's
raised arm. That concurrent crew/camera issue is preserved, not hidden by
calling overview captures normal first-person acceptance.

## Playable changes

Lower Pinball has paired terrain, collision, riverbed and recooked flow for
its two rocks. The second rock's footprint and a shallow right-side bypass
shelf are explicitly authored difficulty adjustments. Their dimensions are
not surveyed bathymetry. Captured source files are preserved. The steady
discharge target remains 45 cubic metres per second, about 1,589 cfs.

Hance and Gulliver's named holes and wave sequences use the same compact
crest, froth and immersed-current functions as the existing water features.
These are authored reconstructions, not a claim of resolved CFD. Wetness,
local depth and current gate their activation. Quiet pools do not acquire a
new persistent foam source. No global flip probability, replacement hull,
boat-only force or change to the user's core solver is introduced.

The normal Hance, Pacuare, Futaleufu and Chilko menu runs now use explicit
river-station finishes. Crossing an old world-X finish plane or volume no
longer ends a station-based descent before its downstream rapids. The HUD
shows distance travelled from the selected put-in, not an absolute river
station divided by the run length.

## Test method

The reproducible matrix contains 37 trials on six production maps. Hance
compares early, late and absent steering from three distinct actual entries.
Meat Grinder and Troublemaker include whole-description boundaries, three
line offsets, diagonal approaches and targeted existing-rock approaches
with and without normal high-side/recovery commands. Terminator and
Gulliver's compare linked, first-move-only and missed/late subsequent moves.

Four uninterrupted descents test Hance to Son of Hance, Lost Hat through
Satan's Cesspool to Son of Satan, Terminator to Khyber, and Chilko from
Bidwell through White Mile. A separately labelled single-person overboard
drill exercises recovery between sections. It is not counted as a natural
washout or evidence of a rapid's class. There is no reset during a trial.

Route markers are measurement planes, not invisible obstacles. Missing one
does not by itself prove a dangerous or impassable rapid. Arrival, correct
line, collision, swimmers and successful recovery are recorded separately.
The strict comparisons do not use the continuous-descent driver's adaptive
depth scouting. All driving uses the existing normal command API.

Collision receipts count committed full-production-hull impulses. The old
six-support-point counter is not valid for this collision path. Contact
seconds are the sum of fixed steps containing impulses, not exact resting
contact duration. Neither impulse count nor a zero count certifies a
minimum geometric clearance. One prolonged contact can contain many impulses.

The old `pin_seconds` counter has an additional limitation: it is populated by
the D4 wrap/pin classifier for `ARaftSimRockObstacleActor` cylinders.
`UpdateRockObstacles` does not feed captured terrain/static meshes into that
classifier. Those meshes still receive exact full-hull collision and water
loads. Zero in this legacy counter therefore does **not** prove absence of a
physical hold against captured terrain. No synthetic cylinder or new pin force
has been added to make the counter turn positive. The report preserves its
scope separately from committed hull impulses and actual boat progress.

The runs use a fixed simulation step for comparison; they are not FPS
measurements. Native activation receipts are required for named challenge
features: a passing source/unit test alone cannot show they are active in
the playable map.

Protocol 12 gives every independent trial a fresh raft condition and full
individual crew stamina, recorded after placement settles. This test-only
setup does not change ordinary checkpoint repair. Fatigue, damage, swimmers
and normal recovery carry throughout each uninterrupted descent.
The original v6 first-move-only control actively held the first lane; that
can supply a useful later correction and is retained as diagnostic evidence.
The revised control stops steering after the first move, while late-second
controls omit steering over an explicit station interval. Forward propulsion
continues, as in Hance's absent-steering comparison. Native receipts must
show the scheduled omission actually occurred; it is not a hands-off descent.
The final paired omission controls share the complete intended route, not just
its upstream waypoints. The driver's 12 m lookahead can read past a shared
prefix before the first move ends; keeping the entire route identical removes
that pre-treatment difference. Only the steering schedule changes.

These are single observations per condition, with matched input definitions,
not bit-identical upstream trajectories. The latest Terminator pair's first
sample was at stations 846.14 and 847.80 m despite matching requested starts;
both local live-field clocks read 3.20 s. Those observations do not establish
the cause of the divergence. The same pair already
had 142 versus 1,007 impulses before the 1180 m omission boundary. That
upstream difference cannot be attributed to omitting the later move. Downstream
contact, achieved lanes and recovery must be reviewed separately; no statistical
causal effect or expert class grade is inferred from one paired observation.

The initial v4 Pinball bar was an explicit gameplay-calibration approximation:
station 2052, lateral -26 m, 34 m wide by 24 m long, crown 154.96 m in the
source vertical frame. The existing second rock was widened to 24 m, without
moving its absolute crown at that stage. These are not newly measured terrain. That
600-second continuation has 0.00141% mass drift and numerical face discharge
44.75–45.20 m³/s. Both named rock crowns remain dry; the bar overtops at about
0.18–0.19 m depth. The normal-map installation changes 409 height samples,
rebuilds collision and Nanite, and verifies exact terrain readback before
the paired runtime files are finalized after editor exit.

## Reproduction

### Runtime crop correction found during calibration

The first fresh Pinball matrix still let the hands-off boat bypass both rocks.
At station 2050, lateral -29.5 m, its native depth was about 2.65 m despite
the verified cook's roughly 0.19 m bar depth. Terrain and sampled bed agreed;
the live water had risen. The normal moving window retained legacy
copy-neighbor cut-edge boundaries and the caller's roughness instead of the
cook's boundary states and roughness. This is the same class of crop defect
already addressed by the existing `cooked_ghost` loader for White Kilometre.

Pacuare, Hance and Futaleufu now explicitly select that existing loader mode,
including in their exporters, with updated streaming-manifest hashes. Earlier
Hance and Futaleufu traces showed depth increases up to 1.50 m and 8.56 m
relative to their source fields; they are not accepted difficulty evidence.
The source fields retain small genuine unsteadiness; equality to a frozen
water sheet is not required. Zambezi's procedural, unsettled reference seed
is not silently treated as a converged cook or switched to this policy.
A fresh native Terminator-to-Khyber route after the correction reached the
exit without swimmers. Across its 1,615 recorded samples, native depth minus
bilinearly sampled source depth had a maximum of +0.000055 m and minimum
-0.0862 m. This is a diagnostic comparison along that actual track, not an
assertion that the whole river is frozen or every location is validated.
It no longer shows the earlier multi-metre artificial rise on that route.
A new native Pinball test evolves the real crop for 120 seconds, transfers
overlap to the downstream window, and probes the flooded bypass location.
Its result and fresh boat trials, not the manifest edit alone, decide acceptance.
The linked-build native crop control passed: maximum stage change was
0.000183 m over 120 seconds including the handoff; maximum depth across its
four shelf probes was 0.227996 m. The unchanged limits were 0.1 m and 0.35 m.
The existing Chilko crop control also passed, with 0.002258 m maximum stage
change on its original failure trajectory and five window handoffs.

### Commands and provenance

Generate the explicit matrix with `unreal/Scripts/build_rapid_calibration.py`,
then pass its output to `unreal/Scripts/run_rapid_assessment.ps1` with
`-PreparedTrials -PlansPath`. Use fresh labels; the runner rejects a busy
shared engine. `unreal/Scripts/report_rapid_calibration.py` preserves failed
and missing trials and hashes each native evidence file.

Pinball geometry changes use `physics/scripts/build_pinball_reference_candidate.py`
and `physics/scripts/export_pinball_reference_candidate.py`. The exporter
requires finite converged flow and checks numerical face discharge against
the target. Footprint revisions preserve absolute crowns; shrinking or
relocating installed shapes requires the preserved pre-patch source.

Installation is two phase. Run `unreal/Scripts/install_pinball_reference.py`
in the editor, exit Unreal, then run
`unreal/Scripts/finish_pinball_reference_install.py` on its pending receipt.
The finalizer verifies the saved map and every old/staged file hash before
replacing memory-mapped flow arrays. Backups and pending receipts are retained.
Native testing and packaging reject an unfinished paired installation.

## Native observations and remaining calibration checks

### Fresh South Fork diagnostics (calibration still in progress)

The protocol-12 whole-Meat-Grinder line and +/-3 m lane trials reached the
exit without hull impulses. The two attempted-diagonal trials reached it
with 1,867/2,032 real full-hull impulses and 14.47/15.61 contact-step seconds.
Neither incremented the legacy pin counter, produced a swimmer, or issued a high-side command. Enabling the
high-side response is therefore **not** evidence of a tested high-side save.

Troublemaker's strict nominal route grounded around station 8340 and stopped
making progress; the diagonal approach reached about 8429 before stalling.
These are failed driver approaches, not proof that the rapid is impassable.
The +3 m requested river-left lane offset subsequently cleared the whole
rapid in 130.2 s, with 43 impulses over about 0.3 contact-step seconds,
no swimmers, no checkpoint reset and no backstroke. It used 133 guide
strokes and 76.4 s of turn commands. This is a nearby successful approach,
not a measured 3 m-wide safe corridor: its actual track varies with the
current, hull rotation and steering response.
Their expanded upstream start and strict route differ from the earlier
shorter, live-depth-scouting assessment, so the earlier easy grade is not a
contradiction or a matched before/after calibration.

The fresh Troublemaker impact receipt identifies the current physical owner
at station 8359.43, lateral -16.27 m. Its boat passed that station near
lateral -3 m; the closest sampled approach was about 10.4 m from the owner
centre, with no new contact impulses in that interval. It then grounded
downstream around 8429. This is a **missed rock approach**, not a pin test
pass. An earlier hypothesis using an older eddy recording (a different
owner, projecting near 8281) was superseded by this current-map receipt.
The old target selection started only 65 m above the catalogue control, leaving
little preparation time for the necessary ferry and broadside alignment.
Protocol 13 inspects actual owners throughout the approach, completes the
lateral ferry before broadside alignment, and records committed impulses by
their actual source component. It does not spawn a convenient obstacle.
This revision requires fresh native trials; compile success is not an impact.
Meat Grinder's unavailable-owner trials remain rejected, not pin passes.

The uninterrupted Lost Hat–Satan–Son of Satan descent reached station
27474.68 in 282.4 s. One deliberately displaced passenger was recovered with
normal rescue controls, with no checkpoint reset, no remaining swimmer and
no hull-contact impulses. Crew fatigue carried through the descent and ended
at zero; it was not replenished between rapids. This validates a controlled
rescue during a continuous descent, not a naturally generated washout.

### Fresh Terminator–Khyber comparison

With the corrected crop closure and fresh independent trial state, the linked
route reached station 1795 in 323.0 s, with 5.35 contact-step seconds and no
swimmers. Four of five requested measuring lanes passed. The Typewriter exit
crossed at +3.12 m against the unchanged +4 m minimum; a slightly more leftward
approach is prepared for a new trial, not retrospectively accepted.

The original first-only control actively held its first-move lane rather than
omitting later steering. It reached the same endpoint in 628.2 s with 242.28
contact-step seconds, missing the Khyber setup lane. Both runs remained finite
and their minimum boat-centre-minus-water heights were -0.066 m and +0.026 m.
This is an observed cost for continuing the wrong lane, not proof that every
missed turn must flip the boat. The revised explicit no-second-steering
control must be reported separately when run.

Evidence: `tmp/rapid-calibration-fresh-v1/south-fork` and
`tmp/rapid-calibration-fresh-v1/futaleufu`. These are full production physics
runs at fixed simulation time, not a packaged frame-rate benchmark.

### Fresh Hance observations (8,000 cfs source band)

These protocol-12 trials reset test-only condition and every crew member's
stamina before each independent trial, and use the corrected live crop closure.
They replace the earlier fatigue/damage-confounded comparison. Ordinary
gameplay checkpoint repair is unchanged. Continuous descents never replenish
fatigue or damage between rapids.

Eight of nine trials reached station 945; absent steering from the far-right
approach stalled upstream. None had swimmers or checkpoint resets.
All observed the six named shared water sites in the production map. Actual
entry centres were -8.4, -14.6 and -20.7 m, so these are distinct approaches,
not three commands that silently recentered to one start. Positive lateral
coordinates are river-left. The first two measuring lanes are [-7, 7] m at
station 745 and [2, 18] m at station 815.

| Steering / nominal entry | Time (s) | Lateral at 745 / 815 (m) | Hull impulses | Contact-step time (s) | Peak roll |
|---|---:|---:|---:|---:|---:|
| Early / -8 | 132.6 | -3.13 / 8.89 | 84 | 0.48 | 10.6° |
| Late / -8 | 150.4 | -12.74 / -5.30 | 0 | 0 | 14.9° |
| Absent / -8 | 168.4 | -11.56 / 10.88 | 13,867 | 62.58 | 10.4° |
| Early / -14 | 149.6 | -6.29 / 9.59 | 112 | 0.78 | 11.8° |
| Late / -14 | 152.2 | -16.60 / -5.38 | 0 | 0 | 12.9° |
| Absent / -14 | 108.0 | -16.60 / -10.35 | 0 | 0 | 4.4° |
| Early / -20 | 151.2 | -8.70 / 8.96 | 0 | 0 | 6.8° |
| Late / -20 | 134.2 | -18.41 / 2.06 | 0 | 0 | 8.5° |
| Absent / -20 | 175.6 (stalled) | -21.08 / -18.31 | 6,049 | 39.12 | 4.2° |

Early steering from -8 and -14 made both moves. Waiting until station 720
missed both from those entries. From -20, both steering treatments missed the
first lane but recovered above Giants; absent steering stalled after prolonged
ground contact. Absent steering from -8 also caused substantial contact, while
the -14 no-steering line flushed through cleanly. Thus approach and timing
matter, but a missed lane is not automatically dangerous and this is not proof
of real-world IV–V difficulty. These are matched forward-rowing controls, not
proof that an expert's alternative back-ferry cannot work.

The fresh uninterrupted Hance–Son of Hance rescue control reached station
1455.03 in 348.6 s, with one completed recovery, no remaining swimmer, no
checkpoint reset and no hull-contact impulses. Its deliberate guide-overboard
drill at station 955.01 is a guide-reentry control on the oar rig, not a
throw-bag rescue or a naturally generated washout.

Evidence: `tmp/rapid-calibration-fresh-v1/colorado` (NullRHI, motion evidence,
not frame-rate or visual acceptance). Older `rapid-calibration-hance-v4` and
`rapid-calibration-feature-canary-v1` receipts remain available but are excluded
from this fresh comparison. The baseline DLLs remain protocol 12 while revised
protocol-13 source is prepared. `native-runtime-snapshot.json` and its verified
source copy preserve the actual compiled driver; later launch working-copy
hashes alone must not be mistaken for the code in those unchanged DLLs.

### Gulliver's baseline identifies an unresolved challenge

The protocol-12 linked route reached 6565 m in 309.8 s and made all four
measuring lanes. The original first-only and late-second controls also cleared
in 302.6/310.4 s without contact or swimmers. The first-only control missed
Director's and Crease lanes but continued through safely. That does not meet
the requested physical consequence/recovery requirement.

This baseline used the earlier Director's feature normal and actively
corrected the first lane; it is not evidence for the revised no-steering
control. Inspection found that the near-surface roller opposes the feature
normal, so the earlier +35-degree normal pushed the wrong way. The revised
-35-degree normal gives the catalogued river-left shove toward the Crease,
using the same surface and immersed-current adapter. A native adapter test
and fresh complete route controls must verify the change before acceptance.
No arbitrary flip probability is added to make a test fail.
The catalogue's 36 m-wide Land of the Giants was also represented by only
one lateral row, whose roller current spans 9.6 m. The revised profile tiles
the existing shared kernel across lateral -12, -6, 0, +6 and +12 m for all six
waves. This is an authored width approximation, not a new survey or new
force law. The native control checks crest and current at the previously
bypassed side lanes, while retaining the dry/pool and local-height limits.

### Continuous descent and rescue coverage

All four baseline uninterrupted descents completed a deliberately induced
single-person rescue and reached their downstream endpoint without a reset
or remaining swimmer. These use normal recovery inputs and carry fatigue;
they do not establish natural washout frequency or an expert difficulty grade.

| Sequence | Simulation time | Exit station | Completed recoveries | Hull contact-step time |
|---|---:|---:|---:|---:|
| Hance–Son of Hance | 348.6 s | 1455.03 m | 1 guide reentry | 0 s |
| Lost Hat–Satan–Son of Satan | 282.4 s | 27474.68 m | 1 passenger | 0 s |
| Terminator–Khyber | 340.4 s | 1795.50 m | 1 passenger | 18.56 s |
| Chilko: Bidwell–White Kilometre–White Mile | 1068.0 s | 3975.69 m | 1 passenger | 0 s |

Chilko's deliberate overboard drill occurred at station 1025.10; all three
section-exit receipts passed, and crew energy was zero at the finish rather
than being replenished between sections. Its state remained finite through
the full descent. These are native motion/rescue observations, not rendered
or frame-rate acceptance. The revised Terminator route is tested separately;
its older continuous receipt is retained, not relabelled as the new route.

### Linked-build regression controls

`tmp/rapid-calibration-final-link-v1.log` records the successful full editor
build. All eight tests in `tmp/rapid-calibration-controls-v5/index.json` passed:
fresh independent trial setup, steering schedule, rock approach, committed
owner-contact totals, shared named challenge profiles, normal scenario finish
boundaries, Pinball crop closure and the existing Chilko crop regression.
The profile test exercises actual surface and immersed adapter calls for
Director's leftward shove and checks the wide train's side lanes and joins.
These are supporting native controls; the paired boat trials remain the
deciding evidence for playable route difficulty.

The 26 exact-ground/flip/water controls in
`tmp/rapid-calibration-exact-controls-v1/index.json` also passed. The extended
full-hull response test confirms that source-owner telemetry leaves poses and
velocities identical. The captured-production-rock pin control observed lift
at 0.100 s, scoop at 1.200 s and flip at 1.567 s, with 328 impulses. This is a
controlled full-hull mechanic regression, not proof of pinning in either
selected South Fork approach. Its obstacle is an engine box mesh registered
through the production captured-ground pipeline, not a surveyed South Fork
boulder; the raft is the actual 38,344-triangle production hull. Native GPU foam transport and rapid-to-pool
release controls passed as well. The flip/recovery test retained a renderer
warning about `r.MotionVectorSimulation` thread-safe access; no test failed.

### Corrected-water Pinball: retained failure and seam correction

Rendered protocol-13 v8: prepared steering cleared in 75.8 s with no contact.
First-only steering caused 1,621 impulses / 6.09 contact-step seconds;
late-second caused 130 / 0.79 s. The prepared first crossing was -1.61 m,
missing the unchanged -2 m margin. The next route moves its approach from
-5 to -7 m rather than relaxing that measuring gate.

Hands-off still cleared in 272.8 s without input or contact, passing the
second rock at lateral -16.62 m in 0.72 m of water. This was a real seam
between rounded footprints, not the old crop flood. It is a clean alternate
line, not a collision merely because it missed a gate. Evidence:
`tmp/rapid-calibration-pinball-ghost-v1`, with unchanged dependencies.

The staged correction expands the explicitly authored bar to 42 m width
and 0.8 flat-crown fraction. Candidate v5 retained the old crown but raised
local stage enough to submerge rock 2 by 0.047 m; export refused it and no
live assets were replaced. Candidate v6 uses fixed authored elevations:
bar 155.19 m, second rock 155.90 m. Rock 1 is unchanged. These are gameplay
approximations, not surveyed dimensions. Its 600 s continuation passed:
0.00321% mass drift, face discharge 44.39–45.34 m³/s, max speed 4.65 m/s,
max final-interval depth change 0.0235 m, dry named crowns, and no more than
0.182 m depth along the bank-to-rock connection. Staging:
`tmp/pinball-reference-export-v6-steady`. Native installation, seam probes
and matched boat trials remain separate from this supporting cook result.

### Localized rock attribution

The protocol-13 Troublemaker target at 8327.02 m / -10 m was a dry island
within a much larger terrain mesh. The trial stalled at 8357.81 m after
160 simulation seconds: 100,084 total impulses, 27,504 on that component,
82.91 contact-step seconds, no swimmer and no legacy pin-counter increment. Closest centre distance to
the selected island was 11.76 m. Component contacts elsewhere on a large
tile cannot prove impact with the selected island.

Protocol 14 restricts targeted approaches to dedicated rock actors or
installed captured-rock meshes. Its reporter does not qualify the old
terrain-tile counts as localized rock impact. Target trials are explicitly
bounded at 240 simulation seconds / 1,200 wall seconds; a limit is a partial
result, never a pass. This changes test selection/attribution, not collision
geometry, boat forces, poses, or pin thresholds.

Both fresh Meat Grinder target trials found no eligible exposed owner.
Its captured search-window manifest says rapid identity is unverified and
underwater bathymetry unknown. This does not prove absence of all collision
geometry, but these pin controls cannot be claimed. Adding inferred rocks
requires an explicit labelled reconstruction decision.

The four rendered rescue regressions passed in
`tmp/rapid-calibration-rescue-controls-v1/automation/index.json`:
equipment, passenger washout, aimed rescue paths, and occupancy-dependent
controls/loads/integrated mass.

### South Fork diagonal/control qualification

The baseline diagonal requests are not accepted diagonal-impact controls.
Meat Grinder attained the requested 45-degree heading (within 15 degrees) in
105/176 sampled hold states, and its recovery-enabled partner in 120/179.
Troublemaker attained it in only 4/151 and 35/167 states. In all four trials,
none of those aligned sample intervals contained an increase in full-hull
impulses. They contacted ground elsewhere/later, not while the recorded
sample was diagonally aligned. The report now records this conjunction
explicitly instead of qualifying an impact from separate angle/contact maxima.
No high-side command was actually issued in these four runs. Thus “high-side
enabled” is not a demonstrated high-side save. Fresh localized-owner trials
are reviewed independently below; the controlled pin regression cannot fill
this map-level gap.

### Fresh Terminator result and recovery follow-up

Protocol 14, `tmp/rapid-calibration-final-linked-v1/futaleufu`, finished with
unchanged dependencies. The revised linked route passed all five gates and
cleared Khyber at 1795.44 m in 334.0 s: 684 impulses / 5.18 contact-step
seconds, no swimmer or checkpoint restore. First-move-only also reached the
exit, but crossed Khyber's setup at +9.25 m rather than at or right of -4 m;
it took 441.6 s and 12,285 impulses / 94.75 contact-step seconds. It did not
flip, wash out a passenger or issue a high-side command.

The wrong-line trial missed the crux and Typewriter lanes, then stalled at
1466.37 m / -19.88 m in 5.58 m of water. At its last sample the current was
0.308 m/s, boat speed 0.044 m/s, crew and guide stamina zero, and the driver
was still calling turns. Its final impulse count was no longer increasing.
This is not a refused solver step or proof that the rapid is impassable.
The failed attempt (including 20 s backpaddling) is retained.

The opt-in protocol-15 follow-up retains that wrong-line approach. Only
after station 1380, at least 15 s without progress, an upright slow boat,
no swimmers and crew energy below 35%, it issues normal Rest for 12 s and
then aims 45 m along the same authored exit route. It does not refill
stamina, reset progress, move the boat, alter water/contacts or add an
autopilot to ordinary play. Actual rest activation, natural energy recovery
and the boat's subsequent progress must be recorded before claiming a save.

The fresh uninterrupted Terminator–Khyber run cleared in 330.2 s with one
deliberately induced passenger successfully recovered, no remaining swimmer
or checkpoint reset, and 6.84 contact-step seconds. This supersedes the older
route's continuous result without discarding that earlier evidence.

### Fresh Gulliver's linked and recovery comparison

Protocol 14, `tmp/rapid-calibration-final-linked-v1/zambezi`, completed with
unchanged dependencies. All three runs observed all 34 named sites in the
actual production water adapter. Prepared steering cleared in 309.2 s,
passed all four measuring lanes and recorded no hull impulses or swimmers.
In Land of the Giants the actual raft support surface varied from -0.306 to
+0.680 m relative to the sampled underlying surface; pitch reached 14.54
degrees. This is a measured boat response, not just registered feature data.

First-move-only cleared in 331.2 s, but crossed Director's at -11.72 m and
Crease/Gap at -20.56 m, outside their requested lanes. By Giants' exit it was
at -64.91 m near the bank, with 1,782 total hull impulses / 14.70 contact-step
seconds by the finish. No swimmer, capsize or high-side occurred. Omitting
later steering therefore caused a physical bank-contact outcome, not merely
a failed measuring gate. It still arrived without active recovery, so this
is not evidence of mandatory recovery or Class V consequences.

Late-second steering missed Director's at -11.73 m, then recovered to +0.80 m
at Crease/Gap through ordinary controls. It cleared in 336.2 s without hull
contact or swimmers: a recoverable missed move with approximately 27 s added
to this single observed descent. These are matched definitions, not repeated
statistical trials or a real-world class certification. The underlying
procedural channel remains much wider than the low-water real-world channel;
the added profile does not constitute a surveyed channel reconstruction.

### Final localized South Fork approaches

Protocol 14, `tmp/rapid-calibration-localized-owner-v1/south-fork`, completed
all four bounded trials with unchanged dependencies. Both Meat Grinder
approaches were explicitly rejected as `physical_rock_owner_unavailable`.
They are not pin/high-side passes. The decision about adding labelled inferred
geometry remains open; captured sources and geometry have been preserved.

Troublemaker selected the installed `SM_CapturedRockEnvelope` actor at
8359.43 m / -16.27 m, not the large terrain tile used in the rejected earlier
attribution. The no-recovery run recorded 71 committed impulses on this rock.
Its first impact observation intervals had headings 86.98 and 90.45 degrees
relative to the river, near the requested 80-degree broadside approach. It
slid past, then stalled downstream at 8429.34 m: 8,844 total impulses and
54.14 contact-step seconds. That downstream stall is not a pin on the target.

The recovery-enabled run recorded 93 impulses on the same rock, issued one
normal HighSide command, and cleared the whole rapid at 8520.13 m in 118.4 s.
It had 256 total impulses / 1.775 contact-step seconds, peak roll 18.50 degrees,
no swimmers, no backstroke and no checkpoint reset. HighSide was visibly
present in the sampled command state during rock contact. Unlike the first
run, its contact headings were approximately 20–32 degrees, not broadside.
Thus the intervention was exercised successfully in a real map, but the two
different impact approaches do not establish a causal high-side save or a
matched flip-prevention comparison. Neither run incremented the legacy D4
pin classifier. A hold/flip against this captured rock remains unproven.

Closest centre distances (10.47/12.04 m) are distances to the selected
owner's reference point, not hull-to-rock clearance. The rock is a broad,
connected captured/interpreted mesh; real owner contacts establish collision
with that mesh, not the exact outline of a small circular boulder. The separate
actual-map eddy/clearance audit is reviewed independently.

### Missed-crux recovery verified with ordinary controls

The linked protocol-15 follow-up in
`tmp/rapid-calibration-rest-recovery-v1/futaleufu` cleared Khyber at 1795.23 m
in 382.0 simulation seconds with unchanged dependencies. It still missed the
crux (+9.32 m versus at least +21 m) and Typewriter (-1.96 m versus +4..+22 m).
At station 1458.29, after losing progress with exhausted crew, the driver
issued normal Rest from 230.0 to 242.0 s. Actual crew energy rose naturally
from 0 to 0.2272. Subsequent ordinary steering with the declared 45 m exit
lookahead reached Khyber's setup at -6.39 m, inside the requested right lane,
and completed the descent. There was no checkpoint reset, backstroke,
swimmer, stamina refill or pose/velocity intervention. Total full-hull contact
was 2,249 impulses / 15.875 contact-step seconds; peak roll was 11.66 degrees.

This is a demonstrated recovery from a wrong approach with normal controls,
not a claim that the earlier stalled driver's continued turn calls would
have worked. The failed attempt is retained. The opt-in observation-driver
policy does not add automatic recovery to normal gameplay.

The rebuilt native control suite v7 passed all nine tests (one unrelated
HTTP connectivity timeout warning), including bounded one-shot rest policy,
crop stability and actual shared feature adapter behavior. Together with
the retained 26 ground/flip/water controls and four rendered rescue controls,
the compact controls receipt records 39 passes under their respective actual
binary hashes. Python calibration, geometry and installer tests total 44
passes. None of those counts constitutes packaged FPS or all-map acceptance.

### Final Lower Pinball reference controls

Protocol 15, `tmp/rapid-calibration-pinball-final-v1/pacuare`, completed with
unchanged dependencies on installed geometry v7 and the v12 input plan.
Holding the prepared exit lane through the whole finish removed the earlier
runout grounding; no gate or collision threshold was relaxed.

| Control | Time | First / second crossing lateral | Hull impulses | Contact-step seconds |
|---|---:|---:|---:|---:|
| Prepared two-move route | 68.2 s | -2.98 / +12.58 m | 0 | 0 |
| Steering ends after first rock | 70.8 s | -2.93 / +24.54 m | 1,209 | 5.02 |
| Second steering delayed to station 2038 | 83.2 s | -2.90 / +27.45 m | 1,001 | 6.02 |
| Hands off, retained matching v10 trial | 329.4 s | -20.21 / +6.29 m | 2,036 | 16.83 |

The three steered controls all passed the first rock with zero prior
impulses. The omission controls already had 103/256 impulses by the second
crossing; passing the first obstacle did not provide a free clean passage
through the next. Their one-sided second measuring gate technically passes
even after overshooting into the bank. Actual contact, not that painted
gate, is the relevant outcome. None capsized or lost a passenger.

Final installed terrain has 917 changed height samples with exact readback,
rebuilt collision and Nanite, and the paired converged flow export. The
authored second crown is 155.90 m and the bank-connected bar is 42 m wide,
24 m long, 0.8 flat-crown fraction, crown 155.19 m in the source vertical
frame. These remain declared gameplay approximations, not new measurements.
The native v7 crop test also retained the 0.1 m stage-change and 0.35 m
maximum seam-depth limits; the shallow connection cannot be accepted solely
from an offline raster or a successful export.

### Actual-map eddy and rendered-water review

`tmp/rapid-calibration-trouble-eddy-v2` completed the actual 60-second native
audit without runtime errors. After its single initial placement, the raft
moved 12.54 m upstream toward the installed terrain island, reached the eddy
head at 27.59 world seconds, and first exited outward/downstream at 32.02 s.
The strongest observed upstream velocity was 2.77 m/s. This selected island
is not the captured-rock component used by the targeted pin controls above.
There are 104 post-setup states, at most 0.751 s apart: genuine world-timer
observations, not dense fixed-step collision coverage or interpolated motion.

The public hull-current and shared surface-current samplers agreed exactly
at the audited probes; none of the originally dry probes became wet. Foam's
submitted transport matched its shared evaluator and committed water clock.
This confirms paired native inputs, not measured pixel advection or CFD.
The clearance diagnostic found one raw-hydraulic wet point 5.32 cm below the
physical ground; the actual raft-support sampler correctly rejected it as
dry. Its submitted macro triangle was terrain-occluded. This is an explicit
bed/sample discrepancy, not a full-hull minimum-clearance certificate. The
201 ms diagnostic scan is not included in a normal performance claim.

The retained eddy video and 43-frame APNG contain real engine backbuffer
images with no adjacent duplicate frames. First/middle/last images were
inspected: physical obstacle, upstream approach and localized froth are
visible. Recording ends at world second 30, so the later downstream exit is
verified by native states, **not shown in this recording**. The first 0.75 s
uses the raft camera before the diagnostic overview activates; debug overlays
remain. Files: `tmp/rapid-calibration-trouble-eddy-v2-review/animation.png`
and `capture.json`; native audit: `entry-audit.json` in the capture directory.

`tmp/rapid-calibration-pinball-overview-v2` completed 60.014 world seconds,
120 actual states (maximum gap 0.704 s), no runtime errors, zero shared-current
error and zero dry-to-wet conversions. Its foam payload had no nonfinite
vertices and zero transport/clock error. The first/middle/last native video
frames show stable water around the raft, but the narrow overhead camera does
not frame both slalom rocks. The direct diagnostic launch also uses the default
Open Water run state; it is not menu-route or whole-slalom visual acceptance.
The separate production trial screenshots show the first rock and second-rock
froth/bank contact, with the guide-arm occlusion described above preserved.

The earlier Pinball overview v1 ended at 53.52 elapsed seconds before its
requested 60-second terminal audit. It is retained as incomplete. V2 extended
the capture to 4,800 frames without changing the duration or sample-gap gates.

### Fresh packaged build and normal-launch performance

Windows Development BuildCookRun completed successfully (exit 0). Cooking
reported zero errors and 292 warnings, including older MetaHuman FaceCroppedV2
materials with missing UDIM inputs. The package includes concurrent crew
commit `599ee02742afba66d27974980e859efcc0b68063`; those changes were preserved,
not included as this calibration's own work. The raft-actor portion changes
visual equipment, not the calibrated boat forces.

`rapid-calibration-package-normal-v1` confirmed the packaged Boot -> main menu
-> South Fork FullReach -> post-travel CSV sequence. It used normal quality,
normal full-hull collision and no legacy/experimental overrides, exiting 0
with no runtime errors. The audit kept its predefined rows 30..1169 from
1,200 actual elapsed-time frames. The executable SHA-256 is
`8dc76d2c6747e95e5ed54cf22c1d5032372289a31007a764112b55fce2a99cde`.

Mean frame time was 48.1642 ms (20.76 FPS average), p95 58.4772 ms,
maximum 113.7213 ms (8.79 FPS for that frame). There were 368 frames above
50 ms and one above 100 ms. **Timing acceptance fails**, including p95;
neither the average nor the error-free launch is substituted for the
20 FPS minimum. This samples the ordinary start, not every rapid or map.

The same CSV indicates a CPU/game-thread bottleneck: mean game-thread time
46.44 ms versus GPU time 15.58 ms. Water-surface tick averaged 21.24 ms and
raft tick 19.62 ms; the fixed water/raft bridge (14.49 ms) is nested inside
the raft tick and must not be added again. These measurements localize cost,
but do not identify a causal regression against an unmodified same-build
control. No fidelity reduction or unvalidated performance tweak was applied
to conceal this failed gate. Full-hull/render equality remained exact at the
logged 26,610 vertices / 38,344 triangles.

Retained package: `tmp/rapid-calibration-package-v1/Windows`.
Frame receipt: `unreal/Saved/RaftSimValidation/rapid-calibration-package-normal-v1-frame-audit.json`.
Original CSV SHA-256:
`9490e9d07ecd23d979e919739d0ba79cda59e9ea931a95c5340f1dcf76c1dd7d`.

### Packaged feature verification and remaining acceptance work

Both packaged Pinball and Gulliver's captures exited 0, completed the requested
60-second native audit and produced valid video/foam receipts without runtime
errors. Pinball had 424 wet probes / 30 changed by feature kinematics;
Gulliver's had 441 / 61. Both had zero shared-current error and no dry-to-wet
conversion. Submitted foam transport error was zero, all vertices were finite,
and the material clock differed by less than 0.000001 seconds. Twelve staged
runtime files, including all changed manifest/streaming files and the Pinball
flow arrays/support field, matched the source SHA-256 values exactly.

Packaged Gulliver's registered the 30 Giants sites within this view; the
whole-rapid trials separately observed all 34 named sites. Its actual decoded
first/middle/last frames show raised crest/froth rows with green water between
them and the production rowing raft. Each packaged recording yielded 641
decoded frames and a verified 43-frame APNG with no adjacent duplicates.
Neither recording is substituted for a controlled navigation comparison or
an all-map visual acceptance pass.

Local review animations:

- `tmp/rapid-calibration-packaged-pinball-v1-review/animation.png`
- `tmp/rapid-calibration-packaged-gulliver-v1-review/animation.png`
- `tmp/rapid-calibration-trouble-eddy-v2-review/animation.png`

This delivery establishes the clean-versus-omitted-second-move Pinball
reference, the nine-condition Hance comparison, actual localized Troublemaker
collision/high-side/eddy observations, recoverable linked moves, and all four
continuous rescue drills. It does **not** close every acceptance item:

- Meat Grinder requires a decision about explicitly labelled inferred exposed
  rocks; its captured source does not verify a suitable installed target.
- Troublemaker needs a matched captured-rock hold/flip/high-side comparison
  before claiming a causal save. Minimum geometric hull-to-rock clearance is
  not established by centre distance or collision counts.
- Hance's clean absent-steering alternative and Gulliver's passive bank-contact
  arrival remain real outcomes; no class-dependent failure was forced.
- The packaged normal launch is healthy but fails the 20 FPS gate. The measured
  CPU costs above need a separate verified optimization pass, not a lowered
  threshold or a simplified hull.

All earlier failed attempts are retained. No user capture, other task's crew
change, or existing core-solver update was discarded to obtain these results.
