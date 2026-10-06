<# Native original-hull collision and physical flip regression controls.
Not full-map rendering, animation, ordinary progression or 20 FPS acceptance.
#>
param([Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_.-]+$')][string]$Label,
    [switch]$IncludeWaterControls)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $root "tmp/$Label"
if(Test-Path -LiteralPath $out){throw 'Fresh native regression evidence required'}
$deadline=(Get-Date).AddMinutes(15);$idleSince=$null
do {
    $busy=@(Get-CimInstance Win32_Process | Where-Object {
        $_.Name -match '^(UnrealEditor|UnrealBuildTool|SmokeEm|ShaderCompileWorker|UnrealPak|raftsim_cartesian_cook|raftsim_water_solver|blender|link\.exe)' -or
        ($_.Name -in @('dotnet.exe','cmd.exe') -and $_.CommandLine -match 'UnrealBuildTool|Build\.bat|RunUAT|AutomationTool')
    })
    if($busy.Count){$idleSince=$null}elseif($null -eq $idleSince){$idleSince=Get-Date}
    if($null -ne $idleSince -and ((Get-Date)-$idleSince).TotalSeconds -ge 60){break}
    if((Get-Date) -ge $deadline){throw 'Other shared engine work still active'}
    Start-Sleep -Seconds 5
} while($true)
New-Item -ItemType Directory -Path $out | Out-Null
$tests=@('RaftSim.Physics.ExactHullValidityCertificate','RaftSim.Physics.CapturedWholeHullBounds','RaftSim.Physics.OriginalVertexEnclosure','RaftSim.Physics.LandscapeOriginalFaceTree','RaftSim.Demo.FlipEnvironmentBaseline',
    'RaftSim.Demo.RockPinExactShapeCache','RaftSim.P2.RaftFlipsAndRecovers',
    'RaftSim.Physics.ClosedGroundTopology','RaftSim.Physics.FullHullAdapterIntegration',
    'RaftSim.Physics.FullHullArcAndFailure','RaftSim.Physics.FullHullArcPlaneCertificate',
    'RaftSim.Physics.FullHullResponse','RaftSim.Physics.FullSurfaceFeatures',
    'RaftSim.Physics.SourceClosedContainment','RaftSim.Physics.SourceSurfaceBVH',
    'RaftSim.Physics.StreamedGroundSources','RaftSim.Physics.SurfaceSeparationProof',
    'RaftSim.Production.CapturedRockPin')
if($IncludeWaterControls){
    $tests+=@('RaftSim.Water.ExactAuthoredRiverEndpoints','RaftSim.Water.RapidPoolFrothRelease',
        'RaftSim.Water.FoamCommittedEvolution','RaftSim.Water.DirectionalFoamSource',
        'RaftSim.WaterDetail.RapidPoolFrothGPU','RaftSim.WaterDetail.FeatureFoamTransportGPU',
        'RaftSim.M3.PairedFeatureSurfaceTransport','RaftSim.P2.SharedFeatureKinematics')
}
$arguments=@((Join-Path $root 'unreal/SmokeEmIfYouGotEm.uproject'),'/Game/RaftSim/Maps/L_RaftSimTestTank',
    '-RenderOffscreen','-RaftSimEphemeralProfile','-Unattended','-NoSplash','-NoSound',
    "-ReportExportPath=$out",'-TestExit=Automation Test Queue Empty',"-AbsLog=$out/engine.log",
    ('-ExecCmds=Automation RunTests '+($tests -join '+')))
$hashes=@{}
foreach($module in @('RaftSimRaft','RaftSimPhysics','RaftSimWater','RaftSimWaterDetail')){
    $file=Join-Path $root "unreal/Plugins/$(if($module -eq 'RaftSimWaterDetail'){'SEIYGECore'}else{'RaftSim'})/Binaries/Win64/UnrealEditor-$module.dll"
    $hashes[$file]=(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash
}
$start=New-Object System.Diagnostics.ProcessStartInfo
$start.FileName='C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$start.WorkingDirectory=$root;$start.UseShellExecute=$false;$start.CreateNoWindow=$true
$start.Arguments=($arguments | ForEach-Object {'"'+[regex]::Replace([regex]::Replace($_,'(\\*)"','$1$1\"'),'(\\+)$','$1$1')+'"'}) -join ' '
$process=[System.Diagnostics.Process]::Start($start)
if(-not $process.WaitForExit(900000)){$process.Kill();$process.WaitForExit();throw 'Owned native control timed out; evidence retained'}
$process.WaitForExit()
[ordered]@{schema='raftsim.exact_ground_flip_regression.v1';arguments=$arguments;tests=$tests;
    dll_sha256=$hashes;process_id=$process.Id;exit_code=$process.ExitCode;
    scope='Native contact and full-hull physical controls, not all-map FPS acceptance'} |
    ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$out/launch.json" -Encoding UTF8
foreach($file in $hashes.Keys){
    if((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $hashes[$file]){throw 'Loaded control DLL changed'}
}
if($process.ExitCode -ne 0){throw "Native controls exited $($process.ExitCode)"}
$report=Get-Content -LiteralPath "$out/index.json" -Raw | ConvertFrom-Json
if($report.failed -or $report.notRun -or $report.inProcess -or $report.succeeded+$report.succeededWithWarnings -ne $tests.Count){throw 'Incomplete or failed native controls'}
foreach($name in $tests){
    $entry=@($report.tests | Where-Object {$_.fullTestPath -eq $name})
    if($entry.Count -ne 1 -or $entry[0].state -ne 'Success'){throw "Mandatory native control failed: $name"}
}
[ordered]@{report="$out/index.json";succeeded=$report.succeeded;warnings=$report.succeededWithWarnings;failed=$report.failed} | ConvertTo-Json
