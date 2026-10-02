# The crew

October 2, 2026. Five people share the raft. Their identities, looks and voices
live in `URaftSimCrewRoster`
(`unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimCrewRoster.h`).

What the roster changes:
- Each person's look: their own helmet, PFD, wetsuit and jacket colours,
  eyewear, and the guide's rescue kit.
- Their names, shown on the rescue HUD.
- Their swimming ability in a rescue.
- What they say on the river.

What it does not change:
- Seats, CC0 bodies and masses.
- The shared paddling cadence, so the crew still paddles in time on the
  guide's call.

## Who is aboard

| Seat | Name | Age | From | Does | On the water |
| --- | --- | --- | --- | --- | --- |
| Stern (guide) | Rhys Calloway | 41 | Queenstown, New Zealand | Head guide, eighteen seasons on the Zambezi | Calm and wry. Calls the lines early, never raises his voice, counts heads after every rapid. |
| Front left (`paddler_1`) | Kwame Asante | 29 | Accra, Ghana (lives in London) | Software engineer | Loud, generous, a little overconfident. Claimed the front seat and paddles like he means it. |
| Front right (`paddler_2`) | Kenji Watanabe | 52 | Osaka, Japan | Retired railway engineer | Methodical and quietly funny. Third trip down the gorge; keeps perfect time. |
| Second left (`paddler_3`) | Ingrid Solberg | 34 | Bergen, Norway | Ski patroller | Competitive adrenaline seeker. Asks for the biggest line and laughs when she swims. |
| Second right (`paddler_4`) | Amara Okafor | 23 | Manchester, England (born in Lagos) | Medical student | First time on a river. Terrified at the top of every rapid, thrilled at the bottom. |

## How each one looks

| Person | Helmet | PFD | Wetsuit | Eyewear | Extra |
| --- | --- | --- | --- | --- | --- |
| Rhys | matte graphite | rescue red | charcoal | dark polarised sport sunglasses | whistle on a lanyard and a 21 cm river knife on the vest |
| Kwame | red | orange | black | none | none |
| Kenji | white | navy | navy-charcoal | clear glasses, thin titanium frame | none |
| Ingrid | yellow | red | black-teal | white-frame sport sunglasses, amber lenses | none |
| Amara | teal | yellow | black | none | none |

Everyone wears a neoprene collar over the top of the wetsuit.

How it is built:
- Colours tint the shared helmet, PFD, splash-jacket and wetsuit materials
  through their `BaseTint` parameter (`RaftSim.CreateRaftCrewMaterials`).
- Eyewear and the rescue kit are small procedural props, fitted every frame:
  - eyewear to the rendered eye line;
  - the rescue kit to the front of the vest's chest frame.
- The collar is fitted to each body when it loads. It covers the saw-tooth
  seam where the source mesh changes from skin to wetsuit round the neck, and
  moves with the upper spine. `RaftSim.CC0NeckCollar 0` hides it.
- The guide's eyewear and collar are hidden in the first-person view.

The vest is fitted to each body:
- **Depth and position:** measured once on the seated body. The chest
  front and the back are taken from the posed vertices in a central strip,
  and the vest's depth and fore-aft position are set so both carriers sit
  about 5 mm off them. Depth comes out at x0.99-1.09.
- **Taper:** a seated paddler's torso is wedge-shaped. The chest front holds
  at 15-17 cm from the spine to mid-chest and falls back to 8-12 cm under
  the collarbones. The back runs from about -3 cm at the lumbar curve to
  -8 cm at the shoulder blades. The vest mesh (`build_production_whitewater_pfd.py`
  v13) is shaped to match:
  - its front leans in up to 5.5 cm above mid-chest;
  - its back moves in up to 4.3 cm over the lumbar curve.
- **Side panels:** foam panels in the vest's colour close the flanks under
  the arms, just inside the side adjustment straps.

## How they behave

- **Swimming:** in an aimed rescue, each person swims as well as they do:
  - Rhys, Kwame and Ingrid are strong swimmers;
  - Kenji is average;
  - Amara is weak.
- **Looking about:** seated, each person turns their head to a look, holds
  it, and moves on, in their own way:

  | Person | Looks about | Holds a look | Eyes |
  | --- | --- | --- | --- |
  | Rhys | wide, 26° either side | about 2.6 s | reads the water ahead |
  | Kwame | widest, 32° | about 1.8 s | level, at everything |
  | Kenji | little, 10° | about 5.5 s | slightly down, steady |
  | Ingrid | 22° | about 3 s | downstream, for the next feature |
  | Amara | 14° | about 1.4 s, quick glances | well down, on the water ahead |

  Paddling narrows the range to about a third. Bracing, high-siding,
  swimming and rescues hold the head still. The first-person guide's head
  never turns. `RaftSim.CC0CrewGaze 0` turns it off.
- **Chatter** (`FRaftSimCrewChatter`, shown as subtitles):
  - **Big water:** when the hull is thrown about, someone reacts. Nervous
    people speak up more often; the guide calls about a third of the time.
  - **Run-outs:** someone comments once the boat settles.
  - **Swims and rescues:** the swimmer speaks, in their own words.
  - **Flips:** the guide calls the flip, then someone takes stock.

  Lines are queued one at a time, about four seconds apart.

## The boat and its gear

The raft is a working commercial paddle raft, not a showroom one
(`M_RaftSim_RaftTube`, `M_RaftSim_RaftFloor`, `RaftSim.CreateRaftCrewMaterials`):
- **Tubes:** commercial red coated fabric, brighter than the earlier
  maroon.
- **Wear:**
  - a brown-green film on the surfaces that ride in the river;
  - lightly sun-faded tops;
  - small pale scuffs on the tube sides and underside, where the raft drags
    over rock.

  The wear is placed in the hull's own space, so it stays put as the raft
  moves and flexes.
- **Paddles:** black anodised aluminium shafts.

Rigged gear (`ARaftSimRaftActor::BuildRaftGear`):
- **Throw bag:** the guide's red bag at the stern, with its drawstring
  collar, the yellow floating rope showing at the mouth, and a webbing
  strap.
- **Painters:** coiled bow and stern lines on the tube tops.
- **First-aid drybag:** a yellow roll-top lashed across the bow floor with
  two straps, ahead of the front paddlers' feet.

## Limits

- **Bodies:** the CC0 bodies, faces and helmet-contained hair are unchanged.
  There are still four paddler bodies and one guide body.
- **Movement:** individual paddling styles are not modelled. The crew
  paddles in sync on the guide's call.
- **Voices:** chatter is text only. The crew still has no recorded voice.
- **Vest fit:** the vest is one rigid shell. It is fitted to the resting
  seated chest and does not flex with the stroke.
- **Gear is rigid:** the bag, lines and drybag do not flex with the tubes.
