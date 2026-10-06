# Colorado River, Hance (`L_Hance`) inspection — 2026-09-02

Scope requested: the same pass as the South Fork inspection, on the Colorado
environment — inspect the crew paddling animation from multiple angles and
verify the characters render and animate correctly; step down the river and
verify that water and rocks render and animate correctly and that the boat
physics behaves; address the issues found.

Method: headless `-game` runs of `/Game/RaftSim/Maps/L_Hance` at 1600x900
with the review commands from the South Fork pass (`RaftSim.CaptureRaftSeries`,
`RaftSim.SurveyReach`, `RaftSim.ManoeuvreCheck`, `RaftSim.CaptureSeries`).
Every claim is backed by a screenshot under `unreal/Saved/Screenshots/`
(`hance_crew_*`, `hance_survey_*`, `hance_run_*`, `hance_win_*`) or a
parseable log line (`RaftSim survey station:`, `RaftSim manoeuvre:`).
Reduced copies of the figures referenced below are in
`docs/reports/images/2026-09-02-hance/`.

The map: a 600 m straight interpreted reach (`hance_runtime_coordinate_map.json`
is an identity station/lateral map at 2 m, vertical datum 950.7 m), cooked at
the 12 000 cfs "moderate release" band. The bed is authored from the window
manifest: boulder garden 150–362 m (44 bed boulders), lead-in 150–250 m,
main drop at 308 m with the lower hole at 334 m, left eddy 398–446 m,
runout waves at 404/420/436 m with the big one at 454 m, and the low-water
rock at 474 m. The player raft launches at station 336 m (56 % of the reach),
which is *below* the main drop; the scenario framing is the runout wave
train, with the first breaking transition about 69 m downstream of the launch.

## 1. Crew paddling animation

Bursts of 16 frames at 0.5 s from a raft-attached camera with `AllForward`
running: rear (guide-like, `3.2 0 2.3 4`), three-quarter (`3.0 3.0 2.0 2.0`),
beam (`0 5.5 1.5 0`), bow-on (`-5 0 1.8 0`), and a back-paddle burst
(`cmd=AllBackward`) from the rear-right quarter.

### Rendering — pass, one defect fixed

- All four paddlers and the guide render: heads sit inside the helmets with
  faces, ears and necks visible (the South Fork "no heads" fix carries over
  unchanged), vests layer over the wetsuits, tonal boots, yellow lens-section
  blades on the shafts. Figures: `crew-rear-stroke.jpg`, `crew-bow-sheet.jpg`,
  `crew-beam-sheet.jpg`.
- **Defect (fixed): the guide's head rendered as a black spike** from every
  external camera (`guide-head-before.jpg`). The guide pawn hides its own
  head for the first-person seat by zero-scaling the CC0 head bone; that hide
  stayed active while a review camera was the view target, and the wetsuit
  collar vertices partly weighted to the head collapsed into the neck joint
  as a cone. `ARaftSimGuidePawn` now treats the seat as first person only
  while the possessing controller's view target is the pawn itself, so any
  external camera (review commands, cinematics, chase cameras that set a
  view target) sees the full guide (`guide-head-after.jpg`). This also
  closes South Fork follow-up #5 ("guide hidden from external cameras").

### Animation — pass with the South Fork notes

- Stroke phases are visible across the bursts: catch ahead of the hips,
  blade buried through the power phase, recovery with the blade clear of
  the water, and the back-paddle burst shows the reversed stroke with the
  raft slowing against the current (log: raft 1.3 m/s in 1.9 m/s water).
- Wave impacts in the runout throw spray around the hull (Niagara puffs,
  `crew-beam-sheet.jpg` frames 9–11) — the map has breaking-water VFX sites
  (9 active, 47 rejected at the lattice edge, per the ownership log line).
- Carried over, still open: crew heads hold a fixed gaze through the stroke;
  paddle blades enter and leave without their own splash or drip.

## 2. Reach survey (water, rocks, boat support), 0–600 m every 10 m

