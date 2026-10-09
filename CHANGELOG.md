# Changelog

All notable changes to this project are recorded here, newest first. Versioning is semver.

## [Unreleased]

### Added

- Holes (2026-10-08, in progress):
  - **Breaking wave** (`RaftSimHoleChurn.{h,cpp}`): a hole's froth is drawn as
    the wave it is, crashing back upstream in place. A white roller stands
    across the trough below the pour-over. Its water rolls up its back, over
    the crest and down a curling front onto the incoming water, and the lip
    throws out and falls back in sections along the span. There is no spray.
    It has its own sound: a steady roar with irregular crashes (new
    `HoleChurn` voice and `HoleCrash` event in the procedural synth).
    It is shown in the test tank only for now (`RaftSim.FeatureDemo hole
    <label> churn[=roll|plunge|big]`).
  - **Water over the crew** (`RaftSimRaftSplash.{h,cpp}`): when the raft hits
    a hole or wave hard, a sheet and droplets of water are thrown over the
    crew. Test tank only (`splash`).
  - **Hole physics** (`RaftSimHolePourOver.h`, `RaftSimHoleWave.h`). The hull
    now meets two things:
    - **the water falling over the pour-over.** Like any falling sheet it
      keeps the speed it came over the crest with and gains only downward
      speed from the drop, sqrt(2 g dh). It drives down whatever it lands
      on: a tube, or the people sitting there.
    - **the breaking wave below it**, the same shape as the drawn one. Its
      white water is mostly air. A hull sinks into it, bearing on it like
      solid water a third as deep, and is pushed down its slopes by a new
      optional surface-slope force (each tube point's buoyancy B also pushes
      -B times the slope). Its water rolls back upstream over it, and in the
      roller under it down to 0.8 of its height, at about its wave speed,
      0.62 sqrt(g H). So a bigger hole holds harder, not just falls harder.

    Nothing forces a flip or a washout: the hull's own drag, upper-face,
    swamping and capsize rules decide. In the test hole (a 0.8 m pour-over
    on a 2 m/s current):
    - **Drifting in**, the raft is stopped by the wave and held, its stern
      under the falling water. The crew's weight keeps it from flipping.
      The same holds drifting in backwards, with the bow under.
    - **Paddling forward**, the crew punch through.
    - **Side-on**, the paddlers on the side under the falling water are
      washed out.
    - **Side-on with a high-side**, everyone stays in and the raft doesn't
      flip.

    Smaller holes flush a raft. Bigger ones keep and flip it, and at 1.2 m
    even a paddling crew can't get out.

    In game it is off by default (`RaftSim.HoleWater 1` to try it)
    until it has been checked on the rivers. It is always on in the test
    tank, which now also has a real crewed raft. Options:
    - `crew`: production seats, play's capsize gate and washouts;
    - `paddle`: the crew paddle forward;
    - `highside`: the crew high-side;
    - `crest=H`: a pour-over H metres high;
    - `yaw=D` and `seconds=N`.
  - **Holes on the rivers** (`ARaftSimHoleWaterActor`, spawned with the raft):
    while `RaftSim.HoleWater` is on, it covers the holes nearest the view
    (up to six within 120 m):
    - each is drawn as its breaking wave, at the size the hull meets it,
      from the water adapter's own hole sites, the authored named holes
      included;
    - the nearest two are heard;
    - water is thrown over the crew when the raft hits hard;
    - the rapid roller and crest-spray particles are hidden.

    Each wave samples the river surface over its footprint five times a
    second rather than at every vertex.

    First river trials with it on, in the rapid assessment's trial driver:
    - Terminator and Hance on the centre line were each held in a hole.
      Terminator lost all five aboard; Hance lost none.
    - Khyber Pass cleared, but the bow stood up to 55 degrees.
    - It is still too violent in big holes, burying and standing up the
      raft. The falling water's push needs a cap.
  - **The guide can be washed out**, by the same impact and swamping rules as
    the paddlers but holding on twice as long as a braced paddler. Guides sit
    at the stern, so a stern held under a hole's falling water can take the
    guide; punching through a hole doesn't.
  - **High-side direction** comes from the river's current a metre down, under
    any surface recirculation. In a hole's roller the surface water runs
    upstream, which would have sent the crew to the upstream tube.
  - `ARaftSimRaftActor::MakeProductionBodyConfig` and
    `ConfigureProductionFlexModel`: the raft body and crew-loaded flexible
    model that play gives the physics runtime, now shared with labs and
    tests.
  - **Test tank fixes:**
    - With `noraft`, the hidden raft is moved out of the scene. Left in
      place, it blotted a raft-shaped gap out of the wave.
    - With the wave shown, the old roller and crest-spray particles are no
      longer created at all; they had been starting by themselves.
  - **Tests:**
    - `RaftSim.Physics.HoleWater` checks the falling water's speed and
      direction, the pile matching the drawn wave, and the push the pile
      gives a hull.
    - `RaftSim.Physics.HoleKeeper` runs the production raft and crew through
      the test hole headless: drifting in, backwards, paddling, side-on and
      high-siding. `-RaftSimHoleSweep` reports the same five across hole
      sizes instead.
- Crew thrown out of the raft fall as rag dolls (2026-10-08):
  - **Rag doll** (`RaftSimCrewRagdoll.{h,cpp}`): a crew member washed out or
    thrown out in a flip tumbles out of the boat as a loose body. It is a
    point-and-bone body, with a stiff torso and head and limbs that fold
    only as far as real joints do. It starts from the pose they were sitting
    in and is thrown up and out over the tube. It falls, splashes into the
    water and is dragged by it. The PFD floats it chest up at the surface,
    where it settles and blends into the swim within about 1 to 4 seconds.

    It keeps hold of its paddle throughout. The lower hand, the one on the
    shaft, never lets go; the paddle swings from it with its own weight and
    drag.

    It is presentation only: gameplay's swimmer still decides where the
    swimmer is, and the body is pulled toward that point. The forced
    overboard drill still swims straight away.
  - **Swimmers keep their paddles** in the hand that held the shaft; the
    other hand strokes. Grips are now solved per hand, so a free hand opens
    while the other still wraps the shaft.
  - **Test tank:** an `uphigh` camera above and behind the downstream tube,
    and `slomo=F` to run the scene slowed down.
  - **Tests:** `RaftSim.Crew.RagdollFall` throws a paddler out over each side
    and checks:
    - the body rises before it falls;
    - the hand stays on the shaft to within 1 cm;
    - its bones keep their lengths;
    - it floats chest at the surface by four seconds, where gameplay has
      the swimmer.
