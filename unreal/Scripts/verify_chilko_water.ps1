# Requires rebuilt editor binaries and the repository's LFS data.
# Water solver checks: ./verify_chilko_water.ps1 -Label chilko-water-v1
# Real raft / all three rapid sections (screenshots):
# ./verify_chilko_water.ps1 -Label chilko-gameplay-v1 -Gameplay -Render
# Use a fresh label. Without -Render, gameplay still uses production physics.
param([Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9][a-zA-Z0-9_.-]*$')][string]$Label,
    [string]$Python='python',[switch]$Gameplay,[switch]$Render,
    [string]$Editor='C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe')
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $root "tmp/$Label"
if(Test-Path -LiteralPath $out){throw 'Fresh evidence directory required'}
$busy=Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match '^(UnrealEditor.*|UnrealBuildTool|SmokeEmIfYouGotEm.*|link)\.exe$' -or
    ($_.Name -eq 'dotnet.exe' -and $_.CommandLine -match 'UnrealBuildTool|AutomationTool')
}
if($busy){throw 'Shared engine is busy; refusing a competing run'}
if($Render -and !$Gameplay){throw 'Render requires Gameplay; water regressions run without rendering'}
if(!$Gameplay){
    & $Python (Join-Path $root 'unreal/Plugins/SEIYGECore/python/scripts/prepare_cartesian_runtime_fixture.py')
    if($LASTEXITCODE -ne 0){throw 'Could not prepare the analytic loader regression fixture'}
}
New-Item -ItemType Directory -Path $out | Out-Null
$arguments=@((Join-Path $root 'unreal/SmokeEmIfYouGotEm.uproject'),'/Game/RaftSim/Maps/L_RaftSimTestTank',
    '-RaftSimEphemeralProfile','-Unattended','-NoSplash','-NoSound',
    "-ReportExportPath=$out/automation",'-TestExit=Automation Test Queue Empty',"-AbsLog=$out/engine.log")
$expected=@('RaftSim.M3.ChilkoCropBoundary','RaftSim.M3.CartesianCropBoundaries','RaftSim.M3.CartesianWindowExactOverlap','RaftSim.M3.WaterDryRockSampling')
if($Gameplay){
    $plan=Get-Content -LiteralPath (Join-Path $root 'unreal/Tests/Data/chilko_gameplay_review.json') -Raw|ConvertFrom-Json
    $plan|Add-Member output_dir $out
    $plan|ConvertTo-Json -Depth 8|Set-Content -LiteralPath "$out/plan.json" -Encoding utf8
    $arguments[1]=$plan.map
    $arguments+=@('-UseFixedTimeStep','-FPS=30','-FixedSeed',"-RaftSimDifficultyPlan=$out/plan.json","-RaftSimScenario=$($plan.scenario)")
    $expected=@('RaftSim.Review.RiverDifficulty')
}
$arguments+='-ExecCmds=Automation RunTests '+($expected -join '+')
if($Render){$arguments+=@('-RenderOffscreen','-windowed','-ResX=1280','-ResY=720','-ForceRes')}
else{$arguments+='-NullRHI'}
$hashes=[ordered]@{}
foreach($relative in @('unreal/Plugins/RaftSim/Binaries/Win64/UnrealEditor-RaftSimWater.dll',
    'unreal/Plugins/RaftSim/Binaries/Win64/UnrealEditor-RaftSimRaft.dll',
    'unreal/Binaries/Win64/UnrealEditor-SmokeEmIfYouGotEm.dll',
    'physics/data/real_world/chilko_river_bc/scenario_lava_canyon_evidence_2023/cooked_flow_fields/manifest.json')){
    $hashes[$relative]=(Get-FileHash -LiteralPath (Join-Path $root $relative)).Hash.ToLowerInvariant()
}
[ordered]@{arguments=$arguments;file_sha256=$hashes}|ConvertTo-Json -Depth 6|Set-Content -LiteralPath "$out/launch.json" -Encoding utf8
$start=New-Object System.Diagnostics.ProcessStartInfo
$start.FileName=$Editor
$start.WorkingDirectory=$root;$start.UseShellExecute=$false;$start.CreateNoWindow=$true
$start.Arguments=($arguments | ForEach-Object {'"'+[regex]::Replace([regex]::Replace($_,'(\\*)"','$1$1\"'),'(\\+)$','$1$1')+'"'}) -join ' '
$process=[System.Diagnostics.Process]::Start($start)
Write-Host "Chilko regression PID=$($process.Id)"
$process.WaitForExit()
if($process.ExitCode -ne 0){throw "Native regression exited $($process.ExitCode); evidence in $out"}
$report=Get-Content -LiteralPath "$out/automation/index.json" -Raw | ConvertFrom-Json
$report.tests.entries.event|Where-Object {$_.message -match 'Chilko|Expected'}|Format-List type,message
foreach($name in $expected){
    $entry=@($report.tests | Where-Object {$_.fullTestPath -eq $name})
    if($entry.Count -ne 1 -or $entry[0].state -ne 'Success'){throw "Native regression missing or failed: $name; evidence preserved"}
}
if($Gameplay){
    $summary=Get-Content -LiteralPath "$out/results.json" -Raw|ConvertFrom-Json
    foreach($trial in $plan.trials){
        $result=@($summary.trials|Where-Object {$_.id -eq $trial.id})
        if($result.Count -ne 1 -or $result[0].outcome -ne 'section_cleared' -or !$result[0].finite -or
            $null -eq $result[0].minimum_center_clearance_m -or $result[0].minimum_center_clearance_m -lt $plan.minimum_center_clearance_m){
            throw "Gameplay regression failed: $($trial.id); evidence preserved"
        }
        if($Render){foreach($frame in @('start','end')){
            if(!(Test-Path -LiteralPath "$out/$($trial.id)-$frame.png")){throw 'Expected rendered evidence missing'}
        }}
    }
    $summary.trials|Select-Object id,outcome,elapsed_s,end_m,minimum_center_clearance_m,max_swimmers|Format-Table
}
Write-Host "Chilko native regression passed: $out/automation/index.json"
