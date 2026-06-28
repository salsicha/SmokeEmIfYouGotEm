# Unreal VR OpenXR Plan

VR support starts with OpenXR and a seated stern-guide posture.

## Baseline

- OpenXR plugin enabled in the `.uproject`.
- OpenXR hand tracking is optional and guarded as an optional plugin.
- The first camera is seated at the guide position in the stern.
- Motion comfort defaults favor stability: recentering, horizon stabilization, impact filtering, comfort vignette, and medium motion intensity.
- Flat-screen controls must remain available for every gameplay-critical input.

## First QA Targets

- Desktop OpenXR headset.
- Headphones with binaural/HRTF spatial audio.
- Flat-screen fallback.
- Mixed input validation for controller, keyboard/mouse, and gamepad.

The runtime config lives at `unreal/Content/RaftSim/VR/openxr_runtime_config.json`.
