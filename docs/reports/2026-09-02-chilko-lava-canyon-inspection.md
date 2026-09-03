# Chilko, Lava Canyon (`L_LavaCanyon`) inspection — 2026-09-02

Scope requested: the same pass as the South Fork, Hance, Pacuare and
Futaleufú inspections, on the Chilko environment — crew paddling animation
from several angles, a walk down the river verifying water, rocks and boat
physics, and fixes for what turns up.

Method: headless `-game` runs of `/Game/RaftSim/Maps/L_LavaCanyon` at
1600x900 with the review commands (`RaftSim.CaptureRaftSeries`,
`RaftSim.SurveyReach`, `RaftSim.ManoeuvreCheck`). Screenshots are under
`unreal/Saved/Screenshots/` (`lava_crew_*`, `lava_survey_*`, `lava_run_*`),
log lines are `RaftSim survey station:` and `RaftSim manoeuvre:`. Reduced
figures: `docs/reports/images/2026-09-02-lava-canyon/`.

The map: a 600 m straight interpreted reach (identity station/lateral map
at 2 m), cooked at the `median_runnable` band, cold-water optics. Bed
features from `scenario_lava_canyon/window_manifest.json`: an entry tongue
48–128 m, a wave train 128–468 m (16 m half width) over 18 bed ribs from
150 m at an 18 m wavelength (crests 1.55 m under the surface), the canyon
constriction 208–356 m whose walls crest 1.4 m above the water (inner half
width 13 m), three broach rocks (crests 1.1 m under the surface) plus 26
bed boulders (crests 0.75–1.25 m under), a lateral wave 320–340 m, a wood
hazard 300–360 m on the right bank, runout waves at 486/508/530/552 m
(crests 1.6 m under) and the recovery eddy 500–556 m on river-left. This is
the one reference map with rock obstacle actors: four `ARaftSimRockObstacleActor`
contacts (three broach rocks at 250/300/392 m and the first seeded boulder
at 406 m) for wrap/pin physics. The player raft launches at 38 % of the
reach (station 228 m, deep subcritical water above the constriction).

## 1. Crew paddling animation — pass

Bursts of 16 frames at 0.5 s with `AllForward`: three-quarter, bow-on and
beam (`crew-three-quarter-sheet.jpg`, `crew-bow-sheet.jpg`,
`crew-beam-sheet.jpg`), taken from the launch at 228 m as the raft runs
into the constriction wave train. Four paddlers and the guide render with
heads, faces, helmets, vests, boots and blades from every angle; stroke
phases are visible in every burst; the guide is present at the stern (the
Hance view-target fix); the beam burst ends with the bow burying into a
breaking wave with spray over the crew (frames 14–15). Carried over, still
open: fixed gaze, no paddle-entry splash.

## 2. Reach survey (water, rocks, boat support), 0–600 m every 10 m

`RaftSim.SurveyReach 0 0 10 3 lava_survey 30`: 61 stations, 61 of 61
reached, no recovery teleports. Figures: `survey-chase-0-290.jpg`,
`survey-chase-300-600.jpg`, `survey-side-0-290.jpg`, `survey-side-300-600.jpg`.

| metric | value |
| --- | --- |
| stations wet (solver) | 61 / 61 |
| stations grounded | 0 |
| freeboard, floor above surface | 12.2–18.6 cm, mean 16.3 |
| water speed at the raft | 0.64–2.18 m/s, mean 1.20 |
| depth at the raft | 0.84–2.69 m, mean 2.03 |
| sweep samples | 181; dry centreline 0; dry sides 0; stagnant 0 |
| largest surface drop / rise per 5 m | 0.93 m (300–310 m) / 0.61 m (350 m) |
| largest lateral tilt over 12 m | 0.75 m (340–350 m, the lateral wave) |
| rock obstacle actors within 30 m | 4 distinct (25 station-counts), all "drowned" (top more than 1 m under the surface) — by placement |
| dressing rock/pebble instances within 30 m | ~1400 per station in the canyon, 9 552 at 550 m (bar) |
| anomalies | `raft_damaged` from 300 m to the end (see physics); 340 m: terrain 68 cm above the water at the centreline, lateral tilt 0.73 m; 350 m: rise 0.61 m/5 m, tilt 0.75 m |

| from m | n | wet | water m/s | depth m | freeboard cm | max drop m/5 m | pitch deg |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 5 | 5 | 1.77–2.10 | 1.90–2.13 | 16–17 | 0.03 | 0.2–0.6 |
| 50 | 5 | 5 | 1.27–1.64 | 2.20–2.37 | 16–17 | 0.03 | 0.0–0.4 |
| 100 | 5 | 5 | 0.92–1.22 | 2.15–2.34 | 16–18 | 0.03 | 0.1–0.6 |
| 150 | 5 | 5 | 0.84–1.52 | 1.31–2.09 | 16–19 | 0.11 | 0.1–0.9 |
| 200 | 5 | 5 | 1.04–1.93 | 1.66–2.24 | 16–18 | 0.05 | 0.3–0.9 |
| 250 | 5 | 5 | 1.12–2.18 | 0.84–1.60 | 16–18 | 0.44 | 0.0–2.5 |
| 300 | 5 | 5 | 1.25–2.07 | 1.13–2.08 | 13–17 | 0.93 | 0.6–1.6 |
| 350 | 5 | 5 | 1.00–1.72 | 1.61–2.21 | 12–17 | 0.58 | 0.1–0.8 |
| 400 | 5 | 5 | 0.70–1.27 | 1.57–2.48 | 15–17 | 0.09 | 0.2–0.5 |
| 450 | 5 | 5 | 0.71–0.87 | 2.01–2.44 | 14–17 | 0.03 | 0.0–0.5 |
| 500 | 5 | 5 | 0.66–0.73 | 2.21–2.36 | 16–17 | 0.03 | 0.3–0.6 |
| 550 | 6 | 6 | 0.64–0.89 | 1.93–2.69 | 15–17 | 0.03 | 0.0–0.4 |

