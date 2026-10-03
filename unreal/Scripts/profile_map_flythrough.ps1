<# Native whole-axis camera render profiling. No boat guidance, screenshots,
recording, solver/effect/quality opt-ins, or percentile-trimmed acceptance.
Live-water and far-field presentation coverage remain separate in the CSV.
#>
param(
    [Parameter(Mandatory=$true)][ValidateSet('L_SouthForkAmerican_FullReach','L_SouthFork_Troublemaker',
        'L_Hance','L_LavaCanyon','L_Terminator','L_UpperHuacas','L_Zambezi','L_ZambeziUpperGorge')][string]$Map,
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$')][string]$Label,
    [ValidateRange(1,100)][int]$SpeedMps=40,
    [ValidateRange(3,50)][int]$HeightM=12,
    [ValidateRange(60,7200)][int]$TimeoutS=3600,
    [string]$PackagedRoot='',
    [switch]$RadixLandscapeOrder,
    [switch]$ReferenceLandscapeOrder,
    [string]$Python='C:/Users/salsi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
)
$ErrorActionPreference='Stop'
if($RadixLandscapeOrder -and $ReferenceLandscapeOrder){throw 'Request one landscape ordering mode'}
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $root "tmp/$Label"
if(Test-Path -LiteralPath $out){throw 'Fresh flythrough evidence label required'}
$binary='C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$working=$root;$saved=Join-Path $root 'unreal/Saved'
$arguments=@((Join-Path $root 'unreal/SmokeEmIfYouGotEm.uproject'))
$scope='Editor-hosted camera route; not packaged game acceptance'
if($PackagedRoot){
    $stage=[IO.Path]::GetFullPath($PackagedRoot)
    $allowed=[IO.Path]::GetFullPath((Join-Path $root 'tmp'))+[IO.Path]::DirectorySeparatorChar
    if(-not $stage.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'Use retained project-local package'}
    $game=Join-Path $stage 'SmokeEmIfYouGotEm'
    $binary=Join-Path $game 'Binaries/Win64/SmokeEmIfYouGotEm.exe'
    if(-not (Test-Path -LiteralPath (Join-Path $game 'Content/Paks') -PathType Container)){throw 'Cooked package missing'}
    $arguments=@();$working=$stage;$saved=Join-Path $game 'Saved'
    $scope='Packaged camera render route; not boat-trajectory or normal Boot/menu acceptance'
}
if(-not (Test-Path -LiteralPath $binary -PathType Leaf)){throw 'Native engine/game executable missing'}
if(-not (Test-Path -LiteralPath $Python -PathType Leaf)){throw 'Python auditor runtime missing'}
$native=Join-Path $saved "RaftSimValidation/FlyThrough/$Label"
if(Test-Path -LiteralPath $native){throw 'Native route evidence already exists'}
$deadline=(Get-Date).AddMinutes(15);$idleSince=$null
do {
    $busy=@(Get-CimInstance Win32_Process | Where-Object {
        $_.Name -match '^(UnrealEditor|UnrealBuildTool|SmokeEm|ShaderCompileWorker|UnrealPak|raftsim_cartesian_cook|raftsim_water_solver|blender|link\.exe)' -or
        ($_.Name -in @('dotnet.exe','cmd.exe') -and $_.CommandLine -match 'UnrealBuildTool|Build\.bat|RunUAT|AutomationTool')
    })
    if($busy.Count){$idleSince=$null}elseif($null -eq $idleSince){$idleSince=Get-Date}
    if($null -ne $idleSince -and ((Get-Date)-$idleSince).TotalSeconds -ge 60){break}
    if((Get-Date) -ge $deadline){throw 'Other engine work remains active; no flight launched'}
    Start-Sleep -Seconds 5
} while($true)
New-Item -ItemType Directory -Path $out | Out-Null
$hashes=@{}
if(-not $PackagedRoot){
    foreach($module in @('RaftSimRaft','RaftSimWater','RaftSimWaterDetail','RaftSimPhysics')){
        $dll=Join-Path $root "unreal/Plugins/RaftSim/Binaries/Win64/UnrealEditor-$module.dll"
        $hashes[$dll]=(Get-FileHash -LiteralPath $dll -Algorithm SHA256).Hash
    }
}else{$hashes[$binary]=(Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash}
$commands="csv.UseLegacyFrameTime 0,csv.TargetFrameRateOverride 20,CsvCategory FMsgLogf disable,RaftSim.FlyThroughMap $Label $SpeedMps $HeightM"
$arguments+=@("/Game/RaftSim/Maps/$Map",'-game','-RenderOffscreen','-RaftSimEphemeralProfile',
    '-Unattended','-NoSplash','-NoSound','-ResX=1280','-ResY=720','-Windowed','-csvCompression=0',
    "-AbsLog=$out/engine.log","-ExecCmds=$commands")
if($RadixLandscapeOrder){$arguments+='-RaftSimRadixLandscapeOrder'}
if($ReferenceLandscapeOrder){$arguments+='-RaftSimReferenceLandscapeOrder'}
$start=New-Object System.Diagnostics.ProcessStartInfo
$start.FileName=$binary;$start.WorkingDirectory=$working;$start.UseShellExecute=$false;$start.CreateNoWindow=$true
$start.Arguments=($arguments | ForEach-Object {'"'+[regex]::Replace([regex]::Replace($_,'(\\*)"','$1$1\"'),'(\\+)$','$1$1')+'"'}) -join ' '
$started=Get-Date
$process=[System.Diagnostics.Process]::Start($start)
if(-not $process.WaitForExit($TimeoutS*1000)){
    # This launcher owns this exact process. Never terminate another task.
    $process.Kill();$process.WaitForExit();throw 'Owned native flight timed out; evidence retained'
}
$process.WaitForExit()
[ordered]@{schema='raftsim.map_flythrough_launch.v1';map=$Map;label=$Label;arguments=$arguments;
    binary_sha256=$hashes;process_id=$process.Id;exit_code=$process.ExitCode;scope=$scope;
    packaged_root=$PackagedRoot;recording=$false;screenshots=$false;boat_guidance=$false
    diagnostic_radix_landscape_order=[bool]$RadixLandscapeOrder;
    diagnostic_reference_landscape_order=[bool]$ReferenceLandscapeOrder;
    production_collision_defaults=(!$ReferenceLandscapeOrder)} |
    ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$out/launch.json" -Encoding UTF8
foreach($file in $hashes.Keys){
    if((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $hashes[$file]){throw 'Loaded native binary changed during flight'}
}
if($process.ExitCode -ne 0){throw "Native flight exited $($process.ExitCode)"}
$log=Get-Content -LiteralPath "$out/engine.log" -Raw
if($log -match 'Log\w+: (?:Error|Fatal):'){throw 'Native map runtime error; preserve evidence'}
if($log -notmatch ('LogLoad: LoadMap: /Game/RaftSim/Maps/'+[regex]::Escape($Map)+'(?:\?|\s|$)')){throw 'Requested map not loaded'}
if($log -notmatch 'vertices=26610 triangles=38344 max_error_m=0'){throw 'Original full hull/render equality missing'}
$receipt=Join-Path $native 'route.json'
if(-not (Test-Path -LiteralPath $receipt) -or (Get-Item -LiteralPath $receipt).LastWriteTime -lt $started){throw 'Native route receipt missing or stale'}
$route=Get-Content -LiteralPath $receipt -Raw | ConvertFrom-Json
if(-not $route.complete -or $route.failure -or $route.map -ne $Map){throw 'Incomplete or wrong native route'}
$csv=[IO.Path]::GetFullPath($route.csv)
$nativePrefix=[IO.Path]::GetFullPath($native)+[IO.Path]::DirectorySeparatorChar
if(-not $csv.StartsWith($nativePrefix,[StringComparison]::OrdinalIgnoreCase) -or
    -not (Test-Path -LiteralPath $csv -PathType Leaf) -or (Get-Item -LiteralPath $csv).LastWriteTime -lt $started){throw 'CSV path missing, stale, or outside this native run'}
& $Python (Join-Path $PSScriptRoot 'audit_map_flythrough.py') --csv $csv --receipt $receipt --output "$out/route-audit.json"
if($LASTEXITCODE -ne 0){throw 'Whole-route timing/coverage audit failed'}
