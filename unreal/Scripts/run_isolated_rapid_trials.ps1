# Fresh engine process per trial. Never reset a running trial or alter forces.
param([Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9][a-zA-Z0-9_.-]*$')][string]$Label,
    [Parameter(Mandatory=$true)][string]$PlansPath,
    [Parameter(Mandatory=$true)][string[]]$Rivers,
    [string[]]$TrialIds=@(),[switch]$Render,
    [ValidateRange(0,300)][int]$IdleSeconds=0,
    [ValidateRange(1,3600)][int]$MaxIdleWaitSeconds=1800)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=Join-Path $root "tmp/$Label"
if(Test-Path -LiteralPath $out){throw 'Fresh isolated campaign label required'}
$plans=Get-Content -LiteralPath $PlansPath -Raw | ConvertFrom-Json
$selected=@(foreach($river in $Rivers){
    $plan=@($plans | Where-Object {$_.river -eq $river})
    if($plan.Count -ne 1){throw "Missing or ambiguous river: $river"}
    foreach($trial in $plan[0].trials){
        if(!$TrialIds.Count -or $trial.id -in $TrialIds){
            [pscustomobject]@{river=$river;id=$trial.id}
        }
    }
})
if(!$selected.Count){throw 'Empty isolated trial selection'}
foreach($id in $TrialIds){if($id -notin $selected.id){throw "Unknown trial: $id"}}
New-Item -ItemType Directory -Path $out | Out-Null
$receipts=@()
$number=0
foreach($item in $selected){
    if($IdleSeconds -gt 0){
        $deadline=(Get-Date).AddSeconds($MaxIdleWaitSeconds)
        $idleSince=$null
        while($true){
            $busy=@(Get-CimInstance Win32_Process | Where-Object {
                $_.Name -match '^(UnrealEditor.*|UnrealBuildTool|SmokeEmIfYouGotEm.*|link)\.exe$' -or
                ($_.Name -eq 'dotnet.exe' -and $_.CommandLine -match 'UnrealBuildTool|AutomationTool')
            })
            if($busy.Count){$idleSince=$null}
            elseif($null -eq $idleSince){$idleSince=Get-Date}
            elseif(((Get-Date)-$idleSince).TotalSeconds -ge $IdleSeconds){break}
            if((Get-Date) -ge $deadline){throw 'Shared engine never remained idle; no competing trial launched'}
            Start-Sleep -Seconds 2
        }
    }
    $childLabel="$Label-case$($number.ToString('D3'))"
    & "$PSScriptRoot/run_rapid_assessment.ps1" -Label $childLabel -PlansPath $PlansPath `
        -Rivers @($item.river) -Rapids @($item.id) -PreparedTrials -Render:$Render
    # Child runner refuses active engines/builds and checks dependency hashes.
    $child=Join-Path $root "tmp/$childLabel/$($item.river)"
    $completion=Get-Content -LiteralPath "$child/completion.json" -Raw | ConvertFrom-Json
    $results=Get-Content -LiteralPath "$child/results.json" -Raw | ConvertFrom-Json
    if($completion.exit_code -ne 0 -or !$completion.stable_dependencies -or
       $results.trials.Count -ne 1 -or $results.trials[0].id -ne $item.id){
        throw "Incomplete or unstable isolated trial: $($item.id)"
    }
    $receipts+=@([ordered]@{river=$item.river;id=$item.id;directory=$child;outcome=$results.trials[0].outcome})
    [ordered]@{scope='Fresh engine process per trial. Compare actual start states and launch hashes before causal claims; not a human class grade or FPS measurement.';
        expected=$selected.Count;completed=$receipts.Count;trials=$receipts} |
        ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$out/index.json" -Encoding utf8
    ++$number
}
