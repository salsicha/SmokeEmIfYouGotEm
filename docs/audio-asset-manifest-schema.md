# Audio Asset Manifest Schema

Every imported or generated audio asset must have a manifest record before it enters the Unreal project as production content.

The schema covers:

- Asset identity and filename.
- Source type.
- License or purchase record.
- Attribution and commercial-use status.
- Platform rights and derivative permissions.
- Sample rate, bit depth, channel count, mic setup, location/date, and recordist.
- Processing chain, editor, loop points, variations, loudness target, category, and UCS metadata.
- Attenuation, spatialization, ambisonic format/order, reverb/occlusion behavior, and intended playback context.
- Approval status and review notes.

Canonical schema: `unreal/Content/RaftSim/Audio/audio_asset_manifest.schema.json`.
