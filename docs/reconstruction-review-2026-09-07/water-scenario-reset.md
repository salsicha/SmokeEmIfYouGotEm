# Water scenario reset isolation

September24 production correction. `Configure` reset coordinates and clocks but
retained the previous LiveWindow, physical boulder/breaking sites, band support,
presentation baseline and local-fluid parameters. A reused adapter could therefore
sample old physical data in a newly reset coordinate frame.

Configure now releases the old window and fixed extent, resets Cartesian bounds,
report state, support/baseline fields, boulder/breaking sites and parameters,
local-fluid state and presentation clock alongside the existing coordinate reset.
Moving-window handoffs are separate and unchanged; this does not reset them on
every crop update. New scenario data must be explicitly loaded.

## Verification and limits

- Editor build16.81s and Game build47.52s pass:
  `tmp/water-scenario-reset-{editor,game}-v1-20260924.log`.
- Native reused-adapter/unavailable-water and Cartesian support suites:2 passed,
  0 failed,0 warnings; `tmp/water-scenario-reset-native-v1-20260924/index.json`.
  Same adapter loads stage5/depth2 tank, is faulted/recovered, gains a boulder
  footprint/support configuration, then reconfigures. It has no window, no boulder
  footprints, no enabled support and no successful physical queries until new
  stage8/depth3 data is loaded; new bed5 is verified. These do not exhaustively
  validate every cached support parameter in live scenery.
- Actual normal FullReach/full_descent launch with4 solver lanes exercises distant
  checkpoint relocation and return. Both restore operations succeed; each phase
  retains wet contact and progressing registered detail. Destination reset wall
  cost0.300546s; return0.027547s. These are transition costs, not frame p95.
  Native replay report:
  `unreal/Saved/RaftSimValidation/south-fork-water-scenario-reset-v1-20260924-checkpoint.json`,
  SHA256 `bee6a3c7d6ad36e94258bb97e7f881684479e94755dcc6a8e8e76e3860eadf9a`.
  Three phase detail advances9.816667/9.900001/9.883334s; fresh frames305/413/347.
  This is a checkpoint regression, not multi-river switching or full traversal.
- Actual phase1-3 and phase2-3 PNGs inspected. Water and raft are visible in both;
  the distant destination has conspicuous floating terrain fragments against the
  sky and largely bare slopes. Return shows the starting canopy and smooth water.
  **Visual acceptance fails**; the floating geometry needs investigation in the
  normal destination terrain/streaming path. Do not classify its cause from these
  images alone or count the native replay pass as a terrain pass.

Process receipt beside the replay ends in `-process.json`: engine exit0, no
timeout, cook suspend/resume statuses0, cook CPU unchanged during replay. Sole
original cook36692 resumed. Captures are editor-hosted gameplay; standalone game
target was rebuilt, not packaged-launch qualified. No new full-frame performance
claim, reconstructed terrain promotion, source change or installed-field change.
South Fork remains unfinished before the queued rivers and full release scope.
