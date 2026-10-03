<# Actual production CPU/GPU froth regression; not a full-map FPS gate. #>
param([Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9_.-]+$')][string]$Label)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $root "tmp/$Label"
if(Test-Path -LiteralPath $out){throw 'Fresh evidence directory required'}
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
$tests=@('RaftSim.Water.RapidPoolFrothRelease','RaftSim.Water.FoamCommittedEvolution',
    'RaftSim.Water.DirectionalFoamSource','RaftSim.WaterDetail.RapidPoolFrothGPU','RaftSim.WaterDetail.FeatureFoamTransportGPU')
$arguments=@((Join-Path $root 'unreal/SmokeEmIfYouGotEm.uproject'),'/Game/RaftSim/Maps/L_RaftSimTestTank',
    '-RenderOffscreen','-RaftSimEphemeralProfile','-Unattended','-NoSplash','-NoSound',
    "-ReportExportPath=$out",'-TestExit=Automation Test Queue Empty',"-AbsLog=$out/engine.log",
    ('-ExecCmds=Automation RunTests '+($tests -join '+')))
$binary='C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$dlls=@('RaftSimRaft','RaftSimWaterDetail')
$hashes=@{}
foreach($module in $dlls){$hashes[$module]=(Get-FileHash -LiteralPath "$root/unreal/Plugins/RaftSim/Binaries/Win64/UnrealEditor-$module.dll" -Algorithm SHA256).Hash}
$start=New-Object System.Diagnostics.ProcessStartInfo
$start.FileName=$binary;$start.WorkingDirectory=$root;$start.UseShellExecute=$false;$start.CreateNoWindow=$true
$start.Arguments=($arguments | ForEach-Object {'"'+[regex]::Replace([regex]::Replace($_,'(\\*)"','$1$1\"'),'(\\+)$','$1$1')+'"'}) -join ' '
$process=[System.Diagnostics.Process]::Start($start)
if(-not $process.WaitForExit(600000)){$process.Kill();throw 'Owned froth regression timed out; evidence retained'}
$process.WaitForExit()
[ordered]@{schema='raftsim.rapid_pool_froth_launch.v1';arguments=$arguments;dll_sha256=$hashes;
    owned_process_id=$process.Id;exit_code=$process.ExitCode;scope='Native CPU and production shader regression, not map pixels or performance acceptance'} |
    ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$out/launch.json" -Encoding UTF8
if($process.ExitCode -ne 0){throw "Native froth regression exited $($process.ExitCode)"}
foreach($module in $dlls){
    if((Get-FileHash -LiteralPath "$root/unreal/Plugins/RaftSim/Binaries/Win64/UnrealEditor-$module.dll" -Algorithm SHA256).Hash -ne $hashes[$module]){throw 'Loaded froth DLL changed'}
}
$report=Get-Content -LiteralPath "$out/index.json" -Raw | ConvertFrom-Json
if($report.failed -or $report.notRun -or $report.inProcess -or $report.succeeded+$report.succeededWithWarnings -ne $tests.Count){throw 'Incomplete or failed froth regression'}
foreach($name in $tests){
    $entry=@($report.tests | Where-Object {$_.fullTestPath -eq $name})
    if($entry.Count -ne 1 -or $entry[0].state -ne 'Success'){throw "Mandatory froth test failed: $name"}
}
[ordered]@{report="$out/index.json";succeeded=$report.succeeded;warnings=$report.succeededWithWarnings;failed=$report.failed} | ConvertTo-Json
