<# Actual cooked FullReach screenshots and raw GPU snapshots. Not FPS,
normal Boot/menu, all-map boat progression, or bubble-rise CFD acceptance. #>
param(
    [Parameter(Mandatory=$true)][string]$PackagedRoot,
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_.-]{0,60}$')][string]$Label,
    [ValidateSet('calm','rapid')][string[]]$Scenes=@('calm','rapid')
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
foreach($scene in $Scenes){
    $captureLabel="$Label-$scene"
    $out=Join-Path $root "tmp/$captureLabel"
    $screens=Join-Path $game 'Saved/Screenshots'
    if(Test-Path -LiteralPath $out){throw 'Fresh capture evidence required'}
    foreach($i in 0..2){if(Test-Path -LiteralPath (Join-Path $screens ('{0}_{1:d3}.png' -f $captureLabel,$i))){throw 'Screenshot evidence already exists'}}
    $deadline=(Get-Date).AddMinutes(15);$idleSince=$null
    do {
        $busy=@(Get-CimInstance Win32_Process | Where-Object {
            $_.Name -match '^(UnrealEditor|UnrealBuildTool|SmokeEm|ShaderCompileWorker|UnrealPak|raftsim_cartesian_cook|raftsim_water_solver|blender|link\.exe)' -or
            ($_.Name -in @('dotnet.exe','cmd.exe') -and $_.CommandLine -match 'UnrealBuildTool|Build\.bat|RunUAT|AutomationTool')
        })
        if($busy.Count){$idleSince=$null}elseif($null -eq $idleSince){$idleSince=Get-Date}
        if($null -ne $idleSince -and ((Get-Date)-$idleSince).TotalSeconds -ge 60){break}
        if((Get-Date) -ge $deadline){throw 'Other shared engine work active; no capture launched'}
        Start-Sleep -Seconds 5
    } while($true)
    New-Item -ItemType Directory -Path $out | Out-Null
    $commands="RaftSim.CaptureSeries 12 3 1 $captureLabel"
    if($scene -eq 'rapid'){$commands="RaftSim.PlaceAtStation 8360,$commands river_station_side focusstation=8360"}
    $arguments=@('/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach','-game','-RenderOffscreen',
        '-RaftSimEphemeralProfile','-Unattended','-NoSplash','-NoSound','-ResX=1280','-ResY=720','-Windowed',
        "-AbsLog=$out/engine.log","-RaftSimDetailSnapshot=$out/detail","-ExecCmds=$commands")
    $hash=(Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash
    $started=Get-Date
    $start=New-Object System.Diagnostics.ProcessStartInfo
    $start.FileName=$binary;$start.WorkingDirectory=$stage;$start.UseShellExecute=$false;$start.CreateNoWindow=$true
    $start.Arguments=($arguments | ForEach-Object {'"'+[regex]::Replace([regex]::Replace($_,'(\\*)"','$1$1\"'),'(\\+)$','$1$1')+'"'}) -join ' '
    $process=[System.Diagnostics.Process]::Start($start)
    if(-not $process.WaitForExit(900000)){$process.Kill();$process.WaitForExit();throw 'Owned capture timeout; evidence preserved'}
    $process.WaitForExit()
    $receipt=[ordered]@{schema='raftsim.packaged_rapid_pool_froth_capture.v1';scene=$scene;
        arguments=$arguments;binary=$binary;binary_sha256=$hash;owned_process_id=$process.Id;
        exit_code=$process.ExitCode;full_hull_and_runtime_health_verified=$false;native_screenshots=@();
        gpu_snapshot_metadata=@();visual_review_completed=$false;performance_qualification=$false;
        scope='Actual cooked FullReach pixels and raw GPU data; rapid uses one diagnostic initial placement then native integration. No guided/interpolated boat, physics/effect/quality overrides, or FPS acceptance.'}
    $receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$out/launch.json" -Encoding UTF8
    if($process.ExitCode -ne 0){throw "Cooked capture exited $($process.ExitCode); evidence retained"}
    if((Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash -ne $hash){throw 'Cooked executable changed during capture'}
    $log=Get-Content -LiteralPath "$out/engine.log" -Raw
    if($log -match 'Log\w+: (?:Error|Fatal):'){throw 'Native capture runtime error; preserve evidence'}
    if($log -notmatch 'vertices=26610 triangles=38344 max_error_m=0'){throw 'Original full hull/render agreement missing'}
    if($log -notmatch 'LogLoad: LoadMap: /Game/RaftSim/Maps/L_SouthForkAmerican_FullReach(?:\?|\s|$)'){throw 'Actual requested map not loaded'}
    $snapshots=@(Get-ChildItem -LiteralPath $out -Filter 'detail_*.json')
    if($snapshots.Count -lt 2){throw 'Two native GPU readbacks required'}
    foreach($snapshot in $snapshots){
        $metadata=Get-Content -LiteralPath $snapshot.FullName -Raw | ConvertFrom-Json
        if(-not $metadata.arrays_complete -or $metadata.performance_qualification -or $snapshot.LastWriteTime -lt $started){throw 'Incomplete/stale GPU snapshot'}
        $elements=1;foreach($dimension in $metadata.shape){$elements*=$dimension}
        foreach($suffix in @('flow','state','surface','mean_geometry')){
            $array=[IO.Path]::ChangeExtension($snapshot.FullName,"$suffix.f32")
            if(-not (Test-Path -LiteralPath $array) -or (Get-Item -LiteralPath $array).Length -ne $elements*4){throw 'Native GPU array size mismatch'}
        }
    }
    foreach($i in 0..2){
        $png=Join-Path $screens ('{0}_{1:d3}.png' -f $captureLabel,$i)
        if(-not (Test-Path -LiteralPath $png) -or (Get-Item -LiteralPath $png).LastWriteTime -lt $started){throw 'Native screenshot missing/stale'}
        $receipt.native_screenshots+=@{path=$png;sha256=(Get-FileHash -LiteralPath $png -Algorithm SHA256).Hash}
    }
    $receipt.full_hull_and_runtime_health_verified=$true
    $receipt.gpu_snapshot_metadata=@($snapshots.FullName)
    $receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$out/launch.json" -Encoding UTF8
    [ordered]@{scene=$scene;receipt="$out/launch.json";screenshots=3;gpu_snapshots=$snapshots.Count;visual_review_pending=$true} | ConvertTo-Json
}
