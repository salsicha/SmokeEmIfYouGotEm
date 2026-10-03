<# Sequential native whole-axis camera routes. A slow route still produces
spatial evidence and the next map is tested; no percentile-only 20 FPS pass.
This index deliberately does not accept full-map live water/boat behavior.
#>
param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_.-]{0,35}$')][string]$Label,
    [string]$PackagedRoot='',
    [ValidateRange(1,100)][int]$SpeedMps=40
)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $root "tmp/$Label"
if(Test-Path -LiteralPath $out){throw 'Fresh all-map evidence label required'}
New-Item -ItemType Directory -Path $out | Out-Null
$maps=@('L_SouthForkAmerican_FullReach','L_SouthFork_Troublemaker','L_Hance','L_LavaCanyon',
    'L_Terminator','L_UpperHuacas','L_Zambezi','L_ZambeziUpperGorge')
$runs=@();$referenceHashes=$null
foreach($map in $maps){
    $runLabel="$Label-$map"
    $runOut=Join-Path $root "tmp/$runLabel"
    try {
        & (Join-Path $PSScriptRoot 'profile_map_flythrough.ps1') -Map $map -Label $runLabel -PackagedRoot $PackagedRoot -SpeedMps $SpeedMps
        $launch=Get-Content -LiteralPath "$runOut/launch.json" -Raw | ConvertFrom-Json
        $audit=Get-Content -LiteralPath "$runOut/route-audit.json" -Raw | ConvertFrom-Json
        if($launch.map -ne $map -or $audit.map -ne $map -or -not $audit.camera_whole_route_complete){throw 'Requested whole map not verified'}
        $hashes=($launch.binary_sha256.PSObject.Properties | Sort-Object Name | ForEach-Object {"$($_.Name)=$($_.Value)"}) -join ';'
        $sameBinaries=$true
        if($null -eq $referenceHashes){$referenceHashes=$hashes}elseif($hashes -ne $referenceHashes){$sameBinaries=$false}
        # Preserve a valid individual native route as diagnostic evidence even
        # after a shared rebuild, but NEVER qualify it as the same-build batch.
        $runs+=@([ordered]@{map=$map;complete=$sameBinaries;native_route_complete=$true;
            same_native_binaries_as_collection=$sameBinaries;audit="$runOut/route-audit.json";
            frames_below_20fps=$audit.frames_below_20fps;minimum_fps=$audit.minimum_fps;
            native_timing_passes_every_frame_20fps=$audit.passes_every_route_frame_20fps;
            passes_every_route_frame_20fps=($sameBinaries -and $audit.passes_every_route_frame_20fps);
            failure=$(if($sameBinaries){''}else{'All-map runs do not use the same native binaries'});
            slow_segments=@($audit.segments | Where-Object {$_.frames_below_20fps -gt 0})})
    }catch{
        $runs+=@([ordered]@{map=$map;complete=$false;native_route_complete=$false;
            same_native_binaries_as_collection=$false;audit='';passes_every_route_frame_20fps=$false;failure=$_.Exception.Message})
    }
    [ordered]@{schema='raftsim.all_map_native_flythrough_progress.v2';requested_maps=$maps;
        runs=$runs;packaged_root=$PackagedRoot;all_eight_routes_complete=($runs.Count -eq 8 -and @($runs | Where-Object {-not $_.complete}).Count -eq 0);
        all_eight_native_routes_complete=($runs.Count -eq 8 -and @($runs | Where-Object {-not $_.native_route_complete}).Count -eq 0);
        all_eight_camera_routes_above_20fps=($runs.Count -eq 8 -and @($runs | Where-Object {-not $_.passes_every_route_frame_20fps}).Count -eq 0);
        all_map_water_and_boat_validation_accepted=$false;
        scope='Whole-axis camera render profiling. Actual live water, feature activation and boat-motion acceptance remain separate. No forced/interpolated boat path.'} |
        ConvertTo-Json -Depth 8 | Set-Content -LiteralPath "$out/index.json" -Encoding UTF8
}
$runs | Select-Object map,complete,minimum_fps,frames_below_20fps,failure | Format-Table -AutoSize
