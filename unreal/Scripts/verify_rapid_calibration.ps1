# Native controls for the linked-rapid calibration. Not a route or FPS pass.
param([Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_.-]+$')][string]$Label)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $root "tmp/$Label"
if(Test-Path -LiteralPath $out){throw 'Fresh native evidence label required'}
$busy=@(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match '^(UnrealEditor.*|UnrealBuildTool|SmokeEmIfYouGotEm.*|link)\.exe$' -or
    ($_.Name -in @('dotnet.exe','cmd.exe') -and $_.CommandLine -match 'UnrealBuildTool|Build\.bat|RunUAT|AutomationTool')
})
if($busy.Count){throw 'Shared engine busy; no competing native controls launched'}
$tests=@('RaftSim.Review.IndependentTrialSetup','RaftSim.Review.TrialSteeringSchedule','RaftSim.Review.TrialStallRecovery',
    'RaftSim.Review.TrialRockApproach','RaftSim.Physics.CommittedHullContactTotals',
    'RaftSim.Water.RapidChallengeProfiles','RaftSim.Progression.LinkedRunBoundaries',
    'RaftSim.M3.PinballCropBoundary','RaftSim.M3.ChilkoCropBoundary')
$arguments=@("$root/unreal/SmokeEmIfYouGotEm.uproject",'/Game/RaftSim/Maps/L_RaftSimTestTank',
    '-unattended','-nop4','-nosplash','-NoSound','-NullRHI','-RaftSimEphemeralProfile',
    ('-ExecCmds=Automation RunTests '+($tests -join '+')),'-TestExit=Automation Test Queue Empty',
    "-ReportExportPath=$out","-abslog=$out/native.log")
$hashes=[ordered]@{}
foreach($path in @('unreal/Binaries/Win64/UnrealEditor-SmokeEmIfYouGotEm.dll',
    'unreal/Plugins/RaftSim/Binaries/Win64/UnrealEditor-RaftSimPhysics.dll',
    'unreal/Plugins/RaftSim/Binaries/Win64/UnrealEditor-RaftSimWater.dll',
    'unreal/Plugins/RaftSim/Binaries/Win64/UnrealEditor-RaftSimRaft.dll',
    'unreal/Plugins/SEIYGECore/Binaries/Win64/UnrealEditor-RaftSimWaterDetail.dll')){
    $hashes[$path]=(Get-FileHash -LiteralPath "$root/$path").Hash
}
New-Item -ItemType Directory -Path $out | Out-Null
[ordered]@{tests=$tests;arguments=$arguments;dll_sha256=$hashes;
    source_commit=(git -C $root rev-parse HEAD);
    scope='Native setup, attribution, shared-feature and live-crop controls; not full-map navigation, rendering or FPS acceptance'} |
    ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$out/launch.json" -Encoding utf8
$start=New-Object System.Diagnostics.ProcessStartInfo
$start.FileName='C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$start.WorkingDirectory=$root;$start.UseShellExecute=$false;$start.CreateNoWindow=$true
$start.Arguments=($arguments|ForEach-Object {'"'+[regex]::Replace([regex]::Replace($_,'(\\*)"','$1$1\"'),'(\\+)$','$1$1')+'"'}) -join ' '
$process=[System.Diagnostics.Process]::Start($start)
Write-Host "Calibration native controls PID=$($process.Id)"
if(!$process.WaitForExit(900000)){$process.Kill();$process.WaitForExit();throw 'Owned native controls timed out; evidence retained'}
$process.WaitForExit()
foreach($path in $hashes.Keys){
    if((Get-FileHash -LiteralPath "$root/$path").Hash -ne $hashes[$path]){throw "Loaded DLL changed during controls: $path"}
}
if($process.ExitCode -ne 0){throw "Native controls failed: $out/native.log"}
$report=Get-Content -LiteralPath "$out/index.json" -Raw|ConvertFrom-Json
foreach($name in $tests){
    $entry=@($report.tests|Where-Object {$_.fullTestPath -eq $name})
    if($entry.Count -ne 1 -or $entry[0].state -ne 'Success'){throw "Missing/failed native test: $name"}
}
if($report.failed -or $report.notRun -or $report.inProcess -or $report.succeeded+$report.succeededWithWarnings -ne $tests.Count){throw 'Incomplete native control coverage'}
Write-Host "Calibration native controls passed ($($tests.Count)): $out"
