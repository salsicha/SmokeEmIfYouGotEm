<# Actual South Fork views with linked tested DLLs; not a packaged/FPS gate. #>
param([Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9_.-]+$')][string]$Label,
    [switch]$Rapid)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $root "tmp/$Label"
if(Test-Path -LiteralPath $out){throw 'Fresh capture directory required'}
$deadline=(Get-Date).AddMinutes(15);$idleSince=$null
do {
    $busy=@(Get-CimInstance Win32_Process | Where-Object {
        $_.Name -match '^(UnrealEditor|UnrealBuildTool|SmokeEm|raftsim_cartesian_cook|raftsim_water_solver|blender|link\.exe)' -or
        ($_.Name -in @('dotnet.exe','cmd.exe') -and $_.CommandLine -match 'UnrealBuildTool|Build\.bat|RunUAT|AutomationTool')
    })
    if($busy.Count){$idleSince=$null}elseif($null -eq $idleSince){$idleSince=Get-Date}
    if($null -ne $idleSince -and ((Get-Date)-$idleSince).TotalSeconds -ge 60){break}
    if((Get-Date) -ge $deadline){throw 'Other engine work still active'}
    Start-Sleep -Seconds 5
} while($true)
New-Item -ItemType Directory -Path $out | Out-Null
$commands="RaftSim.CaptureSeries 12 3 1 $Label"
if($Rapid){$commands="RaftSim.PlaceAtStation 8360,RaftSim.CaptureSeries 12 3 1 $Label river_station_side focusstation=8360"}
$arguments=@((Join-Path $root 'unreal/SmokeEmIfYouGotEm.uproject'),'/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach',
    '-game','-RenderOffscreen','-RaftSimEphemeralProfile','-Unattended','-NoSplash','-NoSound',
    '-ResX=1280','-ResY=720','-Windowed',"-AbsLog=$out/engine.log",
    "-RaftSimDetailSnapshot=$out/detail","-ExecCmds=$commands")
$dlls=@('RaftSimRaft','RaftSimWater','RaftSimWaterDetail');$hashes=@{}
foreach($module in $dlls){$hashes[$module]=(Get-FileHash -LiteralPath "$root/unreal/Plugins/$(if($module -eq 'RaftSimWaterDetail'){'SEIYGECore'}else{'RaftSim'})/Binaries/Win64/UnrealEditor-$module.dll" -Algorithm SHA256).Hash}
$start=New-Object System.Diagnostics.ProcessStartInfo
$start.FileName='C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$start.WorkingDirectory=$root;$start.UseShellExecute=$false;$start.CreateNoWindow=$true
$start.Arguments=($arguments | ForEach-Object {'"'+[regex]::Replace([regex]::Replace($_,'(\\*)"','$1$1\"'),'(\\+)$','$1$1')+'"'}) -join ' '
$process=[System.Diagnostics.Process]::Start($start)
if(-not $process.WaitForExit(300000)){$process.Kill();throw 'Owned screenshot run timed out; evidence retained'}
$process.WaitForExit()
[ordered]@{schema='raftsim.rapid_pool_froth_capture.v1';arguments=$arguments;dll_sha256=$hashes;
    owned_process_id=$process.Id;exit_code=$process.ExitCode;rapid_station_m=$(if($Rapid){8360}else{-1});
    scope='Editor-hosted actual river map; camera/one-time initial placement diagnostic, not packaged launch or full-map performance acceptance'} |
    ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$out/launch.json" -Encoding UTF8
if($process.ExitCode -ne 0){throw 'Native screenshot process failed'}
foreach($module in $dlls){
    if((Get-FileHash -LiteralPath "$root/unreal/Plugins/$(if($module -eq 'RaftSimWaterDetail'){'SEIYGECore'}else{'RaftSim'})/Binaries/Win64/UnrealEditor-$module.dll" -Algorithm SHA256).Hash -ne $hashes[$module]){throw 'Loaded screenshot DLL changed'}
}
$log=Get-Content -LiteralPath "$out/engine.log" -Raw
if($log -match 'Log\w+: (?:Error|Fatal):'){throw 'Actual map runtime error; preserve evidence'}
if($log -notmatch 'vertices=26610 triangles=38344 max_error_m=0'){throw 'Missing original hull/render equality'}
$shots=@(Get-ChildItem -LiteralPath "$root/unreal/Saved/Screenshots" -Filter "$Label*.png" -File)
if($shots.Count -ne 3){throw 'Incomplete native screenshot sequence'}
$shots | Select-Object FullName,Length | ConvertTo-Json
