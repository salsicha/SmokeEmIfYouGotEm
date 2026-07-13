# Named Rapid Realism And Validation Plan

## Goal

Make each authored river behave like its real run, not like a generic sequence of whitewater set pieces. Every notable rapid must be traceable from a published name and station/order through exact terrain and bed geometry, a validated C++ water window, flow-dependent hydraulic behavior, guide-reviewed lines, raft and crew outcomes, visual/audio rendering, and repeatable multi-platform simulator evidence.

The five runs are:

- South Fork American, Chili Bar to Folsom Reservoir.
- Colorado River through Grand Canyon, Lees Ferry to Pearce Ferry.
- Pacuare River, Tres Equis to Siquirres.
- Zambezi River in Batoka Gorge, Boiling Pot to Mukuni Beach below Rapid 25.
- Futaleufu River, Rio Azul Swinging Bridge to The Pasarela.

## Implemented Baseline

The hand-reviewed source catalog is `physics/data/real_world/named_rapid_source_catalog.json`. It currently records 80 markers:

| River | Markers | Current station basis |
| --- | ---: | --- |
| South Fork American | 20 | Published river miles from Chili Bar |
| Colorado Grand Canyon | 15 major rapids | Published river miles; exact values still require NPS/USGS/guide cross-check |
| Pacuare | 15 | Published downstream map order; editor stations are provisional interpolation |
| Zambezi | 25 | Published rapid number/order; editor stations are provisional interpolation |
| Futaleufu | 5 | Published downstream order; editor stations are provisional interpolation |

`unreal/Content/RaftSim/River/named_rapid_editor_markers.json` converts the catalog into editor-ready station pins with aliases, difficulty labels, feature tags, flow hypotheses, expected outcomes, sources, confidence boundaries, and explicit exact-geometry and guide-review blockers.

`unreal/Content/RaftSim/River/named_rapid_editor_geometry.geojson` currently provides 45 candidate map points by interpolating the Pacuare preview scaffold, low-precision Zambezi route trace, and review-gated Futaleufu route trace. Every point remains non-authoritative. South Fork binding is deliberately disabled: the current NHD candidate declares a 26.2 km Chili Bar-to-Coloma line while the published mile log puts Coloma Bridge at about 9.0 km, and the existing Coloma access seed is at 5.2 km. `physics/data/real_world/south_fork_american_chili_bar/review/named_rapid_station_alignment_review.json` records the conflict and blocks plausible-looking but incorrect Meat Grinder/Troublemaker points. Colorado's current 4.7 km Lees Ferry pilot does not reach the first indexed major rapid.

`unreal/Content/RaftSim/Automation/named_rapid_simulator_review_runs.json` defines 423 deterministic review runs across low, reference, and high flow. High and critical features receive both a clean reference line and a bounded feature-contact line. Optional portages receive a portage control. Zambezi Rapid 9, Commercial Suicide, receives only mandatory commercial-portage controls and cannot bind a normal raft line.

The reviewed Unreal `DA_RapidRiverEditorShell` DataAsset now points to both manifests, and the Rapid/River Editor tab displays paths for the named marker set and simulator queue. The UE 5.8 editor target compiles and the reviewed DataAsset generation command saves all five tooling DataAssets successfully.

This is authoring and test-definition progress, not proof that any named rapid has been reproduced. Every generated run remains blocked until its exact geometry, validated C++ window, and guide-reviewed line are attached.

## Source And Rights Rules

- Store factual rapid names, published mile/order, classifications, feature tags, and source URLs in the repository.
- Keep third-party guide prose, maps, photos, footage, captions, comments, and audio link-only unless item-level reuse permission is recorded.
- Preserve disagreement between sources as aliases or review notes. Do not silently choose one name, class, line, or station.
- Exact hazards, access, sensitive locations, and rescue routes require local publication review before public screenshots or packaged maps expose them.
- Social posts can answer visual and behavior questions, but are never geometry or rights authority by themselves.

