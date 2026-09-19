# South Fork prescribed exterior pressure-kinetic trace

Reviewed 2026-09-19 UTC. Supporting physics component only; no playable change.

The front-profile transport includes the original fan's exterior mass flux,
but its homogeneous pressure geometry reflects exterior velocity. These are
different boundary conditions. The new opt-in `FrontPrescribedTrace` supplies
the prescribed velocity contribution without changing the reflecting operator
or enabling the unfinished nonlinear runtime.

For each active original owner, the local kinetic jet is now
`(D v + b, vx, vy)`, where `b = sum(exterior integral(h u.n)) / V`.
The original local Gram forms therefore give an affine functional
`0.5 v.K.v + linear.v + constant`. The implementation retains its exact velocity
gradient, boundary-flux gradient and physical-time derivative, including changes
in divergence, Gram forms, exterior flux and volume. The flux derivative is
integrated analytically over the original fan, not finite-differenced or replaced
by a constant owner velocity. Dry owners gain no artificial unknown; positive
sub-float volumes are retained.

## Checks

All **104** focused provenance, dry-fan, flux, metric, pressure, auxiliary/profile
transport and prescribed-trace tests pass (69.21 s). Eleven are new trace tests:
direct local versus assembled energy; velocity and boundary-flux derivatives;
independent time differences; reversed/subdivided faces; original winding and
mass cancellation; dry domains; positive 1e-400 strips; invalid boundary/shape
rejection. Two adjacent fully wet owners form the important negative control:
reflecting boundaries produce false compression, while the prescribed trace
cancels it exactly, on both flat and sloped beds.

Report: `tmp/front-prescribed-trace-final-20260919.xml`.

Original source replay tests **11 of 13** recorded predictors. Unsupported
records 2 and 7 are preserved untested, not repaired or counted as passes.
Original source triangles, split ownership and represented gravity are retained;
volumes and total exterior mass budget match exactly. Owner mean velocity is
only an evaluation probe, never a replacement for the varying exterior trace.

The qualified profile receipt is explicitly hash-bound. Seven changed,
**non-imported** historical tools have exact Git-blob proofs; both old and new
hashes are recorded with `used_for_this_computation=false`. No measured-input
or loaded-physics exception is allowed. All current protected and implementation
hashes were independently rechecked after the replay: zero mismatches.

- Source report: `tmp/south-fork-front-prescribed-trace-v1-20260919.json`.
- SHA256: `bc8d7b143777e54ce8757a143cf768e9f0c0b8d8f8295314264ba365f8071d15`.
- Size: 8,888,531 bytes; generated exact coefficients remain ignored in tmp.
- Reproduction entry point: `physics/scripts/audit_south_fork_front_prescribed_trace.py`.
  Use the original profile report and its SHA recorded in the source report's
  protected map, the original predictor, and the seven explicitly recorded
  historical revisions. Do not silently refresh provenance hashes.

## Remaining coupling, not acceptance

This is a **prescribed kinetic trace**, not a natural/radiating open-pressure
condition or a coupled nonlinear time step. It is not yet wired into the
original two-pole physical/canonical momentum response, pressure force,
interacting-front evolution or native solver. Those consumers must incorporate
the affine terms consistently before any runtime enablement. Merely adding
`b` to the displayed divergence would omit boundary work and is not a fix.

Current baseline checks also correct stale failure counts: the constant-velocity
and paired-rational suites now pass 27 tests; physical-rate coordinate accuracy
passes all eight, including the block cases. No CG change was made here.
The separate original storage/face consistency test still **fails**, with two
bitwise endpoint differences (maximum 1.77635684e-15). It remains unchanged and
required; neither tolerance relaxation nor dropping positive fragments is
acceptable. This scoped result is not a full-suite pass.

## Independent hydraulic continuation

PID 12672 remains the sole cook, using the previously recorded 12000-second
restart identity. Both state and artificial-bank audits pass at local 1000 /
12050 s and local 2000 / 12100 s. All 86,720 artificial-bank sample cells remain
exactly dry. The 12100 s state has maximum depth 4.001855 m, maximum speed
5.394570 m/s, and maximum per-step conservation residual 1.09226e-8 m3.
Outlet flow is still about 105.057165 versus inlet 45.306955 m3/s: **not settled**.
Next local 3000 / 12150 s needs completion and both audits. No duplicate cook.

Audit receipts, all under `tmp/`:

| File | SHA256 |
|---|---|
| `prescribed-trace-hydraulic-1000-state-20260919.json` | `c324b652611cc716245678934e299716f670cadebb0598f54327a07719455350` |
| `prescribed-trace-hydraulic-1000-banks-20260919.json` | `7fa684b31b552d1a47d806b9cf1db315f2676b28bab094fb319e0f76a526bb77` |
| `prescribed-trace-hydraulic-2000-state-20260919.json` | `891dbecabc14ade059b0c9fbf42998002bb6cb35f990efaee845775fb223166ba` |
| `prescribed-trace-hydraulic-2000-banks-20260919.json` | `ac84fbcc24455241759c8f977f241146d1d3ed3e2e487a3a8acadde636d595b9` |

Normal map, terrain, collision, captured evidence and installed 4950 s fields
are unchanged; nonlinear runtime remains OFF. No build, in-game motion or new
performance acceptance is claimed. Latest ordinary 25.003520 FPS / p95 48.329 ms
still fails 30 FPS. The pending cap interpretation decision is unchanged.
South Fork remains unfinished and ahead of Colorado, Pacuare and Futaleufu.
