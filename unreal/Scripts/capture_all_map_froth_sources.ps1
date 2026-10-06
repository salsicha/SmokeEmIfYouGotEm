<# Native cooked normal-spawn source receipts and first/middle/last pixels.
Not whole-map feature activation, boat progression, FPS or bubble-rise CFD.
No quality/physics overrides, legacy source switch or prescribed boat motion. #>
param(
    [Parameter(Mandatory=$true)][string]$PackagedRoot,
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_.-]{0,35}$')][string]$Label,
    [switch]$RequireCrashGatedClock
)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$stage=[IO.Path]::GetFullPath($PackagedRoot)
$allowed=[IO.Path]::GetFullPath((Join-Path $root 'tmp'))+[IO.Path]::DirectorySeparatorChar
if(-not $stage.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'Use retained project-local cooked game'}
$game=Join-Path $stage 'SmokeEmIfYouGotEm'
$binary=Join-Path $game 'Binaries/Win64/SmokeEmIfYouGotEm.exe'
if(-not (Test-Path -LiteralPath $binary -PathType Leaf) -or
    -not (Test-Path -LiteralPath (Join-Path $game 'Content/Paks') -PathType Container)){throw 'Cooked game unavailable'}
$collection=Join-Path $root "tmp/$Label"
if(Test-Path -LiteralPath $collection){throw 'Fresh all-map source evidence label required'}
New-Item -ItemType Directory -Path $collection | Out-Null
$maps=@('L_SouthForkAmerican_FullReach','L_SouthFork_Troublemaker','L_Hance','L_LavaCanyon',
    'L_Terminator','L_UpperHuacas','L_Zambezi','L_ZambeziUpperGorge')
