# Futaleufú, Terminator (`L_Terminator`) inspection — 2026-09-02

Scope requested: the same pass as the South Fork, Hance and Pacuare
inspections, on the Futaleufú environment — crew paddling animation from
several angles, a walk down the river verifying water, rocks and boat
physics, and fixes for what turns up.

Method: headless `-game` runs of `/Game/RaftSim/Maps/L_Terminator` at
1600x900 with the review commands (`RaftSim.CaptureRaftSeries`,
`RaftSim.SurveyReach`, `RaftSim.ManoeuvreCheck`). Screenshots are under
`unreal/Saved/Screenshots/` (`terminator_crew_*`, `terminator_survey_*`,
`terminator_run_*`), log lines are `RaftSim survey station:` and
`RaftSim manoeuvre:`. Reduced figures: `docs/reports/images/2026-09-02-terminator/`.

The map: a 600 m straight interpreted reach (identity station/lateral map
at 2 m), cooked at the `median_runnable` band, cold-water optics
(`MI_RaftSim_FutaleufuTerminator_LiveVolumeWater`, CPU chop and embedded
aeration V2). Bed features from `scenario_terminator/window_manifest.json`:
an entry wave train at 132/150/168/186 m (crests 0.32 m under the surface),
the scout eddy 196–246 m on river-right (−22 to −34 m) behind a bar
cresting 0.2 m above the water, the marker rock at 266 m (−8 m, radius
3.2 m, crest 0.7 m ABOVE the surface), the Terminator hole at 300 m
(8 m half width, 2.6 m pool) with a second hole at 322 m (+10 m), the
right line 300–332 m, a sneak channel 250–396 m on river-left (+21 to
+30 m) behind a berm cresting 0.2 m above the water, the recovery eddy
468–520 m on river-right, and a portage trail along the right bank. The
player raft launches at 4 % of the reach (station 24 m).

## 1. Crew paddling animation — pass

Bursts of 16 frames at 0.5 s with `AllForward`: three-quarter, bow-on and
beam (`crew-three-quarter-sheet.jpg`, `crew-bow-sheet.jpg`,
`crew-beam-sheet.jpg`). Four paddlers and the guide render with heads,
faces, helmets, vests, boots and blades from every angle; stroke phases
are visible in every burst; the guide is present at the stern (the Hance
view-target fix). Carried over, still open: fixed gaze, no paddle-entry
splash.

## 2. Reach survey (water, rocks, boat support), 0–600 m every 10 m

`RaftSim.SurveyReach 0 0 10 3 terminator_survey 30`: 61 stations, 61 of 61
reached, no recovery teleports, two stations with anomalies (both in the
entry wave train, see below). Figures: `survey-chase-0-290.jpg`,
`survey-chase-300-600.jpg`, `survey-side-0-290.jpg`, `survey-side-300-600.jpg`.

| metric | value |
| --- | --- |
| stations wet (solver) | 61 / 61 |
| stations grounded | 0 |
| freeboard, floor above surface | 5.0–27.6 cm, mean 16.6 (5 cm in the second hole at 400–450 m; 27.6 cm on the entry wave face at 150 m) |
| water speed at the raft | 0.34–2.86 m/s, mean 1.24 |
| depth at the raft | 0.76–3.61 m, mean 2.88 |
| sweep samples | 181; dry centreline 0; dry sides 0; stagnant 0 |
| largest surface drop / rise per 5 m | 2.55 m / 1.18 m (both at 190 m) |
| largest lateral tilt over 12 m | 0.26 m |
| rock obstacle actors | 1 (the marker rock at 266 m, counted at six stations; never floating or drowned) |
| dressing boulder instances within 30 m | 127 over 48 stations |

