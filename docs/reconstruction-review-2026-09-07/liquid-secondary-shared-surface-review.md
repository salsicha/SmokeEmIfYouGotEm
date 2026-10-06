# Shared rendered surface for secondary whitewater

September 9. This is an unsaved South Fork GPU fixture candidate. No production
map is promoted, and neither physical nor photographic acceptance is claimed.

## Change

Previously, secondary foam/spray/bubble classification used the native SDF,
while the visible water used the reconstructed SDF. The new optional
`-RaftSimLiquidSecondarySharedSurface` capture variant publishes the completed
rendered RGBA volume into an independent GPU history volume. Niagara reads that
history in the following step; the native surface rewrite cannot overwrite it.
There is still one visible water surface. No per-frame CPU readback is added.

Source placement, gradients and particle classification use this shared field.
Foam projects along its local SDF gradient and then advects with current flow,
with a proper grid-to-world rotation. There is no fixed upward particle offset.
The split half-float timestamp rejects uninitialized, reset/future and stale
history. This is previous-completed-state coupling, not same-step secondary
feedback or a resolved two-phase fluid solver.

## Failures retained and fixed

`liquid-secondary-shared-surface-12s` allocated and published the cache but
stopped at frame 30 because newly added diagnostic attributes were absent from
the GPU particle dataset. Explicit AttributesToPreserve entries fix that.
The strengthened dataset test then failed because it looked for the graph's
`Particles.` prefix, which executable dataset names omit. The corrected test
checks the actual short names and float types. The failing report is retained
as `engine-liquid-secondary-surface-attributes`; it is not a passing run.

## Verified bounded result

`liquid-secondary-preserved-surface-12s` completes with 750 live updates and 30
distinct motion images, no engine error lines and no rejected spawn batches.
Both active and paused GPU cache exports exactly equal the completed rendered
surface in all RGBA components. Actual particle telemetry records timestamps
0.4833984375, 0.9833984375, 3.9833984375, 7.9833984375 and 11.9833984375 seconds
at the corresponding 0.5/1/4/8/12 second captures: the previous completed step,
not the native surface or an unchanging cache. Pause retains particle state.

At the final paused snapshot:

- 242 foam particles have median signed rendered distance -0.084 cm, compared
  with -3.388 cm in the native-support optical control. Their median absolute
  distance is 0.312 cm, p95 0.954 cm and maximum 1.846 cm.
- Only 1 of 62 spray particles is inside rendered water, by 0.383 cm. The
  control had 12 of 20 inside, with a maximum depth of 40.786 cm. Population
  and trajectories differ; this is not a paired particle-ID comparison.
- No sampled secondary particle penetrates the bed in the six retained
  captures. Physical-domain escapes still occur (10 at frame 240, one at 480,
  four at 720). This does not establish continuous collision/shore acceptance.

Independent live-input and current-foam audits pass; maximum foam coverage
discrepancy is 0.000732421875 and paused history is exact. The latest engine
suite `engine-liquid-secondary-surface-dataset` passes all 14 tests without
warnings. The numerical suite has 105 passing tests, including cache freshness,
reset rejection and rotated interface constraint cases. GPU reset and timestep
convergence remain unverified; these CPU cases do not establish them.

## Still visibly wrong

The captured image remains glossy cyan, with weak froth and rectangular fixture
edges. Top-crossing mean foam coverage is only 0.004063. Fixing surface support
does not establish realistic entrainment, crest shape, spray density, or any
photographic likeness. Artificial domain boundaries and full-scene integration
remain open. This candidate has not been applied to the production river.

## Current paired performance measurement

`liquid-secondary-native-support-benchmark` and
`liquid-secondary-shared-support-benchmark` both pass the uninterrupted-window
audit: 480 editor intervals, no image exports or blocking particle readbacks
inside the measured window, 471 usable post-warmup GPU timing samples, no engine
errors. Mean editor intervals are 23.376 ms control and 23.521 ms shared surface
(+0.145 ms, about 0.62% for this pair); p95 is 25.525 versus 25.332 ms. One pair
does not establish a statistically robust overhead bound.

GPU reconstruction averages 6.115 versus 6.136 ms. Foam/copy averages 0.11215
versus 0.13424 ms: approximately 0.02209 ms extra for publishing the cache.
These reconstruction timestamps exclude Niagara's particle update; the editor
interval includes the overall scene-capture workload. Neither measurement is
packaged-game FPS, and both editor means still exceed the 16.67 ms target.
Full-scene performance is not accepted. Saved contact-system/map/project hashes
remain identical to the previous checkpoint; no production asset was saved.

Next: improve actual surface foam generation and persistence against the reference
whitewater rather than increasing white tint or inflating sprites. Keep the
full South Fork reconstruction and all later rivers in the active queue.