- Crew, gear and raft review fixes (2026-10-07):
  - **Hand grips rebuilt** (`RaftSimCC0CrewGrip.cpp`): every hold is solved
    against the bar it holds. The palm faces the T-grip crossbar or shaft,
    the fingers wrap it with their pads on its surface, the thumb opposes
    them, and the forearm takes 65% of the wrist's twist. The old solve
    treated the back of the hand as the palm, so fingers bent backwards and
    wrists turned an extra half turn. At rest the top hand holds the T-grip.
  - **Paddle stroke:** the paddler leans well forward to plant the blade
    near vertical about 60 cm ahead of the seat, well ahead of the knees,
    and pulls back to upright and a little past, from the torso and core.
    The blade comes out about 18 cm ahead of the seat, before the hips:
    drawn back past the hip, the paddle ran alongside the body and bent the
    wrists past what wrists can do. Back strokes plant ahead of the hip and
    drive forward past the knees. The top hand stays out in front of the
    chest throughout.
  - **Torso turn:** the chest turns on the hips toward the paddle side, 30
    degrees at the catch to 40 at the exit, the lower back taking a third of
    it and the head turning it back so it looks downriver. The rendered spine had never
    turned at all (it took only the host's lean), so the T-grip arm reaching
    across the body cut through the chest and vest. Each elbow now also
    turns about the shoulder-wrist line to keep the arm outside the chest
    and vest. The vest follows the chest bone; it had taken its facing from
    the shoulder joints, which slide toward a reaching hand, and swung
    across the chest mid-stroke. The guide seen through their own eyes
    turns less and holds the T-grip further out, keeping their arms at the
    edge of the view.
  - **Shoulders:** a reaching shoulder stays on its collarbone, sliding at
    most 6 cm round it (was 11); Ingrid's bare shoulder no longer tears away
    from the arm mid-stroke. Each upper arm now turns about its own length
    so the elbow bends the way the rig's elbow hinges. Swung the shortest
    way up from the hanging rest pose, the raised upper arm had rolled
    up to 33 degrees off its elbow on starboard and up to 166 on port, wringing
    the shoulder's skin round it: the armpit rode up in front and the arm
    looked pulled out of its socket.
  - **Neck:** the neck rises from the chest at the rig's own forward bend
    (13-23 degrees, by body). It had been aimed almost straight on from the
    chest with the head tipped forward over it, so the skin at the nape
    folded into a notch and stood off the back of the neck. The head's nod
    and turn are shared, half of each nod and a third of each turn in the
    neck, and the head lifts against most of a forward lean, keeping the
    eyes on the water ahead at the catch instead of bowing chin to chest.
  - **Shaft hand:** the lower hand slides up the shaft as far as each
    body's arm needs, as a paddler chokes up, staying at least 30 cm below
    the T-grip. Held a fixed distance down the rigid shaft, it had been set
    as far as 72 cm from a 46-54 cm arm with the blade low in the power
    phase or the shaft laid flat in the recovery, and the hand stood off the
    end of a straightened arm, the forearm drawn out as much as 21 cm. The
    lifted blade also swings half as far ahead in the forward recovery
    (12 cm, from 24), and in the back stroke's recovery swings ahead only
    as it nears the hip instead of holding out past the knees.
  - **Seats:** the crew sit 3.5 cm into the tube with a full contact patch,
    and the resting paddle line is 1.2 cm higher to stay on the thighs.
  - **Collars** (clothing generator v4): the shirt collar hugs the neck,
    covered in shirt fabric under it, with its weights smoothed round the
    neckline. It had stood 1.3 cm off the neck, a dark trench behind it
    where the spine should be, and went saw-toothed when the head bowed.
  - **Helmets** (generator v9): a full-cut whitewater shell with moulded ear
    covers, a low occipital tail and a short peak, clearing every wearer's
    hair; the per-wearer chin straps are refitted to it.
  - **Vests** (PFD generator v14): a low-profile front-entry guide vest,
    slim front panels either side of a zip, side adjustment straps, padded
    shoulder straps and a chest pocket, fitted to the five seated torsos
    with every strap built on top of the foam. The procedural side slabs
    are gone, and the whistle and knife sit on the pocket and lash tab.
  - **Flip line** (`build_production_guide_flip_line.py`): the guide wears
    two snug wraps of tubular webbing at the vest hem with a locking
    carabiner, replacing the loose procedural loop round the hips.
  - **Vest shoulder straps** (PFD generator v15,
    `build_production_pfd_shoulder_straps.py`): each wearer's straps are
    fitted to their own shoulders, 4 cm wide and inboard by the neck, and
    the panels stop lower. One shared pair had stood high off the narrow
    shoulders and pinned the arm raised to the T-grip under it.
  - **Thumbs:** the fingers close together round the bar and each thumb
    wraps 140 degrees round it the other way, its end meeting the
    fingertips: under the T-grip's crossbar, and round the shaft over the
    fingers. Aimed at the outside of the index finger, out of the thumb's
    reach round the far side of the bar, the thumb had stopped short along
    the shaft and beside the T-grip.
  - **Wrists:** each grip turns about its bar toward the forearm carrying
    it and lays the bar diagonally across the palm as the forearm needs,
    as a hand holds a handle; a raised elbow swings about the
    shoulder-wrist line on its own bone lengths. Laid square across the
    palm, the T-grip's crossbar and the shaft ran nearly along their
    forearms, bending the wrists 75 and 55 degrees sideways. Closing round
    a bar laid toward the fingers, the ring and little fingers converge
    toward the base of the thumb, so the little finger wraps the T-grip
    instead of curling tight beside it.
  - **Knees and ankles:** the legs bend on each body's own thigh and calf.
    The rendered thighs are about 41 cm, the pose's 34-35 cm, and aiming
    each bone at the pose's knee left the thigh's end 7-8 cm from the
    calf's root: the knee skin folded through itself and the ankle sheared
    off the shin. A two-bone solve keeps the hips and planted feet and puts
    the knee where both bones reach; the resting paddle rides higher on the
    higher thighs.
  - **D-rings** (raft generator v3): each D-ring sits on a bonded pad with
    webbing tabs round its bar, and the perimeter line runs through the
    rings. The detail is kept light (40,232 triangles against 38,344): the
    rest mesh is also the physics hull. The FBX is exported from a
    centimetre scene; Interchange applies the 100x node scale Blender wrote
    for a metre scene and had imported a 430 m raft. The flip-line test now
    waits for a capsized hull to stop rolling before calming the water.
  - **Sunglasses:** everyone wears sport sunglasses.
  - **Throw bag:** a rescue throw bag modelled on the common commercial
    design (red body, mesh drain band, flared top with a barrel-lock
    drawstring, yellow line out of the top on a figure-eight loop, grab
    handle) stands on the floor beside the guide. The thrown bag is a bag
    shape, not a ball, and the loose coil at the stern is gone.
  - **Bow line:** tied to the bow grab line with a round turn and two half
    hitches, coiled and wrapped into a neat hank along the bow tube.
  - **Trees:** the white alder and both placed ponderosa forms are rebuilt
    as leaf-spray trees (`RaftSimEditorSouthForkSprayTrees.cpp`): twigs off
    the branches carry clusters of small leaf sprays instead of large flat
    cards, so the alder reads as a leafy crown and the pine as a dark,
    needled cone. The live oaks carry 16 smaller sprays per branch tip
    (was 10 larger ones) for a finer, deeper-green crown.
  - **Review** (`RaftSim.Crew.GearReview`): first-person captures through
    the player's camera while the guide paddles, forward, back and
    steering, with an arm-coverage audit; a look down onto each nape; the
    throw bag, bow line, knot and a D-ring; and the hand-to-face gap at
    twenty points round the stroke. Each paddler is also held at twenty
    points round a back stroke, under a back-paddle order, and both strokes
    are checked for the blade working ahead of the hips, the T-grip arm
    staying out of the chest and vest, and the wrists bending within reach;
    the catch, power, exit and recovery are filmed from in front, from
    above and in profile at the nape, with each thumb close up with the
    paddle hidden. The skin round the neck and shoulders is measured for
    stretch, and each arm's reach, shoulder shift and elbow hinge are logged
    through both strokes and live paddling.

- Crew gear and grips:
  - **Grips:** the T-grip hand caps the crossbar palm-down, and the shaft
    hand holds the shaft thumb-up toward the T-grip, knuckles out, on either
    side of the boat. The grip basis normal is the back of the hand in this
    rig: T-grip palms had faced up, and right-side paddlers' shaft thumbs
    pointed down.
  - **Shoulders:** the top arm's elbow leads out and down, turned clear of
    the face, and a reaching arm's shoulder slides toward the hand and
    rises. The top arm no longer pulls out of its socket and folds the
    shoulder over.
  - **Sandals:** the crew wear river sandals on bare feet
    (`build_production_river_sandal.py`). The sandals are fitted to the five
    CC0 feet, and each one is scaled to its wearer's foot and turns with it.
  - **Chin straps:** helmet retention straps are fitted to each wearer
    (`build_production_helmet_straps.py`) and pass under the chin. The
    shared shell's straps cut through the deeper chins.
  - **Clothing:** the clothing generator returns any shell vertex that
    solidify throws off the body. One stuck out behind Ingrid's seat, and
    the guide's shirt had two.
  - **Seat:** seated, a fin of fabric no longer sticks out between the
    buttocks. MPFB weights the cleft and perineum almost wholly to the
    pelvis while the buttocks beside them follow the thighs, so as the
    thighs swung forward the midline stayed 2-4 cm behind them. The clothing
    generator (v3) now gives the seat's midline the thigh share of its
    neighbours, and all five bodies are re-imported.
  - **Resting paddle:** at rest the paddle lies on top of the thighs, about
    1 cm above the highest, instead of 10-13 cm inside them. Each hand
    holds the shaft where no thigh lies under its fingers: the upper hand
    just inboard of the inboard thigh, the lower hand just outboard of the
    outboard thigh.
  - **Review:** `RaftSim.Crew.GearReview` renders and audits all of this,
    including how far the resting shaft and fingers sit above the thighs.

- Guide helmet seated on the guide's skull: the five CC0 heads share an
  eye-line helmet anchor, and the guide skull is the deepest of them (eyes
  8.7 cm ahead of the head joint against 6.7–7.9 cm for the crew), so the
  shell sat forward with the rear rim crossing mid-skull and the occiput
  bare. The guide anchor now pulls back along the face and the guide shell
  is sized for that skull; `raftsim.CC0GuideHelmetBackCm` and
  `raftsim.CC0GuideHelmetScale` override both for review.

- River boots regenerated (generator v3): the v2 upper used superellipse
  exponents below one, which bulges the cross-section into a rounded box,
  so the boots read as square blocks from the guide seat. The upper now
  lofts an ellipse that pinches toward the instep over a flatter sole
  side, the toe closes on a quarter-circle, and the toe rand hugs the
  narrower toe. Same footprint (33 x 14 x 18 cm), same materials.

- Troublemaker Rapid now runs on the production full reach as a
  station-bounded Free Run section (7900–8700 m) instead of the legacy
  compact `L_Troublemaker` slice, whose authored-band presentation read as
  a milky void with the raft hovering above it. Two runtime fixes behind
  that: a section that starts mid-reach with no saved checkpoint now begins
  at its start station (window reseed + raft move, the checkpoint path
  without the checkpoint), and a fixed river window without a coordinate
  map rejects a support band cooked for a different station frame (the
  compact map's whole-reach band clamped its raft 1.5 m above the water).
  `RaftSim.MenuScreen main start=<scenario id>` presses a river button for
  review runs. The approach-telemetry gate (`RaftSim.P4.SouthForkApproachDraftTelemetry`)
  now scans for wet water from the raft's own station rather than the
  put-in, since the saved section decides where the window boots.

- Main menu restructured around the rivers: the front end now shows one
  button per runnable river run (South Fork American full run and
  Troublemaker, Hance, Upper Huacas, Terminator, Lava Canyon, Zambezi, and
  the Training Eddy) that starts that run directly as a Free Run, plus
  `Guided Descent Career...` (the former mode/section selector on its own
  screen) and `Settings...` (subtitles + captions, UI / text size,
  color-safe cues, motion comfort, hold / toggle controls, difficulty +
  assists, ghost / route assist, pause rebind, restore defaults, credits,
  legal + data notice). Escape or the gamepad's B returns to the main
  screen. `RaftSim.MenuScreen <main|career|settings> [capture=<label>]`
  screenshots a screen from the boot level for review.

- Reference-map inspection passes (Hance, Upper Huacas, Terminator, Lava
  Canyon; reports under `docs/reports/2026-09-02-*-inspection.md`): the
  guide's head no longer renders as a black spike from external cameras,
  the live water lattice keeps its volume-core triangles and coverage at a
  corridor's true ends (the first and last ~18 m of every reference reach
  rendered dry), and the survey tooling walks Landscape-based maps
  (`RaftSim.SurveyReach`, `RaftSim.CaptureRaftSeries station=`,
  `RaftSim.HideTaggedActors`, review cvars for the water presentation).

- Restored native Linux build/test support (originally landed 2026-08-01, lost in a
  history rewrite): `<array>`/`<optional>` includes in the C++ solver,
  a portable bash `build_solver_lib.sh` that uses the engine's bundled
  clang/libc++ toolchain on Linux (a gcc/libstdc++ archive cannot link into UE
  there), the engine zlib dependency in RaftSimWater, `package_linux.sh`
  (now mirroring the Zambezi map pre-generation guard), untracked
  `physics/cpp/build-ue/` again, pytest/matplotlib in the default uv dev group,
  and Pillow floor 12.3. Fixed the game-target compile everywhere by replacing
  editor-only `GetActorLabel()` with `GetActorLabelView()` in the river map
  automation test, and a case-sensitive `scripts/`→`Scripts/` path in the
  safety-gear test. Verified on Linux against a 5.8.1 source engine: editor and
  game targets build; P1 tank, P2 river window, four M8 gates, and all six
  P4 river map loads (including Zambezi) pass under NullRHI. Cross-platform
  byte-reproduction tests (Hance/Pacuare visual terrain+water, Meat Grinder
  committed package) are split or marked xfail off-macOS with recorded reasons;
  the two in-place visual-water builders now restore committed bytes so
  divergent regeneration cannot cascade into hash-lock tests; M9 packet audits
  skip where their machine-local `unreal/Saved` evidence cannot exist.

- A runnable Zambezi Batoka Gorge reference Free Run, including a curved runtime
  coordinate map, procedural full-corridor water seed, gameplay bootstrap, player-facing
  river catalog entry, and validation that keeps production terrain, bathymetry,
  rapid-hydraulic, guide, visual, and performance acceptance gates explicit.
- An independent Project Chrono/PyChrono 10.0.0 D6 runner that consumes only the
  frozen fixture-input package, measures twelve-segment tube and rock-contact
  compliance through `ChSystemSMC`/`ChLinkTSDA`, repeats all seven fixtures
  byte-identically, and exports hashed D5-channel telemetry. Together with the genuine
  Chaos baseline, all 14 records now merge and the 74-metric compliant comparison passes;
  named manual promotion review remains open.
- A source-true Meat Grinder D4 evidence mode that uses the cooked median-flow rapid,
  places a project-owned procedural boulder at station 960 m, and records live contact,
  indentation, wetness, and water-VFX telemetry without writing flexible visual state.
- Runtime wetness material instances for the raft and production-character fallback,
  plus native coverage for live-water edge feathering, shadow suppression, procedural
  evidence-rock ownership, and capture-authority integrity.
- A settled-map fixed-camera command and durable cross-process comparison report for the
  five South Fork release-review views. The verifier locks sparse renderer-drift limits,
  records both hashes and pixel/channel error metrics, and never substitutes tolerance
  success for byte identity.
- Project-owned raw coated-raft-fabric, PFD-ripstop, and wetsuit-neoprene source studies;
  deterministic four-way-mirrored 1024×1024 albedo, normal, and packed PBR derivation;
  Unreal texture/material bindings; and a renderer-backed close-range rejection record.

- A locked-source commit gate (release-1.0-plan.md §8): commits touching
  hash-locked sources must refresh their review locks and pass the full
  physics suite with no failures beyond `Scripts/full_suite_baseline.json`.
  `Scripts/check_locked_source_gate.py --all` runs in CI repo guards;
  `Scripts/install_git_hooks.sh` installs the pre-commit `--staged` mode.
  Pre-existing drift is recorded explicitly: 298 stale lock entries across
  49 review files (`Scripts/locked_source_debt.json`) and 16 known-failing
  tests — both are burn-down lists that may only shrink.
- Re-baselined the release plan platform matrix: native Linux x64 (Vulkan)
  is a shipping tier (P6 packages all three platforms; the Proton report is
  retained as extra coverage), and the six-river runnable-reference reality
  replaces the stale "South Fork only / native Linux cut" rows. The
  release-candidate workflow's native-Linux RC lane is recorded as pending
  wiring.

### Changed

- **The crew's weight bears where they sit** (2026-10-08,
  `RaftSimChronoRuntimeAdapter.cpp`). Their mass was already part of the
  raft's body, but it acted at the hull's centre, so where they sat never
  tilted the boat. Each person's weight now acts at their seat, or wherever
  they lean, brace or high-side to, so the boat's centre of mass is the dry
  hull plus each person aboard. On still water, with the 85 kg guide and
  four 75 kg paddlers:
  - **Full crew**: the boat lists 0.7 degrees to the guide's side and sits
    0.25 degrees bow down.
  - **Two port paddlers washed out**: 150 kg leaves the boat, the centre of
    mass moves 23 cm to starboard and the starboard tube sinks to 1.8
    degrees.
  - **The guide out**: the stern rises (bow down 0.8 degrees) and the list
    goes.
  - **Everyone high-sided onto one tube**: it holds that tube down 3
    degrees, so a high-side now levers the boat.

  The inertia follows them too. The configured inertia is the full crew at
  their seats. Its crew share scales, axis by axis, with how far out the
  crew aboard actually sit, so a guide at the stern leaving takes more pitch
  inertia than a paddler amidships. A full crew at their seats and an empty
  hull keep the inertia they had. The body still turns about the hull's
  centre. Step telemetry now reports the centre of mass and the crew's
  weight torque. New test `RaftSim.Physics.CrewWeightBalance`.
  `RaftSim.Crew.OccupancyControlsLoadsAndIntegratedMass` checks the new
  inertia rule and centre of mass.

  The rescue choreography review's 3.2 m breaking broadside can now stand
  the boat on its tube and drop it back upright, as a raft balanced on its
  side can go either way. If the first wave doesn't roll it over, up to two
  more follow, 10 s apart.