`RaftSim.SurveyReach 0 600 10 3 hance_survey 30`: 61 stations, 25 hops,
3 photographs per station (two chase frames 0.4 s apart and a shore
camera), one `RaftSim survey station:` line per stop with a 5 m water sweep
over ±5 m at the centreline and ±6 m lateral, rock counts within 30 m, and
a terrain trace under the centreline. 61 of 61 stations reached (the 600 m
station needed the end-of-corridor heading fix described under tooling).
Figures: `survey-chase-0-290.jpg`, `survey-chase-300-590.jpg`,
`survey-side-0-290.jpg`, `survey-side-300-590.jpg`.

Whole reach, raft at rest at each station:

| metric | value |
| --- | --- |
| stations wet (solver) | 61 / 61 |
| stations grounded | 0 |
| freeboard, floor above surface | 12.4–19.4 cm, mean 16.8 |
| water speed at the raft | 0.06–2.75 m/s, mean 1.26 |
| depth at the raft | 1.20–4.07 m, mean 3.05 |
| sweep samples | 179; dry centreline 0; dry sides 0; stagnant 1 (470 m) |
| largest surface drop / rise per 5 m | 0.75 m (300–310 m, the main drop) / 0.40 m |
| largest lateral tilt over 12 m | 0.23 m |
| rock obstacle actors | 0 (Hance places no `ARaftSimRockObstacleActor`) |
| dressing boulder instances within 30 m | 81 over 46 stations |

Per 50 m (n = stations, ranges are min–max over the bin):

| from m | n | wet | water m/s | depth m | freeboard cm | max drop m/5 m | rocks | pitch deg | anomalies |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 5 | 5 | 1.80–1.94 | 3.77–3.87 | 16–17 | 0.03 | 0 | 0.1–0.7 | |
| 50 | 5 | 5 | 1.54–1.76 | 3.80–3.96 | 17–18 | 0.03 | 0 | 0.0–0.5 | |
| 100 | 5 | 5 | 1.26–1.50 | 3.89–4.07 | 16–17 | 0.03 | 1 | 0.1–1.3 | |
| 150 | 5 | 5 | 1.86–2.02 | 2.15–2.16 | 16–17 | 0.06 | 9 | 0.0–0.5 | |
| 200 | 5 | 5 | 1.68–1.88 | 2.14–2.17 | 16–18 | 0.06 | 9 | 0.0–0.5 | |
| 250 | 5 | 5 | 0.91–1.93 | 1.64–2.37 | 16–19 | 0.11 | 8 | 0.1–1.0 | |
| 300 | 5 | 5 | 0.85–2.29 | 1.40–3.05 | 15–19 | 0.75 | 9 | 0.3–1.5 | |
| 350 | 5 | 5 | 1.09–2.75 | 1.20–3.64 | 16–17 | 0.24 | 7 | 0.1–3.5 | |
| 400 | 5 | 5 | 0.44–0.61 | 3.20–3.46 | 12–19 | 0.51 | 11 | 0.1–1.6 | |
| 450 | 5 | 5 | 0.06–0.45 | 1.57–3.21 | 16–19 | 0.32 | 10 | 0.0–0.9 | 470: stagnant |
| 500 | 5 | 5 | 0.30–0.65 | 3.29–3.58 | 16–18 | 0.03 | 9 | 0.0–0.4 | |
| 550 | 5 | 5 | 0.64–0.65 | 3.65–3.93 | 16–17 | 0.03 | 8 | 0.0–0.5 | |

### Water — what is right

- The solver field is wet, continuous and plausible along the whole reach:
  a 3.9 m deep lead-in pool slowing from 1.9 to 1.3 m/s, the boulder garden
  shoaling to 2.2 m at 1.9–2.0 m/s, the main drop (0.75 m over 5 m at
  300–310 m, 2.3 m/s), the runout wave train and the eddy pocket at 470 m
  behind the low-water rock (0.06 m/s), then a 3.6–3.9 m pool at 0.65 m/s.
