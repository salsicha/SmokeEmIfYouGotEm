param([Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9][a-zA-Z0-9_.-]*$')][string]$Label,
    [switch]$Oar,[switch]$Render,[switch]$InputOnly)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $root "tmp/$Label"
if(Test-Path -LiteralPath $out){throw 'Fresh evidence label required'}
$busy=Get-CimInstance Win32_Process|Where-Object {
    $_.Name -match '^(UnrealEditor.*|UnrealBuildTool|SmokeEmIfYouGotEm.*|link)\.exe$' -or
    ($_.Name -eq 'dotnet.exe' -and $_.CommandLine -match 'UnrealBuildTool|AutomationTool')
}
if($busy){throw 'Shared engine busy; no competing build/test launched'}
New-Item -ItemType Directory -Path $out|Out-Null
$tests=@('RaftSim.Input.HighSideLiveKeys')
if(!$InputOnly){
    $tests+=@('RaftSim.Crew.CommandsShareVisibleAndPhysicalSeats','RaftSim.Input.OarCommandParity',
        'RaftSim.Crew.OccupancyControlsLoadsAndIntegratedMass','RaftSim.D6.Chaos.TimedHighSideSave')
    # This suite inspects uploaded texture dimensions; NullRHI cannot validate it.
    if($Render){$tests+='RaftSim.M5.CrewAvatarPoseProduction'}
}
$map=if($Oar){'/Game/RaftSim/Maps/L_Hance'}else{'/Game/RaftSim/Maps/L_RaftSimTestTank'}
$scenario=if($Oar){'hance_challenge'}else{'guide_school'}
$arguments=@("$root/unreal/SmokeEmIfYouGotEm.uproject",$map,'-unattended','-nop4','-nosplash','-NoSound',
    '-UseFixedTimeStep','-FPS=30','-FixedSeed','-RaftSimEphemeralProfile',
    "-RaftSimScenario=$scenario","-RaftSimHighSideEvidenceDir=$out",
    ('-ExecCmds=Automation RunTests '+($tests -join '+')),'-TestExit=Automation Test Queue Empty',
    "-ReportExportPath=$out/automation","-abslog=$out/native.log")
if($Oar){$arguments+='-RaftSimHighSideOar'}
if($Render){$arguments+=@('-RenderOffscreen','-windowed','-ResX=1280','-ResY=720','-ForceRes')}else{$arguments+='-NullRHI'}
[ordered]@{arguments=$arguments;source_commit=(git -C $root rev-parse HEAD);
    game_dll_sha256=(Get-FileHash "$root/unreal/Binaries/Win64/UnrealEditor-SmokeEmIfYouGotEm.dll").Hash;
    raft_dll_sha256=(Get-FileHash "$root/unreal/Plugins/RaftSim/Binaries/Win64/UnrealEditor-RaftSimRaft.dll").Hash;
    physics_dll_sha256=(Get-FileHash "$root/unreal/Plugins/RaftSim/Binaries/Win64/UnrealEditor-RaftSimPhysics.dll").Hash;
    source_status=@(git -C $root status --short);protocol='whole_crew_transfer_v1'}|
    ConvertTo-Json -Depth 6|Set-Content -LiteralPath "$out/launch.json" -Encoding utf8
$start=New-Object System.Diagnostics.ProcessStartInfo
$start.FileName='C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$start.WorkingDirectory=$root;$start.UseShellExecute=$false;$start.CreateNoWindow=$true
$start.Arguments=($arguments|ForEach-Object {'"'+[regex]::Replace([regex]::Replace($_,'(\\*)"','$1$1\"'),'(\\+)$','$1$1')+'"'}) -join ' '
$process=[System.Diagnostics.Process]::Start($start)
Write-Host "High-side validation PID=$($process.Id)"
$process.WaitForExit()
if($process.ExitCode -ne 0){throw "Native high-side validation failed; inspect $out/native.log"}
$report=Get-Content "$out/automation/index.json" -Raw|ConvertFrom-Json
foreach($name in $tests){
    $entry=@($report.tests|Where-Object {$_.fullTestPath -eq $name})
    if($entry.Count -ne 1 -or $entry[0].state -ne 'Success'){throw "Missing/failed native test: $name"}
}
if($Render){foreach($frame in @('keyboard-high-side','gamepad-high-side','command-panel')){
    if(!(Test-Path -LiteralPath "$out/$frame.png")){throw "Missing rendered evidence: $frame"}
}}
Write-Host "High-side validation passed ($($tests.Count) tests): $out"
