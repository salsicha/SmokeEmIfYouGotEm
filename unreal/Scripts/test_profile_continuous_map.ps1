# Parameter binding only; does not launch the engine or imply performance.
$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile(
    (Join-Path $PSScriptRoot 'profile_reference_map_ps5.ps1'),[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Profiler must parse'}
$binding=[scriptblock]::Create($ast.ParamBlock.Extent.Text+"`nreturn `$Map")
foreach($map in @('L_Hance','L_LavaCanyon','Continuous/L_Colorado_ContinuousShoreSixSupportV3','Continuous/L_Chilko_ContinuousV1')){
    if((& $binding -Map $map -Label 'binding-only') -cne $map){throw 'Valid authored/candidate map lost'}
}
foreach($map in @('../L_Hance','Continuous/../L_Hance','Continuous//L_Hance',
    'Other/L_Hance','/Game/RaftSim/Maps/L_Hance','Continuous\L_Hance','Continuous/L_X.umap','Continuous/L_X?game=Other')){
    $rejected=$false
    try{$null=& $binding -Map $map -Label 'binding-only'}catch{$rejected=$true}
    if(-not $rejected){throw "Unsafe map path accepted: $map"}
}
'PASS: legacy and continuous map parameter binding; traversal, alternate directories and URL options refused'
$stationBinding=[scriptblock]::Create($ast.ParamBlock.Extent.Text+"`nreturn `$StationM")
foreach($station in @(-1,0,100001,350000,453334)){
    if((& $stationBinding -Map 'Continuous/L_Colorado_Full' -Label 'binding-only' -StationM $station) -ne $station){
        throw 'Full-river station was truncated or rejected'
    }
}
$rejected=$false
try{$null=& $stationBinding -Map 'L_Hance' -Label 'binding-only' -StationM -2}catch{$rejected=$true}
if(-not $rejected){throw 'Unsupported negative station accepted'}
'PASS: full-river station binding, including downstream of 100 km; native chart limits still required'