- The raft floats at a constant 12–19 cm freeboard at every station, with no
  dry or grounded support points anywhere, and no capsize in any run.
- The rendered surface follows the solver: foam and breaking crests appear
  on the drop and the runout waves and nowhere else; the eddy line at the
  left eddy reads as a still pocket next to the tongue.
- Rocks: the 44 bed boulders are bathymetry; at this flow band their crests
  sit 0.05–0.85 m below the surface, so no channel rock is meant to show
  (the manifest offsets are all negative). The 81 dressing boulders counted
  within 30 m of the channel sit on the banks; none floats or drowns.

### Water — defects

1. **Corridor ends render dry although the solver is wet (fixed).** At
   stations 0–10 m and 580–590 m the raft floated 3.8 m above bare sand with
   the water sheet starting 15 m away along a straight edge
   (`corridor-end-before.jpg`). Two mechanisms, both in
   `RaftSimWaterSurfaceActor.cpp`. First, the live lattice fades its
   coverage to zero over 36 m at its first and last rows — right for the
   moving window's hand-off rows, wrong where the grid's edge *is* the
   corridor's end and nothing continues beyond; `StationEdgeCoverage` now
   keeps full coverage on a grid edge that sits at the corridor's station
   range end. That alone moved the water's edge only from ~20 m to ~15 m,
   and a row probe (`raftsim.LogLatticeEdgeRows 1`) showed why: the
   overlay's first twelve rows were wet with coverage 1.0, but the volume
   core — the layer that actually renders the water body — builds its
   triangle topology once per grid shape, at the launch in mid-reach,
   where those edge rows had coverage below the 0.6 cell threshold; the
   rows kept no triangles when the grid later moved to station 0. The
   topology cache is now keyed on the corridor-end state as well
   (`CorridorEndPadState`), and a section whose index buffer no longer
   matches the rebuilt triangle list is recreated instead of updated in
   place. The same gap is the "station 0 on dry gravel" note of the South
   Fork survey. Verification: see section 4.
2. **Corrugated ridges on the pools (open, diagnosed).** From the shore
   camera the deep slow water at 20–140 m and 500–570 m shows regular
   diagonal ridges converging to the horizon (`pool-corrugation-before.jpg`).
   The first suspect was the coupled standing-wave field's two "calm bands"
   (station-periodic 1.1 cm and 0.7 cm sine ridges, ungated by flow, scaled
   0.55 on this map; South Fork zeroes the whole field for a similar
   artefact). A Froude gate on those bands was built and photographed at
   100 m and changed nothing, so it was reverted — the ridges are not
   geometry from the standing wave. They match the dominant diagonal streak
   of the core's mirrored flow-normal texture (item 3 below), i.e. shading,
   not displacement.
3. **Pale, glossier parallelograms with straight edges on the water**
   (`water-layer-seam.jpg`, `hance_win_base_*`). Brighter, sharper-reflecting
   patches with straight edges, filled with the same diagonal ridges as the
   pool corrugation of item 2. Layer isolation (`water-layer-isolation.jpg`):
   hiding the live overlay (`raftsim.HideLiveOverlay 1`) leaves them; hiding
   the static Default Lit ribbon (`RaftSim.HideTaggedActors
   component=PhysicalCorridorRiverRibbon`) changes nothing at all — that
   ribbon contributes no visible pixels on this map; hiding the live water
   actor (`class=RaftSimWaterSurfaceActor`) removes every drop of water and
   exposes the carved landscape. So the patches are inside the live volume
   core, not a seam between layers. Together with item 2 they point at the
   core's flow-normal texture (`T_RaftSim_ColoradoHance_FlowNormalV1.png`, a
   photographic normal map with one strong diagonal streak direction,
   addressed with mirrored tiling): each mirrored tile flips the streak
   direction, so alternate tiles catch the sun as glossy parallelograms
   while their neighbours stay matte, and the streaks read as ridges inside
   them. Open — needs a texture with no dominant direction (or wrap
   addressing on a tileable source) and a calmer normal strength on slow
   water; see the defects table.
