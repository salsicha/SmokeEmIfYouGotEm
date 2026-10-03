<# Same loaded modules, explicit original versus normal exact radix ordering
in both execution orders. Optional complete camera axis; freely integrated
original raft. No guidance, recording, altered water, simplified hull or cook. #>
param([Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_.-]{0,30}$')][string]$Label,
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_.-]+$')][string]$NativeControlLabel='water-face-order-v8b-native',
    [switch]$WholeRoute)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location -LiteralPath $root
$out=Join-Path $root "tmp/$Label"
if(Test-Path -LiteralPath $out){throw 'Fresh ordering comparison label required'}
New-Item -ItemType Directory -Path $out | Out-Null
$phase=[ordered]@{schema='raftsim.same_module_landscape_face_ordering.v1';phase='waiting_for_idle';runs=@()
    owned_wrapper_pid=$PID;wrapper_creation_utc=[datetime]::UtcNow.ToString('o')
    map='L_Zambezi';station_m=$(if($WholeRoute){$null}else{4650});whole_route_camera_only=[bool]$WholeRoute
    packaged_or_whole_map_20fps_accepted=$false}
function Write-Phase([string]$Value){
    $phase.phase=$Value;$phase.updated_utc=[datetime]::UtcNow.ToString('o')
    $phase | ConvertTo-Json -Depth 9 | Set-Content -LiteralPath "$out/progress.json" -Encoding UTF8
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
        if((Get-Date) -ge $deadline){throw 'Shared work remains active; no overlapping native profile'}
        Start-Sleep -Seconds 5
    }while($true)
}
function Read-OrderingCosts([string]$CsvPath,[bool]$Radix){
    $lines=Get-Content -LiteralPath $CsvPath;$footer=-1
    for($i=$lines.Count-1;$i -gt 0;$i--){if($lines[$i].StartsWith('EVENTS,')){$footer=$i;break}}
    if($footer -lt 0){throw 'Native CSV footer missing'}
    $header=$lines[$footer].Split(',');$indices=@{}
    foreach($metric in @('RaftSimGround/LandscapeRadixOrderQueries','RaftSimGround/LandscapeReferenceOrderQueries',
        'RaftSimGround/GameThread/LandscapeFaceOrdering','RaftSimGround/GameThread/LandscapeFaceTraversal')){
        if(@($header | Where-Object {$_ -eq $metric}).Count -ne 1){throw "Exactly one actual ordering column required: $metric"}
        $indices[$metric]=[array]::IndexOf($header,$metric)
    }
    $radixQueries=0.0;$referenceQueries=0.0;$orderingMs=0.0;$traversalMs=0.0;$qualifiedFrames=0;$queryFrames=0
    for($i=31;$i -lt $footer-30;$i++){
        $cells=$lines[$i].Split(',');$values=@{}
        foreach($metric in @('RaftSimGround/LandscapeRadixOrderQueries','RaftSimGround/LandscapeReferenceOrderQueries')){
            $index=$indices[$metric]
            if($index -ge $cells.Count -or [string]::IsNullOrWhiteSpace($cells[$index])){throw 'Native ordering sample missing'}
            $v=[double]::Parse($cells[$index],[Globalization.CultureInfo]::InvariantCulture)
            if([double]::IsNaN($v) -or [double]::IsInfinity($v) -or $v -lt 0){throw 'Native ordering sample invalid'}
            $values[$metric]=$v
        }
        $r=$values['RaftSimGround/LandscapeRadixOrderQueries'];$c=$values['RaftSimGround/LandscapeReferenceOrderQueries']
        if($r -ne [math]::Floor($r) -or $c -ne [math]::Floor($c)){throw 'Native query counters must be integers'}
        if(($Radix -and $c -ne 0) -or (!$Radix -and $r -ne 0)){throw 'Unrequested native ordering mode observed'}
        $radixQueries+=$r;$referenceQueries+=$c
        $qualifiedFrames++
        # Explicit native zero-query counters prove the branch did not run.
        # Do not invent a timing sample for optional unexecuted scopes. Every
        # frame with an actual query must have both complete finite timings.
        if($r+$c -gt 0){
            foreach($metric in @('RaftSimGround/GameThread/LandscapeFaceOrdering','RaftSimGround/GameThread/LandscapeFaceTraversal')){
                $index=$indices[$metric]
                if($index -ge $cells.Count -or [string]::IsNullOrWhiteSpace($cells[$index])){throw 'Executed native ordering timing missing'}
                $v=[double]::Parse($cells[$index],[Globalization.CultureInfo]::InvariantCulture)
                if([double]::IsNaN($v) -or [double]::IsInfinity($v) -or $v -lt 0){throw 'Executed native ordering timing invalid'}
                $values[$metric]=$v
            }
            $orderingMs+=$values['RaftSimGround/GameThread/LandscapeFaceOrdering']
            $traversalMs+=$values['RaftSimGround/GameThread/LandscapeFaceTraversal'];$queryFrames++
        }
    }
    $queries=$radixQueries+$referenceQueries
    if($qualifiedFrames -lt 1 -or $queries -le 0){throw 'No actual terrain ordering queries observed; cannot qualify cost'}
    return [ordered]@{audited_frames=$qualifiedFrames;frames_with_actual_queries=$queryFrames;radix_queries=$radixQueries;reference_queries=$referenceQueries
        ordering_mean_ms=$orderingMs/$qualifiedFrames;traversal_mean_ms=$traversalMs/$qualifiedFrames
        ordering_ms_per_actual_query=$orderingMs/$queries;csv_sha256=(Get-FileHash -LiteralPath $CsvPath -Algorithm SHA256).Hash
        scope='Actual native stage/counter costs; poses need not be identical across freely integrated runs. Same-input exactness and operation costs have separate original-asset native controls.'}
}
try {
    $hashes=@{}
    foreach($module in @('RaftSimRaft','RaftSimPhysics','RaftSimWater','RaftSimWaterDetail','RaftSimAutomation')){
        $path=Join-Path $root "unreal/Plugins/RaftSim/Binaries/Win64/UnrealEditor-$module.dll"
        $hashes[$path]=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
    }
    $phase.module_sha256=$hashes
    $controlDirectory=Join-Path $root "tmp/$NativeControlLabel"
    $controlLaunch=Get-Content -LiteralPath (Join-Path $controlDirectory 'launch.json') -Raw | ConvertFrom-Json
    $controls=Get-Content -LiteralPath (Join-Path $controlDirectory 'index.json') -Raw | ConvertFrom-Json
    if($controlLaunch.exit_code -ne 0 -or @($controlLaunch.tests).Count -ne 26 -or $controls.failed -or $controls.notRun -or
        $controls.inProcess -or $controls.succeeded+$controls.succeededWithWarnings -ne 26){throw 'Complete linked native controls required before timing'}
    foreach($name in $controlLaunch.tests){
        $matches=@($controls.tests | Where-Object {$_.fullTestPath -eq $name})
        if($matches.Count -ne 1 -or $matches[0].state -ne 'Success'){throw "Required linked native control not successful: $name"}
    }
    foreach($property in $controlLaunch.dll_sha256.PSObject.Properties){
        if(!$hashes.ContainsKey($property.Name) -or $hashes[$property.Name] -ne $property.Value){throw 'Native control module differs from comparison module'}
    }
    if(@($controlLaunch.dll_sha256.PSObject.Properties).Count -ne 4){throw 'Four original hull/water native control modules required'}
    $phase.linked_native_controls=Join-Path $controlDirectory 'index.json'
    $sourceHashes=@{}
    foreach($relative in @('unreal/Plugins/RaftSim/Source/RaftSimPhysics/Public/RaftSimFaceOrdering.h',
        'unreal/Plugins/RaftSim/Source/RaftSimPhysics/Public/RaftSimEndpointFaceTree.h',
        'unreal/Plugins/RaftSim/Source/RaftSimPhysics/Private/RaftSimGroundSourceRegistry.cpp',
        'unreal/Plugins/RaftSim/Source/RaftSimPhysics/Private/Tests/RaftSimSurfaceSweepTest.cpp',
        'unreal/Plugins/RaftSim/Source/RaftSimRaft/Private/Tests/RaftSimFlipEnvironmentTest.cpp')){
        $sourceHashes[$relative]=(Get-FileHash -LiteralPath (Join-Path $root $relative) -Algorithm SHA256).Hash
    }
    $phase.source_sha256=$sourceHashes
    $candidateModes=@($false,$true,$true,$false)
    for($i=0;$i -lt $candidateModes.Count;$i++){
        Write-Phase "waiting_for_idle_before_run_$i"
        if(!$WholeRoute){Wait-EngineIdle} # Whole-route launcher owns its60s idle guard.
        foreach($path in $hashes.Keys){if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $hashes[$path]){throw 'Loaded modules changed; no mixed-build comparison'}}
        foreach($relative in $sourceHashes.Keys){if((Get-FileHash -LiteralPath (Join-Path $root $relative) -Algorithm SHA256).Hash -ne $sourceHashes[$relative]){throw 'Candidate source changed; no mixed-candidate comparison'}}
        $radix=[bool]$candidateModes[$i];$runLabel="$Label-$i";Write-Phase "native_zambezi_run_$i"
        if($WholeRoute){
            & ./unreal/Scripts/profile_map_flythrough.ps1 -Map L_Zambezi -Label $runLabel -ReferenceLandscapeOrder:(!$radix) | Out-Null
        }else{
            & ./unreal/Scripts/profile_reference_map_ps5.ps1 -Map L_Zambezi -Label $runLabel -ProfileFrames 600 -StationM 4650 -ReferenceLandscapeOrder:(!$radix) | Out-Null
        }
        foreach($path in $hashes.Keys){if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $hashes[$path]){throw 'Loaded modules changed during profile'}}
        if($WholeRoute){
            $receiptPath=Join-Path $root "tmp/$runLabel/route-audit.json"
            $launch=Get-Content -LiteralPath (Join-Path $root "tmp/$runLabel/launch.json") -Raw | ConvertFrom-Json
            $receipt=Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
            if($launch.map -ne 'L_Zambezi' -or $receipt.map -ne 'L_Zambezi' -or $launch.exit_code -ne 0 -or
                $launch.diagnostic_radix_landscape_order -ne $false -or $launch.diagnostic_reference_landscape_order -ne (!$radix) -or
                $launch.production_collision_defaults -ne $radix -or
                $launch.boat_guidance -ne $false -or $launch.recording -ne $false -or $launch.screenshots -ne $false -or
                !$receipt.camera_whole_route_complete){throw 'Healthy complete unguided requested native route required'}
            $native=Get-Content -LiteralPath (Join-Path $root "unreal/Saved/RaftSimValidation/FlyThrough/$runLabel/route.json") -Raw | ConvertFrom-Json
            $cost=Read-OrderingCosts $native.csv $radix
            $phase.runs+=@([ordered]@{radix_order=$radix;receipt=$receiptPath;frame_worst_ms=$receipt.worst_ms
                all_active_route_frames=$receipt.audited_frames;frames_below_20fps=$receipt.frames_below_20fps;native_ordering_cost=$cost})
        }else{
            $receiptPath=Join-Path $root "unreal/Saved/RaftSimValidation/$runLabel-frame-audit.json"
            $receipt=Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
            if($receipt.map -ne 'L_Zambezi' -or $receipt.station_m -ne 4650 -or @($receipt.runtime_errors).Count -ne 0 -or
                $receipt.diagnostic_radix_landscape_order -ne $false -or $receipt.diagnostic_reference_landscape_order -ne (!$radix) -or
                $receipt.production_collision_defaults -ne $radix){
                throw 'Requested healthy native map and ordering mode not confirmed'
            }
            $cost=Read-OrderingCosts $receipt.csv $radix
            $phase.runs+=@([ordered]@{radix_order=$radix;receipt=$receiptPath;frame_mean_ms=$receipt.mean_ms
                frame_worst_ms=$receipt.max_ms;frames_below_20fps=$receipt.frames_below_20fps;native_ordering_cost=$cost})
        }
    }
    Write-Phase 'terminal_same_module_ordering_cost_review_required'
}catch{
    $phase.failure=$_.Exception.Message;Write-Phase 'failed_evidence_retained';throw
}