| from m | n | wet | water m/s | depth m | freeboard cm | max drop m/5 m | pitch deg | anomalies |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 5 | 5 | 1.59–1.83 | 2.86–3.12 | 16–17 | 0.04 | 0.0–0.6 | |
| 50 | 5 | 5 | 1.17–1.43 | 3.29–3.61 | 16–17 | 0.03 | 0.0–0.4 | |
| 100 | 5 | 5 | 0.52–1.12 | 3.49–3.61 | 16–17 | 0.26 | 0.1–0.5 | |
| 150 | 5 | 5 | 0.58–2.74 | 0.76–3.20 | 17–28 | 2.55 | 0.2–24.2 | 150: pitch −24°, drop 1.04 m; 190: rise 1.18 m, drop 2.55 m |
| 200 | 5 | 5 | 1.83–2.67 | 1.73–1.93 | 16–18 | 0.14 | 0.3–1.2 | |
| 250 | 5 | 5 | 1.44–2.86 | 1.96–2.61 | 9–17 | 0.15 | 0.7–6.4 | |
| 300 | 5 | 5 | 0.59–2.26 | 2.63–2.88 | 16–17 | 0.73 | 0.1–1.1 | |
| 350 | 5 | 5 | 0.46–2.08 | 1.19–3.37 | 16–21 | 0.49 | 0.2–3.7 | |
| 400 | 5 | 5 | 0.44–2.36 | 1.15–3.30 | 5–19 | 0.70 | 0.8–8.4 | |
| 450 | 5 | 5 | 0.34–0.38 | 3.05–3.39 | 16–17 | 0.02 | 0.0–0.6 | |
| 500 | 5 | 5 | 0.43–0.56 | 3.39–3.51 | 16–17 | 0.03 | 0.1–0.3 | |
| 550 | 6 | 6 | 0.54–0.55 | 3.59–3.61 | 16 | 0.03 | 0.0–0.2 | |

### Water — what is right

- The reach reads as big water: a 3 m deep 1.6–1.8 m/s approach, the entry
  wave train shoaling to 0.8–1.0 m at 2.5–2.7 m/s over each hump, the
  marker rock standing 0.7 m proud of the surface at 266 m (a real
  `ARaftSimRockObstacleActor`, correctly at the waterline), the Terminator
  hole and the second hole with breaking crests and spray (frames 036–044),
  and a 3.4–3.6 m deep 0.5 m/s pool below 450 m to the corridor end.
- The raft floats at every station with no dry or grounded support points
  and never capsized in any run; water renders to both corridor ends.
- Bank dressing (boulders, firs, scanned understory) is present on both
  shores; the scout eddy and recovery eddy read as slack water.

### Water — defects

1. **One-cell surface pits in the cooked field render as stepped walls.**
   Reading `h.npy`/`bed.npy`/`u.npy` (median band, 2 m cells) along the
   channel centre: each entry-wave hump shoals the flow to 0.7–1.3 m at
   2.5–4 m/s and the very next cell is a single-cell hole — surface 208.96 m
   between 210.44 and 209.41 at 152 m (1.5 m pit, 6.2 m/s), 206.07 m between
   208.65 and 207.45 at 190 m (2.6 m pit, 6.0 m/s). A scan of all wet cells
   finds 87 pits deeper than 0.5 m (max 1.99 m by the neighbour-mean
   measure) at columns 76–98, 134–161, 187 and 220. The lattice renders
   them faithfully: the 190 m side view shows a 2.5 m stepped wall with
   straight creases and a foam plateau on top (`entry-jump-190m-step.jpg`),
   and the survey sweep reports the 2.55 m drop. The raft rides over them
   because support uses the smoothed coupled surface (pitch −24° when
   parked on the face at 150 m, no dry points). This is a cooking-pipeline
   artefact (a supercritical shock cell), present in all four reference
   fields (Hance 35 cells / 1.03 m, Upper Huacas 13 / 0.65 m, Lava Canyon
   7 / 0.76 m) and by far the strongest here. Open — belongs in the cooking
   limiter or a despike in the cooked-field loader, not in shading.
2. **Foam plateaus with rectangular cut-outs** over the entry waves and
   the holes (`entry-waves-150m-foam-cutouts.jpg`, chase frames 013–019,
   036–044): the breaking-water foam covers whole lattice cells with hard
   edges, so the wave train reads as white slabs with square dark holes
   rather than crests. Same family as the Hance runout carpet, much more
   visible here because the foam covers most of the channel. Open —
   presentation.
