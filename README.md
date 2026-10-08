# RaftSim

**Read the water. Find your line.**

A whitewater guide simulator built with Unreal Engine 5.8. Take the stern of a
raft, call strokes for your crew, pick a line through a rapid, and recover
swimmers when the river wins. This repository is the source for
**SmokeEmIfYouGotEm**.

![The RaftSim river-selection menu](docs/ui-polish/main-menu.png)

## Set out

Launch `SmokeEmIfYouGotEm.exe` from a packaged Windows build. The opening title
plays over a living, painted river valley and is skippable with a click or any
key. Pick a river card for Free Run (each river has its own painted look, grade
and region), visit Guide School to learn the controls, or build your guide
career on the Expedition screen. Returning to the menu skips the title sequence.

On the water, the HUD shows the river, run clock and swims; a route ribbon with
your raft's progress to the take-out; the time and weather; and key prompts.
Pause blurs the river behind the run's options, and Tab opens the crew-call
wheel. As the raft approaches each named rapid, its name and class come up
across the river view in a short title card, then clear before the rapid.

![The in-river HUD on the South Fork](docs/ui-polish/in-river-hud.png)

The front end supports mouse, arrow keys, and gamepad navigation. Settings
include captions, larger text, color-safe cues, reduced motion, assistance,
and route ghosts. Setting motion to zero also skips the opening animation.

| River | Run |
| --- | --- |
| South Fork American, California | Chili Bar to Salmon Falls |
| Colorado, Grand Canyon | Hance |
| Pacuare, Costa Rica | Upper Huacas |
| Futaleufú, Chile | Terminator |
| Chilko, British Columbia | Lava Canyon |
| Zambezi, Batoka Gorge | Boiling Pot to Mukuni Beach; Upper Gorge |

Troublemaker belongs to the South Fork. Its separately cooked reconstruction
map is a development component, not another river to select.

## Controls

| Action | Keyboard / mouse |
| --- | --- |
| Look around | Mouse |
| Paddle forward / backward | W / S |
| Draw left / right | A / D |
| High-side / request reflip when capsized | Space |
| Stern draw / pry | Left / right mouse button |
| Crew command panel | Tab |
| Forward / back / left / right / stop crew | 1 / 2 / 3 / 4 / 5 |
| Back to your seats (after a high-side) | 6 |
| Scout the river | M |
| Select swimmer / reach / throw line / reseat | Mouse wheel / E / R / F |
| Pause and resume | Escape (rebindable in Settings) or P |
| Restart checkpoint / return to rivers | Backspace / Home while paused |
| Photo mode / capture photo | O / F9 in photo mode |
| Change camera / weather | C / T |
| Review a completed run | V |

The pause panel also provides mouse and gamepad buttons. In play, gamepad
**X / Square high-sides**; **View / Select opens crew commands**. Menu pauses,
D-pad Down scouts, and Y enters photo mode. High-side and the command panel
use separate buttons so opening a menu cannot consume the safety action.
On-screen panels show the corresponding command and rescue controls.

Press **Space** (or **X / Square**) while upright to call an immediate high-side.
The guide shouts it, and the crew go to the tube the current is carrying onto a
nearby rock (else the downstream tube in cross-current, else the raised tube).
Everyone aboard, the guide first and the paddlers a few hundredths of a second
apart, leaps within 0.8 seconds: a crouch that pulls the blade out of the water,
one jump across with the legs tucked, a landing that gives into the tube, then a
low hold with the chest out over the tube, the outboard hand on the perimeter
line and the paddle held by its T-grip along the floor. The same displacement
(without the jump arc) moves each person's mass in the raft physics; detached
swimmers do not contribute an invisible weight shift. It is a standing order
until the guide calls the crew back: press **6** (gamepad: **B** with the crew
command panel open) for "Back to your seats!". The guide shouts it and the crew
react in the same ripple: each lets go of the line, gets low with a hand on the
floor and the paddle in the other fist, scrambles back across the boat in a few
steps (no leap), then turns square, sits back onto the tube and lays the paddle
across the lap, ready for the next call. Their weight moves back with them. A
paddle command also brings them back the same way, then they paddle.
If already capsized, the same button requests a reflip instead. Timing matters;
high-side is not a guaranteed save from a pin or powerful current.

Paddling tires the crew. Hard strokes spend each paddler over about three
minutes (fitter people last longer, the guide longest), and a tired paddler's
stroke carries less, down to under half a fresh one; the stroke cadence visibly
drags. Resting, or just sitting braced, brings them back gradually, most of it
within a minute or two. The HUD shows crew energy and names anyone who is spent.

