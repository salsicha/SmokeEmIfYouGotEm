# Adversarial parser fixtures, not an engine or FPS test.
$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'profile_south_fork_menu_launch_ps5.ps1'),[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Profiler AST invalid'}
$functions=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Get-RaftSimRestKeyObservation'},$true))
if($functions.Count -ne 1){throw 'Exactly one actual observation parser required'}
Invoke-Expression $functions[0].Extent.Text
$header=@('RaftSimHull/RestKeySealedChecks','RaftSimHull/RestKeyReferenceChecks')
$sealed=Get-RaftSimRestKeyObservation $header @('8,0','7,1') $false
if($sealed.audited_frames -ne 2 -or $sealed.sealed_checks_sum -ne 15 -or $sealed.reference_checks_sum -ne 1){throw 'Actual sealed counts not preserved'}
$reference=Get-RaftSimRestKeyObservation $header @('0,8','0,8') $true
if($reference.sealed_checks_sum -ne 0 -or $reference.reference_checks_sum -ne 16){throw 'Reference counts not preserved'}
foreach($case in @(
    @{header=$header;rows=@('8,0');reference=$true},
    @{header=$header;rows=@('0,8');reference=$false},
    @{header=$header;rows=@('0,0');reference=$true},
    @{header=$header;rows=@('8,');reference=$false},
    @{header=$header;rows=@('NaN,0');reference=$false},
    @{header=$header;rows=@('Infinity,0');reference=$false},
    @{header=$header;rows=@('-1,0');reference=$false},
    @{header=$header;rows=@('8.1,0');reference=$false},
    @{header=@($header[0]);rows=@('8');reference=$false},
    @{header=@('FrameTime');rows=@('40');reference=$true}
)){
    $rejected=$false
    try{$null=Get-RaftSimRestKeyObservation $case.header $case.rows $case.reference}catch{$rejected=$true}
    if(-not $rejected){throw 'Missing, malformed or wrong native mode must refuse'}
}
if($null -ne (Get-RaftSimRestKeyObservation @('FrameTime') @('40') $false)){throw 'Older unflagged profiles must not invent native counters'}
'PASS: native rest-key modes, counts and missing/nonfinite observations are fail-closed'