3. **Concentric ring ripples on the pools** (chase frames 046–054, side
   frames 046–059; full-size example `pool-rings-480m.jpg`): the calm water
   below 450 m is covered in overlapping circular ripple rings 5–10 m
   across, regular enough to read as a pattern. This is the cold-water CPU
   chop / boil microrelief presentation of this map
   (`RaftSimColdWaterCpuChopV2`). Open — cosmetic, needs a less periodic
   source.
4. **Bright streak bands** at grazing angles on the approach (side frames
   000–012), as on the other reference maps (see the Pacuare report for the
   A/B that excludes the standing-wave field and the overlay as sources).

## 3. Boat physics

### Manoeuvre check (`RaftSim.ManoeuvreCheck`, launch at 24 m)

| phase | command window | raft speed (m/s) | water at raft (m/s) | yaw rate (deg/s) |
| --- | --- | --- | --- | --- |
| drift | 0–2 s Rest | 1.96–1.98 | 1.95 | 0 |
| forward | 2–14 s AllForward | 3.1–3.9 | 1.6–1.95 | 0 |
| stop | 14–20 s Stop | 1.9 → 0.9 | 1.5–1.6 | 0 |
| back | 20–30 s AllBackward | 0.53–1.06 | 1.37–1.48 | 0 |
| turn left | 34–44 s TurnLeft | 1.2–1.4 | 1.2–1.3 | −8.5 to −10.3 |
| turn right | 44–54 s TurnRight | 1.2–1.3 | 1.1–1.2 | +7.4 to +9.7 |
| rest | 54–58 s Rest | 1.22 | 1.07 | 0.2 |

Pass, and numerically almost identical to Pacuare: forward paddling adds
~1.7 m/s over the current, `Stop` holds the raft 0.6 m/s below the water
within five seconds, back-paddling makes 0.4–0.9 m/s upstream against a
1.4 m/s current, turns run 7–10 deg/s both ways, no roll and no capsize.

### Paddle-through from 30 m

`RaftSim.CaptureRaftSeries 6 60 2 terminator_run 3.2 0 2.3 4 paddle
station=30` (`run-30-to-hole.jpg`, `run-hole-to-runout.jpg`): 60 chase
frames at 2 s with `AllForward` from 53 m to 405 m. Pass: the raft ran the
approach, the entry wave train (frames 13–20, buried in foam and spray at
frame 18), the marker rock line, the Terminator hole and the second hole
(36–44), and the wave train below (50–56) without a capsize, with floor
freeboard never below 10.5 cm, pitch within ±7.7°, roll within ±1.1°,
15 kg of retained water at most, and zero ground contacts. The parked
survey readings on the wave faces (pitch −24° at 150 m, 5 cm freeboard in
the second hole) are the extremes of a stationary hull on the steep cooked
surface; underway the hull rides over them.

## 4. Defects and follow-ups

| # | severity | finding | status |
| --- | --- | --- | --- |
| 1 | high | One-cell surface pits behind every entry-wave hump in the cooked field (1.5 m at 152 m, 2.6 m at 190 m; 87 cells > 0.5 m) render as stepped walls with straight creases and drive the survey's 2.55 m/5 m drop | open — cooking-pipeline limiter or a despike in the cooked-field loader; also present, weaker, on the other three reference fields |
| 2 | medium | Breaking-water foam renders as white slabs with rectangular cut-outs over the entry waves and the holes | open — presentation (cell-hard foam coverage); same family as Hance's runout carpet |
| 3 | medium | Concentric ring ripples 5–10 m across cover the calm pools below 450 m | open — cold-water CPU chop / boil microrelief looks periodic |
| 4 | medium | Bright streak bands at grazing angles on the approach | open — see the Pacuare A/B; not the standing-wave field nor the overlay |
| 5 | low | Corridor ends in a hard straight edge at 600 m | authoring boundary, flagged only |
| 6 | low | Crew: fixed gaze; no paddle-entry splash | open (carried over) |
| 7 | info | Parked-hull readings on the wave faces (pitch −24° at 150 m, 5 cm freeboard at 400–450 m) are stationary extremes, not support failures; the paddle-through stays within ±8° | no action |
