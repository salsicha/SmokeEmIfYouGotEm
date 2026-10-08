<#
Capture a production map with its normal raft, water configuration and materials.
Editor-hosted by default; an explicit retained packaged root uses its inner EXE.
Either mode records runtime evidence, not visual or performance acceptance.
No quality overrides, replacement hulls, scripted boat paths or solver opt-ins.
#>
param(
    [Parameter(Mandatory=$true)][ValidatePattern('^(?:Continuous/)?L_[A-Za-z0-9_]+$')][string]$Map,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9_.-]+$')][string]$Label,
    [ValidateRange(2400,9600)][int]$ProfileFrames=2400,
    # Actual limits remain enforced by the native loaded coordinate chart.
    [ValidateRange(-1,2147483647)][int]$StationM=-1,
    [ValidateRange(60,2400)][int]$TimeoutS=900,
    [ValidateRange(8.25,110)][double]$RecordingStartS=12,
    [ValidateRange(10,119)][double]$RecordingEndS=22,
    [ValidateRange(26,120)][double]$FeatureAuditSeconds=26,
    [string]$PackagedRoot='',
    [switch]$Overview,
    [switch]$ClearanceAudit,
    [switch]$EddyEntry
)
$ErrorActionPreference='Stop'
function Get-RaftSimCaptureMapIdentity {
    param([string]$RequestedMap,[string]$NativeLog)
    if($RequestedMap -cnotmatch '^(?:Continuous/)?L_[A-Za-z0-9_]+$'){
        throw 'Unsupported capture map path'
    }
    $package='/Game/RaftSim/Maps/'+$RequestedMap
    if($NativeLog -notmatch ('LogLoad: LoadMap: '+[regex]::Escape($package)+'(?:\?|\s|$)')){
        throw 'Requested map package not confirmed by native load log'
    }
    # FeatureAudit reports UWorld's leaf map name, not its package directory.
    # Verify the full loaded package above before comparing that leaf name.
    return ($RequestedMap.Split('/') | Select-Object -Last 1)
}
function Get-RaftSimCompleteFeatureAudit {
    param($Audit,[double]$RequestedSeconds,[string]$ExpectedMap)
    # Read genuine timer receipts only. A longer requested command does not
    # prove a longer run, and an early CSV exit must not qualify the eddy exit.
    foreach($field in @('requested_audit_duration_seconds','audit_world_seconds')){
        $p=$Audit.PSObject.Properties[$field]
        if($null -eq $p -or $null -eq $p.Value){throw "Native terminal field missing: $field"}
        $v=[double]$p.Value
        if([double]::IsNaN($v) -or [double]::IsInfinity($v)){throw 'Nonfinite native terminal time'}
    }
    if($Audit.map -ne $ExpectedMap){throw 'Native audit belongs to another map'}
    if([Math]::Abs([double]$Audit.requested_audit_duration_seconds-$RequestedSeconds) -gt .0001 -or
        [double]$Audit.audit_world_seconds -lt $RequestedSeconds){throw 'Requested native audit did not complete'}
    if(@($Audit.actual_boat_motion).Count -lt 2){throw 'Actual boat motion receipts missing'}
    $previous=-1.0;$maximumGap=0.0
    foreach($state in $Audit.actual_boat_motion){
        foreach($field in @('world_seconds','world_x_m','world_y_m','world_z_m','yaw_deg','pitch_deg','roll_deg',
            'speed_mps','velocity_world_x_mps','velocity_world_y_mps','velocity_world_z_mps')){
            $p=$state.PSObject.Properties[$field]
            if($null -eq $p -or $null -eq $p.Value){throw "Native state field missing: $field"}
            $v=[double]$p.Value
            if([double]::IsNaN($v) -or [double]::IsInfinity($v)){throw 'Nonfinite native boat state'}
        }
        $t=[double]$state.world_seconds
        if($t -le $previous -or $t -gt [double]$Audit.audit_world_seconds){throw 'Native state times inconsistent'}
        if($previous -ge 0){$maximumGap=[Math]::Max($maximumGap,$t-$previous)}
        $previous=$t
    }
    # Native sampling is a 0.5-world-second timer. These checks require a
    # terminal sample and at most two timer intervals, not fixed-step or
    # render-frame coverage. Do not interpolate missing motion or exempt gaps.
    if($maximumGap -gt 1.0 -or [double]$Audit.audit_world_seconds-$previous -gt 1.0){
        throw 'Native timer motion has a missing or incomplete terminal interval'
    }
    return [ordered]@{requested_seconds=$RequestedSeconds;terminal_world_seconds=[double]$Audit.audit_world_seconds
        actual_samples=@($Audit.actual_boat_motion).Count;maximum_sample_gap_seconds=$maximumGap
        final_sample_world_seconds=$previous;native_timer_duration_complete=$true
        scope='Actual world-timer states; not fixed-step sampling, pixel or FPS acceptance.'}
}
if($RecordingEndS -le $RecordingStartS){throw 'Recording must end after its start'}
if($RecordingEndS -ge $FeatureAuditSeconds){throw 'Motion audit must extend past the finalized recording'}
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if(-not (Test-Path -LiteralPath (Join-Path $root "unreal/Content/RaftSim/Maps/$Map.umap") -PathType Leaf)){
    throw 'Requested map asset is missing; no native capture started'
}
$out=Join-Path $root "tmp/$Label"
if(Test-Path -LiteralPath $out){throw "Fresh capture directory required: $out"}
if(Test-Path -LiteralPath (Join-Path $root "unreal/Saved/WaterFeatureDemo/$Label.json")){throw 'Feature audit label already exists'}
$busy=@(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match '^(UnrealEditor|UnrealBuildTool|SmokeEm|raftsim_cartesian_cook|raftsim_water_solver|blender|link\.exe)' -or
    ($_.Name -in @('dotnet.exe','cmd.exe') -and $_.CommandLine -match 'UnrealBuildTool|Build\.bat|RunUAT|AutomationTool')
})
if($busy.Count){throw 'Shared engine is busy; no capture started'}
New-Item -ItemType Directory -Path $out | Out-Null
$binary='C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$workingDirectory=$root
$projectArguments=@((Join-Path $root 'unreal/SmokeEmIfYouGotEm.uproject'))
$continuousCandidate=$Map.StartsWith('Continuous/',[StringComparison]::Ordinal)
$executionScope=if($continuousCandidate){'Editor-hosted continuous candidate; not production or packaged acceptance'}else{'Editor-hosted actual production map'}
if($PackagedRoot -ne ''){
    $stage=[IO.Path]::GetFullPath($PackagedRoot)
    $allowed=[IO.Path]::GetFullPath((Join-Path $root 'tmp'))+[IO.Path]::DirectorySeparatorChar
    if(-not $stage.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'Use a retained project-local tmp package'}
    $binary=Join-Path $stage 'SmokeEmIfYouGotEm/Binaries/Win64/SmokeEmIfYouGotEm.exe'
    if(-not (Test-Path -LiteralPath $binary -PathType Leaf)){throw 'Packaged inner EXE missing'}
    if(-not (Test-Path -LiteralPath (Join-Path $stage 'SmokeEmIfYouGotEm/Content/Paks') -PathType Container)){throw 'Cooked package missing'}
    $workingDirectory=$stage
    $projectArguments=@()
    $executionScope=if($continuousCandidate){'Packaged continuous candidate; not production or Boot/menu acceptance'}else{'Packaged actual production map (direct diagnostic map launch, not Boot/menu acceptance)'}
}
$commands="csv.UseLegacyFrameTime 0,csv.TargetFrameRateOverride 20,CsvCategory FMsgLogf disable,raftsim.RecordingDir $out"
if($StationM -ge 0){$commands+=",RaftSim.PlaceAtStation $StationM"}
if($EddyEntry){$commands+=",RaftSim.EddyEntry $Label"}
if($Overview){
    # Only a native raft-attached camera; no station walk or crew command.
    # The native camera command exits three seconds after its last screenshot.
    # Ten slots ended the slow 9600-frame recording before its CSV could flush.
    # Use the command's supported maximum200 one-minute slots (last at11949s),
    # beyond this wrapper's maximum2400s owned timeout. CSV remains the normal
    # completion path; motion duration/gap and capture-health gates are unchanged.
    # Screenshot readbacks remain diagnostic cost, never a clean FPS run.
    $commands+=",RaftSim.CaptureRaftSeries 9 200 60 $Label-overview 12 0 12 0"
}
# Optional station setup is a SINGLE placement at 4 s. EddyEntry is a final
# single verified placement at 8 s. No repeating survey timer is installed.
# Preserve setup in raw motion receipts. Optional early capture begins only
# AFTER the final 8 s placement, so it can include the genuine upstream leg.
$startText=$RecordingStartS.ToString([System.Globalization.CultureInfo]::InvariantCulture)
$endText=$RecordingEndS.ToString([System.Globalization.CultureInfo]::InvariantCulture)
$commands+=",RaftSim.ToggleRecording $startText,RaftSim.ToggleRecording $endText,RaftSim.FeatureAudit $Label $FeatureAuditSeconds,csvprofile STARTFILE=$Label,csvprofile FRAMES=$ProfileFrames"
$start=[System.Diagnostics.ProcessStartInfo]::new()
$start.FileName=$binary
$start.WorkingDirectory=$workingDirectory
$start.UseShellExecute=$false
$start.CreateNoWindow=$true
$argsList=$projectArguments+@("/Game/RaftSim/Maps/$Map",
    '-game','-RenderOffscreen','-Unattended','-NoSplash','-NoSound','-ResX=1280','-ResY=720','-Windowed',
    '-RaftSimEphemeralProfile','-csvCompression=0','-ExitAfterCsvProfiling',
    "-AbsLog=$out/engine.log","-RaftSimFoamTransportAudit=$out/foam-transport.json","-ExecCmds=$commands")
