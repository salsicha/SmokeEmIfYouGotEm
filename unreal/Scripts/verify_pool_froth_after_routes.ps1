<# Finish an explicitly identified owned route collection before any build.
Fresh native controls, cook, ordinary launch and real all-map source/clock pixels.
Never replaces a running game's executable; never kills another task. #>
param(
    [Parameter(Mandatory=$true)][int]$PredecessorProcessId,
    [Parameter(Mandatory=$true)][datetime]$PredecessorCreationUtc,
    [Parameter(Mandatory=$true)][string]$PredecessorRouteIndex,
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_.-]{0,25}$')][string]$Label,
    [switch]$PredecessorOrderingComparison
)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location -LiteralPath $root
$out=Join-Path $root "tmp/$Label"
if(Test-Path -LiteralPath $out){throw 'Fresh verification label required'}
New-Item -ItemType Directory -Path $out | Out-Null
$phase=[ordered]@{schema='raftsim.deferred_pool_froth_validation.v1';phase='waiting_for_owned_route_collection';
    owned_wrapper_pid=$PID;
    owned_wrapper_creation_utc=[System.Diagnostics.Process]::GetCurrentProcess().StartTime.ToUniversalTime().ToString('o');
    predecessor_process_id=$PredecessorProcessId;predecessor_creation_utc=$PredecessorCreationUtc.ToUniversalTime().ToString('o');
    predecessor_route_index=$PredecessorRouteIndex;
    predecessor_ordering_comparison=[bool]$PredecessorOrderingComparison;
    native_and_cooked_acceptance=$false;all_map_20fps_accepted=$false}
