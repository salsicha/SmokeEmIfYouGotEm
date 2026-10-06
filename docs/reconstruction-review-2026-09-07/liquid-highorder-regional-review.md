# Wave-preserving interface and shared regional flow — 2026-09-11

South Fork remains incomplete. This is implementation and numerical evidence,
not a claim of photoreal water, volume consistency, steady flow or gameplay FPS.
No saved map promotion or final commit. The full original queue stays active.

## GPU interface transport

Implemented limited BFECC with five GPU stages: forward trace, reverse trace,
source correction, corrected forward trace, and original-donor extrema limiting.
It uses the existing RK2 characteristics and compact velocity basis. Invalid
forward/third-forward traces and nonfinite values invalidate a step. Missing
round-trip or solid support is explicitly counted as first-order fallback.
It does not move particles, guarantee volume or install a visible mesh.

`liquid-highorder-engine-v1` failed its unchanged 0.02 cm arithmetic gate:
owner 1 error 0.0292892 cm. Absolute grid-coordinate addition lost tiny trace
residuals, changing which donors contributed to the solid/validity decision.
The implementation now carries offsets relative to the integer source cell and
computes lower/upper weights independently. No tolerance was relaxed.

- `liquid-highorder-engine-v2`: three clean engine successes. All twelve actual
  fields compare against CPU references; maximum error 0.0113105774 cm.
- `liquid-highorder-engine-v3`: 22 clean successes, one success with an unrelated
  Google connectivity timeout, no failures. Includes 2,202,720 scalar samples:
  twelve actual fields and five fixtures for stationary transport, 24 persistent
  steps of a moving crest, unsupported traces, solid fallback and anisotropic
  cell metrics. GPU/CPU branch counts are not claimed bit-identical.

The actual-field reference manifest is
`tmp/south-fork-liquid-interface-highorder-cases-20260911/manifest.json`, SHA256
`6d892811165d2eaea6c100ce1afc30d97a153bbcbe48e07d93df25ecab4b074c`.
The five-fixture manifest is
`tmp/south-fork-liquid-interface-highorder-analytic-20260911/manifest.json`, SHA256
`7e4a44c63ed3f7ea9d086317ace223c80d1adc253eb477616c13a5e750aee310`.

## Intermediate regional exchange

Calling the single-owner operator independently would revert to lower accuracy
at artificial owner boundaries. The new regional API synchronizes forward,
reverse and corrected-source scalar AND validity fields across every owner
before the following stage. Final scalar halos are also exchanged. Validity is
exact 0/1 R32F; unmapped physical exterior validity stays zero. The API requires
same-age, same-orientation inputs with current velocity and solid halos.

- Build 58976 failed due to an extra brace in the refactor; fixed. Build 43206
  succeeded in 17.87 s.
- `liquid-highorder-regions-engine-v1`: four clean successes. Two-owner versus
  whole-grid transport after 24 steps: 5,200 samples, exactly zero difference.
- Expanded to four XY owners with a shared corner and a solid obstacle crossing
  the cut. Build 74217 succeeded in 42.87 s.
- `liquid-highorder-regions-engine-v2`: four clean successes. After 24 steps,
  7,280 samples including corner halos exactly match the unsplit GPU grid.
  Updated, high-order and fallback counts also match. Existing actual-field
  CPU comparisons still pass. These are numerical seam tests, not rendered motion.

## Actual native velocity mismatch and fix

Before enabling high-order transport in native flow, inspected the actual
600-step baseline's input velocities. Halo values were not synchronized after
`Extrapolate Velocities Again`: shared velocity differed by up to 145 cm/s,
including physical Z layers. The saved before-audit v2 reports 18,909 unequal
RGBA components (14,294 XYZ velocity components). This is an actual input
inconsistency; it is not proof that every visible stripe has this cause.

`liquid-velocity-halo-before-v1.json` incorrectly reports zero observed stages
because its generator had already been consumed by schedule validation. The
auditor now materializes the journal; authoritative v2 reports 601 stages. Both
reports retain the same actual field mismatch. The failed evidence is preserved.

Unified native transport now exchanges current RGBA16F velocity owner-to-halo
immediately after all owners finish extrapolation and BEFORE paired capture,
interface transport and the following FLIP/PIC particle stage. It preserves
physical owners, unmapped boundaries and every native channel. It is copying
ownership, not smoothing velocity or changing the bed. Stage order/count is
checked; capture metadata records the exchange and total dispatches.

