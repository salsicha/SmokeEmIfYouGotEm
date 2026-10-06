# Crew-to-raft contact correction

The visible CC0 glute does not match the old procedural pelvis ellipsoid.
Seat placement previously subtracted that ellipsoid's 15 cm depth and a
4 cm guessed sink from the highest nearby raft vertex. That still left the
rendered crew above the raft.

The shared raft seating path now poses the selected character first, samples
its skinned glute underside in the avatar's own frame, and intersects those
samples with the rendered tube triangles. The seat origin is fitted to actual
contact with 1 cm of neoprene compression. The measurement runs on seating or
reseating, not in the animation tick. Physics mass locations are unchanged.

The first verification rejected an owner-frame mistake: a child actor's owner
is not necessarily its parent avatar. The final implementation uses the actual
parent actor and guards against unavailable CPU buffers. The five CC0 skeletal
assets and importer retain CPU-accessible mesh buffers for cooking; this does
not enable CPU skinning every frame. Non-CC0 adapters retain their old fallback.

## Actual-engine evidence

`docs/crew-review-2026-09-06/seat-contact/` contains the production raft with all
five crew, three contact close-ups per character, two complete-raft views, and
the measured contact report. This is rendered gameplay geometry in an editor
review world, not a generated illustration or a hand-positioned proxy raft.

The new actor Z values are approximately -6.55, -7.37, -7.07, -6.82 cm for the
four paddlers and +8.02 cm for the guide. Compared with the previous placement,
the actual bodies move down approximately 4.1–5.7 cm.

All five idle contacts measure -1 cm; the sampled forward-stroke and brace
contacts range from -0.92 to -0.13 cm, with finite transforms. Side and rear
close-ups show tube contact. The stern guide follows the sloping tube and
retains natural clearance under the forward thigh, not a floating pelvis.

The validation script also checks that translating and rotating the whole
raft does not change the measured contact. It fails if a contact measurement
is missing, floating, excessively sunk, or transform-dependent.

Verification completed: Development Editor build passed; the saved-asset reload
capture passed all 15 contact/finite checks and all five transformed-raft
contacts remained exactly -1 cm. Four plain Python regression checks (two seat,
two helmet) passed by direct execution; pytest is not installed in the bundled
interpreter. `git diff --check` passed.

## Limits

No continuous river run, packaged executable, capsize/reentry sequence, or
heavily deflated/deformed raft was validated in this pass. The fit is computed
at seating; it is not a full dynamic cloth/contact or foot-IK solve. The review
also exposes existing PFD/garment and foot/thwart fit issues, which are not
claimed fixed here. No water, terrain, helmet shape, or physics tuning was
changed. No commit or push was requested or performed.
