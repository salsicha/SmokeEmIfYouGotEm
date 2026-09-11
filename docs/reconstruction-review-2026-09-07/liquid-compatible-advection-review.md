# Compatible particle transport — September 9, 2026

South Fork is incomplete. This is an opt-in primary-transport experiment, not
the selected playable water or a successful physical roller reconstruction.

## Why the grid check was insufficient

New exact interpolation-derivative checks distinguish the quadratic APIC
moment C from the point derivative of the interpolated velocity. Synthetic
finite differences verify both tent and quadratic derivatives. A centered-grid
checkerboard mode has zero discrete divergence yet nonzero divergence under
the old velocity interpolation.

The actual tent capture has projected-grid divergence RMS 0.026740 /s but
0.894675 /s at particle samples with fully fluid interpolation support. For
the quadratic particle-only capture these values are 0.022360 /s and
0.133473 /s. The latter is a substantial reduction, not elimination. The
instantaneous Euler-map Jacobian ranges 0.8773–1.1416 in the tent interior
and 0.9784–1.0163 in the quadratic interior. These are local kinematic volume
ratios, **not measured accumulated mass loss**. Inputs and hashes are retained
in each capture's `advected_divergence.json`.

## Implemented candidate

`RaftSimLiquidCompatibleAdvection` requires quadratic APIC. For trajectory
integration it averages adjacent collocated velocity components onto faces
and applies cubic interpolation normal to each component and quadratic
interpolation transversely. The equivalent compact normal kernel is
K(r) = [B3(r-.5) + B3(r+.5)] / 2. Its derivative is
[B2(r+1) - B2(r-1)] / 2, so continuous divergence equals quadratic
interpolation of the existing centered-grid divergence on complete support.
The five-point component-support union requires 81 grid reads per evaluation.
Midpoint integration uses two evaluations; incomplete support or solid-parent
samples retain the existing integration and are explicitly recorded as fallback.

The B-spline derivative-chain principle is also used in the primary paper
[Local divergence-free polynomial interpolation on MAC grids](https://www.sciencedirect.com/science/article/am/pii/S0021999122005629).
That paper is about MAC grids; the adjacent-face averaging above is a local
adaptation for this collocated fixture, not a claim that it implements the
paper's complete solver. No surveyed bed, forcing or pressure operator changes.

Existing APIC stored velocity and C are retained. This is deliberately a
trajectory experiment, not a new proof of global momentum/energy conservation.
**Foam and secondary transport still use the previous interpolant.** Therefore
this flag must not be promoted as a consistent river-flow solution. Any retained
version needs matching flow consumers and boundary/contact validation.

## Actual engine evidence

`liquid-compatible-advection-motion` completes 12 s under RHI validation.
Actual precontact positions, transport velocities and fallback status are
captured alongside the independent grid and initial sampling coordinates.
57,549 of 59,338 particles use the new midpoint path; 1,789 take the documented
fallback. Independent replay matches every mode selection; maximum velocity
error is 0.001791 cm/s and position error 0.00006699 cm, within predeclared
0.05 cm/s and 0.01 cm tolerances. No fitted scale or relaxed threshold.

All 714 simulation dispatches/GPU clock increments are accounted for. Live
positions differ by at most 0.000001630 m; 30 captured frames are distinct.
The existing active/paused foam calculation passes its own unchanged reference,
which does not prove that it agrees with the new primary interpolant. The
capture has no engine errors. The water remains rounded and finely rippled,
and does not show the intended strong returning roller. Selected-pool reverse
velocity fraction is 0.00310; this is not a visual/physical acceptance result.

`wet_sections.json` measures actual SDF intervals above the registered bed,
including disconnected liquid. Across x=-9..9 m, downstream velocity-area
integrals fall from about 40.6 to 29.5 m³/s, with substantial lateral flow.
Aggregate section Froude proxies are below one, but these full-width oblique
sections are **not** a local hydraulic-jump calibration or a mass budget.
Do not raise tailwater using a rectangular-channel formula from these values.

## Verification and disposition

- 180 numerical liquid tests pass, including derivative finite differences,
  the exact divergence relationship, affine preservation and midpoint rotation.
- Editor build succeeds. An initial diagnostic variable-name compile error
  (`FixtureTransform` instead of the existing `Transform`) was corrected.
- Latest engine suite: 16 successful tests, one with a recorded HTTP
  connectivity timeout warning; zero failed/not-run tests. See
  `engine-liquid-compatible-advection/index.json`. Do not call it warning-free.
- Uninterrupted benchmark: 480 intervals, mean 25.586 ms, p95 27.657 ms,
  maximum 93.023 ms (spike retained). Reconstruction GPU mean 5.240 ms excludes
  Niagara particle-update cost. This is about 0.46 ms slower in mean editor
  interval than the preceding particle-only run, not a full-scene FPS result.

Keep the particle-only surface fix; leave compatible advection experimental.
No long-run/production promotion is justified by this visual result. Next work
must reconnect the physical shape to the reference river: verify named-rapid
landmarks against the captured imagery/returns, review the inferred submerged
control and native boundary forcing, then validate the resulting crest/roller
and playable geometry together. If this transport path is retained, unify foam
and secondary velocity sampling before acceptance. No force/bed changes were
made merely to obtain a more dramatic image.

Online research found an American Whitewater trip report with named Troublemaker
photos and the existing hazard reference, but direct retrieval returned 403;
their search metadata is not new visual registration evidence. Existing source
data and unresolved identity/bathymetry limitations remain authoritative.
No saved production asset promotion or commit; the complete queue remains active.
