# Exercise the actual launch-receipt expression with parser-only bindings.
# These fake bindings are NOT engine launches or performance evidence.
$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'profile_map_flythrough.ps1'),[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Flythrough runner AST invalid'}
$receipts=@($ast.FindAll({param($node)
    if($node -isnot [Management.Automation.Language.HashtableAst]){return $false}
    foreach($entry in $node.KeyValuePairs){
        if($entry.Item1.Extent.Text -eq 'schema' -and $entry.Item2.Extent.Text -eq "'raftsim.map_flythrough_launch.v1'"){return $true}
    }
    return $false
},$true))
if($receipts.Count -ne 1){throw 'Exactly one native launch-receipt expression required'}
$Map='L_Hance';$Label='parser-only-fixture';$arguments=@('parser-only');$hashes=@{fixture='not-a-binary-hash'}
$process=[pscustomobject]@{Id=1;ExitCode=0};$scope='parser-only';$PackagedRoot=''
$receipt=& ([scriptblock]::Create($receipts[0].Extent.Text))
foreach($name in @('recording','screenshots','boat_guidance')){
    if($receipt[$name] -isnot [bool] -or $receipt[$name]){throw 'Native timing receipt must retain explicit false Boolean diagnostics'}
}
if($receipt.map -ne $Map -or $receipt.exit_code -ne 0){throw 'Launch receipt lost actual map/exit bindings'}
'PASS: native launch receipt executes with Boolean flags; fixtures are parser-only'
