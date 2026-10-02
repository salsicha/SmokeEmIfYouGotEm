# Eddy: fractional-boundary controls

October 1 continuation of the newer isolated-water-feature goal. All eight
features and eventual river integration remain unfinished. Neither new
candidate is accepted; preserve the standard padded scene and all old work.

## Visible delivery

`feature.png` is a verified two-second lossless APNG: 24 frames at 12 fps,
1920 x 476. It compares standard padded FLIP, native fractional default
clearance and fractional zero clearance at frames 145..191, stride 2.
Physical playback speed is unchanged; the restart is not a seamless loop.
Each caption explicitly distinguishes the fixed frame-192 volume measurement
from the currently displayed frame's surface-contact measurement.

72 actual 640 x 360 Cycles/OptiX views were rendered at 24 samples with fixed
seed/denoising, identical camera/lights/transparent water IOR 1.333/transmission/
absorption. The domain/particle display is hidden in favor of the actual
copied 2x fluid/obstacle zero-field geometry; every copied vertex is checked
against its float32 engine readback and every triangle index is unchanged.
No surface clipping, smoothing/displacement or invented foam is applied.
All liquid bounds fit the camera. Bright highlights are reflections, not foam.

First/middle/last actual views of each control and the composed frame were
inspected. Every decoded animation frame matches its composed input exactly.
Adjacent mean absolute RGB changes, excluding captions, range 0.881..1.147
for standard, 0.456..0.600 for default clearance and 0.787..0.908 for zero.
All three surfaces move. Default clearance visibly suppresses downstream
surface motion; zero restores much of it but is still coarse/faceted and
physically unaccepted. Rendering took 356.25 seconds, not a real-time FPS
measurement. Clip SHA256:
`a4e966560d799c34d35237f39eb540d184dbffe193ab6a0850f378ab12ce3dc4`.

## What changed

Two new independent native FLIP simulations complete 192 DATA and stock MESH
frames. Both preserve the standard padded flume's authored collider/source
meshes, transforms, gravity, 75 mm grid, 80 x 21 x 42 allocation, FLIP ratio
0.95, adaptive bounds 2/8, radii and 24 fps. The first enables native fractional
boundaries with the installed default 0.5-cell artificial primary-particle
clearance (37.5 mm). The second changes only that clearance to zero. Zero is
not a fitted contact radius or a volume correction. Old caches are not edited.

Enabling fractional handling also changes the native implicit-domain-wall
convention. Identical authored geometry and allocation therefore do NOT imply
identical effective physical boundaries. This comparison is not isolated to
fractional pressure coefficients.

## Measured reason to reject a simple fractional toggle

Read-only cached obstacle profiles at frames 1 and 192 locate the same wall
zeros in the dry region above the authored solids and at a submerged section
downstream of the bank spur:

| Cached zero surface | Standard padded | Both fractional controls |
|---|---:|---:|
| Left/right domain walls, x | 0.044318 / 5.955682 m | 0.150000 / 5.850000 m |
| Lateral domain walls, y | -0.743182 / 0.743182 m | -0.637500 / 0.637500 m |
| Downstream authored bed, z | approximately 0 m | approximately 0 m |

Each closed side moves inward about 105.68 mm, narrowing the effective
lateral span by 211.36 mm. These are interpolated cached-field crossings,
not a claim that the standard coarse wall is an accurate signed-distance
representation. The standard wall values jump from -0.5 to +5 cells near
the border; fractional values span -1.5, -0.5, +0.5. The bed remains in place.
The profiles establish unequal boundaries, not a full 3D pressure/conservation
proof or exact attribution of every cubic metre of volume difference.

| Reconstructed liquid field volume | Standard | Default clearance | Zero clearance |
|---|---:|---:|---:|
| Frame 1, eight subdivisions | 3.183864 m3 | 2.667977 m3 | 2.668602 m3 |
| Frame 192, sixteen subdivisions | 3.409251 m3 | 1.785449 m3 | 2.898272 m3 |
| Supplied-field lower/upper bounds, frame 192 | 3.352834..3.484308 m3 | 1.740208..1.855552 m3 | 2.843296..2.976219 m3 |

The default late volume is 47.6% below standard; zero clearance is 15.0%
below standard. The standard-minus-zero gap is already 0.515263 m3 in frame 1,
versus 0.510980 m3 at frame 192. Removing artificial clearance recovers much
of the late field volume, but does not make the initial/effective boundaries
equivalent. These are integrals and rigorous bounds of supplied trilinear
liquid/obstacle fields, NOT conserved mass or spatial CFD convergence. All
nine requested frames and all 54 interface-column statuses are retained.

## Contact failures are in the solver representation, not only rendering

The standard padded authored-contact probe checks actual native primary
points, field-mesh vertices and triangle centers at frames 145, 169 and 191.
At frame 145 a slope point lies 8.588 mm inside the authored bed while the
interpolated obstacle value is almost zero; a bank point lies 14.801 mm inside
the authored spur while the obstacle value is positive. A derived spur vertex
lies 19.446 mm inside the authored rock at almost zero obstacle value.
Refining extraction cannot repair a rounded/mislocated native obstacle field.

All 1,123,852 default and 595,713 zero-clearance primary records are independently loaded from native
cache arrays and matched to Blender's actual displayed positions and RAW
velocity convention. No culling/projection is used. New-point flag 1 is not
a deletion flag; all point records are retained. Native step instructions
are captured in `authored-contact.json`; resampling later in the step is a
possible contributor to small floor residuals, not a proven complete cause.

