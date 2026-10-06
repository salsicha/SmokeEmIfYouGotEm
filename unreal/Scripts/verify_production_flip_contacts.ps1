<# Native production flip/contact regression. Original mesh, no physics opt-ins. #>
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
$tests='RaftSim.Production.CapturedRockPin+RaftSim.P2.RaftFlipsAndRecovers+RaftSim.Physics.FullHull+RaftSim.Physics.FullSurfaceFeatures+RaftSim.Physics.SurfaceSeparationProof+RaftSim.Physics.SourceSurfaceBVH+RaftSim.Physics.SourceClosedContainment+RaftSim.Physics.ClosedGroundTopology+RaftSim.Physics.StreamedGroundSources+RaftSim.Demo.RockPinExactShapeCache+RaftSim.Demo.FlipEnvironmentBaseline'
$arguments=@((Join-Path $root 'unreal/SmokeEmIfYouGotEm.uproject'),'/Game/RaftSim/Maps/L_RaftSimTestTank',
    '-RaftSimEphemeralProfile','-NullRHI','-Unattended','-NoSplash','-NoSound',
    "-ReportExportPath=$out",'-TestExit=Automation Test Queue Empty',"-AbsLog=$out/engine.log",
    "-ExecCmds=Automation RunTests $tests")
$binary='C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$raft=Join-Path $root 'unreal/Plugins/RaftSim/Binaries/Win64/UnrealEditor-RaftSimRaft.dll'
$physics=Join-Path $root 'unreal/Plugins/RaftSim/Binaries/Win64/UnrealEditor-RaftSimPhysics.dll'
$launch=[ordered]@{schema='raftsim.production_flip_test_launch.v1';arguments=$arguments;
    raft_dll_sha256=(Get-FileHash -LiteralPath $raft -Algorithm SHA256).Hash;
    physics_dll_sha256=(Get-FileHash -LiteralPath $physics -Algorithm SHA256).Hash}
$start=New-Object System.Diagnostics.ProcessStartInfo
$start.FileName=$binary;$start.WorkingDirectory=$root;$start.UseShellExecute=$false;$start.CreateNoWindow=$true
$start.Arguments=($arguments | ForEach-Object {'"'+[regex]::Replace([regex]::Replace($_,'(\\*)"','$1$1\"'),'(\\+)$','$1$1')+'"'}) -join ' '
$process=[System.Diagnostics.Process]::Start($start);$launch['owned_process_id']=$process.Id
if(-not $process.WaitForExit(600000)){$process.Kill();throw 'Owned native test timed out; evidence retained'}
$process.WaitForExit();$launch['exit_code']=$process.ExitCode
$launch | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$out/launch.json" -Encoding UTF8
if($process.ExitCode -ne 0){throw "Native production tests exited $($process.ExitCode)"}
if((Get-FileHash -LiteralPath $raft -Algorithm SHA256).Hash -ne $launch.raft_dll_sha256 -or
    (Get-FileHash -LiteralPath $physics -Algorithm SHA256).Hash -ne $launch.physics_dll_sha256){throw 'Loaded test binaries changed'}
$report=Get-Content -LiteralPath "$out/index.json" -Raw | ConvertFrom-Json
if($report.failed -or $report.notRun -or $report.inProcess -or $report.succeeded+$report.succeededWithWarnings -lt 14){throw 'Incomplete or failed native production regression'}
$required=@('RaftSim.Production.CapturedRockPin','RaftSim.P2.RaftFlipsAndRecovers')
foreach($name in $required){
    $entry=@($report.tests | Where-Object {$_.fullTestPath -eq $name})
    if($entry.Count -ne 1 -or $entry[0].state -ne 'Success'){throw "Mandatory production test did not pass: $name"}
}
[ordered]@{report="$out/index.json";succeeded=$report.succeeded;warnings=$report.succeededWithWarnings;failed=$report.failed} | ConvertTo-Json
