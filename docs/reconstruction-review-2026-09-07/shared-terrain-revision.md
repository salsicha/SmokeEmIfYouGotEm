# Source-matched full-map terrain replacement

2026-09-16. This is a controlled revision of an explicitly **inferred** submerged
prior, not measured bathymetry, a calibrated rapid, or finished playable water.
Troublemaker remains a rapid in South Fork, never a separate scenario.

## Full-domain source and native geometry

The shared operator committed in `bb5af034f` applies the registered bed revision
before the unchanged original-return rock solid. It preserves captured vertices,
registered XY/topology, inferred rock flanks, rapid/seam boundaries, source water
masks/stages, physical discharge/outflow boundaries, roughness and grid resolution.
Only 2,132 authority-2 vertices change. The derived physical domain contains all
841 cores / 5,382,400 cells; four cores change. Eight of 799 source packets change;
791 retain their original fields. No evolved old-bed state is transferred.

The actual saved FullReach map was loaded in Unreal. Its original rapid actor
was reused, with the original transform and material, to replace the base mesh;
no second terrain sheet was added. The unchanged source-rock actor was then added
as in the preceding union experiment. Independent native readback compares every
one of the 803,842 directed terrain triangles, not just a small ray sample:

- 4,466 triangles change, involving exactly the declared 2,132 vertices.
- Every other native corner is bit-exact; all XY and winding are bit-exact.
- Maximum source/import rounding error is 0.0000328831375 cm, below 0.001 cm.
- All 30,066 original-terrain and 34,869 revised-union ray probes pass the
  unchanged 0.1 cm position/ownership gate. This includes every changed triangle.
- A new local review mesh is saved only after these checks. A second fresh
  engine process reloads that package and repeats the entire native comparison
  and collision audit without importing or saving anything.
- All 464 prior protected identities still match: 462 unchanged, two matching
  the previously verified CPU-retention-only revisions. No map or actor save.

The collision probe generator now determines rock ownership against the revised
parent bed. A raised inferred bed is not mislabeled as rock, and a rock exposed
by a lowered bed is not mislabeled as terrain. Covered original roof targets stay
in the evidence; prior isolated-probe failures are not waived.

## Fresh hydraulic state and delivery path

The one-second full-river pilot finishes and passes cell/conservation and all
86,720 exact-dry artificial-bank checks. The fresh longer run reaches 50 seconds
and passes both checks again: maximum depth 4.277083789 m, maximum speed
12.166877129 m/s, maximum step residual 1.18347564e-8 m3. Outflow is
27.973980709 m3/s versus 45.306954547 m3/s inflow: **not settled**.

The 50-second runtime export contains all 841 tiles and 799 packets, verifying
42,185,039 intersecting source-bed samples. All 406,823 original-water coverage
probes pass with a 10 m minimum raft-interior margin. The preexisting physical
outlet coverage repair is retained explicitly, not hidden or counted as a new
geometry change. Native expectations cover all 25,600 cells in the four affected
cores; the previous 12,800-query two-core report cannot satisfy this gate.

A third fresh native run verifies all 25,600 field queries against this exact
50-second atlas, together with the repeated 64,935 collision probes and full
native terrain comparison. Zero wet/dry mismatches; maximum bed/surface error
7.62939453e-6 m, depth error 1.19182048e-7 m, velocity error 2.38175167e-7 m/s.
No solver steps, asset saves or level saves occur in that verification. The
version-2 descriptor is generated successfully with 3,267 hashed dependencies,
initial packet `region_0190`, center (-5437.499999998952, 3606.5) m.

The version-2 preview descriptor requires a freshly reloaded, source-matched
terrain audit. Older cap-only loaders reject it. The updated native loader checks
both original and revised collision-source hashes and requires the original
rapid actor, transform and material before changing anything. It tests the real
water loader first, then installs the terrain and paired water before BeginPlay.
Failure leaves the old terrain/water configuration in place. This still needs
linked-editor and actual playable verification; the existing map is not promoted.