| Worst sampled primary-center intrusion, three frames | Default clearance | Zero clearance |
|---|---:|---:|
| Authored floor | 0 mm | 0.220 mm |
| Authored approach bed | 0 mm | 8.624 mm |
| Authored bank spur | 0 mm | 27.545 mm |

Default point-center clearance passes those sampled contacts only by keeping
particles away from the boundary; it does not validate the liquid surface or
hydraulics. Zero clearance restores contact errors. Neither is promoted.

Each new control has 30 derived meshes: 24 animation-cohort frames at 2x,
plus 1x/4x at frames 145, 169 and 191. All pass closed-edge/nonmanifold-edge/
exact-zero-area checks after exact duplicate-coordinate cleanup only. All
30 in each control FAIL sampled authored contact: floor 0 mm, approach
8.139 mm and bank spur 20.833 mm at 2x/4x. Tests use vertices and triangle
centers of closed solids with 1 micrometre tolerance; they are not exhaustive
triangle intersection/self-intersection checks. Stock particle-mesh contact
is also audited, not silently promoted as a repaired final surface.
Default-clearance interface columns [20,12], [40,9] and [48,9] are ambiguous
at frames 157, 159 and 161 respectively, leaving 53 supported columns in
those frames. All requested statuses are retained, not interpolated away.
All other default-cohort frames and all zero-clearance extractions retain
54 supported columns. This is interface support, not hydraulic acceptance.

## Correction to diagnostic velocity units

The first raw paired volume reports mistakenly used native velocity / 80,
which matches Blender's raw displayed velocity normalization, not physical
metres per second. Their volume integrals are unaffected; their section
m/s and m3/s labels are wrong by a factor of 15 and must not be used as-is.
The old particle audit's `maximum_velocity_component_error_mps` key likewise
describes a raw API-coordinate match, not independently physical speed.
This corrects that interpretation without rewriting preserved old receipts.

Use `default-volume-qualified.json` and `zero-volume-qualified.json` here.
The physical MAC conversion is 0.075 m/cell times 2.5 native seconds per
physical second = 0.1875 m/s per native grid unit. It is derived from cell
and C01 clock conventions, not fitted to the flume. The existing independent
installed-build FLIP calibration infers 0.1871783 (0.17% difference, 0.2921%
gravity error); this verifies the unit convention, not these full hydraulics.
Every one of 180 face/quadrature estimates in EACH paired report is freshly
reintegrated from its pinned native arrays with the correct conversion;
maximum difference from the corrected value is below 6e-16. No cached
velocities, sources, positions, geometry or physical time are changed.

At frame 192 the five standard section fluxes are approximately
0.4303, 0.3955, 0.5013, 0.5655, 0.4985 m3/s. Default-clearance fluxes are
0.3932, 0.1860, 0.0857, 0.0722, 0.0664; zero-clearance fluxes are
0.3935, 0.3225, 0.5067, 0.5394, 0.4586. These partial reconstructed-field
sections are diagnostics, NOT a closed source/drain conserved-flux budget.
The two wrong-unit raw reports remain preserved in the original C: artifact
root and are explicitly superseded for velocity/flux units.

## Reproduction and scope

Scripts in `unreal/Scripts/`: `build_water_feature_padded_fractional.py`,
`build_water_feature_padded_fractional_zero.py`,
`probe_water_feature_authored_contact.py`,
`audit_water_feature_padded_fractional_volume.py`,
`qualify_water_feature_padded_flux_units.py`,
`probe_water_feature_fractional_walls.py`,
`render_water_feature_fractional_controls.py` and
`encode_water_feature_fractional_controls.py`. Existing frozen native mesh
and primary-audit helpers are reused unchanged. Native particle methods need
the exact control source opened with Blender `-b` before importing manta.
Do not monkeypatch classes or reopen a different scene after native import.

Native Blender build is 5.2.0 LTS fbe6228777e7. Default DATA took 58.15 s,
guarded stock MESH 36.37 s; zero-clearance DATA 45.80 s and MESH 30.67 s.
These are offline timings with verification overhead, not game FPS. Cache
warnings about preferences/OptiX do not prevent the successful jobs; no
broad permissions or cache deletion is attempted. All geometry is synthetic
authored laboratory geometry, not a measured river or underwater survey.
No new captured imagery/data/license is invented or bundled.

This delivery includes the animation and sixteen hash-verified reports;
large native caches/mesh arrays remain in their original artifact directories,
not copied into the repository. The standard reference reports/clip remain
unchanged in `../eddy-padded-bed-comparison-v1/`. Existing 156 pure numerical
tests pass; eight new/continued Python files compile with SyntaxWarning as
an error. These checks are not physical or visual acceptance.
Independent final verification rehashes all 3,144 unique pinned dependency/
output paths across the sixteen reports with no conflicts or changed files;
the delivered animation hash matches. All owned Blender jobs have finished.
No Git history, branches, refs or remotes are changed in this continuation.

All accepted-feature requirements remain open: consistent authored/solver/
rendered contact, matched boundaries, conserved budgets, settled circulation,
spatial/time convergence and realistic foam/froth/optics. No playable game
scene/build change or 20 FPS claim. Next qualify explicit physical wall/bed/
spur representation independently of implicit border seeding, then apply a
coupled native repair; do not radius-fit, cosmetically clip the surface or
repeat these unchanged rejected toggles. Keep the newer isolated-feature goal
active and preserve every old clip/cache/receipt.