- Build 47747 succeeded in 23.36 s.
- `liquid-velocity-halo-engine-v1`: three clean GPU successes. Expanded 16-owner
  full-volume test covers two boundary updates and the current velocity entry
  point, including physical/exterior preservation and alias rejection.
- 534 Python liquid tests pass (6.977 s), including exact halo comparison,
  missing-copy detection with no numeric tolerance, auxiliary channel checking,
  nonfinite rejection and duplicate destination rejection.
- Native capture now retains/hash-checks the halo implementation with its other
  boundary sources. The native interface auditor separately verifies a declared
  shared-velocity exchange; a paired scalar arithmetic match alone is insufficient.

## Native replay results

`liquid-native-velocity-halo-12-v1` completed (session 42290 exit 0), 40.02 s
diagnostic wall time. All captured implementation hashes remained unchanged.
The velocity audit requires exact copying, with no epsilon: zero differing
components, 13 recorded exchanges for 13 observed transport stages. Paired
interface error 0.000448935 cm over 2,178,720 samples, full time/owner ledger and
shared velocity verified. All 729,672 positions replay within 0.006871301 cm
(unchanged 0.02 cm tolerance). Original births, 412 later births and 464 exits
account for all survivors; original survey bounds retained.

The first dense audit rejected the new source manifest because the legacy
contract expected exactly seven files. The new declared velocity-exchange mode
now requires exactly ten named snapshots, including halo header, implementation
and shader, and verifies each hash. Legacy mode still requires the original
seven; no provenance checks were removed.

`liquid-native-velocity-halo-600-v1` completed (session 52681 exit 0), 70.52 s
diagnostic wall time, **not FPS**. All captured implementation hashes unchanged.
Stages SHA256:
`667534dcd78fef5ee6e151e1da71aad3b036f63d2696eee84d9148e5ee2eccc1`.

- Exact velocity halos: zero unequal components, 601 exchanges for 601 observed
  transport stages. The immutable selected packet is native step 600; extra
  queued ticks are accounted separately, not mistaken for step 600 evidence.
- Dense audit: 729,724 original + 22,533 births - 25,349 exits = 726,908 survivors.
  All 598 compact commits verified. Original outer survey preserved; one
  internal storage/survey owner difference remains explicitly reported.
- Every surviving particle's motion replays, maximum 0.003011221 cm, below the
  unchanged 0.02 cm gate. Instantaneous interior divergence RMS 0.000272761/s.
  No mass deletion, contact displacement, seed change or terrain edit was used
  to eliminate the velocity mismatch.
- Important non-improvements: peak density remains 12.35897 times nominal;
  the fixed-density candidate misses 6,759 particles and 666 occupied columns.
  That candidate is NOT the actual tracked scalar or a rendered surface.
- Nominal storage changes -59.4375 m3 across 598 commits; last interval inflow
  47.0474 versus outflow 37.5000 m3/s. Requested-duration budget is explicitly
  not a measured physical discharge or steady-flow acceptance.
- Repeated full Python suite: 534 tests pass (6.351 s).

Full transfer/interface audit session 94570 is terminal, exit 0:

- P2G verifies all 726,908 particles and native grid words; zero reduction
  mismatches. Physical-box deposited kernel volume is 15,130.707743 m3 versus
  nominal particle volume 15,143.917118 m3; the numeric comparison is not an
  assertion of exact geometric interface volume.
- Standalone interface audit verifies 599 transports, all clock/owner counters,
  and 2,178,720 selected-step samples: maximum CPU error 0.0005290635 cm.
  Shared velocity is separately verified. Physical outer XY and Z data remain
  provisional; the renderer remains disconnected.

The transfer CLI now has a summary-only option that still checks every particle and every
grid word but avoids a redundant ~197 MB per-particle JSON dump; source capture
is retained intact. No analysis is skipped.

All owned jobs are terminal, including UE 42290/52681 and audits57785/31355/
13945/86353/94570. Scoped whitespace check passes (line-ending notices only).
About 2.94 GB free on C: after retaining the two native replays; avoid redundant
large captures. No deletions were performed in this pass.

## Remaining acceptance

Higher-order interface transport is still not connected to native runtime;
next verify actual twelve-owner intermediate transport and native solid
support. The earlier measured scalar/particle volume drift, concentrated particle
density and non-steady discharge remain unresolved. Need coupled correction,
single visible breaking/frothy water, reference comparison, raft/collision and
FPS validation, then Colorado, Pacuare, Futaleufu and the rest of the queue.

Saved playable map remains SHA256
`36f4bc4222fa8d80d9d7899b5d3d0ab8bc88a1a6ee7435ec749c2b6f77fbdc96`.
