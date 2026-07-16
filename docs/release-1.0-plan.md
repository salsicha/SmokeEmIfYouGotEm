# RaftSim 1.0 Release Plan

Written July 16, 2026, from a fresh full-repo analysis. This plan is the **master plan** for taking this project from its current state to a released, playable game. It is written for an autonomous agent that **cannot ask the owner anything**: every choice is decided here, and §10 gives decision principles for choices this plan did not foresee. Where a step physically requires the owner (account creation, payments, playing the build), the agent prepares everything, adds the item to the §9 owner-handoff checklist, and keeps moving — such items block the *release date*, never the *work*.

This plan supersedes `docs/five-river-photoreal-execution-plan.md` as the top-level driver. That plan's content pipeline survives inside Phase 4 (South Fork only) and becomes the post-1.0 roadmap for the other rivers. `docs/code-review-remediation-plan.md` is complete and stays closed.

## 1. Current state (verified July 16, 2026)

**What exists and is good:**
- A genuine finite-volume shallow-water solver core: Rusanov/HLL/Roe Riemann solvers with entropy fix, hydrostatic reconstruction, bed-slope sources, CFL-limited substepping (`physics/cpp/src/solver_numerics.cpp`), split into maintainable files. Honest parity accounting: **6/40 rows genuine solver parity, 34/40 openly labeled GeoClaw playback** (`physics/reports/solver_truth_baseline/`), toggled by `SolverConfig::disable_fixture_calibrations`. Runtime budget PASSES: South Fork windows at ~0.63 ms/tick vs a 1.6 ms desktop budget (`physics/reports/milestone16/runtime_profile.md`).
- Flexible-raft reference physics D1–D5 (compliant tube, seat-load coupling, overwash/flip, rock wrap/pin, telemetry) — real, deterministic, tested, but quasi-static, Python-only, and stamped `disabled_reference_only`. D6 comparison harness awaits measured engine results.
- A ~48K-line procedural environment authoring toolkit in the RaftSimEditor module (landscape import, materials, foliage, captures, 40+ commands), cleanly split.
- Corridor source data for five rivers; an 85-marker named-rapid catalog with 453 blocked simulator review-run definitions; 677-passing physics test suite; rigorous hash-locked evidence conventions.

**What does not exist (the actual gap to "playable game"):**
- No input bindings (zero `UInputMappingContext`/`UInputAction` assets; `DefaultMappingContexts=()`), no UMG widgets, no menus, no HUD, no save/load calls, no sound assets or playback, no Niagara, no crew actors or animation, no raft movement (the Chrono adapter is a `position += velocity*dt` stub that nothing ticks), no live water (the runtime sampler returns constant depth 1.0 m), no water surface rendered in any map, and the configured boot map `/Game/RaftSim/Maps/L_RaftSimBoot` **does not exist**. The 84 maps are environment previews with a PlayerStart and nothing else. Runtime gameplay C++ totals ~1,900 lines vs ~47,900 in the editor module. The project does not package into a runnable game today.
- No LICENSE file anywhere in the repo — a release blocker for a self-described open-source project.
- South Fork A1 stationing is blocked: the NHD-derived downstream take-out candidates sit >9 km from official California State Parks access geometry; 20.5 vs 21.0 published-mile conventions conflict.

**Conclusion:** the release effort is ~15% content polish and ~85% building the runtime game. The plan below is organized accordingly.

## 2. Product definition (all decisions final)

