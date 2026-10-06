# Independent full-production-map trials with stable dependencies, never an FPS benchmark.
param([Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9][a-zA-Z0-9_.-]*$')][string]$Label,
    [string[]]$Rivers=@('pacuare','chilko','futaleufu','colorado','zambezi','south-fork','zambezi-upper'),
    [string[]]$Rapids=@(),[string[]]$Variants=@('hands-off','center','left','right','missed-turn'),
    [string[]]$ExcludeTrialIds=@(),[switch]$Render,
    [string]$PlansPath='', [switch]$PreparedTrials)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$base=Join-Path $root "tmp/$Label"
if(Test-Path -LiteralPath $base){throw 'Fresh evidence label required'}
if(!$PlansPath){$PlansPath="$root/unreal/Tests/Data/rapid_assessment_reaches.json"}
foreach($pending in Get-ChildItem -LiteralPath "$root/tmp" -Filter 'pinball-reference-install-*.pending.json' -ErrorAction SilentlyContinue){
    if(!(Test-Path -LiteralPath ($pending.FullName -replace '\.pending\.json$','.json'))){
        throw "Unfinished paired terrain/flow installation: $($pending.FullName). Finalize it after Unreal exits before testing."
    }
}
$plans=Get-Content -LiteralPath $PlansPath -Raw|ConvertFrom-Json
New-Item -ItemType Directory -Path $base|Out-Null
foreach($river in $Rivers){
    $busy=Get-CimInstance Win32_Process|Where-Object {
        $_.Name -match '^(UnrealEditor.*|UnrealBuildTool|SmokeEmIfYouGotEm.*|link)\.exe$' -or
        ($_.Name -eq 'dotnet.exe' -and $_.CommandLine -match 'UnrealBuildTool|AutomationTool')
    }
    if($busy){throw 'Shared engine busy; evidence retained, no competing run launched'}
    $plan=$plans|Where-Object {$_.river -eq $river}
    if(!$plan){throw "Unknown river $river"}
    $trials=@()
    foreach($original in $plan.trials){
        if($Rapids.Count -and $original.id -notin $Rapids){continue}
        if($PreparedTrials){
            if($original.id -notin $ExcludeTrialIds){$trials+=$original}
            continue
        }
        foreach($variant in $Variants){
            if($variant -notin @('hands-off','center','left','right','missed-turn','poor-heading')){throw "Unknown variant $variant"}
            if($original.portage -and $variant -ne $Variants[0]){continue}
            $trial=$original|ConvertTo-Json -Depth 8|ConvertFrom-Json
            $trial|Add-Member rapid_id $original.id
            $trial.id="$($original.id)--$variant"
            if($trial.id -in $ExcludeTrialIds){continue}
            $trial|Add-Member variant $variant
            # Progress coordinates are positive river-left.
            $trial|Add-Member lane_m $(if($variant -eq 'left'){4.0}elseif($variant -eq 'right'){-4.0}else{0.0})
            $trial|Add-Member mistake_seconds $(if($variant -eq 'missed-turn'){6.0}else{0.0})
            $trial|Add-Member initial_heading_deg $(if($variant -eq 'poor-heading'){60.0}else{0.0})
            $trials+=$trial
        }
    }
    if(!$trials.Count){throw "Empty selection for $river"}
    $out=Join-Path $base $river
    New-Item -ItemType Directory -Path $out|Out-Null
    $plan.trials=$trials
    $plan|Add-Member output_dir $out
    $plan|ConvertTo-Json -Depth 12|Set-Content -LiteralPath "$out/plan.json" -Encoding utf8
    $arguments=@("$root/unreal/SmokeEmIfYouGotEm.uproject",$plan.map,'-unattended','-nop4','-nosplash','-NoSound',
        '-UseFixedTimeStep','-FPS=30','-FixedSeed','-RaftSimEphemeralProfile',
        "-RaftSimDifficultyPlan=$out/plan.json","-RaftSimScenario=$($plan.scenario)",
        '-ExecCmds=Automation RunTests RaftSim.Review.RiverDifficulty','-TestExit=Automation Test Queue Empty',
        "-ReportExportPath=$out/automation","-abslog=$out/native.log")
    # Cartesian moving detail is a production GPU system: NullRHI cannot assess it.
    if($Render -or $river -in @('south-fork','zambezi-upper')){$arguments+=@('-RenderOffscreen','-windowed','-ResX=1280','-ResY=720','-ForceRes')}
    else{$arguments+='-NullRHI'}
    $hashes=[ordered]@{}
    foreach($path in @('unreal/Plugins/RaftSim/Binaries/Win64/UnrealEditor-RaftSimWater.dll',
        'unreal/Plugins/RaftSim/Binaries/Win64/UnrealEditor-RaftSimPhysics.dll',
        'unreal/Plugins/SEIYGECore/Binaries/Win64/UnrealEditor-RaftSimWaterDetail.dll',
        'unreal/Plugins/RaftSim/Binaries/Win64/UnrealEditor-RaftSimRaft.dll',
        'unreal/Binaries/Win64/UnrealEditor-SmokeEmIfYouGotEm.dll',
        'unreal/Source/SmokeEmIfYouGotEm/Tests/RaftSimRiverDifficultyReviewTest.cpp')){
        $hashes[$path]=(Get-FileHash -LiteralPath "$root/$path").Hash
    }
    $mapPath='unreal/Content/'+$plan.map.Substring('/Game/'.Length)+'.umap'
    foreach($path in @($mapPath,$plan.source)){
        $hashes[$path]=(Get-FileHash -LiteralPath "$root/$path").Hash
    }
    [ordered]@{arguments=$arguments;sha256=$hashes;source_commit=(git -C $root rev-parse HEAD);
        plans_path=$PlansPath;plans_sha256=(Get-FileHash -LiteralPath $PlansPath).Hash;
        scope='Independent normal-input trials, rendered only if not NullRHI. Fixed time, not FPS evidence. Checkpoint placement only before each trial; no resets count as recovery.'}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath "$out/launch.json" -Encoding utf8
    $start=New-Object System.Diagnostics.ProcessStartInfo
    $start.FileName='C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
    $start.WorkingDirectory=$root;$start.UseShellExecute=$false;$start.CreateNoWindow=$true
    $start.Arguments=($arguments|ForEach-Object {'"'+[regex]::Replace([regex]::Replace($_,'(\\*)"','$1$1\"'),'(\\+)$','$1$1')+'"'}) -join ' '
    $process=[System.Diagnostics.Process]::Start($start)
    Write-Host "RUN $river PID=$($process.Id) trials=$($trials.Count)"
    $process.WaitForExit()
    Write-Host "EXIT $river code=$($process.ExitCode)"
    $changed=@($hashes.Keys|Where-Object {
        !(Test-Path -LiteralPath "$root/$_") -or (Get-FileHash -LiteralPath "$root/$_").Hash -ne $hashes[$_]
    })
    [ordered]@{exit_code=$process.ExitCode;changed_dependencies=$changed;
        stable_dependencies=($changed.Count -eq 0)}|ConvertTo-Json -Depth 4|
        Set-Content -LiteralPath "$out/completion.json" -Encoding utf8
    if($changed.Count){throw "Trial dependencies changed during the run; preserve evidence and review: $($changed -join ', ')"}
    if($process.ExitCode -ne 0){throw "Native failure; inspect $out/native.log before any retry"}
    $report=Get-Content -LiteralPath "$out/automation/index.json" -Raw|ConvertFrom-Json
    $receipt=@($report.tests|Where-Object {$_.fullTestPath -eq 'RaftSim.Review.RiverDifficulty'})
    # A start on a bank or a refused contact step is caught and recorded in
    # that trial's outcome; those errors alone do not void the session.
    $latch='surface query refused|Raft fixed substep refused'
    $otherErrors=@($receipt.entries|Where-Object {$_.event.type -eq 'Error' -and $_.event.message -notmatch $latch})
    if($receipt.Count -ne 1 -or ($receipt[0].state -ne 'Success' -and $otherErrors.Count)){throw 'Missing successful native automation receipt'}
    $results=Get-Content -LiteralPath "$out/results.json" -Raw|ConvertFrom-Json
    if($results.trials.Count -ne $trials.Count){throw 'Incomplete trial coverage'}
    $results.trials|Select-Object id,outcome,elapsed_s,end_m,max_swimmers,recovered_route_at_s|Format-Table
}