if($ClearanceAudit){
    if(-not $EddyEntry){throw 'Actual obstacle clearance audit requires the native one-time EddyEntry'}
    $argsList+='-RaftSimEddyClearanceAudit'
}
if($start.PSObject.Properties.Name -contains 'ArgumentList'){
    foreach($arg in $argsList){$start.ArgumentList.Add($arg)}
}else{
    # ProcessStartInfo on Windows PowerShell 5 uses the Windows argv quoting
    # convention directly, not cmd /c or a string-evaluated shell command.
    $start.Arguments=($argsList | ForEach-Object {
        '"'+[regex]::Replace([regex]::Replace($_,'(\\*)"','$1$1\"'),'(\\+)$','$1$1')+'"'
    }) -join ' '
}
$receipt=[ordered]@{
    schema='raftsim.production_map_capture_launch.v1';map=$Map;label=$Label;station_m=$StationM
    initial_condition_eddy_entry=[bool]$EddyEntry;recording_world_seconds=@($RecordingStartS,$RecordingEndS);raw_motion_includes_setup=$true
    motion_audit_world_seconds=$FeatureAuditSeconds;diagnostic_overview_camera=[bool]$Overview
    diagnostic_physical_clearance_audit=[bool]$ClearanceAudit
    scope="$executionScope; recording and world-timer motion are evidence, not pixel, dense collision, normal-launch or FPS acceptance."
    packaged_root=$PackagedRoot;binary=$binary;continuous_candidate=$continuousCandidate
    launched_at=(Get-Date).ToUniversalTime().ToString('o');arguments=$argsList
    binary_sha256=(Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash.ToLower()
    # These are linked editor-build provenance, not loaded packaged modules.
    editor_build_raft_dll_sha256=(Get-FileHash -LiteralPath (Join-Path $root 'unreal/Plugins/RaftSim/Binaries/Win64/UnrealEditor-RaftSimRaft.dll') -Algorithm SHA256).Hash.ToLower()
    editor_build_water_dll_sha256=(Get-FileHash -LiteralPath (Join-Path $root 'unreal/Plugins/RaftSim/Binaries/Win64/UnrealEditor-RaftSimWater.dll') -Algorithm SHA256).Hash.ToLower()
}
$process=[System.Diagnostics.Process]::Start($start)
$receipt['owned_process_id']=$process.Id
if(-not $process.WaitForExit($TimeoutS*1000)){
    $process.Kill()
    $receipt['timed_out']=$true
    $receipt | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath "$out/launch.json" -Encoding UTF8
    throw 'Only this owned capture process was terminated after timeout'
}
$process.WaitForExit()
$receipt['exit_code']=$process.ExitCode
$receipt['finished_at']=(Get-Date).ToUniversalTime().ToString('o')
$receipt | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath "$out/launch.json" -Encoding UTF8
if($process.ExitCode -ne 0){throw "Native map process exited $($process.ExitCode)"}
if((Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash.ToLower() -ne $receipt['binary_sha256']){throw 'Native executable changed during capture'}
$log=Get-Content -LiteralPath "$out/engine.log" -Raw
$nativeMap=Get-RaftSimCaptureMapIdentity $Map $log
if($StationM -ge 0){
    $placements=[regex]::Matches($log,'LogTemp: Display: PlaceAtStation single setup: station=([^ ]+)')
    if($placements.Count -ne 1 -or [double]::Parse($placements[0].Groups[1].Value,[Globalization.CultureInfo]::InvariantCulture) -ne $StationM){
        throw 'Exactly one requested native station placement required'
    }
}
$errors=@([regex]::Matches($log,'(?m)^.*\bLog\w+: (?:Error|Fatal):[^\r\n]*') | ForEach-Object {$_.Value})
$feature=if($PackagedRoot -eq ''){Join-Path $root "unreal/Saved/WaterFeatureDemo/$Label.json"}else{Join-Path $workingDirectory "SmokeEmIfYouGotEm/Saved/WaterFeatureDemo/$Label.json"}
$video=@(Get-ChildItem -LiteralPath $out -Filter '*.mp4')
$csv=@([regex]::Matches($log,'LogCsvProfiler: Display: Capture Ended\. Writing CSV to file : ([^\r\n]+\.csv)'))
[ordered]@{map=$Map;runtime_errors=$errors;feature_audit_exists=(Test-Path -LiteralPath $feature)
    foam_transport_audit_exists=(Test-Path -LiteralPath "$out/foam-transport.json");videos=$video.FullName
    csv_files=@($csv | ForEach-Object {$_.Groups[1].Value.Trim()})} | ConvertTo-Json -Depth 4
if($errors.Count -or -not (Test-Path -LiteralPath $feature) -or $video.Count -ne 1 -or $csv.Count -ne 1){throw 'Incomplete or error-bearing map evidence; no acceptance claimed'}
$audit=Get-Content -LiteralPath $feature -Raw | ConvertFrom-Json
$receipt['native_timer_duration_observation']=Get-RaftSimCompleteFeatureAudit $audit $FeatureAuditSeconds $nativeMap
$receipt['feature_motion_sha256']=(Get-FileHash -LiteralPath $feature -Algorithm SHA256).Hash.ToLower()
$receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$out/launch.json" -Encoding UTF8