| Decision | Value |
|---|---|
| Title | **RaftSim** (subtitle for stores: *RaftSim — Whitewater Guide Simulator*). Repo name stays SmokeEmIfYouGotEm as internal codename. Before first public asset, run a name-collision search (Steam, itch.io, USPTO TESS, Google); if "RaftSim" is taken as a game title, fall back in order: "RaftSim: Big Water" → "River Guide: Whitewater Simulator" → "Chili Bar" (evocative single-name). Record the search evidence and pick in `docs/branding-decision.md`. |
| Genre / pitch | First-person whitewater river-guide simulator: read the rapid, set the angle, call the strokes, keep the crew in the boat. |
| 1.0 content scope | **One river, complete and deep: South Fork American, Chili Bar → Salmon Falls (Folsom Reservoir)**, all 20 cataloged named rapids, three flow bands (900 / 1,600 / 3,000 cfs, the attached presets). Plus a Training Eddy tutorial area (reuses the existing Chili Bar pilot window). No other rivers in 1.0 — Futaleufú, Pacuare, Chilko, Colorado, Zambezi are the post-1.0 roadmap in that order. Depth over breadth is the quality strategy. |
| Game modes | (1) **Guided Descent** — career: run South Fork section-by-section at rising flows, license-tier progression unlocks harder flows/sections. (2) **Free Run** — any unlocked section, any unlocked flow, scored. (3) **Training Eddy** — tutorial drills: strokes, commands, ferrying, eddy catch, flip/swim/rescue. |
| Player fantasy / camera | Guide seat, stern, first person (the existing `ARaftSimGuidePawn` camera + comfort filter). Optional third-person chase cam in Free Run only. |
| Crew | Guide (player) + 4 AI paddlers. Command-driven (radial menu + hotkeys): All Forward, All Back, Left Back/Right Forward, Right Back/Left Forward, Stop, Get Down, High Side (timed QTE-style response window). Crew respond with authored barks; crew weight/safety math already exists (`RaftSimCrewStateContracts.cpp`). |
| Voice input / local AI | **Cut from 1.0.** The bark catalog ships as authored text + TTS-generated audio under the existing AI-audio policy. Local voice recognition is post-1.0. |
| Multiplayer | **Cut from 1.0** (docs already gate it; nothing is implemented). |
| VR | **Cut from 1.0; targeted 1.1.** Zero VR code exists today and VR QA would consume the whole schedule. The comfort-camera scaffolding, OpenXR plugins, and seated-posture design docs stay in place; 1.0 ships flat-screen only. Remove `bEnableHMD=True` from shipped config to avoid accidental HMD capture. |
| Platforms | **Windows x64 (primary) and macOS Apple Silicon (secondary — it is the dev platform and the Metal path is maintained).** Linux via Proton verification only (no native build). No consoles, no handheld. |
| Distribution | **GitHub Releases (primary), itch.io (secondary), Steam (prepared, owner-gated).** The agent produces packaged builds, store-page kits (copy, capsule art from in-engine captures, trailer), and upload-ready archives; account creation/fees/uploads are owner-handoff items. |
| Price | **Free** (open source). Donation links (GitHub Sponsors) optional, owner-configured. |
| Engine features | Nanite ON for terrain/rocks/static meshes (keep the documented masked-foliage exceptions). **Software Lumen** GI+reflections (works on both target platforms; hardware RT off). Virtual Shadow Maps on Windows; on macOS use VSM if the UE 5.8 Metal path passes the P6 verification test, else cascaded maps — decided by that test, criteria in P6. TSR upscaling. World Partition streaming for the corridor (properly converted — external actors, HLOD, the existing 25,600 grid config). |
| Rendering targets | 1080p / 60 fps on RTX 3060 + M2 Pro at High; 1440p/60 on RTX 4070 at Epic. Game thread ≤ 8 ms, water solver ≤ 1.6 ms/tick (existing budget), no streaming hitch > 33 ms on the full-reach descent. |
| Audio | **Unreal-native MetaSounds** (decision already recorded in `docs/audio-middleware-evaluation.md` — keep). Sources: first-party procedural + CC0 (freesound et al.) + AI-generated per the existing audio policies, all manifest-tracked. No Wwise/FMOD, no paid libraries for 1.0. |
| Localization | English only for 1.0; all user-facing strings as `FText` from day one so localization is post-1.0 work, not a rewrite. |
| Licensing | Add at repo root: **`LICENSE` = MIT for all code** (physics, plugin, game); **`LICENSE-CONTENT.md` = CC-BY-4.0 for first-party content** (maps, textures, audio, manifests), with the per-asset manifests remaining authoritative for third-party items; `NOTICE.md` + generated `CREDITS.md` (every third-party asset, source, license — generated from the intake manifests). Local-only licensed content (Fab Standard) never enters the repo or the *source* release; it may ship inside packaged builds where its license permits (verify per item during P4; where not permitted, the committed procedural fallback ships). |
| Versioning / branching | Semver. Current `0.11.0` continues on `main`; release branch `release/1.0` cut at Phase 6 start; ship `1.0.0`. Tag every phase exit (`v0.12.0` = P1 exit, etc.). Changelog in `CHANGELOG.md` from now on. |
| Telemetry | **None.** Local logs and local crash dumps only. Privacy statement in README. |