Colorado and Zambezi use a single rower with two oars. The same numbered
commands and command panel work there: forward/back rows both oars,
left/right uses opposed oars, and stop brakes with the blades. Held W/S/A/D
temporarily overrides a standing order; releasing the keys resumes it.
High-side and get-down affect the one rower, not an invisible paddle crew.

Developer regression: after rebuilding the editor, run
`./unreal/Scripts/verify_high_side.ps1 -Label high-side-check -Render`.
Use a fresh label and add `-Oar -InputOnly` to repeat the live input/pose check
on the Colorado oar raft. The tests press real input keys through the player
controller, check the published character poses, and verify that the command
panel no longer shares the high-side button.

The rendered check also records `transfer-*.png` from the actual game. Package
the transfer/hold/return sequence only after its native checks pass:
`python unreal/Scripts/package_high_side_capture.py tmp/high-side-check`.
Use `-Oar -InputOnly -Render` with a fresh label for the single-rower recording.
These fixed-step captures demonstrate animation, not measured frame rate.

## Rescue equipment

Passengers can be washed out without the raft flipping: breaking water must
reach their hips and deliver a sustained impact relative to the boat. Each
seat is checked independently; bracing/high-side improves retention but is
not immunity. Calm pools, shallow splashes, and current moving with the raft
do not trigger washouts. A seat that goes underwater also sheds its paddler:
if that side of the boat is pushed half a metre under the surface, the paddler
there is swept out after about half a second (sooner when the boat is heeled
over or the water is moving past it, later when braced). The rest of the crew
stays aboard unless their own seats go under. Ejected passengers become
ordinary rescuable swimmers and their weight is removed from the occupied boat
seats.

Aim at a swimmer, select them with **mouse wheel / gamepad shoulders**, and press **R**
(gamepad **right trigger**) to throw the bag. The guide turns on the seat,
calls "ROPE!", keeps the free end in one fist and tosses the bag underhand past
the swimmer, so the line lands across them; the flight time grows with the
distance. A throw that lands too far from the swimmer misses, and the guide
strips the rope back in before you can throw again. A swimmer who catches the
rope rolls onto their back, rope over the shoulder, and the guide hauls them in
hand over hand, round the stern if necessary, to the guide's own tube. Press
**F** (**B / Circle**) to bring them aboard: the guide grabs the PFD shoulder
straps, dunks them, then leans back and falls into the boat with them. They
roll in over the tube and crawl to their seat. Their seat and weight count as
soon as you press F; the pull-in is presentation. **E / A / Cross** retains the
close-range reach rescue. High-side drops the rope and interrupts a throw or
haul; call **Back to your seats (6)** and let the guide return to the seat
before throwing again.

The guide wears a flip line, double-wrapped round the waist and closed with a
carabiner. After a capsize, aim and use **W / left stick** to swim the guide to
the boat. At the overturned tube, **Space / X / Square** starts the flip: the
guide climbs onto the hull, unclips the line from their waist, clips it to the
middle D-ring on that side, backs across to the opposite tube paying out line,
and stands on its edge leaning back. Rope tension and body weight act on the
hull through the boat physics, lifting the D-ring side up and over. The guide
falls back into the water still holding the line. Swim to the upright tube and
press **F / B / Circle**: the guide climbs in alone. Then paddle to the swimmers
or throw them the bag. Passengers remain swimmers until rescued individually.
The lean's force is scaled for gameplay (`FlipLineLeverage`). It is not an
orientation reset or a full rope simulation, and a pin or adverse current can
defeat the attempt. The HUD shows the current rescue stage. These are game
controls, not rescue training; the 120-second crew recovery budget is a
gameplay rule.

`RaftSim.Rescue.ChoreographyReview` plays a throw-bag rescue and a capsize and
flip-line recovery in the test tank. With `-RaftSimRescueReviewDir=<dir>` and a
rendering editor it writes frames of every stage.

## Build from source

Install **Unreal Engine 5.8**, **Git LFS**, and the platform's C++ toolchain.
Windows builds use Visual Studio 2022 C++ Build Tools and a Windows SDK.
Large assets and hydraulic inputs must be fetched through LFS; a source-only
ZIP is insufficient.

