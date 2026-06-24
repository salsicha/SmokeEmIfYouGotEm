# Audio Asset Sourcing Plan

## Goal

Build a high-fidelity audio pipeline for the full Unreal Engine rafting simulator: white water, rapids, raft impacts, paddle strokes, wet rubber, rock scrapes, spray, weather, canyon reflections, passenger barks, guide commands, voice chat, UI, and 3D spatial audio.

The audio goal is realism first. Audio should help the player read water, locate hazards, judge raft impact, understand crew state, and feel present in VR. 3D audio is a core immersion and gameplay-readability requirement, not polish.

## Recommendation

Use professionally recorded/downloaded libraries and custom field recordings as the production backbone.

Use AI-generated audio only as a supplement:

- Fast placeholder sounds during prototyping.
- Ideation and mood exploration.
- Extra non-critical variations after human review.
- Abstract UI, training, or debug sounds where realism and source authenticity matter less.
- Optional crew scratch dialogue or temp narration before final casting.

Do not rely on AI-generated audio as the primary source for white water, raft contact, paddle, rock, rescue, crew voice performance, or shipping music unless the model, output license, training-data policy, performer consent, and commercial rights are explicitly cleared.

## Why Recorded Audio Wins For This Game

White water rafting depends on dense, physical, layered sound:

- Wideband river roar with different flow levels.
- Localized hydraulic holes, standing waves, boils, eddies, laterals, strainers, shore reflections, and canyon slapback.
- Contact sounds from rubber tubes, paddles, helmets, PFDs, rocks, straps, ropes, feet, and wet gear.
- Perspective shifts from the guide's stern seat, swimmer position, scout view, and replay camera.
- VR spatial cues that need stable localization and predictable loop behavior.

Recorded material gives the best physical detail, editability, legal clarity, loop quality, and layering control. AI-generated effects are improving quickly, but they still need strict review for artifacts, loop seams, prompt mismatch, legal provenance, and inability to reliably generate physically specific variations on demand.

## Source Strategy

### 1. Custom Field Recording

Best for the final product's signature sound.

Capture:

- Real rapids at low, medium, and high runnable flows.
- Near-field and far-field river perspectives.
- Guide seat, bow, shore, eddy, underwater/hydrophone, and canyon-wall perspectives.
- Ambisonic, ORTF/XY, spaced stereo, close mono, and hydrophone perspectives where practical so the mix can support headphones, VR, stereo speakers, surround, and spatial beds.
- Raft tube impacts, paddle catches, blade slips, rock scrapes, rope pulls, pump sounds, gear handling, PFD/helmet movement, and wet footsteps.
- Crew calls, exertion, breath, panic, laughter, rescue, and post-rapid reactions with consenting performers.

Pros:

- Highest authenticity.
- Clear ownership.
- Perfect match to target rivers/seasons.
- Strong marketing/behind-the-scenes value.

Cons:

- Requires travel, safety planning, permits, weather/flow timing, recordists, gear, metadata discipline, and editing time.

### 2. Professional Sound Libraries

Best for production speed and broad coverage.

Shortlist:

- BOOM Library: high-end cinematic sound effects, general libraries, nature ambiences, rain/water-adjacent design tools, and construction-kit workflows.
- Pro Sound Effects: curated libraries, SoundQ workflow, metadata support, and broad professional SFX coverage.
- A Sound Effect: large indie marketplace with many human-made libraries, including water, oceans, weather, rocks, wood, impacts, ambiences, and game-audio packs.
- Soundly: searchable cloud/local library workflow, team features, Wwise/FMOD/editor integrations, UCS metadata, 24-bit/96 kHz Pro Library, and Freesound access.
- Fab audio assets: useful for Unreal-ready packs, but each asset's license, quality, update history, and source provenance must be reviewed.
- Sound Ideas / Sounddogs-style legacy catalogs: useful as supplemental broad-coverage libraries, especially for generic impacts, Foley, crowds, and weather.

Use these for:

- Baseline water beds, rain, wind, impacts, Foley, UI, gear, ambience, and safety events.
- Rapid prototyping before field sessions are complete.
- Layering and augmentation under custom recordings.

