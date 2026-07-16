# Custom Water Runtime Baseline

The primary Unreal runtime water candidate is the custom C++ reduced shallow-water / height-field solver: `raftsim_water_cpp_v1`. It is not currently approved as authoritative live water.

## Baseline Decision

- Keep `raftsim_water_solver` as the candidate runtime path for Unreal preproduction, with live stepping disabled behind the current blocked report-set lock.
- Continue validating the custom solver against GeoClaw reference outputs.
- Treat only rows labeled `parity_mode: solver` as solver-parity evidence. Rows labeled `reference_playback` are useful diagnostics but cannot approve live water, regardless of their raw threshold result.
- The honest Milestone 16 v1 gate currently records 6 of 40 passing solver-parity rows and 34 reference-playback rows. The full C++ gate, GeoClaw-to-Unreal readiness report, and Milestone 20 report-set lock are therefore blocked.
- Keep telemetry/replay playback and frozen water snapshots available to Unreal, Chaos, and Jolt while the owner chooses the water-solver strategy.
- Keep Chrono::FSI optional and separate from required builds.
- Preserve frozen scenario, telemetry, replay, and parameter schemas as the interchange contract between Python, C++, Chrono, and Unreal.

## Replacement Rule

Replacing or re-scoping the custom water solver requires the owner decision in `docs/water-solver-strategy-decision.md`. A replacement solver must match GeoClaw honestly, fit desktop/VR/handheld budgets, support deterministic replay/networking needs, and export the same schema-compatible telemetry. A game-feel re-scope requires a separately accepted qualitative/stability/budget gate and may not reuse playback rows as solver evidence.
