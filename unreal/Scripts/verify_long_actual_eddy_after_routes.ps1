<# One-shot continuation of an existing owned batch. Wait without polling
   CSVs or changing game sources during its timing. Reuse its exact package;
   record genuine boat motion at the same native physical obstacle/entry.
   No flow edits, guidance, proxy hull, solver or quality overrides.
#>
param(
    [Parameter(Mandatory=$true)][int]$PredecessorProcessId,
    [Parameter(Mandatory=$true)][string]$PredecessorCreationUtc,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9_.-]+$')][string]$PredecessorLabel,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9_.-]+$')][string]$Label
)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $root "tmp/$Label-driver"
if(Test-Path -LiteralPath $out){throw 'Fresh driver evidence required'}
$predecessor=Join-Path $root "tmp/$PredecessorLabel"
$progressFile=Join-Path $predecessor 'progress.json'
$routes=Join-Path $root "tmp/$PredecessorLabel-routes/index.json"
$stage=Join-Path $predecessor 'Archive/Windows'
$expectedGame='498d3bc6470b53cca0599900853289cfb27e9dedf800216c148b99b23fd9f4ef'
$binary=Join-Path $stage 'SmokeEmIfYouGotEm/Binaries/Win64/SmokeEmIfYouGotEm.exe'
New-Item -ItemType Directory -Path $out | Out-Null
$state=[ordered]@{schema='raftsim.deferred_actual_eddy_observation.v1';phase='waiting_owned_native_routes'
    predecessor_pid=$PredecessorProcessId;predecessor_creation_utc=$PredecessorCreationUtc
    predecessor_progress=$progressFile;owned_driver_pid=$PID;label=$Label
    game_sha256=$expectedGame;all_map_20fps_accepted=$false;actual_eddy_exit_accepted=$false}
function Write-Phase([string]$Phase){
    $state.phase=$Phase;$state.updated_utc=(Get-Date).ToUniversalTime().ToString('o')
    $state | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath "$out/progress.json" -Encoding UTF8
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
        if((Get-Date) -ge $deadline){throw 'Other engine work remains active; nothing interrupted or duplicated'}
        Start-Sleep -Seconds 5
    }while($true)
}
try {
    Write-Phase 'waiting_owned_native_routes'
    $target=Get-CimInstance Win32_Process -Filter "ProcessId=$PredecessorProcessId"
    if($target){
        $expected=[DateTimeOffset]::Parse($PredecessorCreationUtc).UtcDateTime
        if([Math]::Abs(($target.CreationDate.ToUniversalTime()-$expected).TotalMilliseconds) -gt 1){throw 'Predecessor PID was reused; no wait or capture started'}
        try{$process=[System.Diagnostics.Process]::GetProcessById($PredecessorProcessId)}catch [System.ArgumentException]{$process=$null}
        # Native process wait does not repeatedly scan processes or data during FPS capture.
        if($process -and -not $process.WaitForExit(10800000)){throw 'Owned route batch remains active; retained without interruption'}
    }
    $completed=Get-Content -LiteralPath $progressFile -Raw | ConvertFrom-Json
    if($completed.phase -ne 'collection_terminal_manual_pixel_and_per_frame_review_required'){
        throw 'Native batch is not healthy and terminal; no competing capture launched'
    }
    $routeIndex=Get-Content -LiteralPath $routes -Raw | ConvertFrom-Json
    if($routeIndex.runs.Count -ne 8 -or -not $routeIndex.all_eight_native_routes_complete -or
        -not $routeIndex.all_eight_routes_complete){throw 'Eight complete same-build route receipts required'}
    foreach($relative in $completed.source_sha256.PSObject.Properties){
        if((Get-FileHash -LiteralPath (Join-Path $root $relative.Name) -Algorithm SHA256).Hash -ne $relative.Value){
            throw "Candidate source changed during verification: $($relative.Name)"
        }
    }
    Wait-EngineIdle
    if((Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash.ToLower() -ne $expectedGame){throw 'Fresh package differs; retain evidence without launching'}
    Write-Phase 'independent_all_eight_every_frame_and_native_mode_audit'
    $python='C:/Users/salsi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
    $cost=Join-Path $out 'native-cost-diagnosis.json'
    & $python (Join-Path $PSScriptRoot 'analyze_all_map_route_costs.py') --index $routes --output $cost --require-sealed-rest
    if($LASTEXITCODE -ne 0){throw 'Independent all-eight native counter/whole-axis audit refused'}
    # Slow frames remain failures; they do not prevent separate physical observations.
    $state['strict_route_cost_diagnosis']=$cost
    Wait-EngineIdle
    Write-Phase 'native_120_second_same_entry_recording'
    & (Join-Path $PSScriptRoot 'capture_shared_water_map.ps1') -Map L_SouthFork_Troublemaker -Label $Label `
        -PackagedRoot $stage -ProfileFrames 9600 -FeatureAuditSeconds 120 -TimeoutS 2400 `
        -RecordingStartS 9 -RecordingEndS 110 -EddyEntry -ClearanceAudit -Overview
    $entry=Join-Path $stage "SmokeEmIfYouGotEm/Saved/WaterFeatureDemo/$Label-entry.json"
    $motion=Join-Path $stage "SmokeEmIfYouGotEm/Saved/WaterFeatureDemo/$Label.json"
    $initial=Get-Content -LiteralPath $entry -Raw | ConvertFrom-Json
    $physical='/Game/RaftSim/Maps/L_SouthFork_Troublemaker.L_SouthFork_Troublemaker:PersistentLevel.StaticMeshActor_0.StaticMeshComponent0'
    if($initial.physical_source -ne $physical -or $initial.entry_local_x_radius -ne 4 -or
        $initial.entry_local_y_radius -ne .1){throw 'Actual initial owner/entry changed; no matched eddy-exit claim'}
    Write-Phase 'actual_motion_projection_audit'
    $report=Join-Path $out 'eddy-entry-audit.json'
    & $python (Join-Path $PSScriptRoot 'audit_actual_eddy_entry.py') --entry $entry --motion $motion --report $report
    if($LASTEXITCODE -ne 0){throw 'Actual eddy motion projection refused'}
    $observed=Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
    foreach($field in @('maximum_shared_surface_error_mps','dry_became_wet')){
        $p=$observed.PSObject.Properties[$field]
        if($null -eq $p -or $null -eq $p.Value){throw "Missing native physical observation: $field"}
        $v=[double]$p.Value
        if([double]::IsNaN($v) -or [double]::IsInfinity($v) -or $v -lt 0){throw 'Invalid native physical observation'}
    }
    if($observed.map -ne 'L_SouthFork_Troublemaker' -or
        $observed.physical_source -ne $physical){throw 'Native projection belongs to another map or owner'}
    $state['actual_motion_report']=$report
    $state['actual_return_observed']=$observed.actual_return_observed
    $state['actual_head_reached']=$observed.actual_head_reached
    $state['actual_outward_downstream_exit_observed']=$observed.actual_outward_downstream_exit_observed
    $state['actual_eddy_exit_accepted']=($observed.actual_return_observed -and $observed.actual_head_reached -and
        $observed.actual_outward_downstream_exit_observed -and $observed.dry_became_wet -eq 0 -and
        $observed.maximum_shared_surface_error_mps -le .00001)
    $state['pixel_and_video_review_pending']=$true
    Write-Phase 'native_physical_observation_terminal_pixel_review_required'
}catch {
    $state['failure']=$_.Exception.Message;Write-Phase 'failed_evidence_retained';throw
}
