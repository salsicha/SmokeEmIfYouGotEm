# Captured-terrain liquid sources — September 8

Status: actual GPU terrain coupling is now exercised, but **not accepted**.
No production promotion, saved-level change, calibrated discharge claim, or
photorealism/performance completion. The full remaining-work goal stays active.

## Implemented

- `build_south_fork_liquid_sources.py` conservatively distributes each audited
  native 1m numerical face flux over eight wet subfaces of the exact bed.
  It samples the actual bed 1cm inside each boundary, rejects dry/nonzero flux,
  and produces 16 vertical quadrature points per incoming wet subface.
- All incoming native faces have wet support. Maximum subface discharge error
  is 8.88e-16m3/s. Numerical inflow is46.7796170744m3/s; it is **not a measured
  real-world discharge**. Minimum quadrature bed clearance is0.270mm, far below
  the32.8125cm fluid grid. That underresolution is not an acceptance pass.
- New saved `NS_SouthForkLiquidTerrainReview` uses4496 matching positions and
  velocities. A single per-particle weighted alias-table selection supplies
  both arrays, with no per-particle linear search. Source weighting is exact
  in expectation, not a claim of finite-sample exact discharge.
- Nominal rate5296.61848particles/s uses cell volume/4. Actual FLIP particle
  volume, retained mass, outgoing stage and feedback remain uncalibrated.
- Enables the exact terrain mesh SDF, opens four horizontal boundaries and
  adjusts the existing escape-retirement box to21x21x8m. Disables only the
  two connected spawn-stack fluid-overlap rejection modules. Does not disable
  solid-boundary rejection or silently count deleted water as outflow.
- GPU readback now measures the correctly rotated local domain and ray-tests
  every in-domain particle against the exact collision solid. The collider
  remains registered but is excluded from main/depth passes to avoid drawing
  a duplicate terrain top. Original terrain is retained.

Source profile SHA256:
`9f22093c41de2a7ba0fd13575b657dfd7515c4d6932d8f477fc04f7cbe69a4a0`.
Saved system SHA256:
`49be4cc378eca13c1ef2a28742fc82d276d879d7a8af4c43f5c142018209d9e1`.

## Actual GPU comparison

Both runs use an unsaved `SouthForkRegisteredRockPlayable`, fixed1/60s manual
steps, actual GPU sim-cache readback and exact registered terrain. No gameplay
traversal or frame-performance result is inferred from this editor harness.

| Time | Terrain on: particles | Below bed >1mm | Below bed >one cell | Maximum penetration | Collision off: below >one cell |
|---|---:|---:|---:|---:|---:|
|4s|2599|118|2|168.52cm|1261|
|8s|2599|113|4|160.84cm|1285|
|12s|2601|112|1|35.76cm|1248|

Sources: `liquid-terrain-yaw-runtime` and `liquid-terrain-no-collision` particle
JSONs. All terrain-on samples have finite position/velocity, zero escaped
particles and zero missing bed probes. At12s, centre/downstream particles move
downstream on average. This proves a terrain interaction, **not correct mass,
stable bed separation, developed whitewater, or water/raft consistency**.
Most retained particles remain near the inlet and only about2600 remain despite
continuous emission. Particle loss needs accounting before hydraulic acceptance.

The actual compiled terrain shader is retained under
`liquid-terrain-shader-runtime/compiled_shaders`. It confirms matching source
indices and values, domain-sized retirement, and a remaining simulation-stage
kill using rounded cell solid-mask classification (`Grid3D_FLIP_ParticleUpdate`
to `KillParticles`). This is a candidate loss mechanism, not yet a quantified
cause. Do not solve it by merely turning off solid collision or deleting flux.

## Verification and retained failures

- Eight Python unittest geometry/source tests pass (including signed flux,
  dry support and invalid subface widths). Builds71168/66964/17710 succeed.
- Engine suite89124: six clean successes, zero failures/warnings,7.16s.
  `engine-liquid-terrain-sources/index.json` verifies reloaded arrays, matching
  index links, one weighted selector, one visible renderer and actual mesh SDF.
- First factory34307 refused save because recursive name matching found three
  cull modules. Fixed by traversing only the active spawn parameter-map chain.
  Factory84674 saved successfully. Wrapper now checks the physical uasset too;
  an in-memory duplicated object alone was insufficient proof of a saved asset.
- First runtime42462 incorrectly used positional Rotator arguments and tilted
  the terrain. Retained `liquid-terrain-runtime` is invalid evidence. Corrected
  to explicit pitch/yaw/roll, with forward/up-vector guards.
- Correct-yaw runtime68962 completed. Lit42454 and collision-control25404
  completed; shader/exposure capture72573 completed. All sessions terminal.
- Images were actually inspected. Original editor light is3lux; the first
  captures are dark. The unsaved diagnostic light override/exposure combination
  overexposes initial captures. Bracketed lower views show a large blue vertical
  sheet, not a convincing river. SDF render transform/framing/optics require
  investigation; these images are **not** a visual pass. Do not present the
  bracket as photo-calibrated lighting or modify screenshots to conceal defects.
- Project descriptor and registered map hashes remain unchanged:
  `01b95fffdec2649864c397a9a7c786d083371e469efbace3505e0e0ae2ac3b44` and
  `81f31bec7ba8683e3a7479f17333419b6d32eeb277de5630f098d41fdf705ad7`.
  Scoped `git diff --check` passes. No commit yet.

## Next required work

Account for born/retired/solid-rejected particles and measure calibrated flux,
correct terrain penetration without losing prescribed inflow, establish outlet
stage support, verify the SDF render transform against particle bounds, and
obtain readable multi-angle motion. Then single-surface river blending, raft
support, foam/spray/optics and the original performance gates. Keep inferred
submerged-bed and unverified rapid-identity labels. No more sphere/tank work is
needed to establish the terrain question; this real captured patch now runs.
