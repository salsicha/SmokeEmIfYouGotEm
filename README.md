# RaftSim (SmokeEmIfYouGotEm)

An open-source, photorealistic whitewater rafting simulator built with Unreal Engine 5.8 and a first-party shallow-water physics stack. You are the river guide: read the rapid, set the angle, call the strokes, keep your crew in the boat.

**Status (August 2026): pre-release, in active development.** Six rivers are
runnable in-engine. Zambezi is explicitly one of those six and is selectable
as the **Zambezi: Boiling Pot to Mukuni Beach** reference Free Run. The 1.0
production campaign remains the **South Fork
American, Chili Bar to Salmon Falls**, with all 20 named rapids at three real
flow levels. The versioned `L_Zambezi` map adds a source-scale Boiling
Pot-to-Mukuni Beach reference run with all 25 mapped rapids; its missing
bathymetry and
rapid-specific hydraulics are explicitly procedural and remain blocked from
production-fidelity claims. Its current map, regeneration path, validation, and
open gates are documented in
[docs/zambezi-reference-map-and-scenario.md](docs/zambezi-reference-map-and-scenario.md).
The August 4 V15 release-head certification confirms again that the frontend
selector, source scenario, shipping cook, saved map, and live PIE launch all
resolve to `/Game/RaftSim/Maps/L_Zambezi`. Zambezi is runnable river 6, loads
with the vertical-slice game mode and live cooked-field water, and is not an
environment-preview-only map. The focused career and progression gates, all 27
Zambezi registry/source contracts, and all six runnable maps pass on the
current release head. Its gameplay river is now a
solver-owned, wet-cell-clipped transmitting core rather than the former opaque
gray static ribbon. Its V2 optical body now consumes live wet-cell vertex-alpha
coverage across a 7.5 m bank blend. The shared parent now applies that coverage
to scattering, absorption, and behind-water color as well as opacity, so a
zero-coverage bank vertex cannot retain a pale water volume over dry land. This
closes the material ownership defect without claiming that the broad shallow-
water band or final shoreline art is solved,
while restrained river-local reflection settings reduce clipped launch glare;
project-owned flow-normal and solver-masked foam textures still have no
hydraulic authority. The exact contract hashes, tests, runtime counts, and
still-open production gates are recorded in the
[release-head runnable review](docs/environment-captures/photoreal_river_previews/landscape_candidates/zambezi_runnable_release_head_v15_review.json),
with matched visual evidence in the
[V2 transmitting-water review](docs/environment-captures/photoreal_river_previews/landscape_candidates/zambezi_live_transmitting_water_v2_review.json).
The shared optical-bank change and its six-river no-regression evidence are
recorded in the
[full optical bank-coverage review](docs/environment-captures/photoreal_river_previews/landscape_candidates/cold_water_full_optical_bank_coverage_v1_review.json).
The current Batoka V18 presentation pass keeps V17's source-missing upper-scarp
infill on the four non-colliding render tiles, but reduces clipped launch-water
glare and the chalky sun-facing scarp response. It distributes 7,200 shorter,
shadowless launch-cover instances across dry benches and moderate slopes. The
hidden Copernicus Landscape remains collision and height-query authority;
water geometry, wet/dry state, solver samples, buoyancy, and raft forces are
unchanged. In the matched frame, water pixels above 0.90 luminance fall from
1.685% to 0.065%, and the equivalent left-water fraction falls from 3.989% to
0.148%. The exact map, optics, material, cover, runtime, and open-gate evidence
is in the [V18 launch optical-naturalism review](docs/environment-captures/photoreal_river_previews/landscape_candidates/zambezi_launch_optical_naturalism_v18_review.json).
That review retains the bounded visual improvement and still fails photoreal
promotion because the 30 m source canyon remains rounded and smooth, the
synthetic vegetation repeats, and the listed external data and human acceptance
gates remain open.
The August 4 V19 ecology pass now fail-closes on six bank/elevation strata,
retaining 6,512 dry-bank ground-cover instances and 772 woody instances. A
source-grounded launch-camera mosaic breaks up the former continuous skyline
row and adds mid-slope clusters without entering the wet or navigable corridor.
The matched frame is a technical improvement only: the coarse left wall remains
largely bare, so photoreal promotion is still false. Counts, rejected candidates,
hashes, and exact before/after frames are in the
[V19 stratified-ecology review](docs/environment-captures/photoreal_river_previews/landscape_candidates/zambezi_launch_stratified_ecology_v19_review.json).
The current near-field terrain V2 pass replaces the former regular 5 m bank
grid with a deterministic irregular 2.5 m grid, rejects inverted or sub-0.25 m²
curved-offset cells, and adds bounded domain-warped basalt erosion, fracture,
talus, and joint relief. The regenerated runnable map retains 169,222 adaptive
vertices and 246,490 triangles; its matched guide-eye frame removes the former
long black overlap seams and keeps a continuous dry shoreline. This is bounded
technical progress, not photoreal acceptance: the 30 m canyon silhouette,
sparse/repeated cover, flat-looking water, final geology/ecology, and all
external acceptance gates remain open in the current release-head review.
The live rapid presentation now uses six of its eight preallocated Niagara
site pairs around the camera instead of the former two-site ceiling. Zambezi's
PIE gate requires all six aerosol and roller pairs to be active from its eight
solver-owned launch-window breaking sites. The retained result improves bounded
rapid-cluster coverage without changing the map, solver, collision, or raft
forces; it remains visibly short of a coherent overturning whitewater volume.
Evidence and the unchanged external gates are in the
[solver-driven rapid VFX review](docs/environment-captures/photoreal_river_previews/landscape_candidates/zambezi_solver_driven_rapid_vfx_v1_review.json).
The versioned selection and progression manifests explicitly mark Zambezi
`runnable: true` and `availability: free_run`, link the current release-head
review, and enumerate it in the six-river Free Run contract. Catalog tests fail
if its scenario, availability, evidence link, or map path is removed.
The South Fork production campaign still resolves to the 49.1 km
`L_SouthForkAmerican_FullReach` gameplay map. Its August 2 organic foothill
terrain pass now shares dry-grass, oak-litter, granitic-soil, and weathered-
granite shading with the fixed Landscape review, while leaving DEM geometry,
collision, navigation, water, and raft physics unchanged. This is a retained
technical improvement, not photoreal acceptance; evidence and remaining gates
are in the [South Fork terrain review](docs/environment-captures/south_fork_full_reach/m9_south_fork_organic_foothill_terrain_v1_review.json).
The August 3 ground-cover pass retains the 220,759 project-owned grass tufts
and adds 442,938 non-colliding CC0 scanned grass forms under the source-density,
slope, bank-distance, and solver/VFX wet-mask contracts. This materially breaks
up the bare fixed-camera banks, but remains generic visual morphology rather
than species-reviewed ecology or photoreal approval. A matched local performance
A/B measures a 0.418 ms p95 candidate delta but leaves the pre-existing full-map
60 FPS, packaged-window, and VR gates open; exact visual/performance evidence and
open gates are in the [scanned ground-cover review](docs/environment-captures/south_fork_full_reach/m9_cc0_scanned_ground_cover_v216_review.json).
Pacuare's `L_UpperHuacas` is again a runnable map: a physical 600 m reach-local
Landscape, the committed Upper Huacas cooked solver field, explicit vertical
datum alignment, player raft/start, and the full vertical-slice game mode now
ship together. It is reference-runnable, not photoreal-approved; the evidence
and remaining gates are recorded in
[the Upper Huacas water/readability review](docs/environment-captures/photoreal_river_previews/landscape_candidates/pacuare_upper_huacas_solver_whitewater_v2_review.json).
Its August 3 gameplay-water pass replaces the uniform opaque live sheet with a
solver-owned, wet-cell-clipped transmitting core and a narrowly covered live
detail skin. The new project-owned flow-normal and solver-masked foam-lace
textures are visual-only and cannot alter hydraulics or raft forces. The
matched result is retained as a technical improvement, while terrain,
rainforest ecology, whitewater VFX, calibration, external review, and
photoreal promotion remain open in the
[Pacuare live-water review](docs/environment-captures/photoreal_river_previews/landscape_candidates/pacuare_live_transmitting_water_v1_review.json).
Colorado's `L_Hance` is likewise restored as a reference-runnable physical
reach: a 600×320 m Landscape preserves the complete 600×78 m interpreted Hance
solver bed, procedurally fills missing outer-canyon terrain, and launches the
live moderate-release cooked field at station 336 m with the player raft and
game mode. That retains 69 m of subcritical approach to the first accepted
interior solver transition near station 405 m; a separate solver-rapid camera
now records the downstream hydraulic view. It is not surveyed Hance geography
or photoreal-approved; its current evidence and open gates are recorded in
[the Hance nonperiodic-canyon and dryland-ecology V3 review](docs/environment-captures/photoreal_river_previews/landscape_candidates/colorado_hance_nonperiodic_canyon_dryland_ecology_v3_review.json).
Futaleufú's `L_Terminator` and Chilko's `L_LavaCanyon` now use a wet-cell-
clipped Single Layer Water core beneath their live solver detail surfaces.
The shared cold-water rollout removes the high-coverage pale overlay while
preserving raft-floor transmission, live rapid geometry, and solver authority.
Its lateral core reaches the complete sampled wet bank only through all-wet
cells, while an independent station mask clips the rectangular moving-window
ends. This is a retained technical candidate, not photoreal approval;
comparison evidence and remaining defects are recorded in
[the cold-water volume-core review](docs/environment-captures/photoreal_river_previews/landscape_candidates/cold_water_live_volume_core_v2_review.json).
The August 4 cold-water highlight pass gives both runnable maps the same
restrained dielectric/roughness/reflection rig and corrects Futaleufú's water
color after rejecting an initially desaturated bracket. In the matched
Terminator frame, coverage above 0.95 luminance falls 98.20%, p95 falls 1.26%,
and blue-minus-red separation rises 29.79%; the Lava Canyon frame remains the
no-regression control. This is a presentation-only technical improvement, not
photoreal acceptance: broad pale water, foam/VFX, shoreline, terrain, ecology,
characters, calibration, performance, and external review remain open in the
[cold-water highlight review](docs/environment-captures/photoreal_river_previews/landscape_candidates/cold_water_highlight_naturalism_v1_review.json).
The follow-on depth pass now uses cooked depth to separate transmitting
shallows, absorbing deep current, and genuinely aerated whitewater. It removes
the former assumption that ordinary fast current is broadly aerated, while
preserving solver foam and the transparent raft-interior override. Matched
Futaleufú evidence lowers the clear right-body mean 5.65% and raises water-body
contrast 19.11%; matched Chilko evidence lowers mean luminance 21.40%, the far
washed band 14.33%, and p95 4.52%. Both maps remain reference-runnable rather
than photoreal-approved; exact coefficients, hashes, remaining defects, and
external gates are in the
[cold-water depth review](docs/environment-captures/photoreal_river_previews/landscape_candidates/cold_water_depth_attenuation_v2_review.json).
A follow-up adaptive-shoreline experiment was rejected and removed before
release integration. Its 18 m, 1 m-resolution non-colliding bank strips passed
generation and mesh bounds, but matched Chilko views retained the broad pale
rectangular shallow-water band, slightly reduced bank-transition edge density,
and briefly introduced a continuous pale rail. The accepted runnable maps and
terrain materials remain byte-restored; the fail-closed evidence, hashes,
authority boundary, and next-step requirement for water-coverage or surveyed
bank geometry are recorded in the
[cold-water adaptive-shoreline rejection](docs/environment-captures/photoreal_river_previews/landscape_candidates/cold_water_adaptive_shoreline_v1_review.json).
The replacement pass changes the visible presentation boundary itself. A
default-off cold-water opt-in varies the existing bank alpha in global river
station space and retreats only the optical core's outermost wet vertices
inward, capped at 0.90 m and below one 1.50 m render cell. It never adds wet
topology or moves the sampled solver surface. In the fixed Chilko close-up the
contact shifts 3.84 pixels on average and gains 16.69% more detrended contour
variation without the rejected overlay's rail or gap. Futaleufú's matched
rapid-side frame passes as a no-regression control but does not support a
material bank-improvement claim. Both maps remain byte-identical and
reference-runnable, not photoreal-approved; exact implementation, hashes,
captures, limitations, and open external gates are in the
[cold-water presentation-bank review](docs/environment-captures/photoreal_river_previews/landscape_candidates/cold_water_presentation_bank_naturalism_v1_review.json).
The shared live-water renderer now subdivides every authored river's visual
surface from a 3 m analysis grid to 1.5 m presentation spacing. Solver-feature
analysis retains its original physical footprint, the config-less test tank
retains its original topology, and no cooked field, collision, buoyancy, D3,
or D4 authority changes. All six runnable maps pass the native PIE matrix;
matched Zambezi evidence shows a bounded increase in local surface breakup but
still fails photoreal promotion because the broad analytical swell and missing
connected overturning rapid body remain visible. Exact topology, runtime,
visual, hash, and external-gate evidence is in the
[refined live-surface review](docs/environment-captures/photoreal_river_previews/landscape_candidates/zambezi_refined_live_surface_v1_review.json).
The strongest three accepted jumps now also retain one solver-shaped,
crest-to-plunge membrane beneath the production Niagara spray. It uses the
existing masked foam lace and raft/crew exclusion rather than the rejected
three-shell translucent fallback, is capped at 1,512 non-colliding triangles,
and is asserted on all six runnable rivers. Matched Zambezi evidence shows more
crest breakup without dome/card artifacts, but the result remains a bounded
technical improvement rather than a photoreal overturning-water pass; evidence
and open gates are in the
[connected plunge review](docs/environment-captures/photoreal_river_previews/landscape_candidates/zambezi_connected_plunge_v1_review.json).
The shared live-water displacement now replaces its former dominant 11.5 cm
diagonal sinusoid with flow-aligned, phase-warped crest packets. The
presentation envelope falls from 24.8 cm to 16.8 cm; the matched Zambezi
runtime maximum falls from 23.43 cm to 10.46 cm while sampled surface relief,
collision, buoyancy, and D3/D4 authority remain unchanged. P2 passes and all
six runnable river maps pass P4. The retained frame removes the repeated
analytical band, but the low-resolution sampled rise and missing aerated hole,
recirculation, and collision-aware spray still fail photoreal promotion. See
the [nonperiodic live-wave review](docs/environment-captures/photoreal_river_previews/landscape_candidates/zambezi_nonperiodic_live_wave_v1_review.json).
The three strongest solver-accepted interior jumps now also shape the refined
render mesh into a bounded plan-view plunge pocket, broken shoulders, and an
aerated downstream return. Per-site displacement is capped at -0.28/+0.16 m
and combined displacement at -0.30/+0.18 m; cooked water, wetness, collision,
buoyancy, D3/D4, and saved maps remain unchanged. The editor build, P2 water
contract, and all six P4 runnable-map gates pass. Close side review finds no
dome, tent, rail, card, or shoreline artifact, but the result is retained only
as technical progress because volumetric aeration, recirculation, spray,
measured seasonal hydraulics, and named art acceptance remain open. See the
[plunge-pocket review](docs/environment-captures/photoreal_river_previews/landscape_candidates/zambezi_plunge_pocket_v1_review.json).
The shared solver-foam surface now replaces its static unlit rectangular lace
with two independently advected, incommensurate samples of each river's own
first-party mask. The same solver alpha and raft/crew exclusion still own foam
placement, while Default Lit response and a small emissive floor let the lace
enter canyon shadow instead of reading as a white decal. P2 and all six P4
runnable-map gates pass. Matched Futaleufú evidence halves very-white coverage
in the rapid-side diagnostic, but the remaining parallel strokes, thin surface,
analytical rapid shape, and incomplete spray/mist still reject photoreal
promotion. See the
[shared flow-advected foam review](docs/environment-captures/photoreal_river_previews/landscape_candidates/shared_flow_advected_foam_v1_review.json).
The strongest three solver-accepted breaking sites now replace that remaining
zero-thickness rapid membrane with one connected two-skin aerated crest surface
per site. Both skins follow the same solver profile, separate only along its
local normal, stay within 40 cm full thickness, and join at the fully masked
plunge boundary so no visible crown cap can read as a slab. P2 and all six P4
runnable-map gates pass at exact 570-vertex/1,044-triangle topology per site.
Matched Zambezi review rejected an intermediate visible connector with vertical
slivers and retains the artifact-free masked connector, but the subtle result
still lacks convincing aerated volume, hole/pile recirculation, spray, and mist;
photoreal promotion remains open in the
[solver-anchored aerated crest review](docs/environment-captures/photoreal_river_previews/landscape_candidates/solver_anchored_aerated_crest_thickness_v1_review.json).
The rapid particle stack now completes a bounded third scale at those same
solver-accepted sites: eight preallocated `RapidCrestSpray` components share
the existing six-site camera budget and 120 m cull with roller fragments and
downstream aerosol. A dedicated project-owned Niagara system supplies short-
lived, velocity-aligned ballistic droplets; crest-only isolation makes them
readable without forming a fountain or opaque layer in the full Zambezi view.
M4 passes 4/4, the six-system renderer-backed Niagara gate passes 1/1, and P2
plus all six P4 runnable-map gates pass 7/7, including `L_Zambezi`. This is
presentation-only technical progress—not photoreal promotion—because the
droplets remain sprite-based and coherent aerated volume, collision-aware
breakup, measured hydraulics, final art, and external approvals remain open in
the [three-scale breaking-spray review](docs/environment-captures/photoreal_river_previews/landscape_candidates/solver_anchored_three_scale_breaking_spray_v1_review.json).
Lava Canyon's August 3 V3 optical/shoreline pass fixes a legacy map-migration
path that was silently restoring the older reflective water defaults after
regeneration. The runtime now keeps the river-local, wet-cell-clipped volume
core, masks the redundant detail skin away from dry solver-grid vertices, and
uses restrained Chilko lighting and reflection values. The full 600 m bank
layer retains 7,200 gravel and 8,400 short-cover instances, but gives Chilko a
muted material instance, a smaller bounded scale distribution, and fewer large
rock silhouettes. In the matched side-on water band, mean luminance falls
6.18%, pixels above 0.90 fall 59.21%, and pixels above 0.95 fall 98.93%; the
matched bank neon-green fraction falls 64.77%. The editor build and all six
runnable-map gates pass with MapCheck at zero errors and warnings. This remains
a technical candidate—not a photoreal pass—because the far-bank shallow band,
repeated foam strokes, DEM-scale bank form, ecology/geology specificity,
rapid-scale spray and mist, hydraulic calibration, and all six external gates
remain open in the
[Chilko optical/shoreline V3 review](docs/environment-captures/photoreal_river_previews/landscape_candidates/chilko_optical_shoreline_naturalism_v3_review.json).
See [docs/game-completion-plan.md](docs/game-completion-plan.md) for the active
milestone plan and [CHANGELOG.md](CHANGELOG.md) for progress.