4. **Runout breaking water reads as a white carpet.** Through the 404–454 m
   wave train the whole channel width turns into a streaky white sheet for
   ~60 m (`runout-foam-sheet.jpg`). The solver breaking mask does span the
   channel there, so coverage is faithful; it is the flat, streak-textured
   foam rendering (no crest geometry above the sheet) that reads as a
   carpet rather than a wave train. Open — same family as South Fork's foam
   notes; needs crest relief or a foam texture with less directional streak.
5. **Banks.** The dryland terrain is bare tan slopes with sparse shrubs and
   large dark angular terrace slabs with straight edges (`crew-beam-sheet.jpg`
   top rows). This is the known state of the Hance nonperiodic-canyon V3
   review (DEM-scale bank form, ecology and geology specificity are listed
   as open external gates there); not changed in this pass.

## 3. Boat physics

### Manoeuvre check (`RaftSim.ManoeuvreCheck`, launch at 336 m)

| phase | command window | raft speed (m/s) | water at raft (m/s) | yaw rate (deg/s) |
| --- | --- | --- | --- | --- |
| drift | 0–2 s Rest | 2.55–2.61 | 2.34 | 0 |
| forward | 2–14 s AllForward | 3.4–5.0 | 1.9–3.2 | ±0.5 |
| stop | 14–20 s Stop | 2.2 → 1.1 | 1.6–1.9 | −0.2 |
| back | 20–30 s AllBackward | 1.1 → 0.7 (water 1.0–1.5) | 1.0–4.7 | +0.4 to +2.7 |
| turn left | 34–44 s TurnLeft | 1.5–3.1 | 1.1–3.3 | −4 to −10.5 |
| turn right | 44–54 s TurnRight | 1.4–3.4 | 1.2–6.9 | +7 to +12.3 |
| rest | 54–58 s Rest | 1.6–2.0 | 1.1–1.4 | 0 |

Pass: forward paddling adds 1.5–2 m/s over the current, `Stop` holds the raft
0.5–0.8 m/s slower than the water within four seconds, back-paddling makes
0.3 m/s upstream against the current, and turns hold 7–12 deg/s in both
directions — the same envelope as the South Fork check. Two single-sample
water-speed spikes (4.7 and 6.9 m/s at the runout waves) appear in the
sampled velocity while the raft itself stays at 2.9–3.4 m/s; they are wave
crest velocities of the cooked field and did not disturb the hull.

### Capsize and recovery

No run capsized. The capsize latch and the surface-relative re-flip from
the South Fork pass are shared code and were not exercised here.

### Paddle-through from the top of the boulder garden

`RaftSim.CaptureRaftSeries 6 60 2 hance_run 3.2 0 2.3 4 paddle station=100`
walks the raft to 100 m (four 79 m hops) and runs it down with `AllForward`
for 120 s from a chase camera (`hance_run_000..059`). Pass: the raft ran
the lead-in pool, the boulder garden, the main drop (frames 21–25, foam
across the tongue), the runout wave train (35–49, with the wave-impact
spray cloud at frame 46) and out into the lower pool without a capsize, a
grounding, or a dropped frame of support; the whole 500 m above and below
the authored launch is runnable. The guide is visible at the stern in every
frame after fix #1.

## 4. Verification of the fixes

- Guide head: `hance_crew_tq2_*` (three-quarter burst after the fix) shows
  the guide with head, helmet and face from the external camera
  (`guide-head-after.jpg`).
- Gates on the fixed build (nullrhi unless noted): `RaftSim.P4` 8/8
  (`RiverMapLoads` for L_Hance, L_LavaCanyon, L_Terminator, L_Troublemaker,
  L_UpperHuacas, L_Zambezi, plus the two South Fork approach/parity tests),
  `RaftSim.P2` 3/3, `RaftSim.M4.CurvedRiverCoordinateMapDrivesLiveWater` 1/1.
  The Hance map-load test still asserts the reviewed smoothing (0.72) and
  standing-wave/relief scales (0.55), which this pass does not change.