## 3. Architecture decisions (final)

- **A-1. Water runtime = the in-repo C++ FV solver, embedded, on CPU.** Compile `physics/cpp` sources into the `RaftSimWater` module (static lib target added to the CMake + a Build.cs include path; no subprocess at runtime). The solver runs a **moving window** (~500 m × river width, 2–4 m cells) centered ahead of the raft, seeded from **precomputed steady-state fields** per flow band (generated offline per corridor section by the existing pipeline and cooked as textures/arrays). Outside the live window, sampling reads the precomputed fields. `RaftSimWaterRuntimeAdapter::SampleWaterAtWorldPosition` is rewritten to sample live-window state (bilinear over h, u, v, bed, plus surface normal); `StepWater` runs the real solver tick on the physics substep cadence. **Fixture calibrations and GeoClaw playback are compiled OUT of shipping builds** (`disable_fixture_calibrations` forced true + dead-stripped); playback remains a dev/validation tool only.
- **A-2. Water accuracy gate for 1.0 is behavior, not blanket parity.** Option B numerics work continues with a concrete 1.0 target: genuine solver parity on the **8 canonical fixture families most load-bearing for gameplay** (flat pool, uniform channel, sloping Manning channel, wet/dry shoreline, dam break, bed step, drop/ledge, constriction — 16 rows), achieved via second-order MUSCL reconstruction + proper well-balanced wet/dry front treatment in `solver_numerics.cpp`, plus mass-conservation and stability checks on every South Fork window. The remaining rapid-feature families (boulder garden, wave train, hydraulic hole, lateral, eddy line, shear, shelf) are validated **behaviorally** through the named-rapid review runs (feature present, correctly placed, correctly scaled at each flow band) rather than field-norm parity — that is what a player experiences. Full 40-row parity stays a post-1.0 engineering track. If a canonical family cannot reach parity after 3 focused attempts, log the numeric gap, mark the family `behavioral_validation_only`, and proceed — do not stall the release on a research problem.
- **A-3. Raft dynamics = first-party rigid 6-DoF + flexible corrections, in-engine.** Port the Python raft coupling (`raft_coupling2_5d.py`) and the D1–D4 flexible-raft quasi-static models to C++ inside `RaftSimPhysics`, driven by `URaftSimPhysicsBridgeSubsystem` at a fixed 120 Hz substep. Buoyancy/drag from multi-point tube sampling of the water fields; D1/D2 tube deformation modifies freeboard and roll stiffness; D3 overwash adds retained-water mass + roll moment (this is the flip mechanic); D4 provides rock contact/wrap/pin/release (this is the wrap mechanic). The UE port's outputs become the **measured results D6 has been waiting for** — run the D6 comparison harness UE-vs-Python as the acceptance test (tolerance bands already defined in `flexible_raft_d6.py`). Project Chrono stays a local-only optional cross-check, **not** a blocker; Jolt is cut. Chaos handles only non-authoritative debris/secondary motion.
- **A-4. Crew = animated skeletal actors with existing math as the brain.** Crew characters: first-party stylized-realistic meshes rigged to the UE5 Mannequin skeleton (committed, CC-BY), animated by Control Rig procedural paddling (stroke cadence from command state) + physics-driven secondary motion. MetaHumans are NOT used (license prevents committing to an open repo; a local-only path would make crew non-reproducible for contributors). The existing crew weight-shift/safety/rescue/scoring math drives seat-load inputs to D2 and the swimmer/rescue loop.
- **A-5. Swim/rescue loop.** On flip or ejection: crew become swimmer agents (drift model already in `RaftSimCrewStateContracts.cpp`), player throws a rope (aim + timing) or maneuvers the raft; re-entry at the tube. Player-overboard = swim to raft (simple first-person swim) or respawn at the last eddy checkpoint. Checkpoints = the eddy above each named rapid. |
- **A-6. Rapid encounters are data-driven from the existing catalog.** Each named-rapid marker becomes an encounter volume (scout point, line hints in Training/assist mode, scoring triggers, checkpoint eddy, hazard volumes at cataloged holes/waves). The 453 review-run definitions become the automated regression harness: headless runs that drive a scripted raft down each rapid at each flow and assert outcome envelopes (clean line survives, hole line flips, etc.).