- P pauses and resumes the run, as Escape does (and resumes from photo
  mode). Photo mode moves from P to O; gamepad Y and the pause panel's
  Photo Mode button are unchanged.
- South Fork live oaks (the three V3 crown forms, about 80% of the river's
  trees) carry leaf sprays instead of sheets. Each branch tip held two
  crossed leaf-cluster cards 1.6-2.8 m wide, lit as flat planes, so the
  crowns read as flat textures cut into sheets. Each tip now carries ten
  sprays about half that size, scattered along and past the twig at varied
  angles with their faces out of the crown, and their normals lean toward
  the crown's ellipsoid so a crown shades as one rounded mass. The leaf
  material keeps leaves matt (roughness at least 0.88, specular 0.3) and
  transmits less light, so backlit sprays no longer glint or glow white.
  The leaf atlas's chroma-key matte had left a dark grey outline round every
  cluster; edge pixels now take the solid leaf colour beside them. Each mesh
  keeps the height its placements were scaled to (the trees are scaled
  14-18% vertically to reach it), so no placed tree changes height. Review
  record: `docs/environment-captures/south_fork_full_reach/m9_live_oak_leaf_sprays_2026_10_06_review.json`.

- Grand Canyon cliffs no longer look tiled. The Hance walls' rock scan
  (Rock037) was projected on a fixed 6.5 m lattice, so its horizontal
  cracks lined up into rows of identical dashes across every wall. Each
  wall rock layer is now sampled from two projections that drift slowly
  with world-space noise, at tile sizes 1.585x apart, and a noise mask
  swaps between them in patches of about 15 m
  (`RaftSimEditorWallRockBreakup.cpp`). The 21 m broad layer drifts too.
  `RaftSim.RefreshLandscapeCandidateMaterial <river_id>` re-authors one
  river's landscape material in place without rebuilding its map; Hance's
  is refreshed. The other evidence-drape maps (Upper Huacas, Terminator,
  Lava Canyon, Zambezi upper gorge) share the code and pick it up when
  their materials are next refreshed.

- First remediation round for the 2026-08-06 named human visual review:
  CC0 water-detail texture intake (ambientCG, 16 textures, manifest +
  reviewed-import script); two-scale froth on the solver foam mask in the
  authored river-water and live-surface materials with froth colour
  corrected from 48% gray to aerated white, plus a narrow
  `RaftSim.CreateSouthForkTransmissionWater` recreation command for the
  one-time-duplicate parent; bounded interface restoration for the
  Chilko/Futaleufú/Colorado water instances; crew helmet dome coverage,
  seating, and safety colours. Three latent headless-pipeline defects fixed
  (candidate captures gained the 12-frame settle loop; the preview light
  rig falls back to world spawns when editor placement is unavailable; the
  rig SkyLight uses real-time capture instead of baking a black cubemap
  into headlessly regenerated maps). Asset regeneration remains pending an
  interactive session: headless candidate captures still render a
  horizon-sun atmosphere, so no regenerated evidence was committed
  (details in docs/release-review/2026-08-06-first-human-visual-review.md).

- Hardened the locked-source gate to be machine-independent: it now audits
  only git-tracked locked sources (locks over never-versioned machine-local
  evidence such as `unreal/Saved/` captures cannot drift via a commit, differ
  per machine, and are audited by the packet/review tests where they live),
  and it aborts with a distinct error when a checkout holds git-lfs pointers
  instead of content rather than reporting false drift. Recorded debt
  re-scoped from 298 to 187 tracked-source entries. CI checkouts for repo
  guards and the physics suite now fetch LFS content (`lfs: true`), which the
  suite has needed since the 2026-08-05 LFS normalization.

- Test regeneration no longer mutates the repo tree: the South Fork and
  Colorado production-corridor builders, all four river visual-water builders,
  and all five canopy-atlas generators now take an optional `output_dir`
  (sources still read from the committed tree; recorded manifest paths stay
  canonical), and their tests regenerate into pytest tmp directories —
  determinism is proven with two independent output roots. On macOS the old
  in-place rewrites were byte-identical and invisible; on any other platform
  they left ~46 committed files modified after a full suite run and cascaded
  into downstream hash-lock failures mid-run. The `examples/generate_*` CLIs
  keep the explicit in-place evidence-machine flow (default `output_dir`).
- Normalized 129 previously committed binary paths into the repository's existing
  Git LFS policy. All 119 unique payloads (245,078,504 bytes) retain their exact
  pre-normalization SHA-256 and size, and every referenced object is present in
  the local LFS store. This repairs the false dirty-worktree state and makes
  subsequent release-candidate asset commits reproducible; no image, terrain,
  hydraulic, mesh, or gameplay content changed.
- Re-certified Zambezi Batoka Gorge as runnable river 6 after the Pacuare
  forest-floor milestone. The player selection catalog and six-river Free Run manifest explicitly
  retain `runnable: true`, `availability: free_run`, and
  `zambezi_reference_run` → `/Game/RaftSim/Maps/L_Zambezi`, and now link the
  V23 hash-locked review. The committed 1.7 GB map remains byte-identical. Five
  focused release/centerline/portfolio contracts and all five M6 frontend/progression tests pass without warnings;
  the live Zambezi PIE gate passes 1/1 with MapCheck 0/0, the vertical-slice
  game mode, cooked-field water, 10 live breaking sites, and 645 rapid-foam
  vertices. This certifies runnable reference play only; surveyed bathymetry,
  rapid-specific hydraulics, photoreal art, guide/rights review, and target-
  platform qualification remain open.