- Corridor ends: with the coverage change alone the raft at 13 m still
  sat over sand with the water starting a few metres ahead
  (`corridor-end-coverage-only.jpg`); with the topology cache keyed on the
  corridor-end state the same station renders water under and behind the
  raft to the corridor's first row (`corridor-end-after.jpg`,
  `hance_end2_up_*`). The downstream capture at 596 m looks past the end of
  the 600 m world, so it shows haze rather than a bank; the solver reports
  the raft wet and floating there in both runs.
- Pool corrugation: the Froude gate on the calm standing-wave bands was
  built and photographed (`hance_calm_000_00100m_side`) and did **not**
  change the ridges, so it was reverted; the ridges are not the coupled
  standing wave. The layer isolation (`hance_iso2_*`) places both the
  ridges and the glossy parallelograms in the live volume core, consistent
  with the mirrored directional flow-normal texture; no change shipped for
  it in this pass.

## 5. Defects and follow-ups

| # | severity | finding | status |
| --- | --- | --- | --- |
| 1 | high | Guide's head rendered as a black spike from every external camera (first-person hide stayed active for review/chase view targets) | fixed in `RaftSimGuidePawn.cpp`; re-checked in `hance_crew_tq2_*` |
| 2 | high | First and last ~18 m of the corridor solver-wet but unrendered; raft floats above sand at 0–10 m and 580–590 m | fixed (`StationEdgeCoverage` + core topology keyed on `CorridorEndPadState`, section recreate on index change); verified at 13 m; P4/P2/M4 pass |
| 3 | medium | Diagonal ridge corrugation on every pool at grazing angles | open — not the standing-wave field (Froude gate tried and reverted); shading from the mirrored directional flow-normal texture of the live core |
| 4 | medium | Pale glossy parallelograms with straight edges on the water | open — same cause as #3 (alternate mirrored tiles catch the sun); isolation shows they are inside the live core, the static ribbon renders nothing visible on this map |
| 5 | low | Runout breaking water renders as a flat streaky white carpet across the channel | open — foam presentation, same family as South Fork #3 |
| 6 | low | Bank terrain: bare slopes with angular dark terrace slabs | open — known external gate of the Hance V3 review |
| 7 | low | Crew: fixed gaze; no paddle-entry splash | open (carried over) |
| 8 | info | The launch at 336 m puts the main drop (308 m) and the boulder garden behind the player; the reach above is runnable in the survey and the paddle-through | authoring decision (scenario framing), flagged only |
| 9 | info | Hance has no rock obstacle actors, so wrap/pin contacts cannot happen here (Chilko's D4 rocks are the only reference-map contacts) | flagged only |

## Tooling changes in this pass

- `RaftSim.SurveyReach` now works on Landscape-based maps: terrain traces
  accept `ALandscapeProxy` and `RaftSimSourceConditionedTerrain` besides the
  full-reach tile tag, and the rock census counts the reference maps'
  procedural boulder actors by component name (editor labels do not survive
  into `-game`). The last station of a corridor no longer reads
  "unreachable" (heading mirrored from the upstream neighbour).
- `RaftSim.CaptureRaftSeries` accepts `station=<m>` / `lateral=<m>` and walks
  the raft there first (survey hops with terrain-safe heights); the burst
  delay counts from arrival.
- `RaftSim.HideTaggedActors <tag|class=Name|component=Substring> ...
  [capture=<label>]` hides actors two seconds after the map is up (the live
  water actor spawns after `-ExecCmds` runs) and can shoot a three-quarter
  raft-attached burst afterwards, because `-ExecCmds` does not chain a
  second RaftSim command. Editor labels and some tags do not survive into
  `-game`, hence the component-name match.
- `raftsim.LogLatticeEdgeRows 1` logs wet extents and coverage of the
  twelve lattice rows at a corridor end.
- Scratch helpers: `hance_table.ps1` (per-bin survey table), `crop.ps1`,
  `resize.ps1`, `montage.ps1`.
