# Linux review & playtest setup — 2026-08-06

First interactive review session hosted on the Linux machine (RTX 4000 Ada,
UE 5.8.1 source build at `~/UnrealEngine`). This file is both the setup
record and the working instructions; per-session findings go in sibling
`docs/playtest-notes/YYYY-MM-DD-<topic>.md` files with screenshots.

## Launching

Always launch through the hybrid-graphics-safe wrapper (2026-08-06: the bare
editor segfaulted in the NVIDIA driver's swapchain present on this machine;
the wrapper pins Vulkan to the proprietary NVIDIA ICD and the Optimus layer —
see the script header for the crash forensics):

Editor (interactive PIE, recommended for review):

```bash
~/repos/SmokeEmIfYouGotEm/unreal/Scripts/run_editor_linux.sh
```

Standalone uncooked game (menu flow, closest to the shipped experience):

```bash
~/repos/SmokeEmIfYouGotEm/unreal/Scripts/run_editor_linux.sh -game -windowed -resx=2560 -resy=1440
```

Direct-to-map (skip menus; substitute any map below):

```bash
~/repos/SmokeEmIfYouGotEm/unreal/Scripts/run_editor_linux.sh /Game/RaftSim/Maps/L_Troublemaker -game -windowed
```

Maps: `L_RaftSimBoot` (menu), `L_RaftSimTestTank` (Training Eddy),
`L_Troublemaker`, `L_SouthForkAmerican_FullReach`, and the reference runs
`L_Hance`, `L_LavaCanyon`, `L_Terminator`, `L_UpperHuacas`, `L_Zambezi`.

The `__NV_PRIME_RENDER_OFFLOAD=1` prefix keeps Vulkan on the discrete NVIDIA
GPU instead of the integrated Intel one. First-ever map loads compile Vulkan
shaders; a warm-up pass across all six river maps pre-fills the DDC so
interactive loads should be quick.

## Controls (from the generated IMC_RaftSimDefault)

Guide and crew are fully separate channels (2026-08-11): W/S/A/D move
ONLY the guide's own paddle — one stern paddler's power, full steering
authority — and never make the crew stroke. The crew paddles only on
called commands (number keys / D-pad), and a called command holds — the
crew keeps its cadence until Stop or a different call. Steering strokes
(A/D) work over a standing crew command, which is the real technique:
call "all forward", then steer with your own blade.

| Action | Keyboard/Mouse | Gamepad |
|---|---|---|
| Guide's own stroke, forward / back | W / S | Left stick Y |
| Guide steering stroke (stern draw/pry), left / right | A / D | Left stick X |
| Look | Mouse | Right stick |
| Crew command: All Forward (holds until Stop) | 1 | D-pad up |
| Crew command: All Back (holds until Stop) | 2 | D-pad down |
| Crew command: Turn Left (holds until Stop) | 3 | D-pad left |
| Crew command: Turn Right (holds until Stop) | 4 | D-pad right |
| Crew command: Stop (crew rests) | 5 | Y / Triangle |
| High Side (also re-right when capsized) | Space | X / Square |
| Rescue: select swimmer | Mouse wheel | Shoulder buttons |
| Rescue: reach grab (close) | E | A / Cross |
| Rescue: throw line (far) | R | Right trigger |
| Reseat rescued crew | F | B / Circle |
| Chase camera toggle (Free Run only; default is guide POV) | C | Right-stick click |
| Cycle weather (clear morning / overcast / storm dusk) | T | Left-stick click |
| Pause | Esc | Menu button |

