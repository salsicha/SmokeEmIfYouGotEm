# Parser and receipt fixtures only: no engine launch or visual/FPS acceptance.
$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile(
    (Join-Path $PSScriptRoot 'capture_shared_water_map.ps1'),[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Capture script must parse'}
$binding=[scriptblock]::Create($ast.ParamBlock.Extent.Text+"`nreturn @(`$Map,`$StationM)")
foreach($map in @('L_Hance','Continuous/L_Colorado_Full','Continuous/L_Chilko_Full')){
    $result=& $binding -Map $map -Label 'binding-only' -StationM 350000
    if($result[0] -cne $map -or $result[1] -ne 350000){throw 'Full-river capture binding failed'}
}
foreach($map in @('../L_Hance','Other/L_Hance','Continuous/../L_Hance','Continuous//L_Hance',
    'Continuous\L_Hance','Continuous/L_X?game=Other','/Game/RaftSim/Maps/L_Hance')){
    $rejected=$false
    try{$null=& $binding -Map $map -Label 'binding-only'}catch{$rejected=$true}
    if(-not $rejected){throw 'Unsafe map path accepted'}
}
$definitions=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Get-RaftSimCaptureMapIdentity'},$true))
if($definitions.Count -ne 1){throw 'Native map identity parser missing'}
Invoke-Expression $definitions[0].Extent.Text
$valid='LogLoad: LoadMap: /Game/RaftSim/Maps/Continuous/L_Colorado_Full?Name=Player'
if((Get-RaftSimCaptureMapIdentity 'Continuous/L_Colorado_Full' $valid) -cne 'L_Colorado_Full'){
    throw 'Verified full package did not yield native map name'
}
foreach($log in @('LogLoad: LoadMap: /Game/RaftSim/Maps/L_Colorado_Full',
    'LogLoad: LoadMap: /Game/RaftSim/Maps/Continuous/L_Colorado_FullOther',
    'LogLoad: LoadMap: /Game/RaftSim/Maps/Continuous/L_Hance', 'No successful load')){
    $rejected=$false
    try{$null=Get-RaftSimCaptureMapIdentity 'Continuous/L_Colorado_Full' $log}catch{$rejected=$true}
    if(-not $rejected){throw 'Wrong native package accepted from leaf name or prefix'}
}
'PASS: continuous capture paths/full-river stations and exact native package identity; fixtures only'
