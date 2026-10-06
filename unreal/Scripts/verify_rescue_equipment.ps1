param([Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9][a-zA-Z0-9_.-]*$')][string]$Label,
    [switch]$Render,[switch]$LiveRecovery,[switch]$Oar)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $root "tmp/$Label"
if(Test-Path -LiteralPath $out){throw 'Fresh evidence label required'}
$busy=Get-CimInstance Win32_Process|Where-Object {
    $_.Name -match '^(UnrealEditor.*|UnrealBuildTool|SmokeEmIfYouGotEm.*|link)\.exe$' -or
    ($_.Name -eq 'dotnet.exe' -and $_.CommandLine -match 'UnrealBuildTool|AutomationTool')
}
if($busy){throw 'Shared engine busy; no competing validation launched'}
New-Item -ItemType Directory -Path $out|Out-Null
$tests=@('RaftSim.Rescue.Equipment','RaftSim.Rescue.PassengerWashout','RaftSim.M5.AimedRescuePaths','RaftSim.Crew.OccupancyControlsLoadsAndIntegratedMass')
if($LiveRecovery){$tests+='RaftSim.P2.RaftFlipsAndRecovers'}
if($Oar){$tests=@('RaftSim.Rescue.Equipment')}
$arguments=@("$root/unreal/SmokeEmIfYouGotEm.uproject",'/Game/RaftSim/Maps/L_RaftSimTestTank',
    '-unattended','-nop4','-nosplash','-NoSound','-UseFixedTimeStep','-FPS=30','-RaftSimEphemeralProfile',
    ('-ExecCmds=Automation RunTests '+($tests -join '+')),'-TestExit=Automation Test Queue Empty',
    "-ReportExportPath=$out/automation","-abslog=$out/native.log")
if($Render){$arguments+=@('-RenderOffscreen',"-RaftSimRescueCaptureDir=$out/frames",'-windowed','-ResX=1280','-ResY=720')}
else{$arguments+='-NullRHI'}
if($Oar){$arguments+='-RaftSimRescueOar'}
[ordered]@{arguments=$arguments;source_commit=(git -C $root rev-parse HEAD);
    raft_dll_sha256=(Get-FileHash "$root/unreal/Plugins/RaftSim/Binaries/Win64/UnrealEditor-RaftSimRaft.dll").Hash;
    source_status=@(git -C $root status --short);protocol='throw_bag_flip_line_v1'}|
    ConvertTo-Json -Depth 6|Set-Content -LiteralPath "$out/launch.json" -Encoding utf8
$start=New-Object System.Diagnostics.ProcessStartInfo
$start.FileName='C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$start.WorkingDirectory=$root;$start.UseShellExecute=$false;$start.CreateNoWindow=$true
$start.Arguments=($arguments|ForEach-Object {'"'+[regex]::Replace([regex]::Replace($_,'(\\*)"','$1$1\"'),'(\\+)$','$1$1')+'"'}) -join ' '
$process=[System.Diagnostics.Process]::Start($start)
Write-Host "Rescue validation PID=$($process.Id)"
$process.WaitForExit()
if($process.ExitCode -ne 0){throw "Native run failed: $out/native.log"}
$report=Get-Content "$out/automation/index.json" -Raw|ConvertFrom-Json
foreach($name in $tests){
    $entry=@($report.tests|Where-Object {$_.fullTestPath -eq $name})
    if($entry.Count -ne 1 -or $entry[0].state -ne 'Success'){throw "Missing/failed native test: $name"}
}
Write-Host "Rescue validation passed ($($tests.Count) tests): $out"
