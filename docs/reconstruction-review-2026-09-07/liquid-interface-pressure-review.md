# Native evolving-interface pressure — September 11

The actual twelve-region South Fork simulation now has an opt-in connection
between its retained surface, water/air classification and pressure gradient.
It runs beyond the previous step-641 failure through native step 1800. This is
implementation progress, **not physical, visual, performance or scene acceptance**.

## What changed

`-RaftSimRegionalInterfacePressure` requires the already verified continuous
interface transport, dense actual river, parent exterior and paired projection
capture. Saved scenes/defaults are unchanged.

- The existing stage data interface exposes a read-only R32 current surface.
  A render-thread binding selects the owner's newest graph-local state. It does
  not advance the scalar from a material clock or create a second visible layer.
- The active RegisteredTrianglePressureBoundary graph uses negative phi for
  water and nonnegative phi for air. Registered solid and prescribed exterior
  types retain priority. Native boundary halo exchange remains unchanged.
- Pressure coefficients and the final velocity gradient use the same subcell
  wet/air distance. In the existing centred two-cell stencil, the wet-to-air
  coefficient is multiplied by `(phi_air-phi_water)/(-phi_water)`. It is not an
  unrelated nearest-cell Laplacian. External air has zero gauge pressure.
- The pressure solve sees the pre-transport interface; transport uses that
  step's actual projected velocity and immutable fluid timestep afterward.
  The selected pre/post pair remains frozen for readback even when additional
  native ticks are enqueued before stopping. Those additional ticks still
  transport the live pressure-coupled surface rather than freezing its physics.
- The offline pressure reconstruction now uses the captured pre-transport
  scalar and actual tick delta for coupled captures. It checks every captured
  fluid/air classification, then reconstructs the weighted velocity correction.
  The new coverage diagnosis compares the pre-transport scalar to the same-step
  P2G positions and exact registered bed; it does not relabel exceptions as spray.

The scalar is not a signed-distance field; the pressure weights use local
implicit zero crossings. Fixed initial outer XY and two Z edge layers remain
provisional. Particle correction and consistent physical boundary evolution are
still required. No threshold floor, deletion exception or looser exit rule was
introduced to make the runs pass.

## Integration failures retained

Build 67356 succeeded. The first native run (96430) crashed while the installer
allocated nodes during UObject hash enumeration. Node selection and creation
were separated. Build 17521 succeeded; native startup-v2 (8929) then rejected an
older graph version without the active boundary bindings. The installer now
selects the active `GetLatestSource()` graph, matching the contact installer.
Build 28452 succeeded. The first successful native capture is startup-v3, not
either earlier failure.

Build timings: 67356 107.85 s; 17521 26.18 s; 28452 26.67 s;
85009 37.97 s. The last build corrects a regression assertion to use Niagara's
observed translated `Out_RetBoundary` output name, not the source identifier.
It does not change the predicate or weaken the solid/exterior priority check.

## Actual native results

| Capture | Native step | Particle count in paired P2G | Native post-pressure divergence RMS (/s) | Reconstructed velocity RMS error (cm/s) |
| --- | ---: | ---: | ---: | ---: |
| `liquid-native-interface-pressure-startup-v3` | 12 | 729,654 | 0.000676306 | 0.0411835 |
| `liquid-native-interface-pressure-600` | 600 | 727,585 | 0.000435616 | 0.0137975 |
| `liquid-native-interface-pressure-30s` | 1800 | 757,610 | 0.000446368 | 0.0119959 |

Native sessions 23555, 90485 and 95413 exited successfully with complete captures
and empty exchange errors. Full independent particle/P2G audits passed all
three captures with zero reduction mismatches, zero survey/native-float
internal owner disagreements, and unchanged physical exterior bounds.

For step 600, the scalar audit verifies all 599 transports and 982,407,920
updated samples; paired final-step error is at most 0.000505794 cm. At step 1800,
all 1799 transports / 2,950,503,920 updates pass; final-step error is at most
0.000585548 cm. Both full-grid comparisons cover 2,178,720 samples and all
internal halo addresses. Actual fluid/engine delta is 0.01666666753590107 s;
elapsed transported time is 9.983333854 / 29.983334897 s. No rejected trace or
nonfinite sample appears in either ledger.

The previous uncoupled run lost 590.604167 m3 through its 598 compact commits.
The pressure-coupled step-600 run loses 45.333333 m3 through the same number of
commits: 22,496 births and 24,672 approved exits. This short-window improvement
is real, but **must not be reported as solved drainage or steady discharge**.

At step 1800, all 1798 compact commits succeed, with 67,639 births and 39,791
approved exits. Net nominal storage is **+580.166667 m3**. Final interval outflow
falls to about 5.431 m3/s versus 47.047 m3/s prescribed source injection. This
is unresolved accumulation, not acceptable equilibrium. The native density
maximum rises from 12.515 to 65.264 times a cell's nominal volume; particle
clumping/volume consistency remain open despite the small grid divergence.

## Particle/surface consistency

The coverage checks use matching pre-pressure scalar and P2G particle times,
not a later transported surface against earlier particles. Both samples have
zero invalid interpolation stencils and no particle centres below the exact
registered bed.

- Step 600: 1,120 of 727,585 particles (0.153934%) are outside the scalar surface.
  53 of those are within 25 cm of the bed. Largest positive scalar is 43.0438 cm.
- Step 1800: 8,435 of 757,610 (1.113370%) are outside; 104 are within 25 cm of the
  bed. Largest positive scalar is 44.0332 cm.

Those scalar values are not true geometric distances. The outside particles
are not automatically spray, and near-bed exceptions cannot be dismissed as
whitewater splashes. Correct retained surface/particle consistency and volume
behaviour before using the surface for visible reconstruction.

Maximum subcell pressure weight is 26,343 at step 12, 244,785 at step 600 and
326,374 at step 1800. No arbitrary weight cap was applied. The native solver
remains finite in these runs; conditioning still needs ongoing verification.

## Regression and next action

399 Python liquid tests pass. The first engine suite (`liquid-interface-pressure-engine`)
had 18 clean successes, one success with a Google connectivity timeout warning,
and one failed compiled-name assertion in LiquidRegionalExterior. The assertion
was corrected after inspecting the actual compiled native shader. The rerun
is recorded separately in `liquid-interface-pressure-engine-v2`.
That rerun (60184) completed with **20 clean successes, zero failures and zero
warnings**. All native runs, builds and audit sessions described here are
terminal; no engine/build process remained at the final check. Scoped whitespace
checks are clean. The previous goal turn was progress; this turn adds the
actual native pressure coupling and its longer-run evidence.

Next: correct persistent particle/interface/volume drift and diagnose the
collapsing outgoing flux using these paired native fields. Do not substitute
global water-level inflation, silent particle deletion, or a density cutoff
already shown to lose shoreline water. Then connect one visible surface,
breaking foam and spray, and validate real motion and playable GPU cost.

No beauty captures or FPS measurements were produced in this pass. The saved
review map SHA256 remains
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
No scene acceptance, production promotion, final commit or push. South Fork,
Colorado, Pacuare, Futaleufu and the rest of the full goal remain incomplete.
