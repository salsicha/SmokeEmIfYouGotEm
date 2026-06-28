# Audio Asset Sourcing Plan

## Goal

Build a high-fidelity audio pipeline for the full Unreal Engine rafting simulator: white water, rapids, raft impacts, paddle strokes, wet rubber, rock scrapes, spray, weather, canyon reflections, passenger barks, guide commands, voice chat, UI, and 3D spatial audio.

The audio goal is realism first. Audio should help the player read water, locate hazards, judge raft impact, understand crew state, and feel present in VR. 3D audio is a core immersion and gameplay-readability requirement, not polish.

## Recommendation

During active development, use only free/open, first-party generated, procedural, and AI-generated audio. Do not buy or trial paid sound libraries yet.

Paid/professional libraries and larger custom recording plans remain useful research, but the buying decision is deferred until release-readiness. At that point, buy assets only for gaps where free/open and AI-generated assets are not good enough for quality, consistency, rights, or production risk.

AI-generated audio is allowed as a development source when it has manifest metadata:

- Tool and model version.
- Prompt, seed, date, account/license tier, and output terms.
- Human review status.
- Similarity/plagiarism check for music, voices, melodies, or recognizable style.
- Clear development-only or shipping-candidate flag.

Do not ship AI-generated audio unless the model, output license, training-data policy, performer consent where relevant, commercial rights, and review status are explicitly cleared.

See [Free And AI Asset Policy](free-and-ai-asset-policy.md) for the project-wide art and sound decision.

## Why Paid/Recorded Research Still Matters

White water rafting depends on dense, physical, layered sound:

- Wideband river roar with different flow levels.
- Localized hydraulic holes, standing waves, boils, eddies, laterals, strainers, shore reflections, and canyon slapback.
- Contact sounds from rubber tubes, paddles, helmets, PFDs, rocks, straps, ropes, feet, and wet gear.
- Perspective shifts from the guide's stern seat, swimmer position, scout view, and replay camera.
- VR spatial cues that need stable localization and predictable loop behavior.

High-quality recorded material can still give the best physical detail, editability, legal clarity, loop quality, and layering control. That research stays in the plan so the team knows what to buy later if the free/open and AI-generated development set falls short.

For now, the development target is to push free/open and AI-generated audio as far as practical before spending money.

## Source Strategy

### 1. Free / Open / First-Party Sources

Use first during development.

Use:

- CC0/public-domain audio where the source and license snapshot are clear.
- CC-BY audio only when attribution can be tracked cleanly in the manifest and credits.
- First-party procedural or synthesized audio for UI, debug, training, telemetry, and abstract feedback.
- First-party field recordings only when they do not require buying third-party asset licenses.
- AI-generated audio for prototypes, temporary dialogue, water/impact studies, ambience studies, and non-critical variations after review.

Avoid:

- Non-commercial licenses.
- Unclear or legacy licenses.
- Assets that cannot be traced to a source URL, license file, model/tool record, or first-party capture note.

### 2. AI-Generated Audio

Use aggressively for development, but track it rigorously.

Potentially useful for:

- Early sketches of water beds, UI sounds, tutorial feedback, abstract training tones, and debug cues.
- Mood boards for menu music or trailer concepts.
- Additional transient variations after review.
- Temp crew dialogue before recorded actors or approved voice assets exist.
- Research into local generation, but not runtime generation for core gameplay without a separate performance and licensing plan.

Risks:

- Legal uncertainty around training data and output rights.
- Model terms can change.
- Some models restrict commercial use or require separate commercial licensing.
- Generated sound may contain artifacts, unstable stereo images, bad loops, or physically wrong details.
- Voice cloning requires consent, contracts, and performer rights.
- Generated music is especially sensitive because major AI music tools have faced litigation over training data and sound recording rights.

### 3. Custom Field Recording

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

For now, custom recording is planning/research unless it can be done as first-party capture without buying asset licenses.

### 4. Professional Sound Libraries

Best for release-gate fallback if free/open and AI-generated assets are not good enough.

Shortlist:

- BOOM Library: high-end cinematic sound effects, general libraries, nature ambiences, rain/water-adjacent design tools, and construction-kit workflows.
- Pro Sound Effects: curated libraries, SoundQ workflow, metadata support, and broad professional SFX coverage.
- A Sound Effect: large indie marketplace with many human-made libraries, including water, oceans, weather, rocks, wood, impacts, ambiences, and game-audio packs.
- Soundly: searchable cloud/local library workflow, team features, Wwise/FMOD/editor integrations, UCS metadata, 24-bit/96 kHz Pro Library, and Freesound access.
- Fab audio assets: useful for Unreal-ready packs, but each asset's license, quality, update history, and source provenance must be reviewed.
- Sound Ideas / Sounddogs-style legacy catalogs: useful as supplemental broad-coverage libraries, especially for generic impacts, Foley, crowds, and weather.

Keep these notes for future use:

- Baseline water beds, rain, wind, impacts, Foley, UI, gear, ambience, and safety events.
- Release candidate quality gaps after free/open and AI-generated assets are evaluated.
- Layering and augmentation under custom recordings.

### 5. Open / Community Libraries

Use carefully.

Freesound and similar sources can be useful for prototypes and one-off texture, but every asset needs license tracking. Prefer CC0 for commercial production. CC BY requires attribution. CC BY-NC is not acceptable for commercial game builds. Sampling+ and older/unclear licenses should be avoided for shipping unless cleared.

BBC Sound Effects is useful for research, prototyping, and reference, but the public archive is limited to personal/educational use unless licensed separately.

## Downloaded Vs AI-Generated

Development answer: generate/free/open first; buy later only if needed.

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
- Testing whether paid libraries are actually needed.

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

- Build a free/open and AI-generated candidate list for water, weather, impacts, Foley, voice, ambience, UI, music, and multiplayer voice chat.
- Record license terms, costs, platform limits, attribution, model/tool metadata, and source provenance.
- Preserve paid library research as release-gate reference material, but do not buy or trial libraries yet.

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
- Layer river bed, nearby rapid, spray, paddle, raft contact, rocks, weather, and crew audio using free/open and AI-generated development assets first.
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