Console (` key): `stat fps`, `stat unit` (budgets: game thread ≤ 8 ms,
water solver ≤ 1.6 ms/tick, no streaming hitch > 33 ms), `HighResShot 2`
for screenshots (written under `unreal/Saved/Screenshots/`).

## What needs human review (the open gates)

95 review/acceptance JSONs are fail-closed waiting on a named human. They
collapse into five judgment areas:

1. **M9 South Fork acceptance packet** — `docs/release-review/m9-south-fork-acceptance.md`.
   Judge the five canonical fixed-camera views (Chili Bar launch, Meat
   Grinder guide-eye, Troublemaker approach, Coloma bridge, Salmon Falls
   takeout): does each read as a photograph of a real river at guide level —
   water body, banks, canopy, light? Is every hazard readable at a glance?
2. **Per-river photoreal candidates** — 50 reviews under
   `docs/environment-captures/photoreal_river_previews/landscape_candidates/`.
   Each river's guide-seat/river-eye pair is "reference-runnable accepted,
   photoreal rejected". Confirm or overturn per river; name the top three
   visual blockers per river so polish stops being unranked.
3. **Character/crew art** — the MetaHuman roster, CC0 fallback bodies,
   splash jacket, PFD, helmet, paddle grips. Do the paddlers read as real
   rafters in motion, at guide-seat distance? (The repo's own verdicts
   reject them for hand topology, garment integration, silhouette.)
4. **Rapid realism & hazard readability (playable)** — the guide-review
   gates: does each named rapid behave and read like its real counterpart
   (line choice, hole strength, eddy service)? These can only be judged by
   playing, not from stills.
5. **Rights/attribution sign-off** — `CREDITS.md`, per-item manifests, the
   AI-audio and CC0 intake policies; a read-through-and-sign gate, no play
   needed.

There are **no videos** in the repo; all committed evidence is stills plus
in-engine deterministic captures. The P6 trailer does not exist yet.

## Playtest scripts (do these in order; note per item pass/fail + feel)

**A. Training Eddy sanity (10 min)** — `L_RaftSimTestTank` via menu
"Training Eddy". Raft settles level and dry; strokes translate/turn the
raft; crew commands 1–5 visibly change paddling; Space triggers coordinated
high-side lean; Esc pauses; settings persist after quit/relaunch.

**B. Troublemaker scored run (20 min)** — menu → **Change Mode** until
`Mode: Free Run` (every run is `[ready]` in Free Run), **Next Run** until
`Run: Troublemaker Rapid Challenge`, then **Start Selected Run**. Leave
the scout eddy (run starts), read the tongue, run the gut or sneak. Judge:
does the water push the raft believably (tongue acceleration, lateral
shoves, hole grab)? Intentionally drop into the gut hole side-on to force a
flip: crew ejects as swimmers, raft capsizes; Space re-rights; wheel-select
a swimmer, E when adjacent, R at range, F to reseat. Finish line scores and
saves; a second run shows the previous best.

**C. Full South Fork descent (60–90 min)** — menu → **Change Mode** until
`Mode: Guided Descent Career`, **Next Run** to `South Fork I: Chili Bar to
Coloma`, **Start Selected Run** (later sections unlock by completing; the
one-sitting full descent needs the Expedition Guide license, or use Free
Run to open everything). The 49 km flagship: no loading breaks or visible streaming pops
(watch `stat unit` for >33 ms hitches), rapid encounters trigger at all 20
named rapids, career section unlocks advance, save/resume mid-river works,
audio bed follows the water (roar rises into rapids, barks on commands,
impact layer on flips). This descent IS review area 4: log per-rapid realism
notes as you go — the packet needs them rapid-by-rapid.

**D. Five reference rivers (15 min each)** — Free Run mode → **Next Run**
to each of Hance,
Lava Canyon, Terminator, Upper Huacas, Zambezi. Raft floats on live water at
the put-in, visible breaking/foam sites exist, a full reference descent
completes without falling through the world or leaving the corridor, and
frame rate holds (note `stat fps` lows; Zambezi is the 1.7 GB stress case).

**E. Input/device matrix (10 min)** — repeat a short Troublemaker run on
gamepad; verify every table row above; check remapping UI if present.

## Recording findings

One markdown file per session in `docs/playtest-notes/`, named
`YYYY-MM-DD-<topic>.md`: setup line (map, flow, build), then numbered
findings each with severity (blocker / major / polish), a screenshot
(`HighResShot 2`) copied from `unreal/Saved/Screenshots/` into
`docs/playtest-notes/media/` when it materially supports the finding, and a
verdict line per review area touched. Review decisions that close packet
gates also get your name + date in `docs/release-review/` per the packet's
reviewer-record section.

## Machine-move consequence (recorded)

The hash-locked capture evidence was produced on the macOS machine. Fresh
captures rendered on Linux will not be byte-identical to the committed ones
(different GPU/driver); that is expected and does not invalidate review
judgments, but regenerating any *locked evidence* on this machine will shift
hashes — do that consciously, review-by-review, with the locked-source gate
watching (`Scripts/check_locked_source_gate.py`).
