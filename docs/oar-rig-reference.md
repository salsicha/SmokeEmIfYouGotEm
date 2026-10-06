# Oar rig: what a single-rower raft should look like

October 2, 2026. On the Colorado (Grand Canyon) and Zambezi maps the raft
carries one person rowing an oar rig instead of a guide and four paddlers.
This is the visual reference for that boat, from outfitter, gear-maker and
guide-school sources and from photographs (sources at the end).

## The boat in one paragraph

A self-bailing raft, 16-18 ft long, with a centre-mounted aluminium frame
strapped to its D-rings. The rower sits high in the middle of the boat on a
padded box or cooler, facing downstream (toward the bow), feet braced on a
foot bar, with two long oars in oarlocks on short towers at the frame's
sides. Gear is lashed into the bays fore and aft. On the Colorado the boat is
a loaded expedition rig; on the Zambezi it is a lighter day boat with big
wooden oars.

## Raft

| | Grand Canyon (Colorado) | Zambezi (Batoka Gorge) |
| --- | --- | --- |
| Length | 18 ft (5.5 m), the standard Grand Canyon oar boat | 16-18 ft |
| Beam / tubes | about 8 ft (2.4 m) beam, 23-25 in (58-64 cm) tubes | similar |
| Floor | self-bailing | self-bailing |
| Colour | blue, grey or grey-white (commercial and private boats) | yellow with a black lower band (SAFPAR-style), or grey (Shearwater-style) |
| Details | "chicken line" (perimeter rope) round the tubes, bow and stern painters, D-rings for the frame straps | as Grand Canyon; operator name along the tube (do not copy a real logo) |

Our production paddle raft is a 14 ft boat (4.32 x 2.06 m, 0.544 m tubes);
see "What the code needs" for keeping it or building an 18 ft hull.

## Frame

- **Material:** 6061-T6 aluminium pipe, 1 5/8 in (4.1 cm) outside
  diameter, 1/8 in wall, anodised silver or bare, joined with cast aluminium
  fittings (NRS LoPro, Down River Speed Rail). Strapped to the raft's
  D-rings with cam straps.
- **Size:** about 78 in (2.0 m) wide for an 18 ft boat (the side rails run
  over the tube centres, the oar towers 3-4 in outboard of them), and about
  10-12 ft long.
- **Bays, bow to stern:**
  - **Front bay:** a plywood deck ("floorboards") or a dry box. Passengers
    would sit here; on a solo boat it carries gear.
  - **Rower's cockpit (centre):** the seat on a padded dry box or cooler,
    with a foot bar across the bay in front of it. The foot bar is placed
    for the rower's leg length.
  - **Rear bay:** coolers and dry boxes dropped between the rails, with dry
    bags piled on top and cammed down.
- **Oar towers:** short uprights (about 8-10 in / 20-25 cm) on the side
  rails beside the seat, carrying the oarlocks. With the frame centre
  mounted, the oarlocks sit at the boat's mid-length, its pivot point.

## Oars

- **Length:** 1/3 inboard of the oarlock, 2/3 outboard. For an 18 ft
  Grand Canyon gear boat: **11 ft (3.35 m)** (10.5 ft on smaller rivers);
  for a 78 in frame, 10.5-11 ft. Zambezi oar boats use "two big wooden
  oars", 10-12 ft.
- **Shaft:** about 1 7/8 in (4.8 cm). Composite (Cataract SGG, black or
  dark grey; the most popular guide shaft) or wood (Sawyer, varnished
  ash or spruce). The Zambezi boats photographed carry natural-wood oars.
- **Blade:** about 7 in wide by 27-30 in long (18 by 69-76 cm). Composite
  blades are often black, white or yellow; Sawyer square-top wood blades
  have a tipped edge.
- **Oarlock fittings:** open bronze oarlocks (Sawyer Cobra) with an oar
  right (a clamp that holds the blade square) and an oar stop, and a rope or
  sleeve wrap where the shaft rides in the lock. Some big-water boats use
  pins and clips instead (the oar cannot rotate or come loose). Long oars
  carry counterbalance sleeves near the handle.
- **Handles:** with the oars level the handle ends are 3-6 in (8-15 cm)
  apart; during the stroke the handles ride at about shoulder height.
- **Spare:** a third oar strapped along a side rail.

## The rower

- **Position:** seated high in the middle, facing downstream, feet on the
  foot bar, one leg sometimes tucked under to brace.
- **Pull stroke** (used most; it slows the boat and sets the back-ferry):
  blades drop in ahead, the rower leans back pulling the handles to the
  chest, legs driving against the foot bar, "arm bent, legs nearly
  extended" at the finish.
- **Push stroke** (to go faster than the current): the rower leans forward
  and drives the handles away, "like throwing a hard punch", arms extending.
- **Pivots:** one oar pulls while the other pushes, turning the boat about
  its centre; or one blade holds as a rudder while the other drives.
- **Recovery:** blades lift clear between strokes; with oarlocks the rower
  can feather them flat. In tight places the oars are shipped: handle
  pushed out, blade swung in over the tube.