```sh
git clone https://github.com/salsicha/SmokeEmIfYouGotEm.git
cd SmokeEmIfYouGotEm
git switch release/1.0
git submodule update --init --recursive
git lfs install
git lfs pull
```

The water core is a private submodule (`SEIYGE_core`); fetching it needs
access to that repository.

From the repository root in PowerShell:

```powershell
& ./unreal/Scripts/build_solver_lib.ps1
& 'C:/Program Files/Epic Games/UE_5.8/Engine/Build/BatchFiles/Build.bat' `
    SmokeEmIfYouGotEmEditor Win64 Development `
    "$PWD/unreal/SmokeEmIfYouGotEm.uproject" -WaitMutex -NoHotReloadFromIDE
```

Open `unreal/SmokeEmIfYouGotEm.uproject` and play the default
`L_RaftSimBoot` level for the normal intro and menu. To build a standalone game:

```powershell
& ./unreal/Scripts/package_win.ps1 -Config Development
```

The default output is `unreal/Packaged/Win64-Development`. Close running game
and editor instances before rebuilding. See [Unreal setup](unreal/README.md)
for platform scripts and scene ownership.

## Test

Python 3.11+ and `uv`:

```sh
cd physics
uv run pytest -q
```

Standalone solver (C++17, CMake 3.22+, zlib), from the repository root:

```sh
cmake -S unreal/Plugins/SEIYGECore/cpp -B unreal/Plugins/SEIYGECore/cpp/build -DCMAKE_BUILD_TYPE=Release
cmake --build unreal/Plugins/SEIYGECore/cpp/build --config Release
ctest --test-dir unreal/Plugins/SEIYGECore/cpp/build -C Release --output-on-failure --no-tests=error
```

The water core (solvers, shaders, its Python package and tests) is the
`SEIYGE_core` submodule at `unreal/Plugins/SEIYGECore`; its own suite runs
with `uv run pytest -q` from `unreal/Plugins/SEIYGECore/python`.

Unreal's Session Frontend automation includes `RaftSim.M6.MainMenuRender` and
`RaftSim.M6.RuntimeShell` for the actual menu, HUD, pause actions, and input
contracts. Native screenshots are written under `unreal/Saved/Screenshots`.

For repeatable screenshots of a Development package (including South Fork's
actual HUD), close other engine instances and run:

```powershell
& ./unreal/Scripts/capture_ui_polish.ps1 `
    -PackageRoot ./unreal/Packaged/Win64-Development `
    -OutputDir ./tmp/ui-review -CapturePrefix ui-review
```

Use a new capture prefix for each review. The script uses a temporary player
profile, preserves existing screenshots, and records executable/image hashes.

## Development status

This is an actively developed game. The production raft, water effects,
crew, river scenarios, progression, and photo tools are integrated into the
native game. River fidelity and performance continue to be evaluated.
**The performance target is 20 FPS**, not a guarantee for every frame or
machine. A camera fly-through is not a complete boat-physics validation.

Terrain includes measured sources, inferred underwater geometry, and authored
detail. See the [work index](docs/plans/remaining-work.md),
[water-feature evidence](docs/water-features/), and
[scene catalog](unreal/Config/scene_catalog.json) for scope and limitations.
Historical screenshots and hashes describe the revisions they tested.

## Repository guide

| Directory | Contents |
| --- | --- |
| `unreal/Source`, `unreal/Plugins/RaftSim/Source` | Native game, UI, simulation integration |
| `unreal/Content` | Game assets and manifests, including LFS files |
| `unreal/SourceArt`, `unreal/Scripts` | Art sources, authoring, capture, packaging |
| `unreal/Plugins/SEIYGECore` | Water core submodule: shallow-water solvers, shaders, Python, tests |
| `physics/src`, `physics/tests` | Game simulation library and tests |
| `physics/data` | Captured sources, provenance, hydraulic inputs |
| `docs` | Design, validation, rights records, development history |
| `tmp`, `unreal/Saved`, build directories | Local generated output; not source |

Preserve captured data and its licenses. Map-generation scripts can overwrite
scenes; do not run them for a material or UI refresh. See the
[maintenance policy](docs/maintenance/project-normalization.md).

## Credits and licenses

Code: [MIT](LICENSE). First-party content: [CC BY 4.0](LICENSE-CONTENT.md).
Third-party assets and data retain their individual terms; see
[CREDITS.md](CREDITS.md) and [NOTICE.md](NOTICE.md).

RaftSim is a game, not a source of real-world navigation or river-safety advice.