## 4. Phases

Execute in order. Each phase lists its tasks and a hard exit gate. Commit and push after each task (both remotes, per standing rules). Tag the repo at each phase exit. Before P1: commit the in-flight B2 preflight work currently sitting untracked in the working tree (finish that task cleanly), and commit `TODO.md`/plan-doc edits.

### Phase 1 — Playable skeleton (boot → menu → floating raft)
1. Create `L_RaftSimBoot` (menu level: scenic South Fork preview camera + sky) — fixes the broken `GameDefaultMap`.
2. UMG front-end: MainMenu, ModeSelect, SectionSelect (river/section/flow), Settings (video/audio/input/accessibility tabs), Credits — implementing the screen-kind enums that already exist in `RaftSimVerticalSliceFrontend.h`. C++ widget base classes + minimal styled Blueprints (committed as text-diffable where possible; keep BP logic thin over C++).
3. Enhanced Input: author `UInputAction`/`UInputMappingContext` assets for the 23 contracted actions in `RaftSimInputActions.h`; bind in `ARaftSimGuidePawn::SetupPlayerInputComponent`; KBM + gamepad. Rebinding UI in Settings.
4. Save/settings: wire `URaftSimVerticalSliceSaveGame` to `SaveGameToSlot`/load on boot; settings apply/persist (resolution, quality, audio volumes, bindings, comfort options).
5. Test tank map: flat-pool solver window + raft rigid body floating via the new multi-point buoyancy (first slice of A-3), paddle-force strokes move it. No rapids yet.
6. CI: GitHub Actions workflow running the physics suite + CMake solver build/tests on push (Unreal builds stay local scripted: add `Scripts/package_win.ps1` / `package_mac.sh` wrapping RunUAT).
**Exit gate:** packaged Windows build boots to menu, starts Test Tank, player paddles a floating raft with visible water surface, settings persist, quits cleanly. Physics suite green.

### Phase 2 — Water and raft core (the simulation becomes a game)
1. Embed the solver in `RaftSimWater` (A-1): static-lib build, moving-window runtime, live `SampleWaterAtWorldPosition`, precomputed-field fallback, deterministic replay hashes preserved in dev builds.
2. Water rendering v1: heightfield surface mesh driven by live/precomputed fields feeding the existing `M_RaftSim_SolverSurfaceWaterCandidate` material line (elevation, velocity → flow-map, Froude → foam mask); single-layer-water shading; Niagara foam/spray/mist emitters keyed to the telemetry cue outputs that `RaftSimAudio`'s math already computes.
3. Raft dynamics port (A-3) complete: 6-DoF + D1–D4 in C++, 120 Hz, driven by the bridge subsystem from the game loop (subsystem finally gets ticked by the GameMode).
4. Flip/swim/recover loop (A-5) end-to-end with placeholder capsule crew.
5. D6 closure: run the comparison harness with UE-measured results; commit the report; fixture failures are physics bugs to fix now, not later.
6. Solver numerics sprint (A-2): MUSCL + wet/dry front work; re-run truth baseline; record new honest parity counts.
**Exit gate:** in the Chili Bar pilot window, the raft runs moving water with believable current/eddy response; deliberately dropping into the test hole flips the raft via D3 overwash; crew capsules swim and can be recovered; D6 comparison committed and passing within tolerance bands; solver parity ≥ 12/16 canonical rows (log any `behavioral_validation_only` exceptions per A-2).

