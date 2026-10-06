$ErrorActionPreference='Stop'
$tokens=$null; $errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'run_constriction_paired_review.ps1'),[ref]$tokens,[ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
foreach ($name in @('Test-ReviewCookIdentity','Get-ReviewCookProcesses','Test-ReviewCookInventory','Get-ReviewLocalPath','Test-ReviewPlayerCaptureLog','Get-ReviewTerrainRayArguments')) {
    $nodes=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name},$true))
    if ($nodes.Count -ne 1) { throw 'Missing production validator' }
    . ([scriptblock]::Create($nodes[0].Extent.Text))
}
$expected=[pscustomobject]@{pid=42; start_utc='2026-09-18T12:17:39.4321093Z'; executable='C:\repo\tmp\raftsim_cartesian_cook.exe'; sha256=('a'*64); command_line='solver input output 6000 1000 4'}
$actual=$expected.PSObject.Copy()
if (-not (Test-ReviewCookIdentity $expected $actual)) { throw 'Exact identity rejected' }
foreach ($field in @('pid','start_utc','executable','sha256','command_line')) {
    $bad=$expected.PSObject.Copy()
    $bad.$field=if ($field -eq 'pid') { 43 } else { 'different' }
    if (Test-ReviewCookIdentity $bad $actual) { throw ('Changed identity accepted: '+$field) }
}
$dated=$expected.PSObject.Copy(); $dated.start_utc=[datetime]::Parse($expected.start_utc,[cultureinfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind)
if (-not (Test-ReviewCookIdentity $dated $actual)) { throw 'JSON DateTime rejected' }
$dated.start_utc=$dated.start_utc.AddTicks(1)
if (Test-ReviewCookIdentity $dated $actual) { throw '100 ns identity change accepted' }
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$null=Get-ReviewLocalPath 'tmp/test.json' $root
foreach ($bad in @('tmp/../README.md','tmp/../../outside.json')) {
    $rejected=$false
    try { $null=Get-ReviewLocalPath $bad $root } catch { $rejected=$true }
    if (-not $rejected) { throw 'Outside path accepted' }
}
'PASS: exact cook identities and confined review paths, no process mutations'
foreach ($text in @('{"schema":"raftsim.paired_review_cooks.v2","processes":[]}',
    '{"schema":"raftsim.paired_review_cooks.v2","processes":[{"pid":42}]}',
    '{"schema":"raftsim.paired_review_cooks.v2","processes":[{"pid":42},{"pid":43}]}',
    '{"schema":"raftsim.paired_review_cooks.v1","processes":[{"pid":42},{"pid":43}]}')) {
    $manifest=$text | ConvertFrom-Json
    $entries=@(Get-ReviewCookProcesses $manifest)
    $live=@($entries | ForEach-Object { [pscustomobject]@{ProcessId=$_.pid} })
    if (-not (Test-ReviewCookInventory $entries $live)) { throw 'Exact explicit inventory rejected' }
    $extra=@($live)+@([pscustomobject]@{ProcessId=99})
    if (Test-ReviewCookInventory $entries $extra) { throw 'Unlisted active cook accepted' }
    if ($live.Count -gt 0 -and (Test-ReviewCookInventory $entries @())) { throw 'Completed cook accepted' }
}
foreach ($text in @('{"schema":"raftsim.paired_review_cooks.v1","processes":[]}',
    '{"schema":"raftsim.paired_review_cooks.v1","processes":[{"pid":42}]}',
    '{"schema":"raftsim.paired_review_cooks.v2","processes":null}',
    '{"schema":"raftsim.paired_review_cooks.v2"}',
    '{"schema":"raftsim.paired_review_cooks.v2","processes":{"pid":42}}',
    '{"schema":"raftsim.paired_review_cooks.v2","processes":[{"pid":42},{"pid":42}]}',
    '{"schema":"raftsim.paired_review_cooks.v2","processes":[{"pid":42},{"pid":43},{"pid":44}]}',
    '{"schema":"raftsim.paired_review_cooks.v2","processes":[{"pid":"42"}]}',
    '{"schema":"raftsim.paired_review_cooks.v2","processes":[{"pid":0}]}',
    '{"schema":"unknown","processes":[]}')) {
    $rejected=$false
    try { $null=Get-ReviewCookProcesses ($text | ConvertFrom-Json) } catch { $rejected=$true }
    if (-not $rejected) { throw ('Invalid inventory accepted: '+$text) }
}
if (Test-ReviewCookInventory @([pscustomobject]@{pid=42}) @([pscustomobject]@{ProcessId=43})) { throw 'Different same-size inventory accepted' }
'PASS: explicit zero/one/two cook inventories; legacy receipts stay strict; no process mutations'
$log=(@(0..23 | ForEach-Object { "LogTemp: Display: RaftSim PIE player-backbuffer capture: index=$_ saved=1" }) -join "`r`n")
if (-not (Test-ReviewPlayerCaptureLog $log 24)) { throw 'Complete player capture rejected' }
foreach ($bad in @('',($log+$log),$log.Replace('index=1 saved=1','index=1 saved=0'),$log.Replace('index=1 saved=1','index=0 saved=1'))) {
    if (Test-ReviewPlayerCaptureLog $bad 24) { throw 'Incomplete or mixed player-viewport capture accepted' }
}
'PASS: every numbered capture must confirm its actual player viewport'
$valid='{"capture_count":96,"terrain_capture_index":80,"terrain_pixels":[[300,350],[500,300]]}' | ConvertFrom-Json
$argsOut=@(Get-ReviewTerrainRayArguments $valid)
if ($argsOut.Count -ne 2 -or $argsOut[0] -cne '-RaftSimCaptureCarrierShapeIndex=80' -or $argsOut[1] -cne '-RaftSimCaptureTerrainPixels=300,350;500,300') { throw 'Exact bounded ray arguments changed' }
if (@(Get-ReviewTerrainRayArguments ([pscustomobject]@{})).Count) { throw 'Default launch acquired ray diagnostics' }
foreach ($text in @('{"terrain_capture_index":0}', '{"terrain_pixels":[[1,2]]}',
    '{"terrain_capture_index":24,"terrain_pixels":[[1,2]]}',
    '{"terrain_capture_index":0,"terrain_pixels":[[1280,2]]}',
    '{"terrain_capture_index":0,"terrain_pixels":[[1,720]]}',
    '{"terrain_capture_index":0,"terrain_pixels":[[1.5,2]]}',
    '{"terrain_capture_index":0,"terrain_pixels":[["1 -ExecCmds=bad",2]]}',
    '{"terrain_capture_index":0,"terrain_pixels":[]}')) {
    $rejected=$false
    try { $null=Get-ReviewTerrainRayArguments ($text | ConvertFrom-Json) } catch { $rejected=$true }
    if (-not $rejected) { throw ('Invalid ray arguments accepted: '+$text) }
}
'PASS: scoped terrain rays cannot escape the capture series or viewport'
