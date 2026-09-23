# Actual crew sole/floor measurement — 2026-09-23

Historical baseline, retained unchanged below. The implementation and subsequent
failed/passing trials are recorded in [shared crew foot fitting](crew-foot-fit.md).

**Contact is not accepted. No playable fit change was installed.** This is a
new native geometry measurement that rules out a global foot-height offset;
it is not a crew-motion, normal-launch, collision or performance acceptance.

## Evidence

`review_crew_foot_contact.py` spawns the normal production raft and its five
crew, without saving assets or levels. It reads all3,368 uploaded floor
triangles from section1 and the actual production boot LOD0 vertices from
all material sections. It retains the lowest1 mm of source tread, deduplicates
positions and transforms them by each live boot component's full world
transform. Every sample is projected vertically onto triangles directly under
its XY location, selecting the highest intersection, not a nearby vertex.

There are192 unique samples per boot and9,600 posed samples across five
actions. Values below zero indicate penetration into the rendered floor.

| Pose at each identity's initial action phase | Minimum clearance | Maximum clearance | Samples outside floor projection |
| --- | ---: | ---: | ---: |
| Idle | −10.8574 cm | +7.6801 cm |129/1920|
| Forward stroke | −11.1955 cm | +7.8702 cm |190/1920|
| Brace | −10.8574 cm | +7.6801 cm |129/1920|
| High-side port | −11.1450 cm | +7.8818 cm |392/1920|
| High-side starboard | −10.4768 cm | +7.5147 cm |579/1920|

The eight paddler boots' idle minimum clearances range from−10.8574 to
−5.6148 cm. The guide's two boots instead have minimum clearances+5.3264
and+4.6990 cm. Raising every foot would worsen the guide's existing gap.
The floor-edge misses are **not proof of unsupported feet in the complete
raft**: tube/thwart triangles were deliberately not included. A correction
must check those solids as well, rather than treating every miss as empty air.

The two retained actual engine views were inspected. They show the current
leg/raft arrangement but have tube/body occlusion, so they cannot independently
measure the tread gaps. The numeric results come from renderer-owned geometry,
not estimates from those images. Existing garment and overall crew realism
issues remain open.

## Source-level cause and next implementation

`AttachAvatarToSeat` now fits the actual CC0 glute to tube triangles, giving
different seat origins (roughly−7 cm for paddlers versus+8 cm for the guide).
The shared pose still supplies the same6 cm foot Z for every seat. Production
boot placement additionally preserves the source sole-bound offset. These
authorities are not fitted jointly. The old `floor_top` log uses a broad
all-section vertex scan and can hit a nearby thwart; it is not the actual
triangle height beneath either boot.

Next: fit each foot's placement and support to the rendered raft, account for
the actual sole shape and adjacent tubes/thwarts, and propagate the same fitted
foot/knee targets to the host equipment and CC0 body. Do not move only the boot
or compensate by breaking the independently measured glute contact. Verify
the full stroke/brace/high-side sequences, raft transforms/deformation and
normal-game motion/cost after implementation; initial-action samples alone cannot
qualify planted feet throughout animation.

## Reproduction and retained limits

Engine invocation: `UnrealEditor-Cmd.exe` with this project, `-unattended
-nosplash -nosound -RenderOffscreen -d3d12`, and `-ExecutePythonScript` pointing
to `unreal/Scripts/review_crew_foot_contact.py`. Environment
`RAFTSIM_FOOT_REVIEW_OUTPUT` pointed to the fresh directory
`tmp/crew-foot-contact-before-v1-20260923`. Session52725 terminated exit0.
The log warns that the boot asset lacks cooked-build CPU access. This editor
export succeeded with nonempty actual vertices; it does **not** prove those
vertices are readable in a packaged game. Do not enable CPU access or add
runtime mesh reads without considering their shipping/performance cost.

Four independent Python projection tests pass: sloped/reversed triangles,
top versus underside/nearby geometry, missing/degenerate support, and edge/
translation cases. They test measurement arithmetic, not a corrected crew.
No C++/map/material/collision/captured source/installed hydraulic field changed;
no game rebuild or new FPS result is claimed. Original cook36692 continues.
South Fork and the full ordered river/crew/release objective remain unfinished.

Retained SHA256 values:

- Script: `e625d104e0ea20bf01a6972ed08df8fddd76d6a64a6ab5899d3b2aabc92f5c06`
- `tmp/crew-foot-contact-before-v1-20260923/report.json`:
  `a85259617538cfef3f32c310e7df86119c4c8ecaef8d4740b419b3fd79420eea`
- `floor_front.png`: `449a000723d0e4e20a8e08755d63db1f60e244b266a7bea613f9a0da3f3f922d`
- `floor_rear.png`: `8ee432b605e64d998ddefcc8aac799a5209e8643458cee96605e43c64802dc67`
- `tmp/crew-foot-contact-before-v1-20260923.log`:
  `c65c494694b4714f92a7cb30e173fa9b624ef1a2bf90194bd07871ed6b536660`
