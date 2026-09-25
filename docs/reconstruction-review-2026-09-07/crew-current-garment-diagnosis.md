# Current crew garment diagnosis — September25

Fresh production-raft capture via `review_crew_seat_contact.py` completes with
engine exit0. Evidence is in `docs/crew-review-2026-09-06/current-fit-20260925/`;
capture.json SHA256 is
`470793363d00fcc0c640fe5d9d421b1da07d97769c3a1e8a2af041a020bfa6c9`.
All five identities have finite idle/forward/brace transforms. Fifteen sampled
glute clearances range from-1.007190 to-0.308422cm, within the existing gate.
Transformed-raft idle clearances remain within0.007190cm of the-1cm target.
These are static samples, not animation, tread, garment or full-body acceptance.

The fresh seat_0_upper view was inspected at preserved aspect ratio. PFD/body
overlap and bulky seated garment silhouette remain visible. Feet and PFD
placement differ from the September6 retained image, so that older image must
not be treated as the current baseline for a corrective offset. No game assets
were saved by this capture and the production runtime was not changed.

Read-only Blender5.2 import of Crew01's checked-in FBX (exit0) reports one mesh,
35,608 vertices and34,290 polygons: Skin7,492; Wetsuit5,810; Hair20,464;
Eyes140; Brows384. Source SHA256:
`41e2ac4217928d64196a17a2dbc00a7f2b2695b6e2ea76fb987bc84e148cc395`.
No separate wetsuit object was found. This agrees with
`build_cc0_production_character.py::_configure_body_materials`, which assigns
skin versus wetsuit to body polygons at average skin-bone weight0.34.

Consequently the old runtime comment prescribing a Blender cape trim was
misleading. It is corrected without changing code behavior. Do not delete
wetsuit-assigned faces as though they were detachable cloth: they are body
surface. Next distinguish material-region scalloping from posed skin deformation
and rigid PFD overlap using the current mesh/pose, then verify any correction
across all identities and continuous actions. No neckline, garment fit, high-side,
reentry, normal-play or river acceptance is claimed by this diagnostic.

## Attachment metric repaired

`GetProductionPfdTorsoErrorCm` still compared the PFD origin with the legacy
host pose, although CC0 placement follows `GetSolvedChestWorldTransform`.
It now compares actual world-space PFD location with that rendered chest anchor,
returning the existing failure sentinel when the chest is unavailable. Other
visual implementations retain their prior metric. No attachment transform,
body/vest mesh, fit tolerance or simulation behavior changes.

Initial native fixture attempts failed before measurement because the temporary
host world did not activate the child CC0 body. Adding world context removed
teardown warnings but did not resolve activation. Both failed reports remain at
`tmp/crew-vest-attachment-error[-v2]-20260925/index.json`; the existing
VestFollowsTorsoNotHead test passed in both. The new nonfunctional native fixture
was removed, not counted as passing, and the original native test is unchanged.

Equivalent fault-injection checks now use the actual editor-world production
raft setup in `unreal/Scripts/validate_crew_pfd_attachment.py`. It tests five
loaded CC0 identities and idle/forward/brace/reentry after translating and
rotating the raft. All20 attached errors are0cm; independently moving each PFD
by world vector(3,4,0) reports exactly5cm; restoration reports0cm. Real-RHI
commandlet exit0; no assets saved. Receipt
`tmp/crew-pfd-actual-world-20260925.json`, SHA256
`011e411f7a26b25cb6c292ed8e1954019a3bdfef244304f09647f4591fb00d86`.
Initial editor build191.78s and fixture-context rebuild10.24s succeeded.

This corrects an attachment diagnostic used by production-quality checks.
It does not measure PFD/body intersection, strap clearance or continuous motion.
The standalone packaged executable is unchanged; visible fit remains unfinished.

## Render-only anatomical leg experiment rejected

September25 follow-up found that foot-contact IK preserves lengths from the
compact idle host pose, while CC0 segment driving preserves imported bone scale.
The existing source log reports41.4cm thigh/46.0cm calf for its first identity.
A default-off candidate solved each rendered knee with that identity's imported
lengths, retaining both host hip and foot anchors. It changed no gameplay pose,
source asset, boot target or solver. Editor build succeeded in11.27seconds.

Actual five-person production-raft capture completed, engine exit0, at
`docs/crew-review-2026-09-06/anatomical-legs-20260925/`. Console activation is
recorded in `tmp/review-anatomical-legs-20260925.log`; wrapper is
`tmp/review_anatomical_legs_20260925.py`. Existing15pose contact/finite checks
pass, and transformed idle clearances range-1.003861 to-1.000846cm. These checks
do not cover knees against hands/paddles.

Compared current baseline and candidate seat_0_side/upper engine views. The
candidate extends the thighs into the idle paddle/hand area, visibly especially
on the opposite crew member; the bulky hip silhouette remains. Rejected, not
promoted on passing contact checks. Candidate CVar and knee-only solve removed;
existing pending comment and attachment-metric changes preserved. No FBX, map,
packaged executable or capture was overwritten/deleted. Captures remain local.

Next address the coupled posed-body/boot/paddle layout rather than repeat this
isolated knee solve or scale away anatomy. Imported lengths alone do not prove
realistic fit, and this experiment does not establish a single cause for the hip
bulge. Normal motion, collision clearance and all-identity fit remain open.

The post-rejection Editor rebuild succeeded in11.07seconds, so its runtime no
longer contains the rejected CVar/solve. Before committing the attachment fix,
the unchanged receipt SHA256 was rechecked, including exactly four cases for
each of the five distinct CC0 mesh identities. Every attached/restored error
is0cm and every injected displacement is5cm. Large PNG review sets remain
local and are not added to this source checkpoint. No push or release acceptance.