138 focused Python regression tests pass. The new native loader compiles with
the original Unreal C++20 flags to an isolated temporary object, with zero MSVC
diagnostics. The first isolated invocation omitted the original RTTI/C++20 flags
and failed PCH compatibility; that setup failure is retained. No DLL, shader or
game executable was replaced while the package cook was live.

## Evidence identities

All paths below are project-relative local evidence, not redistributed source art.

| Artifact | SHA256 |
| --- | --- |
| `tmp/south-fork-control-ablation-union-geometry-v1-20260916/manifest.json` | `08bab8cedc801ac7fdd525f8c9ab8262c93795afb0e3de5b0aaf5ddd3a0faa53` |
| `tmp/south-fork-control-ablation-flow-v1-20260916/manifest.json` | `8b0b2e15cd5ff629f255996c3e6b89f860617bbec8df4fdd3c2adda959b578e8` |
| `tmp/south-fork-control-ablation-full-map-probes-v2-20260916.json` | `852064b8593c0b68b33d14348f864ad5fff2e35a7bf077ed62f85178181efb21` |
| `unreal/Saved/RaftSimValidation/control-ablation-native-union-v2-20260916.json` | `22a1eb08883d0ff15a27f3e24a10cabf63a0300523782d3f1f3c1ac6c6a6414b` |
| Revised local terrain package | `1064806357216e70510c78f2b37d7c0d38f1fdb1e926e0bf516e024c4c015491` |
| Revised native collision source | `f0d39b640592c1b2cbccf89c1ed07f01587f377de5b5d0db0bab9b254cf888c5` |
| `tmp/control-ablation-50s-state-v1-20260916.json` | `c4b49ecd0c18411491e1d931139fdde8b2e0687831d6940a1c45b1e889eb7dc9` |
| `tmp/control-ablation-50s-banks-v1-20260916.json` | `6deed0e55b2e2849d237a790a4e7352466c12cb56b418fb49c6b6417eb346b73` |
| `tmp/control-ablation-runtime-50s-v1-20260916/atlas/manifest.json` | `60cf8d01dfefa035a479a62df5a3268e2676420f3a5927c98dda7b8d3a017c98` |
| `unreal/Saved/RaftSimValidation/control-ablation-native-runtime-50s-v1-20260916.json` | `727ed3bb99f192a9b7eebd3045e46254c58de2929d46a4a9c654b458200aa7f4` |
| `tmp/control-ablation-50s-joint-preview-v1-20260916.json` (schema v2) | `58c308b54494bb1d169c98ef801f42dfdc4bb151833b2332995cf379aae26131` |
| Isolated editor compile object | `f2fe178da02e4af315d1c7ead1706059486369a4eb7dc8feac3f04dd78f1caeb` |

## Still required

Linked-editor v2 playback, actual motion/capture comparison and normal South Fork
delivery remain required. The source-matched native query fixture is not play.
Settling, convincing breaking/froth, physical contact and the unchanged 30 FPS /
p95 <=33.333 ms performance gate are not accepted by these source checks.
Last uncontended performance remains 17.819710 FPS / p95 81.6343 ms (FAIL).

The full solve remains session46094 / PID22940, output
`tmp/south-fork-control-ablation-full600s-v1-20260916`; next audit is step2000 /
100 seconds, then each completed checkpoint. Preserve this same running job.
Package83678 / cook5852 / shader35032 also remains live. After its terminal result,
verify the actual archive, 444 non-editor sources and 2,405 staged files, then link
the new editor loader and exercise v2 playback. Do not rebuild cook inputs while
it is live; do not restart live jobs on observation timeouts.

Colorado -> Pacuare -> Futaleufu, Chilko/Zambezi and other-scene water, crew
realism/fit/animation, normalization, regressions and release checks remain open.