- Added a bounded mixed near-bank ecology layer to the runnable Futaleufú
  Terminator map. Seven rights-reviewed CC0 small-fir and fern meshes now
  supply 1,440 of 1,800 deterministic screened placements; the remaining 360
  procedural placements and all 4,650 project-owned canopy instances remain.
  Medium firs are excluded, collision is disabled, and the assets carry no
  native-species, ecology, geography, hydraulic, bathymetry, or raft-force
  authority. The editor builds, focused native checks pass 2/2, all six
  runnable maps pass PIE, and 20 focused Python contracts pass. Matched review
  retains the runtime improvement but rejects photoreal promotion.
- Raised only the rendered CC0 fallback head and neck presentation by 5 cm along
  the solved torso-up axis, restoring visible head-to-shoulder clearance without
  moving the authoritative body pose, helmet-to-eye solve, hands, paddle,
  collision, mass, raft, or rescue state. The matched five-character roster now
  reports a 21.9315 cm minimum seated clearance, while helmet error remains
  effectively zero and maximum grip-anchor error remains 5.81e-9 cm. The exact
  editor build, 23 focused contracts, M5 gate, all-six-river P4 gate, and
  before/after frames pass. This retains a technical silhouette improvement only;
  coarse angular collar/PFD geometry, final anatomy and materials, photoreal
  promotion, and named character-art/guide review remain open.
- Re-certified Zambezi Batoka Gorge as runnable river 6 after the shared
  raft/crew breaking-water occlusion milestone. The player catalog and Free
  Run progression manifest explicitly retain `runnable: true`,
  `availability: free_run`, and `zambezi_reference_run` →
  `/Game/RaftSim/Maps/L_Zambezi`, and now link the V17 hash-locked review. The
  map package remains byte-identical. The exact release source builds
  successfully; 27 focused contracts pass, native catalog/progression gates
  pass 2/2, and the
  live Zambezi PIE gate passes 1/1 with MapCheck 0/0. This certifies runnable
  reference play only; surveyed bathymetry, rapid-specific hydraulics,
  photoreal art, guide/rights review, and platform qualification remain open.
- Extended the live raft/crew foam exclusion into the shared connected-
  breaking-water material. A narrower raft-aligned footprint clears the former
  opaque water layer from raft fabric, fittings, passengers, and paddles while
  a waterless isolation retains the six-frame D4 contact plume immediately
  outside the tube and rock. Existing mask and texture assets stay unchanged;
  no map, solver, contact, collision, buoyancy, force, D3, or D4 authority
  changes. The editor build, four focused Python contracts, M4 4/4, production
  Niagara 1/1, P2, and all six runnable-map gates 7/7 pass. Photoreal water,
  general character depth, platform qualification, and external approval remain
  open.
- Re-certified Zambezi Batoka Gorge as runnable river 6 on the current release
  head. Both versioned runtime manifests explicitly retain `runnable: true`,
  `availability: free_run`, and `zambezi_reference_run` →
  `/Game/RaftSim/Maps/L_Zambezi`, and now link the V16 hash-locked review. The
  map package is unchanged. A clean UE 5.8 build, 27 focused Python contracts,
  native catalog/progression checks, and a live PIE load pass with MapCheck 0/0.
  This reaffirms reference playability only; production terrain, bathymetry,
  hydraulics, external review, photoreal art, and platform gates remain open.
- Completed the shared live-volume bank mask: solver-owned vertex coverage now
  fades Single Layer Water scattering and absorption and restores behind-water
  color to identity at zero coverage, instead of fading only surface opacity
  while leaving a pale optical rail. The updated versioned parent is shared by
  all five river-local live-water instances. The exact editor
  build, focused material audit, shared P2 water gate, and all six runnable P4
  map gates pass. Matched Chilko/Futaleufú evidence retains the correction but
  still rejects the broad pale shallow band, analytical breaking water,
  procedural environments, and every external acceptance gate.
- Replaced the rejected cold-water terrain-overlay approach with a default-off,
  presentation-only bank boundary profile for runnable Futaleufú and Chilko.
  Three station-anchored bands vary the existing alpha feather independently
  on river left and right; the Single Layer Water core's outermost wet vertices
  retreat inward by at most 0.90 m and less than one 1.50 m render cell. The
  four-wet-corner topology, sampled wet mask, maps, materials, bathymetry,
  collision, buoyancy, raft forces, D3, and D4 are unchanged. The fixed Chilko
  close-up records a 3.84 px mean contact shift and 16.69% higher detrended contact
  variation without a rail or gap; the Futaleufú rapid-side frame is an honest
  no-regression control, not a claimed visual gain. Photoreal and all six
  external gates remain open.
- Rejected and fully removed a source-conditioned Futaleufú/Chilko shoreline
  overlay after two fixed-camera brackets. The final 18 m bank strips passed
  generation at 11,438 vertices and 21,600 triangles per river, but Chilko's
  pale rectangular shallow-water band remained and bank-transition edge
  density slightly decreased; an intermediate bracket also introduced a pale
  rail. The accepted runnable maps, terrain materials, collision, cooked
  fields, wet/dry masks, bathymetry, hydraulics, buoyancy, and raft forces are
  unchanged. Hash-locked rejection evidence and the required water-coverage or
  surveyed-bank follow-up are retained.
- Reaffirmed Zambezi Batoka Gorge as runnable river 6 on the current release
  head without changing its V19 map package. The player selection catalog and
  six-river progression manifest still map `zambezi_reference_run` to
  `/Game/RaftSim/Maps/L_Zambezi` at `reference_free_run` tier and now link a
  V14 hash-locked release review. A clean 136-action UE 5.8 editor build, 26
  focused Python contracts, the native career and progression gates, the
  focused Zambezi PIE gate, and six isolated runnable-map PIE gates pass with
  MapCheck at zero errors and warnings. This is runnable-reference
  certification only; production terrain, bathymetry, rapid hydraulics,
  guide/rights/flow review, photoreal art, and platform performance remain
  open.
- Reworked the runnable Futaleufú and Chilko Single Layer Water cores so cooked
  depth now drives a strong shallow-transmission/deep-absorption relationship,
  while ordinary fast current no longer receives broad milky aeration. The
  retained matched bracket lowers Futaleufú's clear right-body mean 5.65% and
  raises body contrast 19.11%; Chilko mean falls 21.40%, far-band mean 14.33%,
  and p95 4.52%. Solver foam, raft-interior transmission, wetness, geometry,
  bathymetry, collision, buoyancy, and raft forces are unchanged. Both maps and
  river-local instances were regenerated and all six runnable map loads pass;
  photoreal art, calibration, human review, and platform gates remain open.
- Unified the runnable Futaleufú Terminator and Chilko Lava Canyon maps under a
  restrained cold-water highlight profile, regenerated both stable packages,
  and corrected Futaleufú's shallow/deep/sky tint after rejecting a gray first
  bracket. Matched Terminator evidence reduces >0.95 clipped coverage 98.20%
  while increasing cold blue separation 29.79%; matched Chilko evidence stays
  within 0.0001 for mean, p95, and blue separation as the no-regression
  control. Solver state, wet/dry ownership, water/terrain geometry,
  bathymetry, collision, buoyancy, and raft forces are unchanged. Broad pale
  water, rapid VFX, environment art, calibration, performance, and all six
  external gates keep photoreal promotion open.
- Re-certified the regenerated V19 Zambezi map as runnable river 6 and replaced
  count-only launch ecology acceptance with six fail-closed bank/elevation
  strata. The retained package contains 6,512 source-grounded ground-cover and
  772 woody instances; a 132-instance launch-camera face mosaic breaks up the
  former skyline row while 108 unsafe or unsupported targets remain rejected.
  Schema-v21 validation, runnable manifests, and matched before/after evidence
  are versioned. This is a technical ecology improvement, not photoreal or
  production-hydraulic promotion.
- Replaced the packaged CC0 crew's open reference hands with side-correct,
  palm-aligned articulated paddle grips. All five identities now use distinct
  upper T-grip and lower shaft-hand frames, curl every three-joint finger and
  thumb chain, preserve source bone lengths, and release the grip for swimmers.
  The editor build, 15 focused contracts, 45 related visual-isolation contracts,
  30 renderer views, and renderer-enabled M5 gate pass. This is a technical
  character fallback improvement, not photoreal promotion: coarse topology,
  weak thumb opposition, compression, motion, and named character-art and guide
  acceptance remain open.
- Re-certified Zambezi Batoka Gorge as runnable river 6 at the V18 release
  head. The selection catalog and six-river progression manifest now both
  explicitly record `runnable: true`, `availability: free_run`, and the V12
  release review while retaining `zambezi_reference_run` →
  `/Game/RaftSim/Maps/L_Zambezi`. A clean 79-action UE 5.8 editor build, 25
  focused Python contracts, the native career/progression gates, and the live
  Zambezi PIE load gate pass with MapCheck at zero errors and warnings. This is
  reference-runnable certification; production terrain, bathymetry,
  rapid-specific hydraulics, guide/geospatial/rights, photoreal art, and
  target-platform acceptance remain open.
- Refined the runnable Zambezi launch gorge with a presentation-only V18
  exposure and material bracket. The live water now uses a rougher localized
  reflection response with no calm detail overlay, the sun-facing scarp uses
  darker two-scale basalt shading plus bounded erosion staining, and the first
  kilometre carries 7,200 shorter launch-cover instances. In the matched frame,
  water p95 luminance falls from 0.8859 to 0.8478 and pixels above 0.90 fall
  96.14%; left-water pixels above 0.90 fall 96.30%. The schema-v20 saved-map
  audit, five focused native Zambezi tests, and all six runnable-map PIE gates
  pass with Zambezi MapCheck at zero errors and warnings. Collision, DEM,
  water geometry, wet/dry state, hydraulics, buoyancy, and raft forces are
  unchanged; coarse canyon geometry, procedural ecology, production art,
  hydraulic calibration, and all seven external gates keep photoreal promotion
  open.
- Corrected Chilko Lava Canyon's legacy-config detection so regenerated maps
  retain their authored river-local optical values. A Chilko-only depth-
  coverage mask, restrained lighting/reflection rig, muted vegetation material,
  and smaller full-reach gravel/cover distributions reduce the pale sheet,
  clipped highlights, fluorescent cover, and oversized silhouettes without
  changing cooked fields, hydraulics, collision, buoyancy, or raft forces.
  Matched evidence reduces water-band mean luminance 6.18%, >0.90 coverage
  59.21%, >0.95 coverage 98.93%, and bank neon-green fraction 64.77%. The
  editor build and all six runnable-map gates pass; remaining shore form,
  ecology/geology, foam/VFX, calibration, performance, and external reviews
  keep photoreal promotion open.