- **Dress:** PFD always. Grand Canyon oar guides commonly row in a sun hat
  (straw or wide brim), sun shirt or bare arms, shorts and sandals;
  helmets are uncommon on oar rigs there. On the Zambezi, Class 5 at the
  start of most runs, the rower should wear a helmet with the PFD; guides
  wear T-shirts or rash vests and shorts.

## What it carries

- **Grand Canyon (a multi-day rig):** white, yellow and blue roll-top dry
  bags; aluminium dry boxes ("rocket boxes") and ammo cans; a large cooler;
  blue and black cam straps; a throw bag at the rower's seat; the spare oar;
  bow and stern lines coiled on the tubes. Water is the Colorado's brown
  silt, so everything rides tied down and wet.
- **Zambezi (a day boat):** a throw bag, a small dry box or first-aid
  drybag, the bow line, and the frame.

## What the code needs

Today every map gets the same 14 ft paddle raft with a guide and four AI
paddlers (`ARaftSimRaftActor`, `CrewSize 5`, `PaddlerCount 4`). The project
already plans the Colorado run as an oar rig (`river_portfolio_plan.json`
`oar_rig_rowing`, `named_rapid_registry.py` `manual_oar_rig`), and has unused
pieces for it: `IA_OarLeftStroke`, `IA_OarRightStroke`, `IA_OarFeather` (no
key mappings), `ERaftSimInputGameplayMode::RowingOarRig`,
`URaftSimColoradoRowingRouteConfig` and a `sixteen_foot_oar_rig` handling
profile (260 kg, 4.9 x 2.25 m). The Zambezi data still says guided paddle
crew and would change with it.

1. **Configuration.** An oar-rig mode chosen per map, for `L_Hance`,
   `L_Zambezi` and `L_ZambeziUpperGorge`: no paddlers (`PaddlerCount 0`
   already flows through mass, seats, spawning and the swimmer count), one
   rower in a centre seat instead of the stern guide seat.
2. **Hull.** Either keep the 14 ft production raft (a small but real oar
   boat; nothing in the contact physics changes), or build an 18 ft hull
   with the existing generator (`build_production_whitewater_raft.py`). The
   production mesh is also the authoritative contact hull and the D4 flex
   binding, so a new hull needs the physics retuned and its tests updated.
3. **Rig.** The frame, towers, oarlocks, seat box, foot bar, gear (dry
   boxes, cooler, dry bags, straps, spare oar) and two oars, built like the
   current procedural raft gear, with the oars moving every frame.
4. **Rower.** One CC0 body seated on the frame facing downstream, with
   pull, push, pivot, feather and rest poses gripping the oar handles, and
   river clothes: sun hat and PFD on the Colorado, helmet and PFD on the
   Zambezi.
5. **Rowing physics.** Left and right oar strokes, each a force at its
   blade (so pivots come from the lever arm, not a pure yaw impulse), with
   water purchase sampled at the blades about 2.2 m abeam. Today all strokes
   are impulses at the centre of mass with no point of application.
6. **Controls and UI.** Direct manual rowing, as the game plan specifies
   (no voice or crew commands): the two oars together for pull and push,
   opposite for pivots; on a gamepad, one stick per oar. The crew command
   keys, wheel, HUD text and crew chatter are hidden on these maps;
   rescue becomes self-rescue.
7. **Tests.** The map-load test that expects five crew on the Zambezi, the
   seat-anchor and crew-command tests if class defaults change, the
   Zambezi catalog and scenario tests (`attached_crew_count == 5`,
   `guided_paddle_crew`), and the portfolio test that ties oar rigs to
   voice off.

## What is built (October 2, 2026)

- **Configuration:** `ARaftSimRaftActor::RaftRig` (default Auto) rows
  `L_Hance` as the Colorado rig and `L_Zambezi` / `L_ZambeziUpperGorge` as
  the Zambezi rig; `raftsim.RaftRig` overrides it for test tanks. An oar rig
  has no paddlers (`PaddlerCount 0`, `CrewSize 1`), adds its load to the
  boat's mass (165 kg Colorado, 55 kg Zambezi), and seats the rower at the
  centre in the flexible-raft model.
- **Hull:** the 14 ft production raft, blue on the Colorado and yellow on
  the Zambezi.
- **Rig** (`URaftSimOarRigComponent`): a pipe frame on the tube tops with
  cast fittings, oar towers and open oarlocks at the boat's middle, a padded
  seat on a pedestal behind them, and a foot bar hung below the rails. The
  Colorado boat carries a cooler and three dry bags cammed down in the rear
  bay, a plywood deck with ammo cans and a dry box forward, and a spare oar.
  The Zambezi boat carries one small dry box. The oars are 8.5 ft (2.6 m)
  with 74 cm inboard, so the handle ends clear each other on this narrower
  frame. They are composite on the Colorado and wood on the Zambezi, with a
  rope wrap, an oar stop and an oar right at the lock.
- **Strokes:** each oar runs its own 1.4 s stroke: catch, drive, release and
  feathered recovery. The blade's depth follows the water sampled under it.
  Each drive pushes the hull along the bow axis at that blade's side, so two
  oars drive the boat, opposed oars pivot it, and one oar both drives and
  turns it. Strokes have no purchase on dry ground, and only a little when
  the boat is grounded.
