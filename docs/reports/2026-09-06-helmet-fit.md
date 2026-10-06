# Smaller, correctly seated crew helmets

The gameplay CC0 guide helmet scale changed from 1.08 to 0.90 (16.7% smaller),
and all four crew helmets from 1.02 to 0.84 (17.6% smaller). The shell asset,
head meshes, head rotations and physics are unchanged.

The first smaller-fit capture exposed rear skull clipping: the existing
oversized fit had hidden a forward seating error. The guide's head-local
rearward offset is now 5.5 cm instead of 3 cm; the crew offsets are
5, 5.5, 5, 5 cm instead of 3, 4, 3, 3 cm. The same pose-driven attachment
continues to orient and locate the shell. No extra rear cap was added.

Actual Unreal captures are in
`docs/crew-review-2026-09-04/helmet-fit-2026-09-06-seated/` (the established
capture script retains its original parent directory). All five characters'
front, side and rear head close-ups were inspected. The large rear skin patches
in the rejected first fit are absent in the final views. Forward-stroke, brace
and reentry poses were captured for every identity; representative action
images were also inspected. The capture JSON records actual scales 0.90/0.84,
finite transforms, exclusive CC0 body ownership, and passing attachment
position/orientation for all 15 action-pose checks. These checks are not a
geometric intersection test or a continuous-animation review.

Development Editor builds successfully. Two new fit/capture contract checks
pass. The existing helmet source test was stale: it required the separate rear
cap that earlier work removed. It now checks continuous rear-bowl coverage
and absence of that separate cap while retaining source FBX/Blend hash checks.

Scope is helmet scale and seating on the currently selected CC0 roster.
MetaHuman fits and non-production procedural fallback helmets are unchanged.
Other visible character issues—including strap routing, garment joins, skin
shading and vest fit—are not certified by this helmet correction. No water or
terrain settings were changed in this task, and no commit/push was requested.