| Runnable river | Player-facing run | Current tier |
|---|---|---|
| South Fork American | Chili Bar to Salmon Falls plus Troublemaker | production campaign |
| Colorado, Grand Canyon | Hance | runnable reference signature-rapid Free Run |
| Pacuare | Upper Huacas | runnable reference signature-rapid Free Run |
| Futaleufú | Terminator | runnable reference signature-rapid Free Run |
| Chilko | Lava Canyon | runnable reference signature-rapid Free Run |
| Zambezi, Batoka Gorge | `L_Zambezi`: Boiling Pot to Mukuni Beach, Rapids 1–25 | runnable reference Free Run |

To run Zambezi from the game, choose **Free Run**, then select **Zambezi:
Boiling Pot to Mukuni Beach**. Free Run scenarios are available without a
career-license unlock. In the Unreal Editor, the same runnable map can be
opened directly at `/Game/RaftSim/Maps/L_Zambezi`; the older
`L_ZambeziBatokaGorge_PhysicalCorridorCandidate` preview is not the gameplay
map.

## What's in this repository

| Area | Contents |
|---|---|
| `physics/` | The `raftsim` Python package: deterministic simulation kernel, 2.5D scenario system, GeoClaw/PyClaw reference solvers, dual-solver validation harness, flexible-raft reference physics, and real-world river corridor pipeline. Plus the C++ finite-volume shallow-water runtime solver (`physics/cpp`). |
| `unreal/` | The UE 5.8 project: RaftSim plugin (runtime modules + a large procedural environment-authoring editor toolkit), project content, and packaging scripts. |
| `docs/` | Design docs, production plans, source/rights policies, and hash-locked review evidence. |

## Building

**Physics package** (Python ≥ 3.11, [uv](https://docs.astral.sh/uv/)):
```bash
cd physics
uv run pytest -q          # run the test suite
```

**C++ water solver** (CMake + a C++17 compiler):
```bash
cd physics/cpp && cmake -B build && cmake --build build
```

**Unreal project**: open `unreal/SmokeEmIfYouGotEm.uproject` with Unreal Engine 5.8 (the editor build compiles the RaftSim plugin). Packaging scripts live in `unreal/Scripts/`.

## Data honesty

This project keeps an explicit, hash-locked audit trail. Reference-solution playback and visual conditioning are always labeled as such and are compiled out of shipping builds; diagnostic captures are never presented as gameplay screenshots. Simulated river behavior is approximate and must never be used for real-world trip planning or safety decisions.

## Licenses

- Code: [MIT](LICENSE)
- First-party content: [CC BY 4.0](LICENSE-CONTENT.md)
- Third-party assets/data: per-item intake manifests; summarized in [CREDITS.md](CREDITS.md). See also [NOTICE.md](NOTICE.md).

Contributions are welcome as issues and pull requests. This is primarily a solo project; expect review latency.
