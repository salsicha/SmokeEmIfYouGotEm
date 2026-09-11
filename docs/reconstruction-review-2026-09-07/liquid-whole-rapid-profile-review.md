# Whole-rapid profiles and bounded contact reader

September 10, 2026. South Fork remains incomplete. No production scene changed,
no full-rapid GPU simulation or photorealism acceptance, and no commit.

## Prepared whole-rapid state

Selected package: `tmp/south-fork-whole-rapid-liquid-float-seeds-20260910`.
It preserves the previous 245 by 81 m domain, captured mesh, closed solid and
native face-flux provenance. Source, initial-water, contact and scalar/vector
boundary exporters now support this off-centre rectangle explicitly. Nonlegacy
schemas are versioned; the old fixed-size boundary reader still rejects v3.

[Prepared-data audit](liquid-whole-rapid-profiles/audit.json) passes all 20 checks:

- 719,335 initial particles and 6,144 incoming source sites.
- 352,872 contact triangles; maximum encoded seed contact error 0.00712528 cm,
  below the unchanged 0.01 cm tolerance.
- Maximum incoming native-face discharge error 3.55e-15 m3/s.
- Minimum source clearance 0.215119 cm; all initial particles above exact bed.
- Source, captured geometry, solid and native flux hashes unchanged.

Two concrete initialization/precision defects were corrected during preparation:

1. Six initial particles exceeded the vertical domain because zero-depth native
   cells' terrain elevations were interpolated as water stage. Zero native depth
   now means no liquid column. This excludes 76.998536 m3 of false interpolated
   water without raising the domain ceiling or introducing a new wet threshold.
2. Absolute float32 triangle positions exceeded the contact tolerance (0.01140 cm).
   Quad-relative XY encoding alone still disagreed with double-precision seed
   sites (0.01303 cm). Nonlegacy quadrature sites are now encoded as actual
   float32 positions *before* sampling their bed/stage. Captured terrain is not
   moved; these are generated particle positions, not captured measurements.
   Final volume quantization error is 0.00581593 m3, below half the nominal
   1/48 m3 particle volume.

Continuous native wet-face source remapping retains the earlier zero-residual
result. Discrete ghost-cell centres are a separate remap: one dry outgoing face
cannot represent approximately -2.04e-9 m3/s. It is explicitly reported under
the existing 1e-7 m3/s outgoing dry-noise allowance. Incoming flux uses zero
allowance and fails if wet support is absent. No incoming water is discarded.

## Capacity and implementation

The prepared 490 by 162 by 24 physical grid would allocate 494 by 166 by 24
computational cells. Uniform two-times reconstruction requires 15,744,768
voxels, exceeding the current 2,000,000 limit; even one RGBA16f field is
125,958,144 bytes. The initial particle count also exceeds the live density
packing limit of 262,144. These are arithmetic capacity checks, not GPU timings.
Limits were not increased and the whole package was not installed as one volume.

The engine terrain-contact reader now accepts bounded v2 quad-relative profiles
as well as legacy v1. Each uploaded table carries its own encoding marker
(negative runtime-only column count for v2); disk counts remain positive.
Primary contact/pressure and secondary continuous swept contact subtract the
nominal quad origin before the small vertex offset, including the geographic
reflection. There is no process-global encoding flag or conversion back to
large absolute float32 vertices. Unknown formats, malformed arrays, nonfinite
values, and tables beyond the unchanged 256 by 256 quad limit are rejected.

`physics/scripts/liquid_contact_region.py` extracts explicit bounded rectangles
from the full contact table without resampling vertices or changing diagonals.
It rejects unsupported bounds rather than clamping, checks that every retained
float32 nominal origin is unchanged, and removes inherited whole-domain query
claims. This is contact paging only: it creates no artificial fluid boundaries,
resets no particles, and does not yet implement live region selection.

## Verification and next work

- 190 liquid Python tests and 12 window tests pass (202 total).
- Editor Development build succeeds.
- [Two headless editor tests](engine-liquid-contact-encoding/index.json) pass:
  contact-format decoding and geographic-frame regression, no test warnings.
  These use NullRHI: generated shader text and CPU loaders are checked, **not
  GPU execution of v2 contact or water rendering**. Startup reports unavailable
  non-Windows SDKs; Win64 is valid.
- Scoped diff whitespace check passes. Build and editor sessions are terminal.

Next integrate bounded live regions with conserved shared state/exchange, v3
boundary/source/initial-state consumers, one continuous visible water surface,
and the raft. Do not turn the regions into disconnected resettable fixtures or
promote numerical preparation as realistic water. Actual GPU contact parity,
whole-rapid motion, returning hole/crests, reference comparisons and gameplay
performance remain required before proceeding to Colorado, Pacuare and Futaleufu.