Current source leads include the [South Fork mile guide](https://www.american-rivers.com/sf-rio-descr.htm), [South Fork feature map](https://www.americanwhitewater.com/american-river-rafting/south-fork/map), [NPS Grand Canyon rapids interview](https://www.nps.gov/podcasts/behind-the-scenery.htm?hiderightrail=true&maxrows=10&reinit=false&season=0&sortby=date-desc&startrow=21), [USGS Grand Canyon hydraulic maps](https://pubs.usgs.gov/imap/1897j/), [Pacuare route map](https://rioslodge.com/wp-content/uploads/Pacuare-River-Map.pdf), [Zambezi Batoka Gorge guide](https://www.whitewaterguidebook.com/africa/zambezi-river-batoka-gorge/), and [Futaleufu Terminator guide](https://riversofchile.com/rio-futaleufu-terminator-section/).

## Rapid Production Pipeline

### 1. Fix Stationing And Evidence

For every marker, attach exact WGS84 point/span geometry, route station, source date, flow context, rights status, and confidence. South Fork published miles can seed review, but still need alignment to the production centerline. Colorado miles need NPS/USGS/river-guide cross-check. Pacuare, Zambezi, and Futaleufu order-interpolated markers must be replaced by GPS, aerial interpretation, and guide confirmation.

Exit gate: no production marker uses `provisional_downstream_order_interpolation`.

### 2. Author Real Geometry

Clip a reach-local terrain and channel window around each rapid. Combine DEM/lidar or photogrammetry, hydrography, aerial imagery, exposed-rock interpretation, surveyed cross sections where available, and guide annotations. Author bed steps, shelves, boulder/island geometry, banks, eddies, scout/portage paths, and line polygons. Preserve stitched whole-window exports so reach seams cannot hide physics errors.

Exit gate: geometry has CRS/vertical datum, source hashes, accuracy limits, collision review, upstream/downstream boundary sections, and a stitched validation export.

### 3. Validate The C++ Water Window

Run the analytic fixture guardrails first, then the named window at low/reference/high flow. Record boundary semantics, wet/dry behavior, mass and momentum conservation, Froude and hydraulic-jump structure, grid convergence, seam checks, and GeoClaw comparisons where the reference model is applicable. Feature forcing stays low or disabled for parity and cannot compensate for conservation, boundary, or geometry failures.

Exit gate: the unforced or minimally forced window passes the relevant analytic, GeoClaw, conservation, geometry, and stitched-window gates.

### 4. Tune Flow-Dependent Features

After the base solution passes, use bounded manifest-recorded controls for holes, boils, laterals, eddy lines, wave trains, shelves, boulder push/damping, pins/releases, and flips. Tune each feature over a flow curve rather than a single gain. A hole may be weak at low water, sticky over a middle range, then wash out at high water. Exposed rocks and pin slots may disappear as discharge rises while laterals, boils, wave trains, and recovery distances strengthen.

Exit gate: each gameplay-affecting control has bounds, source/guide rationale, flow curve, C++/GeoClaw comparison impact, conservation evidence, and an off switch for diagnosis.

### 5. Validate Boat, Crew, Swimmer, And Rescue Outcomes

Bind the simulator definitions to exact entry poses and guide-reviewed lines. Colorado uses manual oar-rig controls and no passenger paddle voice commands. The other four runs use guided paddle crews with voice, keyboard, and controller command paths. All runs enable crew center-of-mass shifts, high-side timing, flips, ejections, random swimming skill including non-swimmers, throw/boat/contact rescue, and flow-dependent recovery distance.

Clean lines must reproduce guide timing and trajectory envelopes. Bounded consequence lines deliberately test hole contact, lateral hits, wraps/pins, missed high-sides, flips, swimmers, and releases without redefining unsafe real-world lines as normal gameplay.

Exit gate: trajectory, angle, roll/pitch, center-of-mass shift, retention, pin/release, flip, swimmer count, and rescue time are within reviewed envelopes.

### 6. Match Visual And Audio Evidence

At the same recorded flow and camera position, compare tongue shape, standing-wave spacing, hole pile/boil, foam transport, spray scale, wet-bank extent, exposed rocks, turbidity/color, vegetation, canyon scale, light, and sound. Geometry and solver state remain authoritative; visual-only spray, foam, mist, and audio may add detail but cannot change boat forces.

Exit gate: art, guide, geospatial, rights, hazard-readability, and human lifelike review accept paired river-eye and guide-seat captures.

### 7. Automate Review Runs

Each accepted rapid keeps three flow bands and at least one clean reference line. Critical features also keep bounded consequence runs. Every execution saves:

- Input/source/geometry/solver/forcing manifest hashes.
- Platform and scalability profile.
- Time-series raft, crew, swimmer, and rescue telemetry.
- Depth, velocity, Froude, wet/dry, feature, trajectory, contact, center-of-mass, and conservation overlays.
- Guide-seat video, river-eye video, and fixed comparison frames.
- Pass/fail results plus reviewer identity and evidence links.

### 8. Hold Multi-Platform Physics Constant

The authored geometry, solver state, collision geometry, and outcome envelope stay identical across desktop-high, desktop-scalable, console-quality, console-performance, and handheld-low profiles. Scalability may change foliage density, shadows, reflections, spray, foam detail, audio voices, and Nanite fallback, but not the line, water forces, collision hazards, crew timing, or rescue outcome.

Exit gate: performance profiles meet frame-time/memory budgets and preserve physics hashes plus hazard/readability checks.

## River Priorities

### South Fork American

Start with Meat Grinder, Troublemaker, Satan's Cesspool, Bouncing Rock, and Hospital Bar. They collectively exercise boulder gardens, narrow placement, holes, diagonals, eddies, wraps, rock push, flips, and swimmer recovery, and have the strongest published mile/feature descriptions in the current corpus.

### Colorado Grand Canyon

Start with House Rock, Hance, Horn Creek, Hermit, Crystal, Bedrock, and Lava Falls. These cover big-water holes and waves, low-flow difficulty, multi-move rowing lines, debris-fan geometry, channel choice, loaded oar-rig momentum, long recovery, and flips. USGS hydraulic-map extraction should be evaluated before hand-authoring geometry at the mapped major rapids.

### Pacuare

Start with Upper/Lower Huacas, Double Drop, Cimarrones, Wall of Sorrow, and Dos Montanas. First replace provisional order stations with exact route geometry and rainfall/stage context; then validate tropical gorge constrictions, drops, holes, wall push, continuous water, and restricted rescue visibility.

### Zambezi

Start with Against the Wall, Gulliver's Travels, Midnight Diner, Commercial Suicide portage, Three Ugly Sisters, Washing Machine, Terminators, Double Trouble, and Oblivion. These require big-volume boils, diagonal waves, alternate lines, mandatory portage logic, center holes, flow-dependent wave trains, and realistic flip/surf behavior. The Namaqualand cliff import remains a CC0 scale/structure comparison only and is not Batoka basalt authority.

### Futaleufu

Start with Terminator, Khyber Pass, and Himalayas after exact stationing. Terminator needs a scoutable long multi-line window with a sneak and optional portage. Khyber Pass needs hole-filled continuous big water. Himalayas needs large standing-wave timing and flip/high-side review without turning the wave train into arbitrary forcing.

## Immediate Next Work

1. Use the implemented Unreal JSON browser for all 80 markers, 45 candidate map points, and 423 run definitions, with river, flow, priority, station, exact/candidate geometry, guide, execution, and text filters plus provisional-station badges.
2. Repair and anchor the South Fork NHD candidate before enabling any published-mile projection; then replace the first provisional markers with exact geometry at Meat Grinder and Troublemaker, Zambezi Against the Wall/Commercial Suicide/Oblivion, and Futaleufu Terminator.
3. Bind Meat Grinder to the existing accepted South Fork C++ field as the first executable named-rapid run, or explicitly record why a new higher-resolution window is required.
4. Add run execution and telemetry capture from the Rapid/River Editor, then capture the first clean and consequence videos.
5. Continue production terrain, water, material, foliage, Nanite, lighting, and low/reference/high-flow capture work for all five complete environments.
