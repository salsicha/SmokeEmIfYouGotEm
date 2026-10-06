# Crew model review — September 4–5, 2026

Reviewed the actual packaged CC0 guide and four crew identities in Unreal. This is an improvement pass, **not a photorealism sign-off**.

## Changes retained

- Removed the separate rear helmet ellipsoid responsible for the "bun" silhouette. Raised and moved the crew helmet anchors back to cover the skull with the continuous shell.
- Disabled the redundant procedural neck when a complete CC0 body owns the visible anatomy. The extra neck intersected the skinned collar.
- Tested several life-jacket anchor/depth adjustments. Rejected them after action and rear views revealed front/back clipping tradeoffs; retained the original placement. This needs garment fitting, not another global offset.
- Rebuilt boot seams against the shoe's actual upper profile instead of fixed heights. Added cuff thickness and connected the heel pull tab to the collar.
- Preserved authored equipment geometry in the conventional Nanite fallback: helmet 24,228, PFD 40,232, and updated boot 20,444 triangles. Runtime Nanite remains enabled.

## Evidence and limitations

The `verified` folder contains 65 actual Unreal renders: five identities, each with six body angles, three head close-ups, boots, and forward-stroke, brace, and reentry snapshots. `capture.json` records the actual visual class, mesh, image paths, and pose checks. Representative views from every identity were visually examined, including rear and profile fits and the action snapshots.

Captures use full authored fallback geometry with Nanite and texture streaming disabled **only in the review process**. Synchronous scene captures do not advance Nanite page streaming reliably. These are isolated studio captures, not an in-river performance or animation-continuity test. Lighting is deliberately revealing but overexposes lighter skin; it is not a skin-color calibration reference. Earlier `baseline` and `candidate` captures had incomplete streamed detail and must not be used as fair before/after quality comparisons. `final` was an intermediate rejected tighter PFD fit; use `verified` for the retained result.

Build succeeded. All 15 captured action snapshots reported finite transforms, exclusive CC0 body ownership, helmet anchor error below 0.001 cm, and forward alignment approximately 1. These mathematical checks do not prove collision-free clothing or realistic anatomy.

## Remaining realism issues, in priority order

1. **Wetsuit construction:** the neckline and wrists are jagged, polygon-level skin/material boundaries. The source assigns skin by an average bone-weight threshold (`build_cc0_production_character.py`). Proper garment edge loops, cuffs, and a separate fitted suit are needed; another overlapping body primitive would reintroduce silhouette artifacts.
2. **Hands and joint deformation:** close-ups show bent, stretched fingers and stiff wrists; knees and shoulders lose anatomical volume in poses. Paddle contact metrics alone do not validate skin deformation. Review finger-chain rotation and skin weights against authored grip poses, then test full stroke cycles.
3. **Life-jacket construction:** the rigid shared vest has floating shoulder straps and cannot conform to every torso in every action. Anchor experiments exposed front/back clipping tradeoffs and were rejected. It needs fitted/skinned straps and per-identity garment fitting rather than further global shrinking.
4. **Surface quality:** faces lack convincing eye/skin variation at close range; the boots still have coarse toe-rand transitions. These need material/UV and mesh finishing, not just more triangles.
5. **Gameplay validation:** review the corrected roster seated in the raft and moving through complete stroke/rescue cycles with normal Nanite streaming, lighting, shadows, and LOD transitions. No frame-rate improvement is claimed here.

## Selected views

| Identity | Overall | Rear helmet | Profile | Action |
| --- | --- | --- | --- | --- |
| Guide | [Three-quarter](verified/guide_front_right.png) | [Rear](verified/guide_head_rear.png) | [Side](verified/guide_head_side.png) | [Brace](verified/guide_brace.png) |
| Crew 01 | [Three-quarter](verified/crew01_front_right.png) | [Rear](verified/crew01_head_rear.png) | [Side](verified/crew01_left.png) | [Stroke](verified/crew01_forward_stroke.png) |
| Crew 02 | [Three-quarter](verified/crew02_front_right.png) | [Rear](verified/crew02_head_rear.png) | [Side](verified/crew02_head_side.png) | [Reentry](verified/crew02_reentry.png) |
| Crew 03 | [Three-quarter](verified/crew03_front_right.png) | [Rear](verified/crew03_head_rear.png) | [Side](verified/crew03_head_side.png) | [Brace](verified/crew03_brace.png) |
| Crew 04 | [Three-quarter](verified/crew04_front_right.png) | [Rear](verified/crew04_head_rear.png) | [Side](verified/crew04_left.png) | [Stroke](verified/crew04_forward_stroke.png) |

[Boot close-up](verified/crew01_boots.png) · [Capture manifest](verified/capture.json)

No commit or push was requested for this review. Existing unrelated working-tree changes were preserved.
