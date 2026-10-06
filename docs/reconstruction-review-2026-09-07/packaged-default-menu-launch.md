# Packaged default boot and South Fork menu handler

## Bounded post-travel capture verified, September24 follow-through

Added non-Shipping opt-in `-RaftSimPostTravelCsvFrames=900` to the existing
gameplay-controller five-second weak timer. Positive counts up to18000 call
the public CSV BeginCapture API only when not already capturing. No flag means
no timer/capture change. Existing event-only hook remains available; its prior
failure to start capture has not been attributed conclusively to engine flags.

Game build passed23.95s. Separate staged executable
`SmokeEmIfYouGotEm-BoundedCsvReview.exe`, SHA256
`d5c09179a4ee5f090f9d357bb7dffedf06a009ae887a17fb10c77851d4e9dc5a`;
normal installed executable and cooked content preserved. Launch omitted map
and scenario overrides, used ephemeral profile,1280x720 offscreen D3D12,
`-csvCompression=0 -ExitAfterCsvProfiling`, and ExecCmds
`RaftSim.MenuScreen main start=south_fork_full_descent,csv.UseLegacyFrameTime 0,csv.TargetFrameRateOverride 30,CsvCategory FMsgLogf disable`.
No parallel cook/build/test ran during capture.

Actual log verifies FullReach world_s5.016, capture start frame39,900samples,
wet raft motion, clean shutdown/exit0. Log
`tmp/post-travel-bounded-capture-20260924.log`, SHA256
`7d8228049a8a9c7ce36d5836ce4599ac0763df14b214b288f5557e79c8f4d76e`.
CSV `Saved/Profiling/CSV/Profile(20260924_064334).csv` under staged v7,
SHA256`b4c3c82555983f1ec8a6b1c18763355e52e8d05d7013a32101cd97e367e82b1b`.
Strict unchanged auditor accepts its headers; report
`tmp/post-travel-bounded-frame-audit-20260924.json`, rows60..840(781),
verified nonlegacy timing, scope offset1. Mean75.424625ms, p9583.9472ms,
FAIL33.333333ms. GameThread73.5051ms, surfaceTick44.5607ms,
solver16.13ms, publish18.27ms, SetMesh16.27ms, crest13.28ms.
Scopes nest; do not sum. Not a controlled comparison against earlier direct-map
runs, and no attribution of the higher cost to this hook or input fixes.

This removes the capture blocker only: no visible river improvement, physical
menu-input validation, shoreline/collision acceptance or release acceptance.
Packaged log still warns about blank input actions on mouse/trigger/F9;
input dispatch remains unaccepted. No warning suppression or mapping removal.
Historical failed captures below remain preserved and rejected.

2026-09-24, staged v7 Development executable; unchanged cooked content.
No live Unreal/game/cook process at entry. Both runs use an ephemeral profile,
1280x720 D3D12 offscreen, without map or scenario command-line overrides.

## Default menu rendering

`RaftSim.MenuScreen main capture=staged-v7-default-boot-menu-20260924`
uses the existing menu review hook to capture the UI. Exit0; log confirms
default `L_RaftSimBoot`, main menu and7run buttons. Inspected actual image:
South Fork is first, followed by Colorado, Pacuare, Futaleufu, Chilko, Zambezi
and Training Eddy. Career, Settings and Quit are visible. No clipped button
labels at1280x720. This is menu rendering, not mouse/focus acceptance.

Log: `tmp/staged-v7-default-boot-menu-20260924.log`.
Image: `tmp/standalone-stage-deferred-normal-v7-20260924/Windows/SmokeEmIfYouGotEm/Saved/Screenshots/staged-v7-default-boot-menu-20260924.png`.

## Menu handler to playable world

Second run uses `RaftSim.MenuScreen main start=south_fork_full_descent`.
Source inspection confirms the existing hook invokes the same `StartScenario`
method as the run-button action, rather than directly opening a map. Log shows
boot/menu first, then FullReach travel at engine frame2, completed map load in
2.592865s, single-surface carrier and live-water initialization. It continued
through900CSVframes and exited0. No direct-map/scenario launch overrides.

Log: `tmp/staged-v7-menu-south-fork-travel-20260924.log`, SHA256
`7369eb2ae276673106d16ac5ca218d3306600386782ffe16ab758232e302aec4`.
CSV under the stage's `Saved/Profiling/CSV` shares that label. The strict frame
auditor REJECTED it with `missing or duplicate CSV headers`; no performance
report was produced, and no frame-time acceptance is inferred. Existing
separate no-capture v7 p9544.1487ms still fails33.333333ms.

## Remaining limitation

The computer-use skill was inspected and its prescribed runtime initialization
attempted. The Windows JS tool failed before any app input with
`failed to write kernel assets: The system cannot find the path specified.
(os error 3)`. No alternate UI injection was attempted. Physical clicking,
keyboard focus, and end-to-end input remain unverified; this does not block
other river reconstruction work. The review hook verifies handler travel,
not input dispatch. Earlier direct-map motion captures are separate evidence,
not proof of motion or collision across this menu transition. No river acceptance.

## CSV rejection localized

Fresh inspection finds4columns named `FMsgLogf/FMsgLogfCount` and2named
`NumInstanceTransformUpdates` in the initial header. FrameTime, GameThreadTime,
RenderThreadTime, RHIThreadTime, GPUTime and the checked surface Tick/solver
StepWater columns each occur once. The installed UE5.8source declares the same
global NumInstanceTransformUpdates counter in both
`Runtime/Engine/Private/InstanceData/InstanceDataManager.cpp:741` and
`Runtime/Engine/Private/InstancedStaticMesh/ISMInstanceDataManager.cpp:685`.
Thus disabling FMsgLogf alone cannot cure this capture's duplicate headers.

The auditor intentionally rejects even unrelated duplicates; its existing
regression explicitly covers duplicate FMsgLogf columns. All13frame-auditor
tests pass unchanged. No parser relaxation, raw-CSV rewrite, deduplicated
acceptance report or engine-source edit was made. Avoid repeating the same
boot-spanning capture. Next use a post-travel capture trigger on the still-normal
menu launch (the engine supports csvStartOnEvent/csvCaptureOnEventFrameCount),
after verifying a suitable event exists or adding a scoped project event.
That isolates gameplay timing without substituting direct-map startup or
counting the current rejected file as acceptance. A new run is still required.
