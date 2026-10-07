# The crew

October 2, 2026. Five people share the raft. Their identities, looks and voices
live in `URaftSimCrewRoster`
(`unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimCrewRoster.h`).

What the roster changes:
- Each person's look: their own helmet and PFD colours, their own clothes,
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

| Person | Helmet | PFD | Top | Bottom | Eyewear | Extra |
| --- | --- | --- | --- | --- | --- | --- |
| Rhys | matte graphite | rescue red | long-sleeved sun shirt, faded blue-grey | olive quick-dry shorts, above the knee | dark polarised sport sunglasses | whistle on a lanyard and a 21 cm river knife on the vest; a flip line wrapped snug round the waist |
| Kwame | red | orange | loose white T-shirt | tropical board shorts, blue with a yellow print, to the knee | matte black wraparound sunglasses, smoke lenses | none |
| Kenji | white | navy | navy-and-cream striped T-shirt | stone walking shorts, to the knee | prescription sunglasses, thin titanium frame, grey-green lenses | none |
| Ingrid | yellow | red | coral sleeveless athletic top | black three-quarter leggings | white-frame sport sunglasses, amber lenses | none |
| Amara | teal | yellow | oversized lavender T-shirt | charcoal running shorts, mid-thigh | tortoiseshell sport sunglasses, brown lenses | none |

Forearms, lower legs and feet are bare skin; everyone wears river sandals.

The sandals (`unreal/Scripts/build_production_river_sandal.py`) have a rubber
outsole, a footbed, and toe, instep and heel straps with a buckle. The
generator fits them to all five CC0 feet, read from the dressed FBXs. In
game each sandal is scaled to its wearer's own foot length and ankle
height, and the bare foot turns with its sandal.

How it is built:
- **Clothes:** the MPFB bodies had no garments: their "Wetsuit" slot was the
  bare body from the neck to the toes, so all five wore one black suit.
  `unreal/Scripts/build_cc0_river_clothing.py` (stock Blender) dresses each
  body in its own top and bottom:
  - the body surface under each garment is copied and cut along
    bone-relative planes (neckline, hems, sleeve and leg openings), with the
    skin weights interpolated along the cuts;
  - the copy is pushed off the body (snug on the torso, flaring toward loose
    hems), relaxed so it bridges the body's hollows, and given fabric
    thickness;
  - body faces under a garment take its slot, so anything that pokes
    through while posed shows the same fabric;
  - the seat's midline (cleft and perineum) takes the thigh weight of the
    buttocks beside it. MPFB weights it almost wholly to the pelvis, so
    seated it stayed behind the buttocks as a fin of fabric;
  - a top's collar closes in to 5.5 mm off the neck (the rest of the shirt
    sits 1-2 cm off the body) and its skin weights are smoothed round the
    neckline. Standing off the neck, the collar showed a dark trench behind
    it from above, and its edge went saw-toothed when the head bowed.

  The dressed FBXs, their manifests and previews are in
  `SourceArt/RaftSim/Characters/CC0Production/Dressed/`. The cut and fit of
  each garment are in the generator; its colours and pattern (stripes, a
  print, mottled cotton) are in the roster (`FRaftSimCrewGarmentLook`) and
  go on the shared `M_RaftSim_CC0_RiverClothing` material.
- Colours tint the shared helmet and PFD materials through their
  `BaseTint` parameter (`RaftSim.CreateRaftCrewMaterials`).
- Helmets are a full-cut whitewater shell (`build_production_whitewater_helmet.py`
  v9): moulded ear covers, a low occipital tail, a short peak and a foam
  liner edge, sized to clear every wearer's hair. The chin straps are
  fitted per wearer (`build_production_helmet_straps.py`).
- Eyewear and the rescue kit are small procedural props, fitted every frame:
  - eyewear to the rendered eye line (everyone wears sunglasses);
  - Rhys's whistle hangs from the vest's chest-pocket zip pull and his
    knife's sheath is clipped to the lash tab across the zip.
- The neoprene collar that hid the wetsuit's neck seam is no longer drawn:
  the clothed bodies have no wetsuit slot.
- The guide's eyewear is hidden in the first-person view.

