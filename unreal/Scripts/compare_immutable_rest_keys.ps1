<# Same loaded modules, reference full rest scan versus normal sealed const
owner, in both execution orders. Not a whole-route or cooked FPS gate. #>
param([Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_.-]{0,30}$')][string]$Label)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location -LiteralPath $root
$out=Join-Path $root "tmp/$Label"
if(Test-Path -LiteralPath $out){throw 'Fresh comparison label required'}
New-Item -ItemType Directory -Path $out | Out-Null
$phase=[ordered]@{schema='raftsim.same_module_immutable_rest_key_comparison.v1';phase='waiting_for_idle';runs=@();packaged_or_whole_map_20fps_accepted=$false}
function Write-Phase([string]$Value){
    $phase.phase=$Value;$phase.updated_utc=[datetime]::UtcNow.ToString('o')
    $phase | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath "$out/progress.json" -Encoding UTF8
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
        if((Get-Date) -ge $deadline){throw 'Shared engine work active; no overlapping profile launched'}
        Start-Sleep -Seconds 5
    }while($true)
}
try {
    $hashes=@{}
    foreach($module in @('RaftSimRaft','RaftSimPhysics','RaftSimWater','RaftSimWaterDetail')){
        $path=Join-Path $root "unreal/Plugins/$(if($module -eq 'RaftSimWaterDetail'){'SEIYGECore'}else{'RaftSim'})/Binaries/Win64/UnrealEditor-$module.dll"
        $hashes[$path]=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
    }
    $phase.module_sha256=$hashes
    $referenceModes=@($true,$false,$false,$true)
    for($i=0;$i -lt $referenceModes.Count;$i++){
        Write-Phase "waiting_for_idle_before_run_$i"
        Wait-EngineIdle
        foreach($path in $hashes.Keys){if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $hashes[$path]){throw 'Module changed; no mixed-build comparison'}}
        $reference=[bool]$referenceModes[$i];$runLabel="$Label-$i"
        Write-Phase "native_menu_run_$i"
        & ./unreal/Scripts/profile_south_fork_menu_launch_ps5.ps1 -Label $runLabel -ProfileFrames 600 -ReferenceRestKey:$reference
        foreach($path in $hashes.Keys){if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $hashes[$path]){throw 'Module changed during profile'}}
        $receiptPath=Join-Path $root "unreal/Saved/RaftSimValidation/$runLabel-frame-audit.json"
        $receipt=Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
        if($receipt.execution_host -ne 'editor_game' -or $receipt.launch_mode -ne 'boot_menu' -or $receipt.game_exit_code -ne 0 -or
            -not $receipt.runtime_health_passes -or $receipt.diagnostic_reference_rest_key -ne $reference -or
            $receipt.diagnostic_reference_snapshot_copy -or $receipt.diagnostic_exact_snapshot_copy -or
            $null -eq $receipt.native_rest_key_observation -or $receipt.normal_configuration -ne (!$reference)){throw 'Healthy requested rest-key mode not confirmed'}
        $phase.runs+=@([ordered]@{reference_rest_key=$reference;normal_configuration=$receipt.normal_configuration;receipt=$receiptPath;
            native_rest_key_observation=$receipt.native_rest_key_observation;
            mean_frame_ms=$receipt.mean_ms;frames_below_20fps=$receipt.frames_below_20fps;csv_sha256=$receipt.csv_sha256})
    }
    Write-Phase 'terminal_same_module_cost_review_required'
}catch{
    $phase.failure=$_.Exception.Message;Write-Phase 'failed_evidence_retained';throw
}
