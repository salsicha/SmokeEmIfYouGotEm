# Pacuare, Upper Huacas (`L_UpperHuacas`) inspection — 2026-09-02

Scope requested: the same pass as the South Fork and Hance inspections, on
the Pacuare environment — crew paddling animation from several angles, a
walk down the river verifying water, rocks and boat physics, and fixes for
what turns up.

Method: headless `-game` runs of `/Game/RaftSim/Maps/L_UpperHuacas` at
1600x900 with the review commands (`RaftSim.CaptureRaftSeries`,
`RaftSim.SurveyReach`, `RaftSim.ManoeuvreCheck`). Screenshots are under
`unreal/Saved/Screenshots/` (`huacas_crew_*`, `huacas_survey_*`,
`huacas_run_*`, `huacas_calm_*`), log lines are `RaftSim survey station:` and
`RaftSim manoeuvre:`. Reduced figures: `docs/reports/images/2026-09-02-upper-huacas/`.

The map: a 600 m straight interpreted reach (identity station/lateral map at
2 m), cooked at the `rainfed_runnable_planning` band. Bed features from
`scenario_upper_huacas/window_manifest.json`: lead-in 206–268 m, two entry
boulders at 250 m (river-left, +9 m) and 258 m (river-right, −8 m) with
crests 0.6 m ABOVE the surface, a constriction 270–292 m whose walls crest
0.35 m above the water, the drop at 300 m (11 m half width, 2.6 m pool), a
lateral wall 306–324 m on the right, the second hole at 330 m (+5 m), exit
waves at 350/362/374/386 m with the big one at 400 m, and the recovery eddy
352–396 m on river-left (+16 to +27 m). The player raft launches at 4 % of
the reach (station 24 m), so the whole rapid is ahead of the player.

## 1. Crew paddling animation — pass

Bursts of 16 frames at 0.5 s with `AllForward`: three-quarter (`3.0 3.0 2.0
2.0`), bow-on (`-5 0 1.8 0`) and beam (`0 5.5 1.5 0`); figures
`crew-three-quarter-sheet.jpg`, `crew-bow-sheet.jpg`, `crew-beam-sheet.jpg`.

- Four paddlers and the guide render with heads inside the helmets, faces,
  vests over wetsuits, boots and blades; the guide (yellow helmet) is
  visible at the stern from every external camera — the view-target check
  from the Hance pass applies here unchanged.
- Stroke phases (catch, buried power phase, recovery with the blade clear)
  are visible in every burst; the raft accelerates from 1.6 m/s water to
  3.4 m/s under `AllForward` (drift log of the three-quarter burst).
- Carried over, still open: fixed gaze, no paddle-entry splash.

## 2. Reach survey (water, rocks, boat support), 0–600 m every 10 m

`RaftSim.SurveyReach 0 0 10 3 huacas_survey 30`: 61 stations, 31 hops, 61
of 61 reached, no recovery teleports, no anomalies. Figures:
`survey-chase-0-290.jpg`, `survey-chase-300-600.jpg`, `survey-side-0-290.jpg`,
`survey-side-300-600.jpg`.

| metric | value |
| --- | --- |
| stations wet (solver) | 61 / 61 |
| stations grounded | 0 |
| freeboard, floor above surface | 12.6–19 cm except 57.5 cm at 290 m (see below); mean 17.3 |
| water speed at the raft | 0.35–2.98 m/s, mean 1.07 |
| depth at the raft | 0.28–2.94 m, mean 0.91 |
| sweep samples | 181; dry centreline 0; dry sides 0; stagnant 0 |
| largest surface drop / rise per 5 m | 0.45 m (290–300 m, the drop lip) / 0.12 m |
| largest lateral tilt over 12 m | 0.09 m |
| rock obstacle actors | 0 (the map places none) |
| dressing rock/pebble instances within 30 m | ~1000 per station (11 872 summed; rainforest bank pebbles and boulders) |