$hash=(Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash
$runs=@()
foreach($map in $maps){
    $captureLabel="$Label-$map";$out=Join-Path $root "tmp/$captureLabel"
    $screens=Join-Path $game 'Saved/Screenshots'
    if(Test-Path -LiteralPath $out){throw 'Fresh native capture required'}
    foreach($i in 0..2){if(Test-Path -LiteralPath (Join-Path $screens ('{0}_{1:d3}.png' -f $captureLabel,$i))){throw 'Existing screenshots cannot be overwritten'}}
    $deadline=(Get-Date).AddMinutes(15);$idleSince=$null
    do {
        $busy=@(Get-CimInstance Win32_Process | Where-Object {
            $_.Name -match '^(UnrealEditor|UnrealBuildTool|SmokeEm|ShaderCompileWorker|UnrealPak|raftsim_cartesian_cook|raftsim_water_solver|blender|link\.exe)' -or
            ($_.Name -in @('dotnet.exe','cmd.exe') -and $_.CommandLine -match 'UnrealBuildTool|Build\.bat|RunUAT|AutomationTool')
        })
        if($busy.Count){$idleSince=$null}elseif($null -eq $idleSince){$idleSince=Get-Date}
        if($null -ne $idleSince -and ((Get-Date)-$idleSince).TotalSeconds -ge 60){break}
        if((Get-Date) -ge $deadline){throw 'Other shared engine work active; no duplicate launched'}
        Start-Sleep -Seconds 5
    } while($true)
    New-Item -ItemType Directory -Path $out | Out-Null
    $started=Get-Date
    $arguments=@("/Game/RaftSim/Maps/$map",'-game','-RenderOffscreen','-RaftSimEphemeralProfile',
        '-Unattended','-NoSplash','-NoSound','-ResX=1280','-ResY=720','-Windowed',
        "-AbsLog=$out/engine.log","-RaftSimFoamSourceAudit=$out/source.json","-RaftSimDetailSnapshot=$out/detail",
        "-RaftSimFoamTransportAudit=$out/foam-transport.json",
        "-ExecCmds=RaftSim.FeatureAudit $captureLabel 14,RaftSim.CaptureSeries 12 3 1 $captureLabel")
    $start=[System.Diagnostics.ProcessStartInfo]::new()
    $start.FileName=$binary;$start.WorkingDirectory=$stage;$start.UseShellExecute=$false;$start.CreateNoWindow=$true
    if($start.PSObject.Properties.Name -contains 'ArgumentList'){
        foreach($argument in $arguments){$start.ArgumentList.Add($argument)}
    }else{
        $start.Arguments=($arguments | ForEach-Object {'"'+[regex]::Replace([regex]::Replace($_,'(\\*)"','$1$1\"'),'(\\+)$','$1$1')+'"'}) -join ' '
    }
    $process=[System.Diagnostics.Process]::Start($start)
    if(-not $process.WaitForExit(900000)){$process.Kill();$process.WaitForExit();throw 'Owned source capture timed out; evidence retained'}
    $process.WaitForExit()
    $receipt=[ordered]@{schema='raftsim.all_map_froth_source_capture.v1';map=$map;arguments=$arguments;
        binary=$binary;binary_sha256=$hash;owned_process_id=$process.Id;exit_code=$process.ExitCode;
        source_and_runtime_health_verified=$false;native_screenshots=@();gpu_snapshot_metadata=@();
        visual_review_completed=$false;default_feature_wiring_and_finite_motion_verified=$false;
        all_map_feature_activation_accepted=$false;performance_qualification=$false}
    $receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$out/launch.json" -Encoding UTF8
    if($process.ExitCode -ne 0){throw "Native capture exited $($process.ExitCode)"}
    if((Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash -ne $hash){throw 'Executable changed during collection'}
    $log=Get-Content -LiteralPath "$out/engine.log" -Raw
    if($log -match 'Log\w+: (?:Error|Fatal):'){throw 'Native runtime error; evidence retained'}
    if($log -notmatch 'vertices=26610 triangles=38344 max_error_m=0'){throw 'Original full hull/render agreement missing'}
    if($log -notmatch ('LogLoad: LoadMap: /Game/RaftSim/Maps/'+[regex]::Escape($map)+'(?:\?|\s|$)')){throw 'Requested actual map not loaded'}
    if(-not (Test-Path -LiteralPath "$out/source.json") -or (Get-Item -LiteralPath "$out/source.json").LastWriteTime -lt $started){throw 'Actual source audit missing or stale'}
    $source=Get-Content -LiteralPath "$out/source.json" -Raw | ConvertFrom-Json
    if($source.schema -ne 'raftsim.directional_foam_source.v1' -or -not $source.directional_source -or $source.wet_vertices -le 0){throw 'Corrected shared source did not run on real wet map vertices'}
    foreach($field in @('wet_vertices','generic_reduced_vertices','generic_increased_vertices','legacy_generic_sum',
        'directional_generic_sum','current_final_source_sum','committed_water_seconds')){
        $property=$source.PSObject.Properties[$field]
        if($null -eq $property -or $null -eq $property.Value){throw "Missing native source field $field"}
        $value=[double]$property.Value
        if([double]::IsNaN($value) -or [double]::IsInfinity($value) -or $value -lt 0){throw "Invalid native source field $field"}
    }
    if($RequireCrashGatedClock){
        if($source.observed_is_crash_gated_source_not_optical_floor -ne $true){throw 'Captured mask still bypasses crashing-water source'}
        foreach($field in @('observed_quiet_vertices_suppressed','observed_ungated_source_sum','observed_gated_source_sum')){
            $property=$source.PSObject.Properties[$field]
            if($null -eq $property -or $null -eq $property.Value){throw "Missing observed source field $field"}
            $value=[double]$property.Value
            if([double]::IsNaN($value) -or [double]::IsInfinity($value) -or $value -lt 0){throw "Invalid observed source field $field"}
        }
        if([double]$source.observed_gated_source_sum -gt [double]$source.observed_ungated_source_sum+0.000001){throw 'Observed source gate amplified appearance evidence'}
        $transportPath="$out/foam-transport.json"
        if(-not (Test-Path -LiteralPath $transportPath) -or (Get-Item -LiteralPath $transportPath).LastWriteTime -lt $started){throw 'Current native transport/clock payload missing or stale'}
        $transport=Get-Content -LiteralPath $transportPath -Raw | ConvertFrom-Json
        if($transport.uses_committed_water_clock -ne $true -or $transport.material_clock_present -ne $true){throw 'Authored foam evolution or optical clock is not paired to accepted water'}
        foreach($field in @('foam_clock_origin_seconds','foam_field_committed_seconds','cpu_foam_phase_seconds',
            'committed_solver_seconds','material_clock_error_seconds')){
            $property=$transport.PSObject.Properties[$field]
            if($null -eq $property -or $null -eq $property.Value){throw "Missing native clock field $field"}
            $value=[double]$property.Value
            if([double]::IsNaN($value) -or [double]::IsInfinity($value) -or $value -lt 0){throw "Invalid native clock field $field"}
        }
        if([double]$transport.foam_clock_origin_seconds -gt [double]$transport.foam_field_committed_seconds -or
            [double]$transport.foam_field_committed_seconds -gt [double]$transport.committed_solver_seconds -or
            [double]$transport.cpu_foam_phase_seconds -le 0 -or
            [Math]::Abs([double]$transport.cpu_foam_phase_seconds-([double]$transport.foam_field_committed_seconds-[double]$transport.foam_clock_origin_seconds)) -gt 0.000001 -or
            [double]$transport.material_clock_error_seconds -gt 0.00001){throw 'Native accepted-water clock relationship failed'}
        if($transport.schema -in @('raftsim.carrier_foam_transport_payload.v1','raftsim.curved_foam_transport_payload.v1')){
            if($transport.shape_valid -ne $true -or $transport.feature_current_enabled -ne $true -or
                $transport.vertices -le 0 -or $transport.non_finite_vertices -ne 0){throw 'Actual carrier payload shape/current failed'}
            $errorField='maximum_submitted_transport_error_mps'
        }elseif($null -ne $transport.PSObject.Properties['audited_source_anchors']){
            if($transport.feature_kinematics_enabled -ne $true -or $transport.audited_source_anchors -le 0 -or
                $transport.wet_vertices -le 0){throw 'Actual Cartesian submitted anchors/current missing'}
            $errorField='maximum_source_transport_error_mps'
        }else{throw 'Unknown native transport payload cannot qualify froth'}
        $property=$transport.PSObject.Properties[$errorField]
        if($null -eq $property -or $null -eq $property.Value){throw 'Missing submitted current parity error'}
        $value=[double]$property.Value
        if([double]::IsNaN($value) -or [double]::IsInfinity($value) -or $value -lt 0 -or $value -gt 0.00001){throw 'Submitted froth current differs from actual backtrace'}
        $receipt['crash_gated_source_and_committed_clock_verified']=$true
        $receipt['native_transport_clock_payload']=$transportPath
    }
    $featurePath=Join-Path $game "Saved/WaterFeatureDemo/$captureLabel.json"
    if(-not (Test-Path -LiteralPath $featurePath) -or (Get-Item -LiteralPath $featurePath).LastWriteTime -lt $started){throw 'Native feature/motion history missing or stale'}
    $feature=Get-Content -LiteralPath $featurePath -Raw | ConvertFrom-Json
    if(-not $feature.feature_kinematics_enabled -or $feature.wet_probes -le 0 -or
        $feature.actual_boat_motion.Count -lt 2 -or $feature.dry_became_wet -ne 0){throw 'Default shared feature wiring/motion not verified'}
    $sharedError=$feature.PSObject.Properties['maximum_shared_surface_error_mps']
    if($null -eq $sharedError -or $null -eq $sharedError.Value -or
        [double]::IsNaN([double]$sharedError.Value) -or [double]::IsInfinity([double]$sharedError.Value) -or
        [double]$sharedError.Value -lt 0 -or [double]$sharedError.Value -gt .00001){throw 'Native shared surface/boat current parity failed'}
    $previousMotionTime=-1.0
    foreach($state in $feature.actual_boat_motion){
        foreach($field in @('world_seconds','world_x_m','world_y_m','world_z_m','yaw_deg','pitch_deg','roll_deg',
            'speed_mps','velocity_world_x_mps','velocity_world_y_mps','velocity_world_z_mps')){
            $property=$state.PSObject.Properties[$field]
            if($null -eq $property -or $null -eq $property.Value){throw "Missing native boat motion field $field"}
            $value=[double]$property.Value
            if([double]::IsNaN($value) -or [double]::IsInfinity($value)){throw 'Nonfinite native boat motion'}
        }
        if([double]$state.world_seconds -le $previousMotionTime){throw 'Native motion history is not advancing'}
        $previousMotionTime=[double]$state.world_seconds
    }
    $receipt.feature_motion_history=$featurePath
    $receipt.default_feature_wiring_and_finite_motion_verified=$true
    foreach($i in 0..2){
        $png=Join-Path $screens ('{0}_{1:d3}.png' -f $captureLabel,$i)
        if(-not (Test-Path -LiteralPath $png) -or (Get-Item -LiteralPath $png).LastWriteTime -lt $started){throw 'Native screenshot missing or stale'}
        $receipt.native_screenshots+=@{path=$png;sha256=(Get-FileHash -LiteralPath $png -Algorithm SHA256).Hash}
    }
    # Preserve actual detail readbacks when present. Their absence is recorded,
    # not fabricated as a zero-error GPU/foam result or all-map activation pass.
    $receipt.gpu_snapshot_metadata=@(Get-ChildItem -LiteralPath $out -Filter 'detail_*.json' | ForEach-Object {$_.FullName})
    $receipt.source_and_runtime_health_verified=$true
    $receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$out/launch.json" -Encoding UTF8
    $runs+=@{map=$map;launch="$out/launch.json";source="$out/source.json";native_screenshots=3;visual_review_completed=$false}
    [ordered]@{schema='raftsim.all_map_froth_source_collection.v1';maps=$maps;runs=$runs;
        binary_sha256=$hash;all_eight_source_receipts_complete=($runs.Count -eq $maps.Count);
        all_map_feature_activation_accepted=$false;performance_qualification=$false} |
        ConvertTo-Json -Depth 7 | Set-Content -LiteralPath "$collection/index.json" -Encoding UTF8
    [ordered]@{map=$map;receipt="$out/launch.json";wet_vertices=$source.wet_vertices;visual_review_pending=$true} | ConvertTo-Json
}
