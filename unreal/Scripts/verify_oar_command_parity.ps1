param([Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9_.-]+$')][string]$Label)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $root "tmp/$Label"
if(Test-Path -LiteralPath $out){throw 'Fresh evidence directory required'}
$busy=Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match '^(UnrealEditor.*|UnrealBuildTool|SmokeEmIfYouGotEm.*|link)\.exe$' -or
    ($_.Name -eq 'dotnet.exe' -and $_.CommandLine -match 'UnrealBuildTool|AutomationTool')
}
if($busy){throw 'Shared engine is busy; not starting a competing regression run'}
New-Item -ItemType Directory -Path $out | Out-Null
$tests=@('RaftSim.Input.OarCommandParity','RaftSim.Input.PawnContextIsolation',
    'RaftSim.Crew.CommandsShareVisibleAndPhysicalSeats')
$arguments=@((Join-Path $root 'unreal/SmokeEmIfYouGotEm.uproject'),'/Game/RaftSim/Maps/L_RaftSimTestTank',
    '-RenderOffscreen','-RaftSimEphemeralProfile','-Unattended','-NoSplash','-NoSound',
    "-ReportExportPath=$out",'-TestExit=Automation Test Queue Empty',"-AbsLog=$out/engine.log",
    ('-ExecCmds=Automation RunTests '+($tests -join '+')))
$binary='C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$start=New-Object System.Diagnostics.ProcessStartInfo
$start.FileName=$binary;$start.WorkingDirectory=$root;$start.UseShellExecute=$false;$start.CreateNoWindow=$true
$start.Arguments=($arguments | ForEach-Object {'"'+[regex]::Replace([regex]::Replace($_,'(\\*)"','$1$1\"'),'(\\+)$','$1$1')+'"'}) -join ' '
$process=[System.Diagnostics.Process]::Start($start)
Write-Host "Oar command regression PID=$($process.Id)"
$process.WaitForExit()
if($process.ExitCode -ne 0){throw "Native regression exited $($process.ExitCode); evidence in $out"}
$report=Get-Content -LiteralPath "$out/index.json" -Raw | ConvertFrom-Json
foreach($name in $tests){
    $entry=@($report.tests | Where-Object {$_.fullTestPath -eq $name})
    if($entry.Count -ne 1 -or $entry[0].state -ne 'Success'){throw "Mandatory test failed: $name"}
}
Write-Host "All three native command/crew regressions passed: $out/index.json"
