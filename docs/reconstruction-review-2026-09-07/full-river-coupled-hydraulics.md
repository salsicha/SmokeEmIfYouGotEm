# Cartesian hydraulic coupling prerequisite — September 12

Status at 08:18 UTC: native coupling implemented and tested; Unreal target
rebuild RUNNING. No whole-river flow cook or normal-map promotion in this pass.
South Fork remains the scenario; Troublemaker stays a rapid inside it and off
the menu. Breaking-wave/froth appearance is not accepted by these diagnostics.

Follow-up at 08:44 UTC: that rebuild finished exit 0 (1,938.63 seconds).
The subsequent two-axis surface build also finished; sixteen runtime and two
actual-game regressions pass. All jobs are now terminal. See
[Cartesian surface and disjoint geometry](full-river-cartesian-surface.md)
for the completed build/test ledger and source-exact 826-core flow geometry.
No whole-river flow or normal-map terrain promotion has occurred yet.

## Implemented

Native boundary profiles now carry two layers of explicit bed, depth and signed
XY velocity on any of the four edges. Profiles are validated and loaded from
scenario JSON. MUSCL reconstruction uses the same limiter, positivity treatment
and source bed as interior faces. Scalar boundaries retain their old behavior.

`CartesianWaterDomain` joins disjoint, equal-sized tiles on one common lattice.
Internal edges exchange exact neighboring states at both RK2 stages, with a
barrier between stages and a common CFL timestep. They are not physical river
inlets or banks. Missing neighboring tiles retain explicit physical boundary
conditions; the class does NOT infer correct river inflow, outflow or stage.
Internal-interface treatment is consistent with the distinction documented in
[Clawpack's boundary documentation](https://www.clawpack.org/bc.html).

Tile coupling rejects incompatible solver settings, misaligned/duplicate
footprints, invalid state and incomplete boundary profiles. Existing row workers
also distribute tiles without nested parallel row work. Existing MUSCL final
combination/friction/state update arithmetic is shared, not duplicated.

## Verification

Candidate: `tmp/troublemaker-row-solver-cartesian-v1-20260912` (historical build
directory naming is not a scenario/menu entry). Latest CTest: all FOUR pass,
2.99 seconds: Cartesian domain, wet/dry shoreline, lake-at-rest, transcritical.

- Analytic nonflat still water and moving wet/dry cases, including positive
  shallow film, use four and sixteen tiles with non-square metric cells.
  Fifty steps produce zero state/face-flux difference from the unsplit solver.
  Reversing tile order also passes. Maximum closed volume drift is
  3.41061e-13 cubic metres. Source bed remains exact.
- Signed uniform four-edge profiles pass in both flow directions. Invalid
  profile lengths/depths, first-order mode, misaligned and duplicate tiles fail.
- The retained South Fork join package is cropped without interpolation to
  256 by 256 cells (offset column 100, row 32). Its actual adjacent source cells
  supply two exterior ghost layers. Sixteen 64 by 64 tiles over ten 0.005-second
  steps match the unsplit diagnostic: maximum state difference 4.74338e-20,
  face flux difference 5.55112e-16, summed volume difference 7.27596e-11 m3.
  Finite states and fluxes are explicitly checked. Its open-boundary volume
  change of 0.0188484 m3 is NOT closed-domain mass drift or a settling result.
  Fixed initial exterior states are a short partition test, not accepted
  physical full-river boundaries or a new settled discharge measurement.
- On-disk native parser test:
  `tmp/south-fork-cartesian-profile-parser-v3-20260912/parser_audit.json`.
  All three output frames retain uniform depth and XY velocity exactly.
  Native exit 0. Scenario SHA256
  `accef250811e9a7355e96ec262993bfe5641abbd76e9df1c36784501d3fa5f20`.
  Retained first failure used unsupported uint8 wet-mask dtype; corrected to
  bool. Second solver succeeded but harness looked in the wrong CSV directory;
  corrected in v3. Neither earlier failure was deleted.

Actual-source diagnostic command, after building the candidate:

```powershell
& tmp/troublemaker-row-solver-cartesian-v1-20260912/raftsim_cartesian_domain_tests.exe tmp/south-fork-composite-join-cook-20260912/scenario/south_fork_composite_join_1m
```

## Runtime rebuild — inspect before any editor launch

Installed archive `physics/cpp/build-ue/raftsim_water.lib` SHA256:
`e69772d2c856054f6bb37035486e6828c47d3ee3eebdbf9b0261dec6fb9a678c`.
Candidate matches. Previous archive retained and hash-verified at
`tmp/troublemaker-row-solver-cartesian-v1-20260912/previous-playable-before-cartesian.lib`,
SHA256 `385a1622637a573c47f48f38981cb47e33182f0c58cc3ba9e066daf28152b565`.
Installation followed passing native tests with no editor running. Later
test-only rebuilds did not change the installed or candidate archive.

The boundary structure changed native ABI. ALL Unreal consumer DLLs must finish
rebuilding before launching editor/game. Full 172-action build started 08:05 UTC,
PTY session 43455, UBT dotnet PID 27180. At 08:18 UTC action 83/172 is complete;
the process is still RUNNING. Do not start a duplicate build or claim runtime
regressions passed against this archive yet. Inspect session/process and
`C:/Users/salsi/AppData/Local/UnrealBuildTool/Log.txt`, then await terminal status.
Build uses `-NoUBA -MaxParallelActions=4 -WaitMutex -NoHotReloadFromIDE`.

After successful build, rerun catalog/migration, Cartesian exact overlap,
both-axis streaming actor, moving river window, Cartesian source selector and
global-progress regressions under an ephemeral profile. Inspect report JSON:
Unreal process exit 0 alone does not prove tests passed.

## Remaining delivery

This removes internal tile-wall/one-edge assumptions, not the need to establish
physical put-in/outlet conditions and settled, conservative whole-river flow.
The 799 overlapping geometry packets can supply disjoint 80 m cores on their
common 1 m lattice, but no such full-domain cook was started here. Captured
surface remains distinct from measured bed and settled water stage.

Next: whole-river package/driver and physically appropriate exterior conditions;
flow/conservation/settling checks; two-axis render-carrier geometry and temporal
handoff; coherent normal FullReach terrain/material/global-axis/start/section/
finish migration; actual gameplay visuals and cost. Keep the full-grid survey
replay safeguard. Do not promote isolated rapid flow as the whole river.

Normal map and user save hashes were rechecked unchanged at 08:18 UTC:
map `e77da92b73bf0a2c566fe69ee8a0ef7115d26182bb2f91648582aa1197ce13a0`;
save `181d1e570485d1ec3139aec4e1d9b56d0a420fd107ce5a94218368324207f5b1`.
Free space then 4,622,315,520 bytes. No files deleted, maps saved or commits made.
