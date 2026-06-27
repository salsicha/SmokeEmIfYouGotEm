# Chrono::FSI Policy

Chrono::FSI is an optional research/reference path, not a baseline runtime dependency for the UE5 simulator.

## Policy

- Do not require Chrono::FSI for default C++ builds, Python validation, Unreal runtime work, or CI smoke tests.
- Use Chrono::FSI only behind explicit experiment flags or separate local build instructions.
- Keep reduced shallow-water / height-field simulation as the runtime baseline and validate it against PyClaw.
- Any Chrono::FSI experiment must export the same frozen telemetry and replay schemas before its results can be compared to the baseline.
- FSI results may inform tuning, edge-case references, or future research, but they do not replace the custom C++ water solver without a separate milestone decision.

## Reason

The simulator needs deterministic, budgetable water behavior for desktop, VR, handheld, replay, networking, and Unreal integration. Full particle/fluid-solid coupling may be useful for research, but it is too heavy and installation-specific to anchor the first production runtime.
