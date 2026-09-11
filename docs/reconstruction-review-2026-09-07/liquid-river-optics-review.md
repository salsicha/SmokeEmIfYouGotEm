# South Fork optical comparison — September 9, 2026

Actual engine captures, not generated illustrations. Isolated, unsaved liquid
review; South Fork and the full reconstruction queue remain incomplete.

## Cause and change

Runtime material inspection found absorption RGB `(0.6, 0.05, 0.02)` multiplied
by alpha `0.056`: effective coefficients `(0.0336, 0.0028, 0.00112)` per cm.
Together with neutral scattering `0.001 /cm`, this strongly suppresses red and
produces the cyan cast. The source material graph confirms the RGB-times-alpha
operations; these are optical coefficients, not display-color values.

The new transient-only `RaftSim.LiquidTerrainExtinctionControl` exposes explicit
absorption/scattering RGB and roughness. It does not alter density, surface shape,
particle state, foam coverage, lighting or camera. Source assets are unchanged.

`liquid-river-extinction-sweep` compares three spectra at roughness 0.12, 0.22 and
0.35, all with exposure bias -10, the same camera and frozen water. The independent
audit verifies **identical complete captured simulation state across all nine
cases**, actual material coefficients, opacity zero, foam strength one and image
hashes. RHI validation reports no engine errors. The coefficients below are
authored visual hypotheses, **not measured South Fork turbidity**.

| Spectrum | Absorption RGB, /cm | Scattering RGB, /cm |
| --- | --- | --- |
| Inherited cyan | 0.0336, 0.0028, 0.00112 | 0.001, 0.001, 0.001 |
| Muted green | 0.003, 0.0018, 0.0022 | 0.0002, 0.00025, 0.00022 |
| Neutral turbid | 0.004, 0.0035, 0.0038 | 0.0005, 0.00055, 0.0005 |

The muted-green case at roughness **0.22** is selected for continued review. It
reduces the cyan cast and razor-like highlights while retaining dark green
troughs. Roughness 0.35 broadens the highlights further but looks softer/waxier;
the neutral-turbid case looks too gray/brown in this lighting. This is a visual
judgment against the user's real whitewater reference, not a colorimetric match
between differently exposed cameras.

Inherited, same frozen geometry:

![Inherited optics](liquid-river-extinction-sweep/optics_00.png)

Selected optics, same frozen geometry:

![Muted green, roughness 0.22](liquid-river-extinction-sweep/optics_04.png)

## Motion and regression evidence

`-RaftSimLiquidTerrainRiverOpticsMotion` applies the selected profile during
simulation, not only for a paused screenshot. `liquid-muted-green-motion` verifies
714 first-stage dispatches, reconstructions and positive GPU time steps over
12 seconds; final GPU age 12 versus independent 11.999989 seconds. Actual live
positions, finite fields and active/paused foam transport pass. Coverage error
remains 0.00048828125 with unchanged tolerances. Thirty distinct frames show
moving flow and splashing; this does not establish physically calibrated motion.

160 numerical tests pass. All 15 latest-binary engine liquid regressions pass
without test warnings/failures in `engine-liquid-current-optics-validated`, with
RHI validation. The material comparison's actual runtime coefficient audit is
separate from that engine suite. The earlier per-step benchmark remains an
isolated cost measurement, not performance acceptance for this optical variant.

## Not accepted yet / next work

The green water is still gelatinous: rounded reconstructed fragments, overly
regular small ripples, coarse breaking sheets and rectangular fixture faces are
visible. The supplied real reference has irregular dark troughs, thin spilling
crests, piled aerated water and finer airborne spray. Changing color does not
repair those geometric differences.

Continue with primary free-surface/fragment geometry, physically supported
hole/roller flow and source/outlet accounting. Preserve the current-stage
synchronization and foam transport fixes. Do not conceal coarse geometry by
turning up foam, flattening normals, or adding a second surface. Then integrate
into continuous playable water and test shoreline, raft/current, boulders and
whole-scene cost. Colorado -> Pacuare -> Futaleufu and remaining rivers/crew/
cleanup/release are still pending. No production promotion or commit.