| from m | n | wet | water m/s | depth m | freeboard cm | max drop m/5 m | pitch deg |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 5 | 5 | 1.09–1.15 | 0.68–0.74 | 16–18 | 0.07 | 0.2–0.7 |
| 50 | 5 | 5 | 1.10–1.16 | 0.64–0.66 | 16–18 | 0.07 | 0.2–1.0 |
| 100 | 5 | 5 | 1.16–1.18 | 0.62–0.64 | 15–17 | 0.08 | 0.5–0.9 |
| 150 | 5 | 5 | 1.16–1.22 | 0.56–0.61 | 17–18 | 0.09 | 0.0–1.2 |
| 200 | 5 | 5 | 0.68–0.99 | 1.20–1.47 | 16–17 | 0.39 | 0.1–0.4 |
| 250 | 5 | 5 | 0.95–2.98 | 0.28–1.62 | 15–58 | 0.45 | 0.0–0.8 |
| 300 | 5 | 5 | 0.35–1.95 | 0.84–2.94 | 13–19 | 0.12 | 0.1–7.3 |
| 350 | 5 | 5 | 0.79–1.43 | 0.49–0.61 | 16–18 | 0.09 | 0.2–1.1 |
| 400 | 5 | 5 | 1.21–1.27 | 0.63–0.64 | 16–17 | 0.09 | 0.2–1.0 |
| 450 | 5 | 5 | 1.21–1.27 | 0.61–0.62 | 17 | 0.09 | 0.3–1.0 |
| 500 | 5 | 5 | 0.90–1.20 | 0.63–0.81 | 15–18 | 0.08 | 0.1–1.1 |
| 550 | 6 | 6 | 0.50–0.84 | 0.85–1.41 | 16–18 | 0.03 | 0.1–0.5 |

### Water — what is right

- A shallow (0.6–0.7 m), steady 1.1–1.2 m/s run above the lead-in, the
  lead-in pool deepening to 1.5 m at 200–260 m, the constriction sill at
  290 m (0.28 m deep, 3.0 m/s), the drop into a 2.9 m pool that runs at
  0.35 m/s at 300–310 m, the second hole (pitch −7.3° at 320 m, 1.95 m/s),
  then the exit waves and a 0.6 m deep 1.2 m/s runout to a slower 1.4 m
  pool at the end. The eddy behind the drop and the recovery eddy read as
  slack water in the side views.
- The raft floats at 13–19 cm freeboard at every station with no dry or
  grounded support points and no capsize. The 57.5 cm freeboard at 290 m
  is the raft resting across the drop lip: the sampled surface under its
  centre is already the lower pool while the tubes still ride the sill, a
  rigid-hull artefact of a 2.5 m step, not a support failure (pitch −0.4°,
  no dry points).
- Water renders to both corridor ends (the Hance corridor-end fix is
  shared code): the side view at 0 m shows the raft on water at the first
  station, and the 600 m station sits at the corner of the last rendered
  row.
- Rocks: the two entry boulders (250/258 m, crests +0.6 m) and the
  constriction walls are carved into the landscape and show as brown rock
  above the water (`entry-boulders-250m.jpg`); bank dressing (pebbles and
  boulders) is dense on both shores; none floats or drowns. There are no
  rock obstacle actors on this map, so no wrap/pin contacts.
- Foam and spray: breaking crests on the drop and the exit waves only; the
  wave-impact spray cloud fires at 320–330 m and at 200–210 m where the
  raft hits the lead-in wave.

### Water — defects

