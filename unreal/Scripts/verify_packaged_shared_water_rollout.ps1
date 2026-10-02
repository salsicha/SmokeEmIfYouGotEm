<# Run settled shared water effects in every actual playable river map.
   No solver, quality, material, collider, force or scripted-motion overrides.
   Capture and runtime parity are regression evidence, not a 20 FPS benchmark.
#>
param(
    [Parameter(Mandatory=$true)][string]$PackagedRoot,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9_.-]+$')][string]$Label,
    [ValidateRange(0,7)][int]$FirstMap=0,
    [ValidateRange(1,8)][int]$MapCount=8
)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $root "tmp/$Label"
if(Test-Path -LiteralPath $out){throw 'Fresh rollout directory required'}
if($FirstMap+$MapCount -gt 8){throw 'Map selection exceeds the eight playable rivers'}
$maps=@(
    @{Name='L_SouthForkAmerican_FullReach';Station=8360},
    @{Name='L_SouthFork_Troublemaker';Station=95},
    @{Name='L_Hance';Station=750},
    @{Name='L_LavaCanyon';Station=850},
    @{Name='L_Terminator';Station=750},
    @{Name='L_UpperHuacas';Station=1050},
    @{Name='L_Zambezi';Station=600},
    @{Name='L_ZambeziUpperGorge';Station=1500}
)
New-Item -ItemType Directory -Path $out | Out-Null
$results=@()
foreach($map in $maps[$FirstMap..($FirstMap+$MapCount-1)]){
    $deadline=(Get-Date).AddMinutes(15);$idleSince=$null
    do {
        $busy=@(Get-CimInstance Win32_Process | Where-Object {
            $_.Name -match '^(UnrealEditor|UnrealBuildTool|SmokeEm|raftsim_cartesian_cook|raftsim_water_solver|blender|link\.exe)' -or
            ($_.Name -in @('dotnet.exe','cmd.exe') -and $_.CommandLine -match 'UnrealBuildTool|Build\.bat|RunUAT|AutomationTool')
        })
        if($busy.Count){$idleSince=$null}
        elseif($null -eq $idleSince){$idleSince=Get-Date}
        if($null -ne $idleSince -and ((Get-Date)-$idleSince).TotalSeconds -ge 60){break}
        if((Get-Date) -ge $deadline){throw 'Other engine work remains active; no duplicate launched'}
        Start-Sleep -Seconds 5
    } while($true)
    $captureLabel="$Label-$($map.Name)"
    Write-Output "Starting actual packaged map $($map.Name)"
    & (Join-Path $PSScriptRoot 'capture_shared_water_map.ps1') -Map $map.Name -Label $captureLabel `
        -StationM $map.Station -PackagedRoot $PackagedRoot -ProfileFrames 2400 `
        -RecordingStartS 12 -RecordingEndS 22 -FeatureAuditSeconds 26 -TimeoutS 600
    $feature=Join-Path $PackagedRoot "SmokeEmIfYouGotEm/Saved/WaterFeatureDemo/$captureLabel.json"
    $audit=Get-Content -LiteralPath $feature -Raw | ConvertFrom-Json
    $transportPath=Join-Path $root "tmp/$captureLabel/foam-transport.json"
    $transport=Get-Content -LiteralPath $transportPath -Raw | ConvertFrom-Json
    $finite=$true
    foreach($state in $audit.actual_boat_motion){
        foreach($property in $state.PSObject.Properties){
            if($property.Value -is [double] -and ([double]::IsNaN($property.Value) -or [double]::IsInfinity($property.Value))){$finite=$false}
        }
    }
    $pass=$audit.feature_kinematics_enabled -and $audit.wet_probes -gt 0 -and `
        $audit.maximum_shared_surface_error_mps -le 0.00001 -and $audit.dry_became_wet -eq 0 -and `
        $audit.actual_boat_motion.Count -gt 1 -and $finite
    $results+= [ordered]@{map=$map.Name;label=$captureLabel;station_m=$map.Station;
        enabled=$audit.feature_kinematics_enabled;wet_probes=$audit.wet_probes;changed_probes=$audit.changed_probes;
        shared_surface_error_mps=$audit.maximum_shared_surface_error_mps;dry_became_wet=$audit.dry_became_wet;
        motion_states=$audit.actual_boat_motion.Count;finite_motion=$finite;physical_eddy_owners=$audit.active_physical_eddy_owners;
        runtime_regression_passed=$pass;feature_receipt=$feature;foam_transport_receipt=$transportPath;
        scope='Actual default shared current/hull parity and timer states. Not all-obstacle trajectory, fixed-step collision, visual or 20 FPS acceptance.'}
    [ordered]@{schema='raftsim.packaged_shared_water_rollout.v1';packaged_root=$PackagedRoot;
        maps=$results;visual_accepted=$false;fps_accepted=$false} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$out/index.json" -Encoding UTF8
    if(-not $pass){throw "Actual map regression failed $($map.Name); inspect retained evidence"}
    Write-Output "Actual packaged map completed $($map.Name); shared-current parity and finite motion passed"
}
