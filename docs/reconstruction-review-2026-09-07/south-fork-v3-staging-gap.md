# Current South Fork bundle: standalone staging gap

September 26, 2026 follow-through after `ce5260aeb`.

The saved editor scene uses the new discharge-bed runtime and the build rules
select `south_fork_discharge_bed_v3`. However, the actual standalone staging
tree at `unreal/Binaries/Win64/RaftSimRuntimeData` still contains earlier runtime
directories and is missing the new snapshot and streaming manifest. The
[failed active-bundle receipt](south-fork-v3-stage-before.json) records the
first missing dependency, the 600 s snapshot's `h.npy`.

This is a standalone rebuild/staging gap, not evidence that editor gameplay
loads the old water. The internally verified v3 bundle exists and is intact;
selecting it in build rules does not retroactively update a previous standalone
build or cooked installation. The preceding integration's word "staged" should
not be read as standalone execution acceptance.

## Repair completed

`unreal/Scripts/verify_south_fork_runtime_bundle.py` previously hardcoded v2.
It could compare an old staged tree with old source data without checking the
bundle now selected by the build. It now resolves the single active
`StageVerifiedRuntimeBundle` call from `RaftSimWater.Build.cs`, rejects ambiguous
or unsafe selections, and records the selected bundle in its result. It also
rejects using the source root as the staged root.

The new command-line verifier uses the same selection and validates the actual
staged dependency closure. Three tests pass for changed selection, ignored
historical comments, ambiguous/missing calls and unsafe/non-South-Fork paths.
The real v3 staging check correctly fails; that failure is not waived.

## Remaining action

Run a normal standalone Development rebuild, then verify the resulting staged
v3 tree and run the fresh native staged-path comparison. Finally regenerate and
validate the cooked game before claiming packaged execution acceptance.

The other session was running rendered, CSV-profiled
`RaftSim.P4.SouthForkApproachDraftTelemetry` (PID11024). After it exited,
a guarded standalone build was attempted; the guard detected the next profile
(PID33088, `traverse-approach3-20260926`) and stopped before invoking the build.
No parallel compiler, engine, recook or manual staging copy was started; the
rebuild must wait for an idle host to avoid contaminating that measurement.
This is not a permission or disk-space blocker and needs no new user authority.
Do not rerun the unchanged missing-file check until a build/staging change occurs.

```powershell
python -B -m unittest discover -s physics/tests -p test_active_south_fork_stage.py -v
python -B physics/scripts/verify_active_south_fork_stage.py --staged-root unreal/Binaries/Win64/RaftSimRuntimeData --report tmp/NEW_UNIQUE_AUDIT/current-stage.json
```

These checks add no visual improvement and accept neither hydraulics nor
performance. South Fork remains the eligible river.
