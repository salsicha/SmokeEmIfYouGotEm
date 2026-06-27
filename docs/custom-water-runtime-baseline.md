# Custom Water Runtime Baseline

The primary Unreal runtime water candidate is the custom C++ reduced shallow-water / height-field solver: `raftsim_water_cpp_v1`.

## Baseline Decision

- Keep `raftsim_water_solver` as the default runtime water path for Unreal preproduction.
- Continue validating the custom solver against PyClaw reference outputs.
- Feed Project Chrono from the custom water query/coupling layer for raft rigid-body, collision, and contact dynamics.
- Keep Chrono::FSI optional and separate from required builds.
- Preserve frozen scenario, telemetry, replay, and parameter schemas as the interchange contract between Python, C++, Chrono, and Unreal.

## Replacement Rule

Replacing the custom water solver requires a later milestone decision showing that another solver matches PyClaw at least as well, fits desktop/VR/handheld budgets, supports deterministic replay/networking needs, and exports the same schema-compatible telemetry.