### Phase 3 — First rapid vertical slice (Troublemaker)
1. Resolve South Fork A1 with the following **decided** anchors: downstream anchor = the official California State Parks *Salmon Falls Lower Water Raft Take-out* geometry (official access geometry is ground truth; the conflicting NHD-derived mileage candidates are rejected); mainstem route = re-selected NHD flowline chain validated against the official access points and aerial imagery; published mile figures (20.5 vs 21.0) become metadata aliases with a recorded divergence note, not anchors. Regenerate full-reach windows and stationing on that basis. Items previously gated on "local guide review" are marked `pending_human_review` (batched to the P7 owner review) and do **not** block binding.
2. Bind the first two rapids (Meat Grinder, Troublemaker) to exact geometry; author their reach-local bed/boulder geometry from DEM + NAIP + cataloged feature descriptions.
3. Build the Troublemaker encounter (A-6): scout eddy, hazard volumes at the right-side hole, line scoring, checkpoint, three flow bands.
4. Crew v1 (A-4): rigged paddler characters, Control Rig paddling, command radial menu + responses, High Side timed event, seat-load → D2 coupling.
5. Audio pass 1: MetaSounds water bed (level-crossfaded by the telemetry cues), paddle/hull/contact one-shots, command VO barks (TTS per policy), menu/UI sounds.
6. HUD v1: speed/heading ribbon, command state, crew status, scoring toasts, subtitle system.
7. Run the review-run harness for these two rapids (the first of the 453 definitions unblocked); commit outcome reports.
**Exit gate:** a stranger can launch the build, pick Training Eddy or Troublemaker, run it with crew and sound, flip in the hole at high flow, swim/recover, get scored, and their progress saves. This is the "it is now a game" gate.

### Phase 4 — Full South Fork (content at scale)
1. Convert the full-reach corridor to proper World Partition (external actors, HLOD build, streaming verified over a continuous full descent).
2. Extend rapid binding/encounters to all 20 cataloged rapids across the 33 km reach, using the review-run harness per rapid per flow as the acceptance test (behavioral validation per A-2).
3. Environment art completion, external-first per the existing intake policy: execute the B2 asset selections already committed for South Fork (CC0 committed; Fab hero items local-only with committed procedural fallbacks — and verify per-item packaged-build redistribution rights, else the fallback ships). Canopy strategy per the recorded review: **the hybrid pilot is hereby authorized** — analog species for distant mass (honestly labeled `visual_analog` in manifests), project-owned assets only where they already pass gates; the ≤6-cycle stop-loss rules in `docs/futaleufu-canopy-strategy-review.md` apply to any new in-repo authoring.
4. Water rendering v2: bank wetness, shallows tint by depth field, rapid-specific spray/mist densities, wet raft/paddle materials.
5. Section structure for career mode: Chili Bar Gorge / Coloma Valley / The Gorge / Salmon Falls approach — each a Guided Descent chapter with license-tier thresholds.
6. Full-reach performance pass against the §2 budgets (Nanite/HLOD/streaming tuning; the 1.6 ms solver budget already passes with margin).
**Exit gate:** complete Chili Bar → Salmon Falls descent, no loading breaks, all 20 rapids reviewed at 3 flows via harness reports, frame/streaming budgets met on the two target platforms, screenshots of five different rapids read as photoreal per the automated artifact checks (human confirmation batched to P7).

