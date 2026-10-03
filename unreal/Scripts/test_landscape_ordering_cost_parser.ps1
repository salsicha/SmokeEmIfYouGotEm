# Adversarial parser fixtures only, never native timings or FPS acceptance.
$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'compare_landscape_face_ordering.ps1'),[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'Ordering comparator AST invalid'}
$definitions=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Read-OrderingCosts'},$true))
if($definitions.Count -ne 1){throw 'Actual native cost parser missing'}
Invoke-Expression $definitions[0].Extent.Text
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$fixtureDir=Join-Path $root ('tmp/ordering-parser-fixtures-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $fixtureDir | Out-Null
$header='RaftSimGround/LandscapeRadixOrderQueries,RaftSimGround/LandscapeReferenceOrderQueries,RaftSimGround/GameThread/LandscapeFaceOrdering,RaftSimGround/GameThread/LandscapeFaceTraversal'
function New-Fixture([string]$Name,[string]$Row,[string]$Header=$header){
    $path=Join-Path $fixtureDir "$Name.csv"
    @('start')+@(1..70 | ForEach-Object {$Row})+@("EVENTS,$Header") | Set-Content -LiteralPath $path -Encoding UTF8
    # Actual UE CSV footer begins EVENTS in column0. Include that column in
    # every fixture row too; otherwise field alignment would be invalid.
    $lines=Get-Content -LiteralPath $path
    for($i=1;$i -le 70;$i++){$lines[$i]=','+$lines[$i]}
    $lines | Set-Content -LiteralPath $path -Encoding UTF8
    return $path
}
$reference=Read-OrderingCosts (New-Fixture 'reference' '0,2,.4,.6') $false
$radix=Read-OrderingCosts (New-Fixture 'radix' '2,0,.1,.6') $true
if($reference.reference_queries -ne 20 -or $radix.radix_queries -ne 20 -or
    $reference.audited_frames -ne 10 -or $radix.frames_with_actual_queries -ne 10 -or
    [math]::Abs($radix.ordering_ms_per_actual_query-.05) -gt 1e-12){throw 'Actual fixture values not retained'}
$failures=@(
    @{name='wrong-mode';row='2,0,.1,.6';mode=$false},
    @{name='both-modes';row='2,1,.1,.6';mode=$true},
    @{name='missing-counter';row=',0,.1,.6';mode=$true},
    @{name='nan-counter';row='NaN,0,.1,.6';mode=$true},
    @{name='infinite-counter';row='Infinity,0,.1,.6';mode=$true},
    @{name='fractional-counter';row='2.5,0,.1,.6';mode=$true},
    @{name='negative-counter';row='-1,0,.1,.6';mode=$true},
    @{name='missing-executed-timing';row='2,0,,.6';mode=$true},
    @{name='nan-executed-timing';row='2,0,NaN,.6';mode=$true},
    @{name='negative-executed-timing';row='2,0,-.1,.6';mode=$true},
    @{name='no-queries';row='0,0,,';mode=$true}
)
foreach($case in $failures){
    $path=New-Fixture $case.name $case.row;$rejected=$false
    try {Read-OrderingCosts $path $case.mode | Out-Null}catch{$rejected=$true}
    if(!$rejected){throw "Malformed/unqualified fixture accepted: $($case.name)"}
}
$missingHeader=$header.Replace('RaftSimGround/LandscapeReferenceOrderQueries','wrong')
$rejected=$false
try {Read-OrderingCosts (New-Fixture 'missing-column' '2,0,.1,.6' $missingHeader) $true | Out-Null}catch{$rejected=$true}
if(!$rejected){throw 'Missing actual counter column accepted'}
# Genuine zero counters permit absent unexecuted timing, but never absent
# counters or absent timing for an executed query.
$path=New-Fixture 'mixed-zero-query' '2,0,.1,.6'
$lines=Get-Content -LiteralPath $path;$lines[31]=',0,0,,'
$lines | Set-Content -LiteralPath $path -Encoding UTF8
$mixed=Read-OrderingCosts $path $true
if($mixed.audited_frames -ne 10 -or $mixed.frames_with_actual_queries -ne 9 -or $mixed.radix_queries -ne 18){throw 'Explicit native no-query semantics lost'}
'PASS: two requested modes, explicit zero-query frame and twelve invalid/missing/no-query controls; parser fixtures only'
