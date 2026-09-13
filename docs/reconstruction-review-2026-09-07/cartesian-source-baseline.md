# Source-backed Cartesian presentation baseline — September 12

The render baseline outside the moving Cartesian solver crop now reads actual
shared atlas fields. It no longer calls the legacy station-band approximation
that derives a 0.8–2.4 m depth and straight-ahead current from an energy value.
This closes a runtime data-integration gap. It does **not** constitute normal
FullReach scene delivery, settled hydraulics, visual realism or cost acceptance.

## Implemented behavior

Each live window retains shared ownership of its verified immutable atlas.
Presentation lookup uses an integer tile index and constant-size sample stencil,
not a scan of all river packets, disk reads or a mutable global cache selection.
A later cache replacement cannot change the source retained by an earlier
window. Live solver steps cannot mutate the presentation source.

`SamplePresentationSource` bilinearly samples source bed/h/u/v across modeled
tile seams. Every nonzero-weight corner must exist; it does not bridge a missing
tile or extrapolate past a physical end. Valid dry cells retain their real bed
and zero depth. Missing coverage returns invalid instead of synthetic water.
Surface gradients use neighboring source cells, with one-sided differences at
true coverage edges. Atlas storage remains float64; the existing float render
API receives the same cast values as the independent reference data.

The adapter applies the river datum exactly once and retains hydraulic XY
velocity/normal components. Cartesian windows without a shared source cannot
fall back to the old energy-derived baseline. An unloaded Cartesian frame also
fails field/world gameplay sampling instead of inventing the default tank.
Legacy non-Cartesian baseline behavior is unchanged.

The live-to-source presentation handover now measures distance to all four
actual live crop edges, using the current inclusive cell-center bounds. North
and south receive the same 30 m transition as east and west. This does not rely
on a previous-frame column mask or a stale center after a moving-window handoff.
The existing station/lateral compatibility path retains its station feather.

The baseline is render-only. It does not enlarge live field or raft-support
authority, supply off-crop physics, alter solver boundaries or change source
state. The surface refresh calls this source path through the existing baseline
API; the normal map has not yet been switched to the reconstructed dataset.

## Verification

- Initial build: 41 actions, success, 280.29 s. Initial baseline/shared-atlas
  run: two tests pass in `south-fork-cartesian-baseline-v1-20260912`.
- Final build: 41 actions, success, 255.82 s. Two existing C4305 damping-literal
  warnings remain; no new build errors.
- `unreal/Saved/RaftSimValidation/south-fork-cartesian-baseline-v2-20260912/index.json`:
  **25 native/D3D12 tests pass**, zero failed/unrun tests and zero test warnings
  or errors. Includes baseline, boulder/foam, GPU crest, crop/overlap, streaming,
  source catalog, menu migration and prior water regressions.
- The new source test checks 7,921 analytic positions, including 5,912 outside
  the moving live crop: scalar and normal errors are both **0** at the public
  API precision. It also checks dry islands, missing northeast tile/corner,
  physical source endpoints, immutable ownership, datum/north handling,
  unloaded-frame rejection and separation from gameplay sampling.
- Four-sided handover checks use the actual solver bounds and equal edge,
  half-feather, interior and outside cases, including translated north motion.
- For **each** real 201 s / 832-tile and 301 s / 833-tile atlas, all 151,875
  cells in three full 224 m independent reference crops are checked:
  97,794 modeled cells match baseline bed/depth/surface/current with **0** error;
  54,081 unavailable dry-context cells have exactly zero source water. No wet
  reference cell is lost at a tile seam. Live shared/dense state and three
  subsequent steps still match bit-exact.
- `unreal/Saved/RaftSimValidation/south-fork-cartesian-baseline-gameplay-20260912/index.json`:
  **two actual-game crew/scoring/save tests pass**, zero errors/warnings, using
  an ephemeral profile. Normal FullReach and the real save hashes remain
  `e77da92b...` and `181d1e57...`, respectively.

These fixtures prove source/coupling behavior, not the appearance or frame cost
of the whole rendered river. They intentionally keep acceptance flags false.

## Continuing flow and next integration work

The 400 s / 833-core snapshot passed mass/state checks but wetted 17 artificial
boundary cells. Two captured-source tiles were added with zero added water;
all 5,331,200 retained native cells and clock are bit-exact. The 401 s pilot has
all artificial banks dry. See [the exact continuation record](full-river-expanded-checkpoint.md).

CURRENT LIVE: **session2578 / PID13424**, 835 cores, output
`tmp/south-fork-expanded-flow-to600s-v3-20260912`. Verified live at local step870 /
443.5 s, maximum step mass residual 1.14644e-8 m3. Local step2000 is 500 s and
step4000 is 600 s. The prior PID8116/session48811 is terminal; all its files are
retained. Do not rebuild the live executable or overwrite its input/output.

Next, finish actual two-dimensional shoreline geometry: the current column-wide
wet-span/reference-height and dry-vertex collapse paths cannot represent every
island or separate channel. Boulder eligibility/support lists and shore weights
also need alignment. Source-backed baseline and four-sided authority alone do
not close these geometric issues.

Then promote the common source-matched crest/carrier configuration into the
coherent normal FullReach scene, together with all source terrain/collision,
33.334 km route, hydraulic coordinates, starts/finish and progression stations.
`BuildGrid` still enables shared/refined captured crests through the old bounded
rapid/review identity; do not leave the full-river integration behind that gate.
Troublemaker must stay a rapid inside South Fork, not return to the menu.
Continue complete-snapshot bank/section-discharge/settling checks and actual
playable visual/motion/performance review. The broader goal remains open.