### 3. Open / Community Libraries

Use carefully.

Freesound and similar sources can be useful for prototypes and one-off texture, but every asset needs license tracking. Prefer CC0 for commercial production. CC BY requires attribution. CC BY-NC is not acceptable for commercial game builds. Sampling+ and older/unclear licenses should be avoided for shipping unless cleared.

BBC Sound Effects is useful for research, prototyping, and reference, but the public archive is limited to personal/educational use unless licensed separately.

### 4. AI-Generated Audio

Use as a tool, not as the core library.

Potentially useful for:

- Early sketches of UI sounds, tutorial feedback, abstract training tones, and non-realistic debug cues.
- Mood boards for menu music or trailer concepts.
- Additional transient variations after a sound designer compares them against recorded material.
- Temp crew dialogue before recorded actors or approved voice assets exist.
- Research into local generation, but not runtime generation for core gameplay without a separate performance and licensing plan.

Risks:

- Legal uncertainty around training data and output rights.
- Model terms can change.
- Some models restrict commercial use or require separate commercial licensing.
- Generated sound may contain artifacts, unstable stereo images, bad loops, or physically wrong details.
- Voice cloning requires consent, contracts, and performer rights.
- Generated music is especially sensitive because major AI music tools have faced litigation over training data and sound recording rights.

AI-generated audio must have:

- Tool and model version recorded.
- Prompt, seed, date, account/license tier, and output terms archived.
- Human review and approval.
- Similarity/plagiarism check when music, voices, melodies, or recognizable style are involved.
- Clear "prototype only" flag unless legal and audio directors approve shipping use.

## Downloaded Vs AI-Generated

Production answer: download/license and record first; generate second.

Downloaded/licensed libraries are better for:

- Realistic white water.
- Physical Foley.
- VR spatial reliability.
- Loopable ambience beds.
- Legal predictability.
- Fast implementation in Unreal, Wwise, FMOD, or MetaSounds.

Custom field recording is better for:

- Signature identity.
- Real river/season authenticity.
- Accurate guide-seat perspective.
- Marketing and expert validation.

AI-generated audio is better for:

- Cheap iteration.
- Placeholder sounds.
- Creative exploration.
- Filling small gaps after review.
- Non-critical or stylized sounds.

AI-generated audio is worse for:

- White water realism.
- Shipping crew voice without performer consent.
- Music with unclear training provenance.
- Critical gameplay cues that need exact repeatability.
- Assets that must survive legal, platform, storefront, and console review.

## Unreal Implementation Direction

Start with Unreal-native audio and MetaSounds unless middleware needs become obvious. The first implementation should include 3D audio from the beginning.

Recommended path:

- Use Unreal Audio Mixer, Sound Waves, Sound Cues/MetaSounds, attenuation, spatialization, submixes, audio modulation, and Quartz/MetaSound timing where useful.
- Use MetaSounds for procedural layering: water intensity by flow, raft speed, hull contact, paddle catch, rain, spray, foam, turbulence, and debug meters.
- Use Sound Attenuation assets for 3D positioning, distance falloff, air absorption, listener focus, reverb sends, and occlusion.
- Use binaural/HRTF spatialization for headphones and VR where platform support and performance allow.
- Use panning/surround spatialization for flat-screen speaker playback.
- Use 3D stereo spread and non-spatialized radius for large water features such as rapids, waterfalls, wave trains, and canyon-scale river roar.
- Use ambisonic beds for canyon, forest, storm, crowd, and river ambience where fixed directional texture matters.
- Use audio volumes, reverb zones, occlusion traces, and geometry-aware mix states to make rocks, canyon walls, banks, raft tubes, and player head/body position affect the soundfield.
- Keep Wwise and FMOD as evaluation options if the project needs deeper interactive authoring, mature mixing workflows, localization, large-team audio tooling, or platform-specific middleware support.
- Use UCS-style metadata and a source manifest from the start regardless of runtime.

Runtime parameters should drive audio:

- Solver flow speed, depth, turbulence, aeration, Froude number, eddy-line shear, hazard tags, raft impact impulse, paddle blade velocity, raft scrape, weather, season, canyon geometry, player camera, and VR comfort mode.