The vest (`build_production_whitewater_pfd.py` v14) is a low-profile
front-entry whitewater guide vest:
- **Construction:** two slim front foam panels (2.4 cm) either side of a
  centre zip and one back panel (1.9 cm), thinning toward the side seams;
  dark side panels under four side adjustment straps with ladder-lock
  buckles; padded shoulder straps with adjusters; a zippered chest pocket,
  a lash tab, reflective strips and a blank back label. The armholes are
  large and the hem is short, so it rides above the seat.
- **Fit:** the inner surface follows the five seated torsos, measured from
  the posed bodies, with 6 mm clearance; every strap is built on top of
  whatever lies under it, so none sinks into the foam or the body.
- **Depth and position:** measured once on the seated body, as before: the
  vest's depth and fore-aft position are set from the chest and back in a
  central strip of the posed vertices.
- **Flip line:** the guide's flip line (`build_production_guide_flip_line.py`)
  is two wraps of 1-inch tubular webbing at the vest hem, a sewn end loop
  and a locking carabiner at the front, 0.25-0.7 cm off the vest. It is a
  child of the vest, hidden while the line is out for a righting pull.

## How they paddle

Each paddler holds the paddle as a rafter does: the inboard hand caps the
T-grip palm-down, fingers over the crossbar, and the outboard hand grips the
shaft about 66 cm down, thumb up toward the T-grip and knuckles out over the
water, on either side of the boat.
- **Catch:** they lean well forward from the hips and turn the
  paddle-side shoulder ahead. The top hand is stacked out over the blade
  about 45 cm ahead, at forehead height, and the shaft stands near
  vertical with the blade planted 60 cm ahead, just outside the tube.
- **Power:** the torso pulls back through upright to a slight lean back,
  carrying the paddle; the blade travels back to the hip.
- **Exit and recovery:** the blade comes out behind the hip with the top
  hand at chin height ahead of the chest, lifts clear of the water and
  swings forward low over it as they lean forward again.
- The top hand stays out in front of the body, 36-40 cm from the head and
  well off the line of sight; from the guide's eye the arms stay out of
  view through forward strokes and steering.
- **Back strokes:** the blade plants behind the hip and drives forward
  while the top hand works against it, drawn back to the chest. **Turns**
  pair forward and back strokes.
- **At rest** the paddle lies across the tops of the thighs, just behind
  the knees, with the blade out over the tube. The upper hand holds the
  T-grip and the lower hand the shaft just outboard of the outboard thigh.

The T-grip crossbar runs parallel to the blade, as on a real paddle. Elbows
bend on each body's own arm lengths: out, down and a little back on the shaft
arm. The top arm, reaching across the chest, leads with its elbow out and
down, turned as far as needed to keep the forearm clear of the face. As a
hand nears full reach the shoulder slides toward it and rises, as a
paddler's shoulder blade does, so the arm stays in its socket.
`RaftSim.Crew.GearReview` renders each paddler's hands, shoulders, face and
chin strap, feet and seat, and audits grip orientation and arm stretch.
`review_crew_paddle_stroke_cycle.py` renders the crew at the catch, in the
power phase, at the exit and in the recovery.

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
- **Throw bag:** the guide's red bag, about the size of a grapefruit, on
  the stern tube beside the guide's hip, with its cinched drawstring and the
  yellow floating rope showing at the mouth. Thrown, it is the same size.
- **Painters:** coiled bow and stern lines on the tube tops.

## Limits

- **Bodies:** the CC0 bodies, faces and helmet-contained hair are unchanged.
  There are still four paddler bodies and one guide body.
- **Clothes are skinned, not simulated:** they follow the body but do not
  flutter, cling or darken when wet.
- **Paddling:** at the exit the top forearm crosses in front of the chest
  a few centimetres below the chin, as a real paddler's does. The paddle
  path is one stroke for everyone; it is not tuned to each body's reach.
- **Movement:** individual paddling styles are not modelled. The crew
  paddles in sync on the guide's call.
- **Voices:** chatter is text only. The crew still has no recorded voice.
- **Vest fit:** the vest is one rigid shell. It is fitted to the resting
  seated chest and does not flex with the stroke. Its shoulder straps
  clear the tallest shoulders, so on Kwame and Ingrid they stand 2-4 cm
  proud, and resting forearms touch the vest's lower front corners.
- **Gear is rigid:** the bag and lines do not flex with the tubes.