function Write-Phase([string]$Value){
    $phase.phase=$Value;$phase.updated_utc=[datetime]::UtcNow.ToString('o')
    $phase | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath "$out/progress.json" -Encoding UTF8
}
function Wait-EngineIdle {
    $deadline=(Get-Date).AddMinutes(15);$idleSince=$null
    do {
        $busy=@(Get-CimInstance Win32_Process | Where-Object {
            $_.Name -match '^(UnrealEditor|UnrealBuildTool|SmokeEm|ShaderCompileWorker|UnrealPak|raftsim_cartesian_cook|raftsim_water_solver|blender|link\.exe)' -or
            ($_.Name -in @('dotnet.exe','cmd.exe') -and $_.CommandLine -match 'UnrealBuildTool|Build\.bat|RunUAT|AutomationTool')
        })
        if($busy.Count){$idleSince=$null}elseif($null -eq $idleSince){$idleSince=Get-Date}
        if($null -ne $idleSince -and ((Get-Date)-$idleSince).TotalSeconds -ge 60){return}
        if((Get-Date) -ge $deadline){throw 'Shared engine work active; no overlapping build/capture launched'}
        Start-Sleep -Seconds 5
    } while($true)
}
Write-Phase 'waiting_for_owned_route_collection'
try {
    # Retain exact candidate identity while deferred. Later edits require a new
    # explicit verification job, not a silent claim about the earlier candidate.
    $sourceHashes=@{}
    foreach($relative in @(
        'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp',
        'unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimWaterSurfaceActor.h',
        'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimStatefulDetailComponent.cpp',
        'unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimImmutableRestMesh.h',
        'unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimRaftActor.h',
        'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimRaftActor.cpp',
        'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimHullPrepareCache.h',
        'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimRaftHullGeometry.cpp',
        'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/Tests/RaftSimFlipEnvironmentTest.cpp',
        'unreal/Plugins/SEIYGECore/Source/RaftSimWaterDetail/Public/RaftSimDetailEntrainment.h',
        'unreal/Plugins/SEIYGECore/Source/RaftSimWaterDetail/Private/Tests/RaftSimRapidPoolFrothTest.cpp',
        'unreal/Plugins/RaftSim/Source/RaftSimPhysics/Public/RaftSimHullArcPair.h',
        'unreal/Plugins/RaftSim/Source/RaftSimPhysics/Public/RaftSimFaceOrdering.h',
        'unreal/Plugins/RaftSim/Source/RaftSimPhysics/Public/RaftSimEndpointFaceTree.h',
        'unreal/Plugins/RaftSim/Source/RaftSimPhysics/Private/RaftSimGroundSourceRegistry.cpp',
        'unreal/Plugins/RaftSim/Source/RaftSimPhysics/Private/RaftSimTriangleSweep.cpp',
        'unreal/Plugins/RaftSim/Source/RaftSimPhysics/Private/Tests/RaftSimHullContactTest.cpp',
        'unreal/Scripts/capture_all_map_froth_sources.ps1')){
        $sourceHashes[$relative]=(Get-FileHash -LiteralPath (Join-Path $root $relative) -Algorithm SHA256).Hash
    }
    $phase.source_sha256=$sourceHashes;Write-Phase 'waiting_for_owned_route_collection'
    $prior=Get-CimInstance Win32_Process -Filter "ProcessId=$PredecessorProcessId"
    if($prior){
        if($prior.CreationDate.ToUniversalTime() -ne $PredecessorCreationUtc.ToUniversalTime()){throw 'Predecessor PID reused; no build launched'}
        try{$process=[System.Diagnostics.Process]::GetProcessById($PredecessorProcessId)}
        catch [System.ArgumentException]{$process=$null}
        # Native process wait causes no repeated process/CSV scans during FPS capture.
        if($process -and -not $process.WaitForExit(10800000)){throw 'Owned predecessor still active after three hours; retained without interruption'}
    }
    $routes=Get-Content -LiteralPath $PredecessorRouteIndex -Raw | ConvertFrom-Json
    if($PredecessorOrderingComparison){
        # Qualification collection is four real routes, not an eight-map pass.
        # Preserve that scope and every slow frame. The NEW game still must
        # independently complete all eight source/clock views and FPS routes.
        if($routes.phase -ne 'terminal_same_module_ordering_cost_review_required' -or
            $routes.failure -or $routes.whole_route_camera_only -ne $true -or
            $routes.runs.Count -ne 4){throw 'Complete healthy ordering comparison required'}
        $expectedModes=@($false,$true,$true,$false)
        for($i=0;$i -lt 4;$i++){
            $run=$routes.runs[$i];$cost=$run.native_ordering_cost
            if($run.radix_order -ne $expectedModes[$i]){throw 'Original/candidate comparison order differs'}
            foreach($metric in @('radix_queries','reference_queries','ordering_mean_ms','traversal_mean_ms')){
                if($null -eq $cost.$metric -or [double]::IsNaN($cost.$metric) -or
                    [double]::IsInfinity($cost.$metric) -or $cost.$metric -lt 0){throw 'Native ordering evidence incomplete or nonfinite'}
            }
            if(($run.radix_order -and ($cost.radix_queries -le 0 -or $cost.reference_queries -ne 0)) -or
                (!$run.radix_order -and ($cost.reference_queries -le 0 -or $cost.radix_queries -ne 0))){throw 'Actual requested ordering queries required'}
            $audit=Get-Content -LiteralPath $run.receipt -Raw | ConvertFrom-Json
            if($audit.map -ne 'L_Zambezi' -or $audit.camera_whole_route_complete -ne $true -or
                $audit.audited_frames -ne $run.all_active_route_frames -or
                $audit.frames_below_20fps -ne $run.frames_below_20fps -or
                $audit.worst_ms -ne $run.frame_worst_ms){throw 'Independent complete-route evidence differs'}
        }
        foreach($module in $routes.module_sha256.PSObject.Properties){
            if((Get-FileHash -LiteralPath $module.Name -Algorithm SHA256).Hash -ne $module.Value){throw 'Qualified native modules changed before rebuild'}
        }
        $phase.predecessor_scope='Four same-module ordering routes, not all-map FPS acceptance'
    }elseif($routes.runs.Count -ne 8 -or $routes.all_eight_native_routes_complete -ne $true -or
        $routes.all_eight_routes_complete -ne $true){throw 'Predecessor did not complete eight healthy same-build routes; evidence retained'}
    Wait-EngineIdle
    foreach($relative in $sourceHashes.Keys){
        if((Get-FileHash -LiteralPath (Join-Path $root $relative) -Algorithm SHA256).Hash -ne $sourceHashes[$relative]){throw "Deferred source changed: $relative"}
    }
    Write-Phase 'building_native_controls'
    $buildArgs=@('SmokeEmIfYouGotEmEditor','Win64','Development',
        "-Project=$root/unreal/SmokeEmIfYouGotEm.uproject",'-WaitMutex','-NoHotReload')
    & 'C:/Program Files/Epic Games/UE_5.8/Engine/Build/BatchFiles/Build.bat' @buildArgs 2>&1 |
        Tee-Object -FilePath "$out/native-build.log"
    if($LASTEXITCODE -ne 0){throw 'Native editor build failed; no cook launched'}
    Write-Phase 'native_original_hull_water_controls'
    & ./unreal/Scripts/verify_exact_ground_and_flip.ps1 -Label "$Label-native" -IncludeWaterControls
    Wait-EngineIdle
    Write-Phase 'fresh_game_build_cook_archive'
    $cookArgs=@('BuildCookRun',"-project=$root/unreal/SmokeEmIfYouGotEm.uproject",'-platform=Win64','-clientconfig=Development',
        '-build','-cook','-stage','-pak','-package','-archive',"-archivedirectory=$out/Archive",'-nop4','-utf8output','-unattended')
    & 'C:/Program Files/Epic Games/UE_5.8/Engine/Build/BatchFiles/RunUAT.bat' @cookArgs 2>&1 |
        Tee-Object -FilePath "$out/build-cook.log"
    if($LASTEXITCODE -ne 0){throw 'Fresh standalone build/cook failed; evidence retained'}
    Wait-EngineIdle
    Write-Phase 'normal_packaged_menu'
    & ./unreal/Scripts/profile_south_fork_menu_launch_ps5.ps1 -Label "$Label-menu" -ProfileFrames 600 -PackagedRoot "$out/Archive/Windows"
    Wait-EngineIdle
    Write-Phase 'all_eight_actual_source_clock_and_pixels'
    & ./unreal/Scripts/capture_all_map_froth_sources.ps1 -Label "$Label-sources" -PackagedRoot "$out/Archive/Windows" -RequireCrashGatedClock
    Wait-EngineIdle
    Write-Phase 'actual_fullreach_rapid_pool_readbacks'
    & ./unreal/Scripts/capture_packaged_rapid_pool_froth.ps1 -Label "$Label-pools" -PackagedRoot "$out/Archive/Windows"
    Wait-EngineIdle
    Write-Phase 'whole_axis_native_routes'
    & ./unreal/Scripts/profile_all_map_flythroughs.ps1 -Label "$Label-routes" -PackagedRoot "$out/Archive/Windows"
    # Completion here is evidence collection, not automatic visual/physical/FPS acceptance.
    Write-Phase 'collection_terminal_manual_pixel_and_per_frame_review_required'
}catch{
    $phase.failure=$_.Exception.Message;Write-Phase 'failed_evidence_retained';throw
}