### Water — what is right

- A 2 m deep 1.3–2.1 m/s approach, the wave train shoaling over the ribs
  (0.84 m at 250–290 m), the canyon constriction with breaking crests and
  spray at 300–340 m (chase frames 030–034, side 030 and 034), the lateral
  wave at 340–350 m (0.75 m of cross-channel tilt), then a 2–2.7 m deep
  0.7 m/s runout to the corridor end; the recovery eddy on river-left reads
  as slack water.
- The raft floats at every station with no dry or grounded support points,
  never capsized in any run, and water renders to both corridor ends (the
  corridor-end fix from the Hance pass is shared code).
- Banks: rock ledges of the constriction walls, gravel bars, firs and
  dressing boulders on both shores; the wood hazard on the right bank.

### Water — defects

1. **Bright streak bands** at grazing angles on every pool (side frames
   036–054), the same material banding as the other three reference maps
   (see the Pacuare A/B: not the standing-wave field, not the overlay, not
   the vertex normals — the live core's material).
2. **Landscape above the water at the centreline at 340 m** (68 cm, from
   the survey's terrain trace) while the solver has 1.1 m of water there:
   a gravel bar of the visual landscape intrudes into the cooked channel
   at the lateral wave (side frames 034–035 show the bar next to the
   raft). Authoring mismatch between the conditioned landscape and the
   cooked bed; the raft floats past it because support follows the solver.
3. **One-cell surface pits** in the cooked field: 7 cells deeper than
   0.5 m, max 0.76 m, at columns 152 and 175 (304 m and 350 m) — the
   weakest of the four reference fields (see the Futaleufú report for the
   scan); not visible here beyond the constriction's own foam.

## 3. Boat physics

### The invisible broach rocks pin the raft

Lava Canyon is the only reference map with `ARaftSimRockObstacleActor`
contacts: three broach rocks at 250 m (+3.5 m), 300 m (−4 m) and 392 m
(+2 m) plus the first seeded boulder at 406 m, all with contact radius
2.4 m and their visual crests 1.03–1.1 m BELOW the water. The flexible
raft model's rock contact is planar — `XyDistance` between tube segment and
rock, a port of `_contact_payload` in `physics/src/raftsim/flexible_raft_d4.py`
— so every rock is an infinite vertical cylinder and a crest a metre under
the surface stops the hull like a surface rock:

- Paddle-through from 30 m (`run-30-to-broach-rock.jpg`,
  `run-pinned-at-bank.jpg`): clean run at 3.3–3.9 m/s to 176 m, then at the
  250 m rock fabric integrity dropped 1.00 → 0.74, the raft was swung
  13.7 m to river-left and finished the 120 s pinned against the left
  bank at 249 m, spinning slowly (frames 40–59).
- Survey: the centreline teleport at 300 m sat the raft on the 300 m rock
  (pressure 1.00 → 0.90, integrity 0.78) and the damage flag persisted to
  the end of the reach (`raft_damaged` at every station from 300 m).
- Manoeuvre check (launch at 228 m): forward paddling reached 3.1–3.7 m/s,
  `Stop` and `AllBackward` behaved as on the other maps (1.7 and 0.9–1.4
  m/s in 1.8–2.5 m/s water), then at t = 31–33 s the raft stalled to
  0.05 m/s in 2.4 m/s water on the 300 m rock, `TurnLeft` spun it around
  the rock at up to 20.8 deg/s, and it washed off at 3.2 m/s facing 62°;
  `TurnRight` continued the rotation to 158° — the raft ended the sequence
  travelling stern-first. No capsize.

This is the review-gated D4 wrap/pin scenario doing what its placement
intended, and the wrap, release and damage mechanics all fired. But from
the player's seat the raft snags and pins on nothing visible, and every
downstream reading carries the damage. Either the contact rule needs the
rock's height (skip rocks whose top is below the tube bottom — in the
Python reference model and its C++ port together, because the parity
fixtures pin the current planar rule), or the four rocks need their
visual crests raised to the surface. Flagged, not changed here.

### Manoeuvre and support envelope elsewhere

Away from the rocks the envelope matches the other maps: 12–19 cm
freeboard at rest, pitch within ±2.5°, forward paddling +1.5–2 m/s over
the current, turns 7–10 deg/s once clear of the rock.

## 4. Defects and follow-ups

| # | severity | finding | status |
| --- | --- | --- | --- |
| 1 | high | Submerged D4 broach rocks (crests 1.0–1.1 m under the surface, invisible) pin and damage the raft because the flexible model's rock contact is planar | open — design decision: height-aware contact in the Python reference model and its C++ port, or raise the rocks' crests to the surface |
| 2 | medium | Bright streak bands at grazing angles on every pool | open — live core material (see the Pacuare A/B) |
| 3 | medium | Landscape gravel bar 68 cm above the solver water at the centreline at 340 m | open — landscape/bed authoring mismatch |
| 4 | low | One-cell cooked-field pits at 304 m and 350 m (max 0.76 m) | open — cooking-pipeline limiter (weakest of the four fields) |
| 5 | low | Corridor ends in a hard straight edge at 600 m | authoring boundary, flagged only |
| 6 | low | Crew: fixed gaze; no paddle-entry splash | open (carried over) |