- Replaced the shared live-water renderer's dominant 11.5 cm diagonal
  sinusoid with deterministic flow-aligned, phase-warped crest packets and
  analytical normals. The theoretical presentation bound drops from 24.8 cm
  to 16.8 cm and the matched Zambezi runtime maximum drops from 23.43 cm to
  10.46 cm without changing solver samples, collision, buoyancy, or D3/D4.
  The editor build, focused water gate, and all six runnable river gates pass;
  photoreal hydraulic and external acceptance remain open.
- Kept one connected, masked crest-to-plunge water membrane active beneath
  production Niagara at the three strongest accepted solver jumps. This
  replaces the production-path choice between disconnected particle spray and
  the rejected three-shell translucent dome, caps the mesh at 1,512
  non-colliding triangles, and reuses the raft/crew-excluded solver foam lace.
  The editor build, focused water test, and all six runnable river gates pass.
  Fixed-camera Zambezi edge coverage rises 12.78% and high-pass detail 8.23%
  without dome/card artifacts, but the subtle analytical result still fails
  photoreal water and external acceptance.
- Refined the render-only live-water mesh on all six authored river maps from
  3 m to 1.5 m spacing while retaining 3 m physical neighbourhoods for
  smoothing, hydraulic-relief detection, derivatives, and breaking-site
  classification. Two bounded short oblique wave bands add subcell surface
  breakup; topology and refresh-time diagnostics make the cost explicit. The
  config-less test tank remains at 3 m, all six runnable PIE map gates pass,
  and no cooked water, wet/dry state, collision, buoyancy, D3, or D4 authority
  changes. Matched Zambezi evidence retains the technical improvement but
  rejects photoreal promotion pending a connected overturning rapid body,
  measured hydraulics, target-hardware performance, and external approvals.
- Replaced Chilko Lava Canyon's inherited pale gameplay-water response with a
  river-local transmitting V2 path. The solver-owned wet-cell core now binds
  project-owned flow-normal and solver-masked foam-lace textures, while the
  live surface remains a 3.5%-14% detail skin. The regenerated map preserves
  1,632 core triangles, 1,098 wet vertices, the station-300 m rapid, collision,
  bathymetry, and raft forces. Identical-camera water-band coverage above 0.90
  luminance falls from 5.74% to 3.38%, and coverage above 0.95 falls from 1.68%
  to 0.12%. The editor build, focused material audit, live map-load gate,
  shared water-render gate, and 11 Python contracts pass. Broad wave faces,
  procedural shoreline/terrain/ecology, sparse rapid foam/spray/mist,
  unconverged hydraulics, and all six external gates keep photoreal and
  production promotion closed.
- Replaced Pacuare Upper Huacas's uniform opaque gameplay-water sheet with a
  live solver-owned transmitting core clipped to all-wet cells. The smoothed
  surface remains a 3.5%-14% hydraulic-detail skin, while the authored packed-
  field water and foam remain hidden capture-only actors. Project-owned flow-
  normal and foam-lace textures are provenance-locked, visual-only, and masked
  by solver state. The editor build, four focused native audits, live PIE map-
  load gate, four Python contracts, and matched runtime comparison pass. This
  is a bounded readability improvement; procedural terrain and ecology, thin
  optics, sparse rapid VFX, unconverged hydraulics, and all six external gates
  keep photoreal and production promotion closed.
- Reaffirmed Zambezi as the sixth runnable river on the current release head
  after the Pacuare and Chilko transmitting-water milestones. The unchanged
  committed `L_Zambezi` package remains selectable
  as **Zambezi: Boiling Pot to Mukuni Beach** in Free Run and remains in the
  shipping cook. Eighteen focused registry/source contracts, a clean 136-action
  UE 5.8 editor build, the native career catalog, and the live PIE map-load gate
  pass. The V9 review hash-locks the selector, manifest, scenario, cook list,
  and map package while retaining reference-tier status and leaving production
  terrain, bathymetry, hydraulics, photoreal art, guide/geospatial/rights, and
  performance acceptance open.
- Corrected Colorado Hance's runnable rapid framing without changing the
  committed cooked fields. `L_Hance` now launches at station 336 m instead of
  24 m, retaining a 69 m deep subcritical approach to an accepted interior
  solver transition near station 405 m. The live map reports seven active
  breaking sites, 18 m strongest-interior clearance, hydraulic relief, and
  visible rapid foam; low, moderate, and high bands pass the matching 3 m
  runtime-sampling contract. A separately serialized solver-rapid camera also
  replaces the duplicate guide/rapid evidence view. The three frames remain
  photoreal-rejected for flat banded water, weak foam/spray volume, terraced
  terrain, sparse repeated ground cover, and all six open external gates.
- Reaffirmed Zambezi as the sixth runnable river again after the Colorado Hance
  rapid-approach milestone. The unchanged committed `L_Zambezi` package remains
  selectable as **Zambezi: Boiling Pot to Mukuni Beach** in Free Run and remains
  in the shipping cook. Focused registry/source contracts, the native career
  catalog, and a live PIE map-load gate pass; the new V5 review hash-locks the
  selector, manifest, scenario, cook list, and map package. This retains
  reference-tier runnable status without claiming production terrain,
  bathymetry, hydraulics, photoreal art, guide/geospatial/rights, or performance
  acceptance.
- Replaced the production character's rotationally symmetric hip-to-knee tube
  with a 695-vertex directional thigh overlay. The retained mesh now follows a
  torso-aligned anterior axis, carries bounded quadriceps, hamstring, and
  adductor envelopes, and tapers into the solved knee while preserving the
  existing buried hip/knee overlap. All five fixed-view roster identities
  report 1.000 forward alignment, continuous opaque coverage, and less than
  `2.4e-8` cm maximum knee-centreline error; the focused native M5 gate, Python
  source contract, editor build, and renderer capture pass. Identical-camera
  front/profile/rear evidence retains this as a technical anatomy improvement,
  not photoreal promotion: simplified skinned deformation, overlap seams,
  materials, pose, and named character-art/whitewater-safety approval remain
  open.
- Corrected the Chilko Lava Canyon scenario framing after proving the committed
  cooked fields already contain an interior solver-owned hydraulic jump near
  local station 300 m. The runnable map now launches at station 228 m instead
  of 24 m, retaining a 72 m subcritical approach while placing that jump inside
  the initial 240 m moving live-water carrier. The PIE gate reports one
  interior site, full presentation coverage, 15 m edge clearance, and visible
  solver foam; all three flow bands pass the matching 3 m runtime sampling
  contract. No cooked field, wet/dry mask, bathymetry, collision, or raft force
  changed. Visual and external acceptance remain fail-closed because water is
  still pale/sheet-like and terrain, ecology, rapid morphology, VFX,
  calibration, guide review, and target-hardware approval remain incomplete.
- Retained a narrowly bounded Futaleufú live rapid-lace improvement and rejected
  two unproven water brackets. Terminator now maps existing solver foam through
  a `0.08-0.58` focus window instead of `0.12-0.72`, increasing visible rapid
  vertices from 47 to 53 while leaving the accepted shared calm material byte-
  identical. The experimental shared normal/aeration rewrite was removed after
  it rendered a pale frosted sheet. Chilko's lower threshold was also removed:
  its current cooked window has zero interior breaking sites and all four
  detected candidates are correctly rejected at the wet-mask edge. Filtered
  river generation now reuses shared solver textures and foam material without
  resaving them. The editor build, 42 focused Python checks, both river-water
  audits, shared-material audit, both map-load gates, water/occlusion render
  gate, and 75-file protected-work audit pass. The retained Futaleufú frame
  remains too pale and sheet-like for photoreal promotion, and all external
  guide, geospatial, hydraulic, art/VFX, and performance gates remain open.
- Rechecked Zambezi at release head and retained it as the sixth runnable
  river. `RaftSim.M6.CareerCatalog` resolves the player-facing
  `zambezi_reference_run` to `/Game/RaftSim/Maps/L_Zambezi`, while
  `RaftSim.P4.RiverMapLoads.L_Zambezi` loads that committed package into PIE
  with the vertical-slice game mode, a 5,908-point curved coordinate map, live
  cooked-field water, 2,673 wet vertices, eight active breaking sites, and 125
  visible rapid-foam vertices. The editor builds, 11 focused Python contracts
  pass, both native gates pass, and MapCheck reports zero errors and zero
  warnings. The new hash-locked review records the benign connectivity-probe
  timeout and existing motion-vector warning separately. This is a
  runnable-reference verification, not photoreal or production-hydraulic
  promotion.
- Rebuilt the shared runnable Futaleufú/Chilko fallback canopy as first-party
  Structure V3 geometry. Compound asymmetric crownlets, varied and staggered
  conifer whorls, overlapping distance-stable crown bodies, bounded shortened
  limbs, and trunks that stop at the highest whorl replace the repeated
  bare-pole/diamond-tip silhouette while preserving the four-form family,
  6,200 instances per river, water and physics authority, and deterministic
  placement. Both regenerated maps pass their focused native load contracts;
  fixed-camera review accepts only an incremental fallback improvement because
  species/ecology, close botanical detail, water, terrain, guide/art review, and
  target-hardware performance gates remain open.
- Pinned Zambezi in the versioned six-river Free Run progression contract.
  The manifest now binds `zambezi_batoka_gorge` to
  `zambezi_reference_run` and `/Game/RaftSim/Maps/L_Zambezi`, while focused
  Python and native catalog checks prevent the runnable entry from silently
  falling back to the superseded preview map or disappearing from the menu.
- Rebased all five packaged CC0 fallback FBXs so their raw reference vertices,
  evaluated Blender geometry, and imported Unreal LOD0 agree. The generator and
  canonicalizer now bake the evaluated shape/armature result and promote the
  current armature pose to rest before restoring one clean modifier; a new
  fail-closed validator checks raw reference, evaluated reference, and a 58°
  synthetic head pose. Unreal now derives the live helmet anchor from the
  actually rendered Eye section and applies reviewed per-identity seating.
  All five source reports pass, native eye/brow p95 separation remains below
  1.25 cm, the renderer capture completes 20/20 views, and M5 completes five
  tests with zero failures. This closes the detached/closed-looking eye and
  off-head helmet regressions technically, but simplified anatomy, material
  response, garment/arm/hand/PPE intersections, and missing named character-art
  and qualified whitewater-safety approval still reject photoreal promotion.
