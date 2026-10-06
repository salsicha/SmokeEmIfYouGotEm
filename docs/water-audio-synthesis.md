# Water audio: how the river is synthesized

October 2, 2026. All of the game's water sound is first-party procedural
audio (see `docs/production-audio-source-policy.md`). It is synthesized live
on the audio render thread by `RaftSimSynth::FVoice`
(`unreal/Plugins/RaftSim/Source/RaftSimAudio`). `ARaftSimRunAudioDirector`
plays the voices and drives them from the live water and raft simulation.

## What changed

The former mix looped one 2 s buffer per layer, built from seeded noise:

- The repeat was audible: lag correlation was about 1.0 at 2 s.
- Every loop seam clicked, because the brown-noise state did not wrap.
- The river was a 115 Hz rumble with flat hiss over it.
- The rapid layer was white hiss.
- The rapid, foam and turbulence layers all followed one Froude number.
- Nothing in the sound told you where water was, or how far away.

## The model

Moving water sounds mostly like air bubbles ringing. A bubble of radius r
rings as a sine at the Minnaert frequency, f0 = 3.26 / r (r in metres). It
decays with damping d = 0.13 / r + 0.0072 r^-1.5 and rises in pitch as it
rings down: f(t) = f0 (1 + sigma d t) (van den Doel, 2005). So a 1 mm bubble
is a 3.3 kHz blip lasting about 20 ms, and an 8 mm bubble a 400 Hz "gloop".
Radii are drawn from a power law, so small bubbles outnumber large ones.

Each voice runs live random processes, so nothing repeats:

| Voice | Sounds | Driven by |
| --- | --- | --- |
| Near water (port and starboard emitters) | Pink-noise wash brightening with flow; gurgling bubbles (0.9-7 mm); laps (low filtered slaps with a few large bubbles) | Water speed past the tubes, turbulence, heave |
| Whitewater (port and starboard) | Dense small-bubble cloud (0.6-6 mm, up to 2,700/s); broadband roar (low-passed pink, 1.6-7 kHz); a low rumble; slow surging; breaking-wave crashes | Aeration from the Froude number, turbulence from shear and surface tilt |
| Distant rapid | Whitewater placed at the loudest whitewater found within 150 m. It fades with distance (natural falloff, -42 dB at 250 m) and loses its highs (300 Hz + 18 kHz e^(-d/45 m)), so a rapid is heard ahead before it is seen | A survey of 112 water samples round the boat every 0.3 s |
| Spray | Droplet bubbles (0.25-1.2 mm), crackling fizz above 2.8 kHz, patter | Aeration, hull slams |
| Strokes | The catch: a cut-in "thwup", one deep bloop as the blade's air closes, the pull's swish, and shed bubbles; for oars, drips as the blade lifts out | Actual blade entries: the guide's strokes, the crew's planted blades, each oar's catch and release |
| Hull | A low thud gliding from 110 to 52 Hz (the tube's resonance), slaps, and a rough scrape on rock | Slams (a falling boat stopped hard), rock contact onsets, dragging |

Controls glide sample by sample, so levels never step. Water layers are not
muffled by a blanket low-pass any more. A crew call dips the water by at
most 37 %, where the old duck was 75 %. Rushing water still buries paddle
strokes, as playtests asked.

## Verifying it

`RaftSim.Audio.WaterSynthScenes` renders seven scenes offline:

- still pool
- moving current
- a rapid approached from 120 m
- inside a rapid
- paddle strokes
- oar strokes
- hull hits

It writes each scene to `unreal/Saved/RaftSimValidation/audio/water-synth/*.wav`
for listening, and checks that:

- nothing repeats (lag correlation under 0.08);
- nothing clips;
- a pool is quiet, current louder, and a rapid far louder;
- a distant rapid is darker and quieter than a near one;
- catches and hull hits stand out.

In game, `RaftSim audio mix:` lines in the log (every 2 s) give each layer's
level and its drivers.
