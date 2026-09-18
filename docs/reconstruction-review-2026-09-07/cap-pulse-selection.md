# Conservative cap selection experiment: not ready for playable promotion

September18,2026. This run advances the identified downstream cap, not the
unrelated foreground ground. It produces a new, source-preserving geometry
hypothesis and checks its hydraulic consequences. **No visible normal-play
improvement is delivered**, no new engine build/capture/performance pass is
claimed, and the previous actual motion remains visibly unacceptable.

## Acquisition metadata recovered without changing captured data

Replayed all four hash-verified original LAZ tiles using the exact original
crop, projection and NAVD88 US-survey-foot conversion. Every one of2,815,491
archive IDs reproduces its original XYZ and classification exactly and in the
same order. The separate pulse-field archive retains return number, number of
returns, flight/source ID, GPS timestamp, tile and original point index.
1,899,608 are last/only returns;915,883 are earlier returns. None is reclassified
as rock or vegetation. All original LAZ and derived captured NPZ remain intact.

Pulse archive SHA256:
`f5c55fdc0465cbbc82938899ddfb54c57676cc272abd98fe3e8e0f87ca0c7902`.
Generated metadata remains under ignored
`tmp/troublemaker-original-pulse-fields-v1-20260918`; the generator and source
identity report are versioned. No new source acquisition/licensing claim.

## Explicit alternative interpretation, not a blanket classification fix

The existing source-connected cap builder now accepts an **opt-in experiment**:
last/only returns may seed/refine NEW landward extension geometry. The same
reviewed selection,0.5m bins, minimum two observations, source connectivity,
1m maximum triangle edge and exact original XYZ remain required. The original
549-vertex seed cap and every original seed roof triangle remain exact,
including any seed that does not satisfy the experimental pulse rule. Existing
default selection is unchanged. No point is lowered, averaged or deleted from
the archive; only the hypothesis's selected IDs and inferred adjacency change.

The experiment is deliberately not a claim that first returns are vegetation
or last returns are ground. It tests whether acquisition-order ambiguity is
sufficient to explain the already identified cap spikes before another expensive
cook or playable replacement is attempted.

Candidate `tmp/troublemaker-last-return-cap-v1-20260918` has1,586 roof vertices/
2,923 roof triangles versus1,601/2,954 before.34 previously selected original IDs
are omitted from this interpretation and19 different original IDs added. Both
meshes independently replay all roof XYZ and classifications exactly.
Source-cap SHA256:
`769ad5b2e1707c9a202968287d8c509cd4f36776e08375541da1565ee2127430`.

Projected area changes321.544940→319.500801m².2.193680m² of previous coverage is
lost and0.149542m² added; lost coverage is NOT a measured gap or exposed ground.
Both remain one connected component with one interior hole. Roof area steeper
than60degrees decreases114.812127→100.788954m². That still leaves most of the
steep geometry, and minimizing slope is not the physical reconstruction goal.
The closed-solid builder passes its exact roof, winding, manifold and volume
checks. These are geometry checks, not actual native collision acceptance.

## Hydraulic consequences prohibit a visual-only swap

Independently reconstructed the OLD exact source-ground/cap union in both
intersecting hydraulic cores, reproducing every existing bed, owner, captured
stage and mask field byte-for-byte before evaluating the new cap. The completed
300s candidate state is bound by input, geometry, completion and depth hashes.

The alternative cap changes17 one-metre bed cells:16 in core0629 and one in
core0631.12 have positive water depth and exceed the solver's1e-6m wet threshold.
Changed-cell depth reaches0.770887m; bed change spans-2.153097..+0.288615m.
This is **not a dry cosmetic roof-only change**. Copying the existing water or
swapping just the rendered mesh would make the bed, collision and water disagree.
No water state was transferred and no replacement cook was launched.

Do not install this experiment merely because it removes one nonlast anchor or
reduces steep area. Next, qualify the retained cap's interpreted source selection
and missing coverage against the actual local rock structure; pulse order alone
does not resolve the shape. Keep the original and this explicit alternative.
Once a justified shape is selected, derive the physical union/fresh fields and
incremental normal-play integration together. Do not rerun this unchanged
filter experiment or start a speculative cook before that decision.

## Tests and live work

79 focused Python tests PASS, including strict pulse numbering/identity,
source-connected constraints, cap geometry, altered wet cells versus positive
sub-dry films, and runtime union/probe controls. The final wet-impact audit was
rerun after its tested helper was extracted; results are unchanged.

Baseline9850/9900/9950/10000 and candidate250/300s each pass BOTH full-state and
artificial-bank audits, all86,720 artificial-bank cells exactly dry. Neither
is settled. The original candidate job30276 completed normally at300s; it was
not killed or restarted. Its completion has depth4.812067m, speed12.111935m/s,
and maximum step conservation residual1.504465e-8m³. Baseline13584, started
2026-09-18T12:17:39.4321093Z, continues toward12000. Next unaudited baseline
checkpoint is10050/local21000. There is now only ONE live cook: the old dual-cook
review manifest must not be reused as though30276 were still running.

Installed terrain/4950s water and scenario hierarchy remain unchanged;
Troublemaker stays inside South Fork, not on the menu. Nonlinear runtime OFF.
Latest ordinary24.937420FPS/p9549.3295ms still FAIL30. South Fork, Colorado,
Pacuare and Futaleufu remain unfinished in that order.

Evidence is retained in [cap-pulse-selection](cap-pulse-selection/): exact
source replay, candidate manifest, independent geometry comparison, wet-cell
impact, six pairs of checkpoint audits and test results.