- Added a retained V2 cold-water presentation bracket to the runnable
  Futaleufú Terminator and Chilko Lava Canyon maps. Their river-local Default
  Lit parents now use three moving normal directions, three world optical
  scales, and varied roughness; the noncolliding capture ribbons use 48
  cross-current samples, bounded multiscale/cross-current chop, embedded
  aeration color, and zero-displacement bank tapers. Live solver geometry,
  collision, hydraulic state, bathymetry, buoyancy, and raft forces are
  unchanged. Build and focused native/Python/map gates pass, while opaque
  near-field water, sparse rapid VFX, coarse terrain, procedural ecology, and
  all named external reviews still reject photoreal promotion.
- Clarified the working Zambezi launch contract in the player and design docs:
  **Free Run → Zambezi: Boiling Pot to Mukuni Beach** is available without a
  career-license unlock and resolves to the committed, cooked
  `/Game/RaftSim/Maps/L_Zambezi` package. This reaffirms runnable reference
  status without claiming production terrain, hydraulic, guide, art, rights,
  or performance acceptance.
- Replaced South Fork's washed-out Unlit Landscape review response and uniform
  green runnable ground plate with a shared, shade-only organic foothill graph.
  Three incommensurate world-space fields add dry grass, oak litter, granitic
  soil, slope-aware weathered granite, and fine mineral value; the review
  candidate uses a stronger correction while the actual
  `L_SouthForkAmerican_FullReach` terrain parent retains registered source
  colour. Build, exact material audit, renderer-enabled full-reach route, fixed
  captures, and focused Python contracts pass. Geometry, collision, shoreline,
  navigation, hydraulics, water, and raft forces are unchanged. Coarse terrain,
  synthetic vegetation, sparse mid-story cover, smooth water, and external
  review still reject photoreal promotion.
- Revalidated Zambezi Batoka Gorge as the sixth runnable river and regenerated
  the committed `/Game/RaftSim/Maps/L_Zambezi` package from the filtered source
  corridor pipeline. The frontend `zambezi_reference_run` entry, source model,
  scenario, cook list, schema-v16 saved-map audit, M6 career catalog, and live
  P4 PIE map-load gate all resolve to that package. The regenerated reference
  map retains all 25 rapid markers, Rapid 9's mandatory-portage policy, one
  player raft/start, live cooked-field water, four source-conditioned terrain
  tiles, two adaptive near-field banks, 360 launch talus instances, and 8,927
  vegetation instances. Conditioned render-only wet-bank masks now use an
  explicit vertex-red scalar, while the talus material reads one conditioned
  waterline per instance; neither path changes collision, bathymetry,
  hydraulics, or raft forces. This is runnable acceptance, not photoreal or
  real-world hydraulic promotion.
- Reworked the runnable Zambezi Single Layer Water parent's normal projection
  into shorter, crossed wavelengths while retaining its accepted sediment
  volume response. Only the secondary layer swaps UV axes; bounded normal and
  variation response rise to 0.10 and calm presentation displacement falls to
  0.06. Brighter reflection/emissive brackets were rejected as pale sky sheets.
  The editor build, exact saved-material audit, runnable-map load, general
  surface-render gate, MapCheck, and focused Zambezi source/route tests pass.
  Broad smooth water, residual streamwise grooves, sparse whitewater VFX,
  coarse terrain/ecology, the dark fixed-route offscreen-capture defect, and
  all named external reviews still reject photoreal promotion.
- Reduced Colorado Hance's capture-only cooked-field relief ceiling from 45 cm
  to 9 cm and added a river-local, plane-preserving five-tap presentation filter
  to both capture and live render geometry. The live path smooths a temporary
  presentation array only; raw solver samples, collision, bathymetry, buoyancy,
  and raft forces remain unchanged. A narrower lace-foam bracket reduces bright
  neutral coverage in the guide/solver water band from 3.68% to 0.37%. Build,
  regeneration, native water-authority, runnable-map, and nine focused Python
  gates pass. Horizontal bands, sparse foam, opaque water, terraced canyon
  geometry, missing rapid VFX, unconverged hydraulics, and external review still
  reject photoreal promotion.
- Repaired the Zambezi runnable-map regression guard so the player-facing
  `zambezi_reference_run` catalog entry, M6 progression test, Python shipping
  contract, and cook configuration all resolve to the committed
  `/Game/RaftSim/Maps/L_Zambezi` package instead of the former ignored preview
  candidate.
- Gave runnable Colorado Hance an isolated four-scale Default Lit canyon
  surface and Colorado-only opaque Default Lit capture-water parent. The new
  shade graph adds sandy-bench, weathered-rock, dark-basement-rock, iron-cliff,
  talus, and fine mineral breakup without moving the Landscape or changing
  collision, bathymetry, hydraulics, or raft forces. Hance now samples its
  reach-local cooked field once through CPU-authored vertex color and uses two
  moving native normal layers instead of re-sampling the shared South Fork
  shader field. Fixed water-band mean luminance rises from 0.1922 to 0.2716 in
  the guide view and from 0.2225 to 0.3312 at river eye. The editor build, two
  native material audits, runnable-map gate, and focused contracts pass.
  Polygonal canyon terraces, stepped opaque water, coarse foam sheets, sparse
  ecology, missing surveyed Hance geography, unconverged hydraulics, and all
  six external acceptance gates keep photoreal and production promotion open.
- Corrected Chilko Lava Canyon water provenance and optical response without
  changing its ribbon geometry, collision, hydraulics, or raft forces. The
  capture ribbon now uses an isolated opaque Default Lit parent, Chilko's own
  normal atlas, two moving normal layers, and two non-harmonic world-space
  optical scales; its reach-local cooked field is sampled once into CPU-authored
  vertex color instead of being overlaid with the shared South Fork shader
  field. The live solver carrier now exposes river-local reflection, ripple,
  foam, and color controls. Across the fixed water-band region, mean luminance
  rises from 0.1522 to 0.2529 in the guide view and 0.1518 to 0.2514 at river
  eye, while RGB variation rises from 0.0463 to 0.0771 and 0.0473 to 0.0777.
  The editor build, native saved-material audit, runnable-map gate, and focused
  contracts pass. Broad synthetic water, weak rapid-scale relief, sparse foam
  and spray, coarse terrain, repeated ecology, unconverged hydraulics, and
  named external review keep photoreal and production acceptance open.
- Replaced Chilko Lava Canyon's nearly black generic bank plate with an
  isolated four-scale Default Lit organic surface. Source-registered macro
  color, water zones, detail normals, wet-bank conditioning, and the existing
  Landscape remain authoritative while non-harmonic world fields add open-
  bench value, dry grass and mineral soil, slope-aware wet/oxidized basalt,
  scree, and fine mineral response. The change has no world-position offset
  and does not alter terrain geometry, collision, bathymetry, hydraulics, or
  raft forces. Fixed left-bank mean luminance rises from 0.1199 to 0.2375 in
  the guide view and from 0.1397 to 0.2616 at river eye; near-black coverage
  falls from 30.05% to 1.04% and 32.90% to 0.85%. The editor build, saved-
  material audit, runnable-map gate, and focused contracts pass. Broad 30 m
  terrain, visible horizontal banding, generic ecology, uniform water, weak
  rapid VFX, unconverged hydraulics, and external acceptance remain open.
- Corrected Futaleufú Terminator water provenance and optical response without
  changing its ribbon geometry, collision, hydraulics, or raft forces. The
  capture ribbon now uses an isolated opaque Default Lit parent, Futaleufú's
  own normal atlas, two moving normal layers, and two non-harmonic world-space
  optical scales; its reach-local cooked field is sampled once into CPU-authored
  vertex color instead of being overlaid with the shared South Fork shader
  field. The live solver carrier now exposes river-local reflection, ripple,
  foam, and color controls. Across the fixed water-band region, mean luminance
  rises from 0.1611 to 0.2063 in the guide view and 0.1583 to 0.2028 at river
  eye, while RGB variation rises from 0.0482 to 0.0722 and 0.0479 to 0.0719.
  The editor build, native saved-material audit, runnable-map gate, and focused
  contracts pass. Broad synthetic water, sparse foam/spray, coarse terrain,
  repeated ecology, missing local bathymetry, and named external review keep
  photoreal and production acceptance open.
- Corrected Futaleufú Terminator's generated Landscape material from an
  unlit/manifest mismatch to a saved Default Lit organic temperate graph. Three
  incommensurate world-space fields now vary humid-forest value, moss and leaf
  litter, slope-aware wet granite and lichen, and fine mineral response without
  moving terrain or changing collision, hydraulics, or raft forces. Fixed-camera
  comparison reduces near-black left-bank coverage from 13.17% to 4.77% in the
  guide view and from 7.72% to 3.99% at river eye. The editor build, saved-material
  audit, runnable-map gate, and 32 focused contracts pass, but coarse 30 m terrain,
  repeated procedural vegetation, flat dark water, understated rapid hydraulics,
  sparse bank structure, and missing named external review keep the result
  photoreal-rejected.
- Superseded the smooth production splash-jacket sleeves with denser folded
  garment shells. Each shoulder-to-elbow overlay now uses 28 axial rings and
  36 radial sides, two bounded diagonal fold fields, cuff gathering, underarm
  seam relief, an elliptical profile, and finite-difference surface normals.
  An isolated opaque Cloth parent uses the complete project-owned ripstop set
  and shares the PFD's bounded presentation-only wetness. All five production
  identities pass the 1,000-vertex, live-material, visibility, and joint-anchor
  gates; the editor build, isolated material audit, 16 focused contracts,
  five-identity renderer roster, and renderer-enabled M5 test pass. The result
  is retained as a technical improvement but remains photoreal-rejected for
  regular procedural folds, abrupt garment integration, missing skinned cloth
  deformation and tailoring, and absent named character-art/guide review.
- Replaced the production splash-jacket's uniform shoulder-to-elbow primitives
  with closed, tapered garment sleeves. An 18-ring, 28-sided profile now carries
  a broad deltoid into a smaller cuff; all five production identities retain the
  live solved joint anchors and pass the new 550-vertex fail-closed guard. The
  editor build, roster renderer, and renderer-enabled M5 gate pass technically.
  Procedural topology, abrupt cuff integration, cloth deformation, wet response,
  and named character-art/guide approval keep photoreal acceptance open.