### Phase 5 — Game systems and polish
1. Guided Descent career: progression, license tiers, unlock flow, per-section medals, stats.
2. Training Eddy tutorial: guided drills with objective tracking (strokes, ferry, eddy catch, commands, flip recovery, rope throw).
3. Accessibility: full rebinding (done P1), subtitles + sizes, colorblind-safe HUD palette, camera-shake/vignette sliders, hold/toggle options, UI scale.
4. Photo mode (free camera, DoF, time-of-day slider in Free Run) — it markets the environment work.
5. Audio pass 2: full mix, distance/occlusion, canyon reverb zones, dynamic crew chatter density, menu music (first-party or CC0, manifest-tracked).
6. Difficulty/assist options: line ghost (Training + optional), scout-mode slow pan, forgiving vs realistic swim timers.
7. Legal/branding tasks: LICENSE/LICENSE-CONTENT/NOTICE/CREDITS files (per §2), README overhaul (what it is, screenshots, how to play, how to build, contribution guide), name-collision search + `docs/branding-decision.md`, in-game credits screen, third-party license screen.
**Exit gate:** feature-complete 1.0; all §2 scope items implemented or formally cut in the changelog; zero known crash/blocker bugs; licensing files complete and consistent with every intake manifest.

### Phase 6 — Platforms, packaging, release engineering
1. Cut `release/1.0`. Windows + macOS packaged builds via the P1 scripts; determinism spot-check (same seed → same replay hashes) on both.
2. macOS verification pass: VSM-vs-cascade decision test (VSM ships on macOS only if the full-reach descent shows no Metal shadow artifacts and stays ≥ 55 fps at High/1440p on M2 Pro; else cascades), Metal foliage-masking checks (the known alpha-as-mask issues), Proton verification of the Windows build on Steam Deck/desktop Linux (playable = 40 fps Medium; report only, not a gate).
3. QA sweep: scripted full-descent soak runs (all flows, both platforms, overnight loops via the review-run harness in packaged builds), input-device matrix (KBM, XInput, DualSense), save-migration test, fresh-machine first-run test.
4. Release artifacts: GitHub Release draft (builds + checksums + changelog), itch.io kit, Steam kit (store copy, capsule/screenshot/trailer asset set — trailer cut from in-engine captures of five rapids + a flip sequence), press kit page in `docs/presskit/`.
5. Version/lock: `1.0.0`, cook manifests, LFS assets verified present, final physics suite + full gate report regeneration.
**Exit gate:** both platform builds pass the QA sweep from a fresh machine; release artifacts staged; repo tagged `v1.0.0-rc1`.

### Phase 7 — Release candidate review and launch
1. Assemble the **owner review packet**: every `pending_human_review` item (guide-eye rapid realism judgments, photoreal "lifelike" confirmations, hazard-readability, the branding pick, store metadata) presented as a single checklist with builds, captures, and per-item accept/redo buttons (a simple markdown checklist + capture gallery).
2. Fix what the owner rejects; re-tag RCs as needed.
3. On owner sign-off: publish the GitHub Release; hand the owner the itch/Steam upload steps (accounts and fees are theirs); announce post (draft provided).
4. Open the post-1.0 roadmap: 1.1 = VR mode; 1.2 = Futaleufú; then Pacuare, Chilko, Colorado (windowed), voice commands, multiplayer evaluation — reactivating the five-river plan's remaining workstreams in that order.
**Exit gate:** v1.0.0 tag public with downloadable, playable builds.

## 5. Explicit cut list for 1.0 (do not implement, do not partially implement)

