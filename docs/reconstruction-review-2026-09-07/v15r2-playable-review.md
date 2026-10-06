# v15r2 packaged South Fork review - September28 UTC

The hydraulic-normal root repair is now in the rebuilt normal playable game.
The retry, staged-data audit, normal-menu/two-rapid timing and approach capture
are all terminal. South Fork is NOT accepted: both rapid timing gates fail,
and sampled actual views retain flat foam and weak breaking. No later river
may be treated as eligible on the strength of this delivery alone.

## Delivery and identity

Package session5066/wrapper35132 completed with exit0 at03:35:28 UTC;
BuildCookRun took325.70s. The three frozen inputs are unchanged. The package
receipt records the pre-commit HEAD; the frozen repaired material and author
were subsequently committed locally as `01da56b19`. Do not describe the
package as an unmodified build of that receipt's older HEAD.

Stage: `tmp/south-fork-playable-v15r2-20260928/Windows`.
Inner game executable SHA256:
`8d31f984e0cbd6097164913e477565bd761b81355fbc64601dbcca28182db401`.
Repaired normal material SHA256:
`6e7884ed44c1f3a372cda6dd1aae675409031fd1c1fbdd3a73bcb5a2effbc96a`.
The staged v8 manifest remains
`8190b5e81951986070664344a8a53c953a44961fc7d881f0633ba2cf9a7eb190`:
2,405 files /917,995,570 bytes verified with no external-source fallback.
Fields remain450s; the still-draining1350s continuation is not installed.

The sole follow-through session57198/wrapper39640 completed exit0 at03:41:14
UTC. It sequenced validation1772 and capture24292/game32056 after packaging;
no duplicate cook or test was started. The existing MetaHuman dependency
warnings remain release issues, not a clean-release pass. See the
[normal repair and storage-failure history](hydraulic-normal-root-repair.md).

## Actual normal launch and cost

Three isolated1200-frame runs used the same executable,1280x720 D3D12,
ordinary configuration and no quality/solver/candidate-console override.
Normal-menu exercised Boot and the actual menu; rapid probes start within
the same playable FullReach. All three exit0 with zero logged runtime errors.
Each retains all1140 audited frames, rows30..1169 inclusive.

| Start | Mean ms | p95 ms | Maximum ms | Frames >100ms | Timing gate |
| --- | ---: | ---: | ---: | ---: | --- |
| Normal Boot/menu | 37.6430 | 46.9160 | 80.3434 | 0 | PASS |
| Troublemaker approach8310 | 42.6916 | 54.2271 | 115.4698 | 3 | FAIL |
| Rapid11520 | 46.1006 | 52.4001 | 97.1394 | 0 | FAIL |

The user's20FPS goal remains p95<=50ms and no frame>100ms. Neither rapid
passes. Differences from v14 are not controlled same-trajectory A/B evidence
of a speedup from the material fix. Do not repeat unchanged tests seeking a
lucky pass, remove failed rows, reduce quality or hide simulation work.

Native requested/committed backlog peaks0.043171s at normal-menu and ends
0.012942s. At8310 it starts/peaks0.7192s and ends0.005591s; at11520 it
starts/peaks0.4784s and ends0.003171s. All report zero failed-frame flags.
End-of-run catch-up does not establish full interval real-time capacity.
The independent auditors retain the verified one-row frame/scope association;
nested scopes and overlapping thread costs must not be added together.

Frame receipts: `unreal/Saved/RaftSimValidation/sf-v15r2-<start>-20260928-frame-audit.json`.
Scope/clock receipts: `tmp/sf-v15r2-<start>-20260928-scopes-and-clock.json`.
CSV SHA256, with start names `normal-menu`, `rapid8310`, `rapid11520`:

- normal-menu: `1ab323eb2c21a596790c2e16a9b0c21595ccfe1ec3a45e8e77a5e8726eeff32a`.
- rapid8310: `12a9672d73bcb55944b2d54db445defc296f5752f580a266b968cfd8cc8d78ea`.
- rapid11520: `baf998799c7729f040660cc2afa021a1a441598f9ef316818991830522ea5cb0`.

## Actual packaged motion and sampled views

The ordinary boat-camera passive8310 approach completed all80 requested
samples, station8313.787m at world2.434s to8487.307m at81.046s (173.520m).
No paddle, free-camera, quality or solver override. The capture receipt binds
the same normally launched executable and verifies the normal plunge default.

Video: `tmp/south-fork-playable-v15r2-20260928/Windows/SmokeEmIfYouGotEm/Saved/VideoCaptures/RaftSim_20260927-203947.mp4`.
SHA256: `33ca9d1542a823f0cc5b402146fc9bdce5a0e004e80b9b259423f0068098d2af`.
All2,480 frames decode with increasing presentation timestamps through82.633s;
41 exact adjacent repeats after the first second. These counts and encoded
30Hz are NOT game FPS. Fixed image ROIs are not calibrated for the moving
boat camera and establish no physical velocity, amplitude or visual acceptance.
Unmodified decoded frames and receipt:
`tmp/sf-v15r2-motion-decoded-20260928/`.

Actually inspected6/11/20/40/60/80s. The raft passes the exposed right-bank
rocks and continues into quieter downstream water. Sampled views show a
continuous-looking carrier but broad white sheets, flat foam, coarse rock
silhouettes and detached-looking spray remain. No convincing overturning or
returning roller is established. This is not a pixel-matched A/B: do not
quantify visual gain from differences in trajectory, camera or world time.
Sparse visual inspection and full decoding do not establish continuous
shoreline stability, all-frame motion, collision correctness or full-river
traversal. Passive crew poses do not validate paddling/contact animation.

The thresholded ground-contact report is absent, NOT proof of zero contact or
penetration. The profile datum-v2 parser passes14 selected sites, with
`legacy_plunge_relief_requested=false`. Profile SHA256:
`4d09a0dc29ecae4dcad88928cab4cd077dac79088ec1fed1b6f7e70117170e60`.
Actual adaptive mesh audit reports1,660,680 samples, target error0.81058859cm,
tracking0.00110840797cm and source change0cm. Its limited analytic-crest scope
excludes hydraulic mean, other relief and GPU perturbation; the coarse-only
8.57cm comparison is not actual adaptive submitted-mesh error. These are
supporting geometry checks, not full rendered/contact or physical acceptance.

Process/profile/height/mesh/log receipts share
`tmp/sf-v15r2-spatial-approach-20260928` prefix. Capture log SHA256:
`09b1ce80e37da0c38f3b4a1f3b1bbdee499d690f81cf17c75f44a3ea32fa52f8`.

## Next work and limits

The delivered change restores the live hydraulic-detail normal in ordinary
water lighting while retaining its existing displacement input. It changes
neither captured geometry/collision/bed nor solver/field physics. No new
measured geographic feature, inferred underwater control or artistic rock
detail was introduced. Prior source provenance and licensing remain unchanged.

Continue with changing-profile/refresh and publication cost, using the
[existing localization and rejected trials](v14-playable-review.md), and
dynamic breaking/roller work. Do not repeat the rejected assembly-coordinate
or foam-edge-normal trials, enable the failed nonlinear solver, or fit the bed
to still-settling fields. Ground collision, shoreline/surface continuity,
rapid timing, hydraulic settling and reconstruction/visual acceptance remain
open. South Fork stays first; Colorado, Pacuare and Futaleufu remain queued.