- Rebuilt the production rescue PFD as a fitted soft-carrier V3 across every
  runnable river. Two front carrier halves and one rear carrier now support
  thinner rounded foam cells; rigid side wings are removed in favor of three
  flat fit bands per side; the rescue belt is a flat torso-following loop; and
  duplicate tubular adjustment geometry is gone. The deterministic Blender
  source, fail-closed Unreal importer, 39,448-triangle Nanite asset, five-identity
  roster captures, dry/wet close views, and renderer-enabled M5 gate all pass
  technically with zero torso-origin error. Remaining faceting, fabric/hardware
  fidelity, deformation, and named character-art/safety approval keep photoreal
  acceptance and release promotion open.
- Reverified Zambezi Batoka Gorge as a selectable sixth runnable river. The
  generated player-selection model, Unreal river catalog, frontend scenario,
  source scenario, shipping cook list, versioned `L_Zambezi` map, and focused
  runtime acceptance contract all resolve the same `reference_free_run` while
  production terrain, hydraulics, guide, art, rights, and performance gates
  remain open.
- Added two source-conditioned, non-colliding 5 m adaptive bank meshes over the
  first kilometre of the runnable Zambezi map, with bounded dry-shoreline and
  sub-metre erosion/talus infill where the 30 m source lacks local detail. The
  retained bracket suppresses the first iteration's catastrophic self-shadow
  wedges, expands launch ecology to 1,721 ground-cover and 174 woody instances,
  and binds a tagged four-actor dry-season atmosphere contract. Saved-map schema
  v13, the focused runtime gate, and Python regression lock the authority
  boundary. The default frame remains photoreal-rejected because the canyon,
  ground cover, water, rocks, ecology, and atmosphere are visibly synthetic.
- Promoted the complete Zambezi Batoka Gorge reference run from an ignored
  `EnvironmentPreviews` candidate package to the stable, versioned
  `/Game/RaftSim/Maps/L_Zambezi` runnable-map contract. The frontend, generated
  selection model, scenario, shipping cook list, packaging fallback, runtime
  map-load gate, and documentation now resolve the same package. This changes
  delivery, not authority: the 25-rapid route remains a runnable reference Free
  Run with procedural water/bathymetry and open production-fidelity gates.
- Restored Colorado Hance as a physical reach-local runnable map instead of a
  flat rapid shell or mismatched Lees Ferry preview. The 600×320 m Landscape
  preserves the complete interpreted 600×78 m cooked-field bed, procedurally
  fills only the missing outer canyon, aligns the 950.713 m runtime datum, and
  launches live moderate-release solver water with the player raft and game
  mode. Focused PIE and MapCheck gates pass; surveyed Hance geography,
  converged/calibrated hydraulics, organic ecology, photoreal water and foam,
  guide review, and production performance acceptance remain explicitly open.
- Pacuare Upper Huacas now derives its capture-only water color, bounded surface
  relief, and separate masked foam sheet from the committed rain-fed cooked
  depth/speed/Froude field. Canonical cameras frame the station 286 m hydraulic
  crux, and capture automation temporarily reveals the two authored water actors
  before restoring their serialized hidden-in-game state. The live solver remains
  the sole gameplay renderer and force authority; the focused build, map, material,
  and provenance gates pass, while field convergence and photoreal/guide approval
  remain explicitly rejected.
- Restored Zambezi Batoka Gorge to the generated player-selection source model,
  aligning it with the already-runnable Unreal Free Run catalog, scenario,
  shipping cook target, and saved map. A cross-model regression now locks the
  `reference_free_run` tier, frontend scenario, map package, and runnable
  normal-big-water reference band; the focused Unreal map-load acceptance and
  Zambezi Python suites pass again.
- Restored Pacuare Upper Huacas as a physical reach-local runnable map instead
  of the flat signature-rapid shell and scale-mismatched broad DEM preview.
  `L_UpperHuacas` now combines a 600×78 m Landscape, bounded outer-bank infill,
  an explicit 454.283 m solver/world vertical datum, live cooked water, player
  raft/start, and the vertical-slice game mode. The focused PIE gate passes with
  a wet finite window, upright raft, and zero swimmers; opaque preview water,
  generic foliage, missing visible rapid foam/spray, higher-resolution source
  geography, and external acceptance still block photoreal promotion.
- Retained a second Zambezi sediment-water profile on the runnable Batoka Gorge
  reference Free Run. The isolated Single Layer instance now uses darker
  sediment absorption, 0.48 opacity, 0.50 roughness, 0.26 specular, 0.04 normal
  and optical-variation strength, 0.92 mesh-normal up blend, and 0.08 authored
  ribbon displacement. Matched gameplay evidence reduces the calm launch's
  mean horizontal image gradient by 39.7%, removing most long artificial
  streamwise grooves while preserving solver foam, raft/crew foam exclusion,
  collision, navigation, and hydraulic authority. Saved-material, water-render,
  runnable-map, and 25-marker scenario gates pass; the environment remains
  photoreal-rejected pending the documented external terrain, bathymetry,
  hydraulics, ecology, art, guide, rights, and performance gates.
- Replaced the uniformly plastic production-PFD shell response on every runnable river
  with project-owned ripstop Cloth shading, restrained dry fuzz, and a per-avatar dynamic
  wetness instance driven by native raft surface wetness plus swimmer, re-entry, and falling
  state. A rejected over-glossy bracket was tightened to a 0.42 wet specular endpoint,
  0.40 saturated-roughness floor, and retained 0.16 wet cloth response. Matched dry/wet
  renderer evidence and all five M5 production-quality rows pass technically; simplified
  construction, body deformation, surrounding character art, and named art/safety review
  remain open, so this is not photoreal promotion.
- Reaffirmed Zambezi Batoka Gorge as the sixth runnable river at the bounded
  `reference_free_run` tier across the portfolio, generated scenario, player
  catalog, frontend launch contract, cook/regeneration checks, and current
  documentation. A cross-layer regression now prevents the runnable map from
  silently falling out of any one of those registries; the historical 5+1
  editor report is explicitly marked as superseded rather than rewritten as
  new execution evidence.
- Restored Zambezi to the authoritative six-river named-rapid portfolio as a
  `reference_free_run`, regenerated editor markers and all 123 Zambezi review-run
  definitions with runnable metadata, and changed the live Rapid/River Editor summary
  from five runnable plus one additional environment to six runnable rivers. The
  generated Batoka map is now a shipping cook target; Mac and Windows packaging
  regenerate it from source-controlled inputs when the ignored local map is absent.
- Extended the bounded 12-card connected-crown treatment from interior live oak to all
  six active South Fork canopy profiles using project-owned Ponderosa-pine, white-alder,
  and deerbrush branch atlases. Each deterministic 4×4 atlas carries twelve occupied
  sprays, tangent normals, packed AO/roughness/subsurface, and cell-bounded mip padding;
  every retained mesh is 56 vertices, 28 triangles, two material slots, and non-colliding.
  Five fixed Unreal views show restrained added crown depth without chroma halos or
  obvious clutter, but the planar cores, dark repeated stands, and wider scene still fail
  photoreal acceptance. The regenerated world preserves 176 stable actor identities and
  all 24 HLOD actors converge to a zero-save repeat with zero errors.
- Replaced the South Fork interior-live-oak two-plane endpoint with a project-owned,
  deterministically alpha-matted 4×4 branch atlas and a bounded connected crown. A
  20-card bracket was rejected for dark clumping; the retained 12-card/28-triangle
  endpoint keeps one spray per occupied tile, adds visible crown depth, and shows no
  chroma fringe across five fixed Unreal views. It remains an active technical fallback,
  explicitly rejected for photoreal and release promotion. The regenerated full-reach
  world preserves 176 stable actor identities, and all 24 HLOD actors converge to a
  zero-save repeat with zero errors.
- Added bounded per-instance radiometric and opacity variation to the six active
  project-bound South Fork canopy profiles, with a small species-specific base and
  transmission lift. Five fixed Unreal views retain controlled masked edges and show
  modestly better crown separation, but the two-plane foliage remains visibly card-like
  and is explicitly rejected as photoreal art. The material refresh converged through
  24-actor HLOD rebuild passes to a zero-save terminal repeat with zero errors.
- Replaced the periodic far-field procedural land-cover palette with deterministic,
  coordinate-stable domain-warped dry-grass, chaparral, woodland, and rock regions and
  widened the authoritative-imagery feather from 256 m to 720 m. Two independent
  generations are byte-identical; five fixed Unreal views show materially reduced
  diagonal banding and hard source rectangles. The current world then rebuilt 24/24
  HLOD actors and produced a zero-save settled repeat. This is retained as an incremental
  terrain improvement, not photoreal art acceptance.
- Rebuilt all 24 terminal World Partition HLOD actors after the authoritative
  South Fork world regeneration, proved a zero-save settled repeat, and refreshed the
  manifest-linked package-hash evidence. The complete qualified Python matrix now has
  1,112 passes and three expected skips; its sole failure remains the deliberately stale
  and fail-closed M9 release-candidate raft-source assertion.
- Softened the solver-driven contact-water patch's runtime opacity and analytic breakup
  contrast. The retained 96-triangle sheet now reads as a continuous aerated fan instead of
  a bright cellular quilt while preserving D3/D4, collision, raft, rescue, material-package,
  and contact topology authority. The matched v735 frame and M4 suite pass, but the full
  scene remains explicitly rejected as photoreal release art.
- Corrected the production crew's high-side pose so shoulders, hips, knees, and
  progressively planted feet follow the torso/head shift instead of stretching the
  rigged CC0 bodies through the raft and PPE. The follow-up v570 adapter makes terminal
  head bones derive orientation from their reference up axis so heads and helmets follow
  the same high-side rotation, with a CC0-only outer-shell allowance to reduce scalp
  intersection. The v570 source-true wrap frame retains
  four D4 contacts, three wrapping nodes, one pin, one recovery, 0.220 m indentation,
  and 0.998 wetness. This is a technical pose upgrade only: faces, hands, helmet/PFD fit,
  clothing, raft, rock, water, lighting, shoreline, spray, and terrain remain rejected as
  photoreal release art. Exact-current M4/M5/M7/M8/M9 gates and the 1,086-test matrix pass.
