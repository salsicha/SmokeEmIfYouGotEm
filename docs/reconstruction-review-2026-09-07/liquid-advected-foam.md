# South Fork: actual transported foam and single-surface optics

2026-09-08 local. **Implementation progress, not photographic/scene acceptance.**
The full completion goal and reconstruction sequence remain active. All changes
below are in an unsaved bounded review; no production asset promotion or commit.

## What changed

`RaftSimLiquidFoam.h` installs a separate scalar aeration field in the owned
Niagara candidate. The `foam` variant includes the existing full-vector inflow,
centered particle transfer, compatible projection, native outlet stage and exact
terrain contact. It does not alter those velocity/contact equations.

The foam model uses actual grid-local velocity to backtrace previous coverage,
with a four-second decay time. Local vorticity and horizontal compression drive
generation near the reconstructed surface; solid cells and the outer exchange
edge suppress generation. Combined source/decay is integrated analytically and
bounded to [0,1]. This is a heuristic aeration model, not resolved two-phase CFD
or calibrated photographic foam coverage.

History is read from `SimRT.g` in stage16, after X smoothing has produced the
current SDF. Stage17 writes the new coverage to green alongside distance in red.
Read/write are deliberately separate: engine source explicitly supplies a black
read texture when RenderTargetVolume is read and written in the same stage.

The optical candidate samples green at the **actual SDF ray hit**. Coverage blends
the same surface toward diffuse pale foam, higher roughness and opaque BSDF
response. No second surface or tiled foam texture is added. Normals always come
from distance gradients, transformed into world space; green is not a normal.
Zero foam strength is available as a same-frame control. Source material assets
are not modified.

## Failures retained and corrected

- `liquid-advected-foam-v1`: adding `RiverFoam` moved SDF to attribute slot1, but
  inherited Y/Z convolutions still read slot0. The final SDF became nonnegative
  foam-like values and the surface was invalid. `foam_audit_rejected.json`
  correctly fails the new signed-distance sanity check.
- v2/v3: the initial named-index override accidentally read its own downstream
  parameter map and caused Niagara compiler recursion/stack overflow. Logs are
  retained. Input reads now bypass the reused override set, and an acyclic graph
  guard rejects future back-edges before requesting compilation.
- v4: named SDF resolution restores signed geometry. However, foam remains at
  approximately one-step strength (maximum0.01945 at12s), not accumulated foam.
- v5 direct rendered-volume readback identifies **PF_R16F**, configured RTF_R16f.
  The inherited renderer silently discarded every green write. Scratch-grid
  success and compiled green assignments alone were insufficient evidence.
- v6 explicitly allocates RGBA16f history with interpolated volume sampling.
  Actual readback verifies both red and green exactly match their scratch fields.
  Foam now accumulates (maximum0.41724 at12s). The saved baseline remains intact.

The original broad storage test incorrectly included unused default DI objects
created by Niagara custom input metadata. Its failure is retained in
`engine-liquid-foam-optics`. The corrected regression checks the actual compiled
SystemSpawn binding named `SimRT`; runtime GPU readback separately verifies its
allocated pixel format and data, not just an object property.

## Sustained GPU evidence

`liquid-advected-foam-60s` completes3600 steps at1/60s, blend0.75 and pressure40.
Blocking correctness capture wall time93.58s is **not game frame time**.

| Actual measurement | Result at60s |
| --- | ---: |
| Particle count | 80,629 |
| Exact bed probes | 80,545 |
| Missing / penetrating probes | 0 / 0 |
| Nonfinite particle velocities | 0 |
| Mean particle speed | 90.760cm/s |
| Foam range | 0 to0.49463 |
| Nonfinite render-volume values | 0 |
| Renderer red vs SDF max difference | 0cm |
| Renderer green vs foam max difference | 0 |
| Highest top-crossing foam mean | 0.00942 |
| Highest top-crossing foam p95 / max | 0.05730 /0.19698 |

Highest crossings use all14,460 wet render-grid columns, including patch edges,
and linear interpolation of the vertical zero crossing. They are not projected
image coverage. The low top-surface concentration explains why a sizeable volume
maximum does not imply convincing surface whitewater.

Frozen `optics_00/01/02.png` use strengths0/1/4 with identical simulation,
camera, scattering0.001/cm, roughness0.12 and exposure−10. Strength1 changes78,614
pixels by more than one channel level relative to strength0; strength4 changes
100,450. The controls establish an active shading path, not calibrated realism.
Gain4 is a diagnostic, not a new production/default foam multiplier.

## Motion and visual review

Thirty actual engine images cover the final two simulation seconds at15fps.
`motion.png` is a lossless animated PNG assembled by `encode_liquid_motion.py`.
All decoded frames exactly match their hash-verified source RGB images; no
adjacent frames are duplicates. See `motion_report.json`. Playback rate is not
runtime performance. The reviewed individual frames show changing surface shape;
the image-change metric is not proof of physically correct foam trajectories.

Compared with the user's real-whitewater reference (the September screenshot
showing a raft approaching irregular dark troughs and breaking white crests),
the captured candidate is still glossy cyan and rounded/pillowy. Its visible
froth is insufficient, there is no convincing overturning crest/spray volume,
and the diagnostic window exposes rectangular exchange walls. The captured bed
also remains an untextured, angular diagnostic mesh. **Not photorealistic.**

## Verification and next work

- Build passes, latest16.23s.
- `engine-liquid-foam-optics-v2/index.json`:10 clean passes,0 warnings/failures,
  22.90s. Includes actual GPU compilation, named SDF channel binding, bound
  RGBA history/filter and single-surface material graph regressions.
- 44 focused `test_liquid*.py` tests pass, latest1.384s. Transport, reset,
  bounded generation/decay and invalid SDF rejection are covered.
- Saved Niagara asset, review map and `.uproject` SHA256 identities match the
  preceding checkpoint. No engine source assets changed.

Next: improve coherent free-surface reconstruction and free-surface aeration
rather than increasing a white multiplier. Measure where foam is generated vs
the top SDF crossing, and distinguish actual breaking flow from submerged shear.
The native/3D lateral exchange mismatch, calibrated storage, full-scene carrier
handoff, motion/performance and photographic acceptance remain open. Subsequent
Colorado/Pacuare/Futaleufu, other water, crew, cleanup and release work remain
queued; nothing in this report closes those tasks.

### Research informing the next aeration step

The authors' primary description of [Guided Bubbles and Wet Foam for Realistic
Whitewater Simulation](https://alexey.stomakhin.com/research/whitewater.html)
distinguishes submerged bubble transport from surface foam, converting bubbles
when they reach the surface and constraining foam motion to the fluid surface.
That supports separating these behaviors in the next prototype rather than
treating a passively advected volume scalar as a complete foam simulation. The
current code does **not** implement their coupled bubble/SPH foam method. The
linked26MB paper could not be fetched by the web reader; only the authors'
overview was inspected in this turn. No claim of a paper-faithful implementation.
