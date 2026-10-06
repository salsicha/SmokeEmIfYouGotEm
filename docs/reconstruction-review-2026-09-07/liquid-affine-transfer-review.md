# South Fork affine transfer and froth transport — September 9

Status: working **isolated candidate**, not production or scene acceptance.
South Fork and the complete queue remain open. The registered map, saved
contact system, terrain source and hydraulic boundaries are not replaced.

## Implementation and execution evidence

The previous control-centred 60 s capture had almost no resolved pool return
flow: four of 1,673 fluid cells in the selected pool box moved upstream faster
than 0.05 m/s. The prescribed outlet stage was correctly applied; its absence
was not the cause. The new `analyze_liquid_pool_circulation.py` records submerged
cells as well as the surface, without interpreting a single snapshot as a
complete hydraulic-jump measurement.

`RaftSimAffineTransfer.h` adds persistent local velocity-gradient columns to
particle/grid transfer. It uses trilinear values and analytic weight derivatives,
following a collocated adaptation of the fluid formulation in
[Jiang et al., APIC (2015), equations 13–14](https://media.disneyanimation.com/uploads/production/publication_asset/104/asset/apic-aselle-final.pdf).
There is no noise force, FLIP increment or changed discharge/stage. This is not
the paper's MAC grid, nor proof of conservation through this implementation's
contact and open-boundary operations. The numerical transfer tests cover
affine-field reproduction, repeated stationary-sample rotation, linear momentum,
anisotropic cells and grid-face/node sampling.

The first installation failed because recursive UObject enumeration included
two contact graphs. Selecting `GetLatestSource()` removed that ambiguity but
was **wrong**: the Niagara function call pins an older version. An actual GPU
capture showed every gradient and sample position still at its spawn default.
The working installer follows `GetFunctionScriptSource()` on the function call.
It also uses the verified grid API `GetPreviousVectorValue`, not the nonexistent
`GetPreviousVector3Value`. The capture now requires both transfer markers in
the actual compiled GPU shader. Shader dumps are decoded as UTF-16 when marked
with that BOM, not the Windows default text encoding.

Persisted GPU gradient columns and their pre-advection world/unit sample
positions are read through SimCache. `audit_liquid_affine_transfer.py` replays
the gradient from an independently captured velocity grid and validates the
sample coordinates against the actual captured transform. Using an ideal
inverse instead of Unreal's stored float matrix gave incorrect boundary-cell
comparisons; no audit tolerance was increased to hide them. In the verified
60 s capture, sampling-coordinate error is 8.35e-8 unit coordinates, maximum
gradient error is 2.80e-6 /s, and unsupported gradients are exactly zero.

## Actual 12 s and 60 s results

The first real affine run produced substantial motion and foam, unlike the
inactive-gradient capture. `liquid-affine-sample-unit-12s` verifies 50,663
nonzero gradient states among 51,605 primary particles. All are finite and
the exact terrain probes find no primary penetration. Secondary contact fails:
67 particles penetrate the bed, up to 12.59 cm.

Stronger foam exposed another real interpolation error: hardware filtering of
the half-float velocity/history textures made the active coverage audit fail
(0.003662 coverage error in `liquid-affine-selected-api-12s`, tolerance 0.001).
`RaftSimLiquidFoam.usf` now performs explicit float32 trilinear interpolation
for RK2 midpoint velocity and advected history, as already done for the source
stencil. It does not change the source threshold, gain, decay or physical field.
A new actual-GPU high-contrast history test covers this failure.

`liquid-affine-float-transport-60s` completes 3,630 live reconstruction updates
and 30 distinct motion frames after 3,600 simulation steps. The active foam
audit passes: coverage error 0.00048828125, source error 4.51e-6 /s, history
error 4.54e-6, exact paused coverage and unchanged distance/clock channels.
Actual GPU position readback matches reconstructed input within 1.45e-6 m.
There are no engine error lines.

At 60 s the primary population is 69,598, with no nonfinite state or exact-bed
penetration; 91 particles are outside the physical exchange region pending
retirement. Median/p95/p99/max primary speeds are 1.016/4.124/5.488/7.679 m/s.
These values do not by themselves establish measured discharge, physical
volume conservation, hydraulic-jump accuracy or long-duration stability.

In the fixed pool box, 5.72% of 1,258 fluid cells move upstream faster than
0.05 m/s, versus 0.239% in the baseline. There is appreciable rising and falling
flow. This is evidence of changed circulation, **not proof of a correctly
positioned and sized returning surface roller**. Pressure/stage readback still
matches prescribed stage classification; final divergence RMS is 0.02629 /s.

Secondary failures remain substantial: 29,958 particles, 73 bed penetrations
(maximum 11.95 cm), and 1,354 of 10,746 classified spray particles inside the
current rendered surface in the paused sample. The shared surface is an exact
copy but is consumed one step late. No surface-coupling acceptance is claimed.

## Appearance and cost

Inspected actual engine `motion_020.png` at 12 s and 60 s and the user's supplied
real whitewater reference `codex-clipboard-d8abf384-5a0e-44a3-8de0-1baee54963ed.png`.
The candidate now has piled, detached splashes and a coherent white region,
rather than only a smooth sheet. It remains cyan/glossy, with rounded blobs,
overly similar small-scale ridges, insufficient dark troughs and unresolved
crest shape compared with the reference. The rectangular edge and untextured
terrain belong to the bounded diagnostic; this is not a playable-scene capture.
Sampled top-interface mean coverage is 0.2143 (baseline 0.00922), which is an
internal field statistic, not photographic foam coverage.

`liquid-affine-float-transport-benchmark` verifies 480 uninterrupted editor
intervals: mean 25.928 ms, p95 27.904 ms, max 29.253 ms. Earlier baseline mean
was 23.442 ms. Reconstruction GPU mean is 5.301 ms, of which density is 4.549,
distance 0.581 and foam/copy/cache 0.171 ms. The GPU timings exclude Niagara's
primary/secondary simulation cost. This is a roughly 2.49 ms editor-frame
regression, not a packaged-game or whole-scene performance pass.

## Checks and retained failures

- 136 numerical liquid tests pass, including rejecting zero/inactive/transposed
  affine states and testing exact GPU sampling coordinates.
- All 14 engine `RaftSim.Editor.LiquidFixture` tests pass in
  `engine-liquid-affine-foam-transport`; the foam test contains 15 analytic cases.
- Active gradients, live reconstruction and active/paused foam checks pass
  in `liquid-affine-float-transport-60s`.
- The full secondary-contact/surface audit fails; its command's successful
  export exit code is not acceptance.
- `liquid-affine-transfer-v1-12s`, `v2-12s`, `v3-12s`,
  `liquid-affine-transfer-state-12s`, `liquid-affine-selected-version-12s`,
  and `liquid-affine-selected-api-12s` remain as failed/incomplete evidence.
  `affine_audit_utf16.json` corrects the first auditor's shader-decoding error
  without replacing its failed report. The earlier no-sampling-coordinate
  gradient comparison is likewise retained, not relabelled as passing.

## Next required work

1. Secondary terrain contact: the current five-point coarse boundary-grid
   check misses the true bed between voxel centres. Use the same registered
   triangle surface as primary contact, with swept checks and explicit domain
   handling; do not delete primary water to conceal penetration.
2. Correct secondary classification/projection against the current surface,
   addressing one-step lag at higher speeds. Recheck cost as well as contacts.
3. Review physically plausible hole/crest shape, source/exit mass accounting
   and station-dependent velocity/depth. Keep uncalibrated submerged bed and
   unverified rapid identity explicit. Do not just raise whitening gain.
4. Improve optics and surface detail against real references, integrate into
   the single playable water surface with continuous shoreline/raft support,
   then measure full-scene performance and complete South Fork acceptance.
   Continue Colorado → Pacuare → Futaleufu and the rest of the queue afterward.

No production promotion or commit is justified by this diagnostic milestone.