- Reworked the project-owned procedural evidence boulder with a deterministic
  multiharmonic profile, shouldered crown, corrected tangent basis, and separate mineral
  material branch. The source-true v552 wrap capture retains the same D4 contact/pin/
  recovery authority but remains rejected as photoreal art; the optional CC0 scan remains
  disabled after a non-visible diagnostic. This visual delta makes the prior v527 Shipping
  package/performance/archive evidence historical until a fresh build is qualified.
  Exact-current M4/M5/M7/M8/M9 automation and the 1,086-test Python/data/source matrix pass.
- Recalibrated the South Fork Single Layer Water and bounded live-water overlay to reduce
  flat white foreground foam, improve olive depth/readability, remove surface-mesh seam
  shadows, and preserve solver-conditioned spray, mist, sheets, and droplets.
- The exact-current macOS arm64 Shipping diagnostic passes a full 1,082-of-1,089 package
  cook with seven platform skips, five packaged QA reports, two cooled 60-second
  normal-window Metal soaks with zero hitches, archive creation, and independent artifact
  verification. The adhoc-signed 1,272,361,448-byte archive has SHA-256
  `4f92bc38bec8cac643c656fd547b9ee79b7843d732b2132fe0d6328fd0812d53`.
  Six offscreen diagnostics remain variable and are not release-qualified; final
  photoreal/marketing art and external acceptance remain open.
- Release evidence capture now loads the saved full-reach World Partition map without
  regenerating or resaving it, hard-loads all actors, and resolves guide-eye elevation
  from the saved median-flow centerline mesh. Independent v269/v270 runs pass with three
  byte-identical views and at most seven changed pixels in either remaining view.
- M9 remains fail-closed for photoreal production art, named human review, external
  platform/input hardware, distribution signing/notarization, approved media, and clean
  immutable Shipping promotion.
- The coated-fabric response is retained as a reusable technical fallback. The same
  v280 frame rejects residual PFD grain, mannequin anatomy/generic wardrobe, and the
  procedural raft as final photoreal art or release media.

## [1.0.0-rc1] — 2026-07-19

### Added

- A continuous 49.1 km South Fork American guide campaign with four career sections,
  a full descent, Free Run, Training Eddy drills, progression, medals, saved checkpoints,
  route ghosts, accessibility settings, and keyboard/gamepad rebinding.
- All 20 named rapids at 900, 1,600, and 3,000 cfs, driven by the packaged first-party
  finite-volume shallow-water solver and validated across 60 rapid/flow combinations.
- Deterministic, source-conditioned procedural terrain and bathymetry infill wherever
  authoritative DEM, imagery, bank, or hazard information is absent. Generated areas are
  permanently labelled as inferred and not suitable for navigation.
- A visibly flexible raft with local tube compression, buckling, wrap, pin, capsize,
  damage, recovery, and live rock-contact coupling, plus five-person crew commands,
  swimmer rescue, throw line, reach grab, re-entry, and checkpoint recovery.
- Runtime weather, camera, layered synthesized audio, HUD, scouting, command wheel,
  after-action review, legal/credits screens, and packaged validation entry points.
- Release-candidate source, package, signature, QA-report, archive, and checksum tooling.

### Changed

- Runtime water and raft physics remain at 60/120 Hz while visual water refreshes at
  15 Hz on a 3 m mesh, retaining validated hydraulic authority with lower presentation
  cost.
- Live-water UVs now stay in a three-metre river-coordinate scale while the solver
  window recentres; hydraulic foam is restricted to actual high-energy cells, and the
  terrain material exposes more of its licensed soil/rock detail without overriding
  the source-conditioned aerial macro.
- Single Layer Water scattering and absorption now use Unreal's inverse-centimetre
  units and are reference-calibrated for darker olive South Fork water; detailed and
  far-field terrain give the source imagery 66 and 78 percent macro influence.
- Generated pine/live-oak canopy proxies now use three radial photographic planes,
  species-specific shaded fill, and deterministic nonuniform crown variation. The
  full-reach builder now assigns stable GUIDs and stable object names to all 163
  generated actors, including the World Partition minimap, so repeated editor runs
  reuse the same external actor package paths.
- Cooked rapid fields retain their absolute source elevation datum through runtime
  loading, with automated above-water chase-camera and clean PIE environment captures
  guarding the corrected full-reach presentation.
- The procedural production raft now carries a deforming safety-yellow perimeter grab
  line, textured commercial tube/floor surfaces, and cleaner spray; guide and crew
  silhouettes now include 25 first-party components, with six rounded PFD foam/shoulder
  submeshes, both helmet-retention straps, and seventeen facial submeshes batched into
  three animated components. Four deterministic skin tones, project-owned 1024×1024
  synthetic micro-albedo/normal maps, a 20×28 parametric head, vertex-coloured eyes,
  eyelids, brows, mouth and nostrils, a subsurface face material, 10×24 front-cut open
  helmet shells, rear webbing, buckles, necks, hands, boots, and four deterministic body
  profiles retain the same component budget and authoritative pose/rescue behavior. The
  current character pass remains explicitly below photoreal human-art acceptance. It is
  present in the v3 Shipping archive and passes local diagnostic-clone functional and
  Metal performance gates; sandboxed startup, clean-source, representative-art, and
  external platform qualification remain open.
- Volumetric weather uses bounded temporal samples, stable sun state, and cached skylight
  capture to meet the 1080p60 workload budget on the locally available Apple M5 system.
- Project version advanced from the development line to `1.0.0-rc1`.

### Known release-candidate constraints

- Windows x64, RTX target, Proton, Developer ID/notarization, and external guide,
  geospatial, art, and legal acceptance require their named M9/M10 platform or human
  lanes. They are not represented as completed by this RC source tag.
- VR and multiplayer are explicitly deferred beyond flat-screen single-player 1.0.

### Game completion M3 — Full South Fork hydraulics (July 19, 2026)

- Cooked all 20 South Fork named rapids at 900, 1,600, and 3,000 cfs through the
  genuine first-party finite-volume solver; all 60 combinations pass finite-state,
  mass/volume, velocity, inflow/outflow, discharge-response, and 105 catalogued
  hydraulic-feature envelopes.
- Added flow-specific preferred lines, scout eddies, hazards, checkpoints, rescue zones,
  and outcome envelopes for every named rapid.
- Added a deterministic full-reach procedural transit seed, explicit inferred/not-for-
  navigation authority, and no-gap streaming coverage across the 49.1 km descent.
- Added state-preserving Unreal moving-water handoffs with global stationing, authored
  full-edge boundary forcing, transmissive crop edges, overlap depth/velocity transfer,
  continuous solver time, handoff telemetry, and non-overlap reset rejection.
- Added C++ replacement-state coverage, five hydraulic artifact tests, and two Unreal M3
  automation gates. The full physics/content suite passes 1,026 tests with 3 expected
  optional-dependency-path skips.

### Game completion M2 — Procedural geography completion (July 19, 2026)

- Added a deterministic full-reach South Fork geography generator that conditions all
  eight official 3DEP/NAIP windows along the adopted 49.1 km axis and fills missing
  bathymetry, banks, rapid controls, boulders, and shoreline detail.
- Added explicit source-authority, procedural-infill, uncertainty, material, and
  hydraulic-feature masks plus a seeded 115-boulder catalog. Generated content is
  permanently marked as inferred and not suitable for navigation.
- Added a 4 m canonical solver/collision/render grid and thirteen overlapping Unreal
  import tiles whose collision and render height hashes are identical.
- Added geography continuity, provenance, determinism, feature-coverage, and exact tile
  overlap automation. The focused suite passes 19/19 and the full physics/content suite
  passes 1,021 tests with 3 expected dependency-path skips.

### Game completion M1 — Flexible raft and rock contacts (July 19, 2026)

- Added runtime-authoritative rock actors and connected nearby world rocks to the D4
  flexible contact/wrap/pin/release solve.
- Exported D1-D4 per-segment visual state and made the procedural raft tubes and floor
  visibly compress, lose freeboard, indent around contacts, and recover after release.
- Regenerated all five runnable river maps with deterministic hydraulic-crux rock gardens
  and added automation for wrap deformation, stable topology, recovery, and serialized
  contact authority.
- Added an explicit wrap-test capture command and made latent gameplay tests select the
  newest PIE world/reset inherited motion when run after other tests.
- Published `docs/game-completion-plan.md` as the active milestone roadmap through 1.0.

### Phase 0 — Governance reset, licensing, repo trim (July 17, 2026)

- Froze the superseded five-river execution plan and its external-review/DoD apparatus; `docs/release-1.0-plan.md` (revision 2) is the single top-level driver.
- Recorded the July 17 owner reversal of the July 16 no-prune retention decision in `docs/generated-artifact-retention-policy.md`; repo trim and history clean authorized.
- Retired the July 16–17 process-artifact machinery: ~230 review-form / recommendation / readiness / briefing / acceptance / work-order generator modules, their tests, generated JSON templates, and per-gate form docs. Product evidence (source pulls, audits, diagnostics, corridor data, review JSONs) is untouched; git history and the pre-rewrite archive retain everything deleted.
- Added `LICENSE` (MIT, code), `LICENSE-CONTENT.md` (CC BY 4.0, first-party content), `NOTICE.md`, `CREDITS.md`, root `README.md`, and this changelog.

### Phase 1 (in progress) — Playable skeleton (July 17, 2026)

- South Fork A1 stationing adopted per plan §6: official Salmon Falls take-out anchor (station 49,077.7 m / 30.495 mi), all 20 named rapids re-stationed on the corrected axis, guide-review items converted to `pending_human_review`.
- First runtime gameplay code: `ARaftSimRaftActor` (multi-point tube buoyancy, drag, paddle impulses, 120 Hz self-integration), Enhanced Input bindings on `ARaftSimGuidePawn` (paddle/turn strokes, look, high-side, guide commands), `URaftSimMainMenuWidget`, `URaftSimSaveSubsystem`, `ARaftSimBootGameMode`.
- Generated runtime content via new headless bootstrap commands: 24 `IA_*` input actions + `IMC_RaftSimDefault` (KBM+gamepad), `L_RaftSimBoot` (fixes the broken GameDefaultMap), `L_RaftSimTestTank` (flat-water raft tank).
- CI (`.github/workflows/physics.yml`): physics suite, C++ solver build/tests, repo guards (`Scripts/check_repo_guards.py`). Packaging scripts for macOS/Windows under `unreal/Scripts/`.