VR (1.1) · multiplayer · local-AI voice recognition · all rivers except South Fork · Zambezi anything · Chrono runtime integration · Jolt · native Linux · consoles/handheld · localization beyond FText hygiene · paid asset libraries · Wwise/FMOD · online telemetry · level editor for players (the RaftSim editor tools remain dev-only).

## 6. Standing engineering rules

1. Commit + push to both remotes after every task; phase tags; changelog entries per task.
2. `cd physics && uv run pytest -q` green before every push (current baseline 677 passed / 3 skipped — never lower without a logged reason); UE editor target must compile before every push touching `unreal/`.
3. Hash-locked manifests regenerate through generators only. The honesty conventions are non-negotiable: playback ≠ solver parity, analogs are labeled `visual_analog`, diagnostic captures are never presented as photoreal.
4. LFS: owner's no-prune decision stands. New heavy generated binaries: commit only meaningful revisions (no churn); packaged builds go to GitHub Releases, never into the repo.
5. New user-facing strings are `FText`. New gameplay values live in data assets/config, not hardcoded.
6. Keep BP logic thin; gameplay logic in C++ so it stays diffable and testable.

## 7. Test/verification strategy

- **Physics**: existing suite + D6 UE-vs-Python comparison + solver truth baseline re-runs after every numerics change.
- **Gameplay**: the 453 review-run definitions become packaged-build automation — headless scripted descents asserting outcome envelopes per rapid/flow; run nightly and at every phase exit.
- **Rendering/perf**: automated capture + frame-time harness on 5 fixed descent segments per platform per quality tier; budgets from §2.
- **Manual**: each phase exit includes one full human-playable descent by the agent driving the build interactively (screenshots + notes committed to `docs/playtest-notes/`).

## 8. Risks and predecided responses

| Risk | Response (decided now) |
|---|---|
| Solver numerics can't reach parity on a canonical family | After 3 attempts: `behavioral_validation_only` label, behavioral gate via review runs, post-1.0 track. Never re-enable playback in shipping. |
| Full-reach corridor too heavy for streaming budgets | Reduce foliage density tiers and HLOD distances first; if still failing, split the descent into 4 section maps with eddy-pause transitions (career already sections there). |
| D3/D4 flexible corrections feel bad (twitchy/unfair) at 120 Hz | Tune clamp constants via the D-fixtures within recorded bounds; if still bad, ship D1/D2+D3 (sag + overwash flip) and defer D4 wrap/pin to 1.0.x with the rocks acting as rigid colliders meanwhile. |
| Fab hero-asset licenses disallow packaged redistribution | Ship the committed procedural fallback for that slot; note in CREDITS. |
| macOS falls below perf floor | Lower the macOS default tier to Medium and state it; never delay Windows for macOS parity. |
| Owner review (P7) rejects a rapid's realism | Rework that rapid's window/geometry only; other rapids ship; a single rapid may ship flagged "under revision" in the changelog rather than slipping the release. |

## 9. Owner-handoff checklist (agent prepares; owner executes; these gate the launch date only)

- Create/verify itch.io and Steam partner accounts; pay Steam fee; upload staged kits.
- Confirm the branding pick from `docs/branding-decision.md`.
- Play the RC and complete the review packet (P7.1).
- Optional: GitHub Sponsors/donation links; announcement posts from the provided drafts.

## 10. Decision principles for anything this plan missed

1. Prefer cutting scope over cutting quality; prefer the smaller, finished thing.
2. Prefer the choice that keeps evidence honest, even when it looks worse.
3. Prefer deterministic and testable over impressive and fragile.
4. Prefer CC0/first-party content; when licensing is ambiguous, treat it as disallowed and use the fallback.
5. Prefer Windows-path certainty over multi-platform parity.
6. When a gate requires a human, convert it to a `pending_human_review` item in the P7 packet and continue; never fabricate a human judgment.
7. When two existing docs conflict, this plan wins for 1.0 scope; record the conflict in this file's execution log.
8. Log every nontrivial decision, dated, in an execution log section appended to this file — the same convention the previous plans used.