3D audio validation should cover:

- Headphone/binaural localization in VR.
- Stereo speaker play.
- 5.1/7.1 surround where supported.
- Ambisonic ambience rotation with head movement.
- Large-source behavior for rapids that should feel enveloping rather than point-like.
- Occlusion and reverb changes near canyon walls, boulders, shorelines, raft tubes, and underwater/near-water perspectives.

## Asset Manifest

Every imported or generated asset should have a manifest record:

- Asset id and filename.
- Source: field recording, purchased library, open library, AI-generated, authored synth, voice actor, or middleware.
- License file or purchase record.
- Attribution requirement.
- Commercial-use status.
- Allowed platforms.
- Derivatives allowed.
- Original sample rate, bit depth, channels, mic setup, location, date, and recordist when known.
- Processing chain and editor.
- Loop points, variations, loudness target, category, UCS metadata, attenuation preset, spatialization mode, ambisonic format/order, reverb/occlusion behavior, and intended playback contexts.
- AI tool/model/prompt/seed/license tier if generated.
- Shipping status: prototype, candidate, approved, rejected, or replaced.

## Milestones

### Milestone A: Audio Source Inventory

- Build a candidate library list for water, weather, impacts, Foley, voice, ambience, UI, music, and multiplayer voice chat.
- Record license terms, costs, platform limits, attribution, and source provenance.
- Buy or trial a small set of high-value water/river/impact libraries.

### Milestone B: Field Recording Plan

- Pick first target rivers and seasons from the real-world river content plan.
- Plan recording permissions, safety, recordists, mic kits, hydrophones, camera sync, and metadata.
- Capture first guide-seat, shore, eddy, rapid, raft, paddle, and gear sessions.

### Milestone C: Audio Manifest And Ingest

- Define source manifest schema.
- Normalize sample rates, loudness, naming, metadata, and versioning.
- Add LFS/storage policy for raw recordings, edited masters, and Unreal-ready exports.

### Milestone D: Interactive Water Audio Prototype

- Build MetaSounds or middleware events driven by solver telemetry.
- Layer river bed, nearby rapid, spray, paddle, raft contact, rocks, weather, and crew audio.
- Add 3D spatialization presets for point sounds, line/area water sources, large rapids, ambisonic beds, occluded rock/bank sounds, and voice/crew sources.
- Validate in stereo, headphones, VR binaural/HRTF, and surround where supported.

### Milestone E: AI Audio Policy

- Pick approved AI tools, if any.
- Define prohibited use cases.
- Require provenance, human review, and legal approval before shipping generated assets.
- Keep AI-generated crew voices out of shipping builds unless performer consent and license terms are explicit.

## Reference Sources To Re-check

- Epic Unreal Engine MetaSounds: https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-the-next-generation-sound-sources-in-unreal-engine
- Epic Unreal Engine Audio documentation: https://dev.epicgames.com/documentation/en-us/unreal-engine/audio-in-unreal-engine
- Epic Unreal Engine Sound Attenuation: https://dev.epicgames.com/documentation/en-us/unreal-engine/sound-attenuation-in-unreal-engine
- Epic Unreal Engine Native Soundfield Ambisonics Rendering: https://dev.epicgames.com/documentation/en-us/unreal-engine/native-soundfield-ambisonics-rendering-in-unreal-engine
- Fab Standard License: https://www.fab.com/eula
- BOOM Library: https://www.boomlibrary.com/
- Pro Sound Effects: https://www.prosoundeffects.com/
- A Sound Effect: https://www.asoundeffect.com/
- Soundly: https://getsoundly.com/
- Freesound licensing FAQ: https://freesound.org/help/faq/
- BBC Sound Effects Archive licensing: https://sound-effects.bbcrewind.co.uk/licensing
- Stable Audio Open model card: https://huggingface.co/stabilityai/stable-audio-open-1.0
- Woosh sound effects model: https://github.com/SonyResearch/Woosh
- RIAA/Suno/Udio coverage example: https://www.theverge.com/2024/8/2/24211842/ai-music-riaa-copyright-lawsuit-suno-udio-fair-use
