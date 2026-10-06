<# Guarded full native rebuild and exact production-array controls, then an
ordinary Boot/menu pilot. No cook or full-route/FPS acceptance is inferred. #>
param([Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_.-]{0,30}$')][string]$Label)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location -LiteralPath $root
$out=Join-Path $root "tmp/$Label"
if(Test-Path -LiteralPath $out){throw 'Fresh pilot label required; prior evidence retained'}
New-Item -ItemType Directory -Path $out | Out-Null
$phase=[ordered]@{schema='raftsim.exact_snapshot_copy_pilot.v1';phase='waiting_for_shared_engine_idle';packaged_or_whole_route_20fps_accepted=$false}
function Write-Phase([string]$Value){
    $phase.phase=$Value;$phase.updated_utc=[datetime]::UtcNow.ToString('o')
    $phase | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$out/progress.json" -Encoding UTF8
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
        if((Get-Date) -ge $deadline){throw 'Shared work remains active; no overlapping build or game launched'}
        Start-Sleep -Seconds 5
    }while($true)
}
try {
    $hashes=@{}
    foreach($relative in @(
        'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimHullPrepareCache.h',
        'unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimImmutableRestMesh.h',
        'unreal/Plugins/RaftSim/Source/RaftSimRaft/Public/RaftSimRaftActor.h',
        'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimRaftActor.cpp',
        'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimRaftHullGeometry.cpp',
        'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/Tests/RaftSimFlipEnvironmentTest.cpp',
        'unreal/Plugins/RaftSim/Source/RaftSimPhysics/Public/RaftSimHullArcPair.h',
        'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimWaterSurfaceActor.cpp',
        'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/RaftSimStatefulDetailComponent.cpp',
        'unreal/Plugins/SEIYGECore/Source/RaftSimWaterDetail/Public/RaftSimDetailEntrainment.h')){
        $hashes[$relative]=(Get-FileHash -LiteralPath (Join-Path $root $relative) -Algorithm SHA256).Hash
    }
    $phase.source_sha256=$hashes;Write-Phase 'waiting_for_shared_engine_idle'
    Wait-EngineIdle
    foreach($relative in $hashes.Keys){
        if((Get-FileHash -LiteralPath (Join-Path $root $relative) -Algorithm SHA256).Hash -ne $hashes[$relative]){throw "Candidate source changed before build: $relative"}
    }
    Write-Phase 'native_full_build'
    & 'C:/Program Files/Epic Games/UE_5.8/Engine/Build/BatchFiles/Build.bat' 'SmokeEmIfYouGotEmEditor' 'Win64' 'Development' "-Project=$root/unreal/SmokeEmIfYouGotEm.uproject" '-WaitMutex' '-NoHotReload' 2>&1 |
        Tee-Object -FilePath "$out/native-build.log"
    if($LASTEXITCODE -ne 0){throw 'Native full build failed; no new game or cook launched'}
    Write-Phase 'native_original_hull_and_water_controls'
    & ./unreal/Scripts/verify_exact_ground_and_flip.ps1 -Label "$Label-native" -IncludeWaterControls
    Wait-EngineIdle
    Write-Phase 'ordinary_editor_boot_menu_pilot'
    & ./unreal/Scripts/profile_south_fork_menu_launch_ps5.ps1 -Label "$Label-menu" -ProfileFrames 600
    foreach($relative in $hashes.Keys){
        if((Get-FileHash -LiteralPath (Join-Path $root $relative) -Algorithm SHA256).Hash -ne $hashes[$relative]){throw "Candidate source changed during verification: $relative"}
    }
    Write-Phase 'native_pilot_terminal_packaged_and_whole_route_measurement_required'
}catch{
    $phase.failure=$_.Exception.Message;Write-Phase 'failed_evidence_retained';throw
}