- **Rower:** the guide body, posed every frame from the oars: hands overhand
  on the handles, the trunk leaning back to the chest at the finish of a
  pull and forward to reach for its catch, twisting in pivots, and the feet
  braced on the foot bar.
- **Controls:**
  - W pushes both oars (bow downstream) and S pulls both (the power stroke
    and back-ferry).
  - A and D pivot on opposed oars.
  - The left or right mouse button pulls only that side's oar.
  - The shared numbered commands and command wheel now operate the real oars:
    forward/back use both blades, turns use opposed blades, and stop brakes
    without resetting velocity. Idle input preserves the standing order.
  - Shared stroke/steer APIs also drive the blades. High-side/get-down pause
    rowing and apply the visible and physical action to the single rower.
- **Tests and review:**
  - `RaftSim.P4.RiverMapLoads` checks that the three maps carry one rower on
    their oar rigs, that other rivers keep the paddle crew, and that the
    Zambezi rower rows strokes after launch.
  - `unreal/Scripts/review_oar_rig_stroke_cycle.py` renders the rig through
    rest, a pull, a push and a pivot.
  - The Zambezi data (portfolio, scenario and review runs) now says
    `oar_rig_rowing` / `manual_oar_rig` with voice commands off.
- **Not yet:** a sun hat for the Colorado rower (still the helmet), shipping
  the oars, a gamepad stick per oar, and self-rescue for the solo rower.

## Sources

- Center-mount frames and the rower's position:
  [paddlingmag: The Ultimate Canyon Rig](https://paddlingmag.com/stories/the-ultimate-canyon-rig/),
  [paddlingmag: raft oar setup](https://paddlingmag.com/boats/raft-oar-setup/).
- Grand Canyon oar boats (18 ft, guide centred, two long oars):
  [CRATE oar trips](https://www.crateinc.com/rowing-rafting),
  [OARS: How to raft the Grand Canyon](https://www.oars.com/blog/how-to-raft-the-grand-canyon),
  [Western River: five boats in Grand Canyon](https://www.westernriver.com/blogs/stories/motors-oars-and-paddles-in-grand-canyon).
- Frame pipe and fittings:
  [NRS frame products](https://www.nrs.com/learn/raft-rowing-frame-features),
  [NRS Bighorn II frame](https://shop.aldercreek.com/products/nrs-bighorn-ii-raft-frame).
- Oar length:
  [Whitewater Guidebook: proper oar size](https://www.whitewaterguidebook.com/how-to-determine-proper-oar-size/),
  [Colorado Kayak: oar length](https://coloradokayak.com/blogs/cks-blog/how-to-choose-the-right-oar-length-for-your-raft),
  [NRS: adjust raft oars and mounts](https://nrs.com/learn/adjust-raft-oars-and-mounts).
- Oar hardware:
  [Cataract Magnum II blade](https://www.aire.com/products/cataract-magnum-ii-oar-blade),
  [Sawyer DyneLite wide blade](https://backcountry.com/sawyer-oars-sawyer-dynelite-wide-blade-oar),
  [Cataract SGG shaft](https://www.riversports.com/products/cataract-sgg-oar-shafts-raft-cataraft-fiberglass),
  [Sawyer Cobra oarlock](https://coloradokayak.com/products/sawyer-cobra-oarlock-deluxe-with-lock-nut),
  [Oarlocks vs pins and clips](https://outdoors.codidact.com/posts/56397).
- Rowing technique:
  [NRS Guide School: using your oars](https://community.nrs.com/duct-tape/2018/07/16/guide-school-using-your-oars/),
  [Northwest Rafting: oar maneuvering terms](https://www.nwrafting.com/schools/oar-raft-maneuvering-terminology).
- Zambezi oar and stern-mount boats:
  [Civitatis: Zambezi rafting raft types](https://www.civitatis.com/en/victoria-falls/rafting-river-zambezi/),
  [Water by Nature: Zambezi](https://www.waterbynature.com/?p=428).
- Photographs (Wikimedia Commons):
  [Grand Canyon NPS: running a rapid](https://commons.wikimedia.org/wiki/File:Grand_Canyon_National_Park,_Colorado_River_Running_A_Rapid_3767_-_Flickr_-_Grand_Canyon_NPS.jpg)
  (blue 18 ft oar rig, rower centred on a box seat, dry bags and boxes
  strapped in, plank deck forward);
  [Lees Ferry launch ramp](https://commons.wikimedia.org/wiki/File:Grand_Canyon_National_Park_Lees_Ferry_Launch_Ramp_0608_(6176486711).jpg)
  (grey-white rafts rigged with frames and dry boxes, yellow oars);
  [Zambezi rafting, Simonga](https://commons.wikimedia.org/wiki/File:Zambezi_Rafting,_Simonga_(20260521-P1086552).jpg)
  (yellow and black rafts with frames and long wooden oars);
  [Rafting Zambezi](https://commons.wikimedia.org/wiki/File:Rafting_Zambezi.jpg)
  (a grey Shearwater paddle raft for comparison).
