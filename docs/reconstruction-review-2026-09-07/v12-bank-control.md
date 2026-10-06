# V12 bank contact: control run and source-field context

September27. Supporting diagnosis, not a new playable improvement or full
traversal/physics acceptance. Existing v12 geometry,450s fields and executable
remain unchanged. No rocks, inferred bed, collision or acceptance gates edited.

## The failed unsteered path is not an impassable-channel proof

The existing upstream capture issues AllForward once at1s and no guide steering.
`RaftSimCaptureCommand.cpp` schedules that input; `RaftSimRaftActor.cpp` applies
ongoing forward impulses along the changing raft heading. The recorded raft
turns toward the right bank: route8404.954/lateral-9.318/yaw-81.093degrees by
27.119s, before the first recorded >=5mm projection at27.681783s. Later records
show continuing command1 propulsion while progression stalls near8404m.
This establishes the input context, not a complete force decomposition.

Read-only hash-bound nearest-source-cell audit:
`tmp/audit-v12-bank-contact-20260927.py`, output
`tmp/sf-v12-bank-contact-20260927.json`, SHA256
`4e8381cc1860907469c40a2e912ce41dee707b8845f7564259db49affee4f9d5`.
All atlas arrays verify their450s hashes. Grid origin is a cell CENTER;
world centimetres map to hydraulic meters as(X/100,-Y/100). All57 sampled
contacts resolve one unique1m cell. At first contact the nearest center-cell
depth is1.621584m and world flow(0.124429,-0.041801)m/s, while actual recorded
pre-projection raft velocity is(0.362856,-1.790082)m/s. Their projections on
the recorded outward normal are respectively-0.034555 and-1.588095m/s.
All57 raft velocities point into the bank;34 nearest source-cell flow vectors
point outward. Center depths remain1.567007..1.621584m; bow supports reach
the wet/dry slope. Source-cell sampling is neither bilinear live engine sampling
nor the evolved local runtime state. These numbers do not prove exact force
causality, and subcell bed/triangle differences are not a mismatch diagnosis.

## Passive control completed

One same-build control, recipe `tmp/capture-sf-v12-passive-approach-20260927.ps1`,
session91743/PID35444 completed exit0. Same route8310 start, ordinary camera,
450s fields, physics/quality settings and audit arguments; omitted the paddle
command and extended recording to80 one-second observations. Rest is the actor's
default. No crew-propulsion or capture-input-issued log entries, no runtime
errors. No contact report was emitted by the >=5mm capped observation hook;
this is NOT a full zero-contact ledger. No process from this recording remains.

The raft starts at8313.787m/world2.433s, passes8405.870m at38.045s and reaches
8486.616m at81.038s. Therefore at least one passive trajectory through the
unchanged channel passes the prior bank-contact location. This does not prove
all player inputs succeed, establish exact AllForward-only causality under
variable frame timing, or qualify the whole reach. It removes the basis for
altering captured geometry simply to make the unsteered capture clear that bank.

Original video:
`tmp/south-fork-playable-v12-20260927/Windows/SmokeEmIfYouGotEm/Saved/VideoCaptures/RaftSim_20260927-153718.mp4`,
SHA256 `6be47f76b285b3ab7d8efa82fe50046610c84989045c8b4eb4132813e3191d1e`.
Decoded2,483 frames/82.733333s/40 adjacent duplicates,1280x720, originals under
`tmp/sf-v12-passive-approach-decoded-20260927`. Inspected9/20/40/47s confirms
changing raft positions and passage past the bank, but broad flat foam/spray
and coarse rocks persist. No convincing breaking/recirculating roller is shown.
Encoded rate is not performance. Hash-bound camera/site report:
`tmp/sf-v12-passive-framing-20260927.json`. Actual Cartesian submitted mesh
reports52,599 triangles,1,660,680 samples, target error0.810642cm, fine temporal
tracking0.000598cm and zero source movement over9,134 anchors. That verifies
representation of the current target, not correctness of its wave dynamics.

## Crest-reference constraint

Rechecked the primary USACE [EM1110-2-1601 notation](https://www.publications.usace.army.mil/portals/76/publications/engineermanuals/em_1110-2-1601.pdf)
and its [undular-jump discussion](https://www.publications.usace.army.mil/Portals/76/Publications/EngineerManuals/EM_1110-2-1601.pdf?ver=2013-09-04-070804-047).
The height variable is referenced above the initial depth, not an instruction
to add a full crest amplitude above an already-raised downstream surface.
Inference: this check does not justify deleting the resolved-rise subtraction
to make waves taller. Existing blend/caps/static crest-toe-tail geometry remain
authored closure, not a calibrated natural-rapid or recirculating roller model.
No reference imagery or document assets added to the game; no measured wave
dimensions or new reuse license asserted. Real breaking dynamics remain open.

## Exact continuation now running

Preparation65179 completed:450s input manifest SHA256
`0da8f20062847aea0097084f0dab7791961ebeef2972d7eb39e91a9a4c3e7657`.
ONE continuation session99863 is live, native12676/wrapper34600, started
2026-09-27T22:41:44UTC. Recipe `tmp/continue-envelope450to900-v1-20260927.py`;
receipt `tmp/troublemaker-envelope450to900-process-v1-20260927.json`;
output `tmp/troublemaker-envelope450to900-v1-20260927`.
Native frame0 independently reproduces all5,382,400 h/u/v cells bit-exact;
no context/water added, bed/roughness/boundaries/settings/features unchanged,
volume discrepancy9.313226e-10m3. Restart audit passes, not equilibrium.
9,000 steps at.05s,8 lanes, snapshots at450/600/750/900s, with final state,
bank, regional storage and local-flow audits scheduled. Observed180/459s;
poll SAME handle/receipt, never start another copy or measure FPS concurrently.
Current v12 playable450s fields stay installed pending numerical and local-flow
review. Do not build another stage merely because a snapshot exists. This run
addresses the documented6.72m3/s8..9km storage change; it is not a substitute
for dynamic breaking-water work. South Fork remains first unfinished.