1. **Bright bars spanning the channel on every pool** (`pool-bars-before.jpg`,
   every `huacas_survey_*_side` frame). From the shore camera the whole
   surface is crossed by regular bright bands perpendicular to the flow,
   converging with perspective — far more visible than the Hance
   corrugation, and matching the South Fork description of the
   station-periodic calm bands of the coupled standing-wave field ("at
   grazing angles its 2 cm sine ridges become bright bars spanning the
   channel"). This map runs the field at `LivePresentationStandingWaveScale
   0.78` (Hance 0.55), on a 0.6 m deep 1.2 m/s run (Fr 0.5). Status: see
   the A/B in section 4.
2. **The corridor ends in a hard straight edge** at 600 m with haze beyond
   (`huacas_survey_060_*`); the map is 600 m long and nothing continues.
   Authoring boundary, not a render defect; flagged only.

## 3. Boat physics

### Manoeuvre check (`RaftSim.ManoeuvreCheck`, launch at 24 m)

| phase | command window | raft speed (m/s) | water at raft (m/s) | yaw rate (deg/s) |
| --- | --- | --- | --- | --- |
| drift | 0–2 s Rest | 1.47–1.52 | 1.45–1.48 | 0 |
| forward | 2–14 s AllForward | 3.0–3.6 | 1.5–1.6 | 0 |
| stop | 14–20 s Stop | 2.0 → 1.0 | 1.5–1.6 | 0 |
| back | 20–30 s AllBackward | 0.55–1.07 | 1.40–1.49 | 0 |
| turn left | 34–44 s TurnLeft | 1.4–1.5 | 1.35–1.38 | −8.6 to −10.4 |
| turn right | 44–54 s TurnRight | 1.4–1.5 | 1.31–1.35 | +8 to +10.2 |
| rest | 54–58 s Rest | 1.45 | 1.30 | 0.6 |

Pass: forward paddling adds ~2 m/s over the current, `Stop` brings the raft
0.5 m/s below the water speed within five seconds, back-paddling holds
0.4–0.9 m/s of upstream way against a 1.45 m/s current, turns run 8–10 deg/s
both ways and the heading returns to within a degree after the sequence.
The shallow, steady run above the lead-in gives cleaner numbers than the
Hance wave train: no water-speed spikes and no roll.

### Paddle-through from 30 m

`RaftSim.CaptureRaftSeries 6 60 2 huacas_run 3.2 0 2.3 4 paddle station=30`:
the raft was already within 6 m of the station (launch at 24 m), so no walk
was needed; 60 chase frames at 2 s with `AllForward` (`run-30-to-drop.jpg`,
`run-drop-to-runout.jpg`). Pass: the raft ran the shallow lead-in run at
3–3.7 m/s, the lead-in pool, the entry boulders and the constriction, the
drop (frame 25: spray over the bow), the second hole and the exit wave
train (frames 35–47: breaking crests and two spray clouds), and settled
into the runout, with no capsize, no grounding and the guide visible at
the stern throughout. Drift telemetry over the run: 49 m to 385 m, floor
freeboard never below 5.1 cm (in the drop), pitch never beyond 10°, zero
ground contacts.

## 4. Bright-bar A/B and the cooked-field pits

Three single-station shots from the shore camera at 100 m
(`pool-bars-ab.jpg`, `huacas_ab_*_side`), same raft position:

| variant | how | result |
| --- | --- | --- |
| base | — | bars |
| live overlay hidden | `-dpcvars=raftsim.HideLiveOverlay=1` | bars unchanged |
| standing-wave field off | `-dpcvars=raftsim.PresentationStandingWaveScale=0` (new review override; the presentation log confirms `standing_wave_scale=0.00`) | bars unchanged |

An earlier A/B with the calm bands of the standing-wave field gated by
Froude number (built, photographed at 40 m and 100 m, then reverted) also
left the bars unchanged — at this station the gate only reached 73 % of
the bands, which is why the full field override above was added. A fourth
run replaced every live-water vertex normal with straight up
(`-dpcvars=raftsim.FlatWaterNormals=1`, new review override): bars
unchanged again (`huacas_ab3_flat_000_00100m_side`,
`pool-bars-flat-normals-ab.jpg`). So the bars are not
geometry at all — not the analytic standing-wave field, not the overlay,
not the solved vertex normals, and the cooked field beneath is a clean
grade. They come from the live core's material: its flow-normal texture
or ripple layer, tiled in river coordinates so that the pattern lines up
across the channel. That is the same conclusion as the Hance corrugation
(a mirrored, directional flow-normal texture). Open — the fix is on the
material/texture side (`MI_RaftSim_PacuareUpperHuacas_LiveVolumeWaterV1`
and `T_RaftSim_PacuareUpperHuacas_FlowNormalV1.png`); the two overrides
above make any further bisection a matter of single runs.

The cooked field itself was read directly (`h.npy`, `bed.npy`, `u.npy` of
the rainfed band, 2 m cells): along the channel centre the surface is a
clean linear grade (second difference 0.000 over 40–70 cells), so the bars
are not solver rows. A scan of all wet cells for one-cell surface pits
(mean of the two station neighbours minus the centre) finds 13 cells deeper
than 0.5 m, max 0.65 m, all at columns 149 and 164 (the drop at 298 m and
the second hole at 328 m) — the same supercritical shock-cell artefact that
is far stronger on Futaleufú (see that report); here it stays inside the
drop's own foam and is not visible.

## 5. Defects and follow-ups

| # | severity | finding | status |
| --- | --- | --- | --- |
| 1 | medium | Bright bars spanning the channel on every pool from the shore camera | open — A/B excludes the live overlay and the analytic standing-wave field (both toggled off, bars unchanged) and the cooked field is smooth; shading on the live core itself (vertex normals or material); review overrides `raftsim.PresentationStandingWaveScale` and `raftsim.FlatWaterNormals` added for the next bisection |
| 2 | low | One-cell surface pits in the cooked field at the drop (298 m) and the second hole (328 m), up to 0.65 m | open — cooking-pipeline limiter; hidden inside the drop's foam here |
| 3 | low | Corridor ends in a hard straight edge at 600 m with haze beyond | authoring boundary, flagged only |
| 4 | low | Crew: fixed gaze; no paddle-entry splash | open (carried over) |
| 5 | info | 57.5 cm freeboard reading at 290 m is the rigid hull straddling the drop lip, not a support failure | no action |
| 6 | info | No rock obstacle actors, so wrap/pin contacts cannot happen here | flagged only |
