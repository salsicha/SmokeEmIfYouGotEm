$ErrorActionPreference = 'Stop'
$tokens = $null
$parseErrors = $null
$source = Join-Path $PSScriptRoot 'profile_south_fork_current_map.ps1'
$ast = [Management.Automation.Language.Parser]::ParseFile($source, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw 'Profiling script must parse without errors' }
$laneFunction = @($ast.FindAll({
    param($node)
    $node -is [Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -eq 'Test-RaftSimSolverLaneLog'
}, $true))
if ($laneFunction.Count -ne 1) { throw 'Expected one production worker-limit validator' }
. ([scriptblock]::Create($laneFunction[0].Extent.Text))
$archiveHash = 'a' * 64
$laneLog = "[time][  0]LogTemp: Display: RaftSim live-water solver archive: $archiveHash`r`n[time][  0]LogTemp: Display: RaftSim live-water solver lane limit: 8 (diagnostic override)`r`n"
if (-not (Test-RaftSimSolverLaneLog $laneLog 8 $archiveHash)) { throw 'Confirmed worker limit rejected' }
foreach ($invalid in @('', '-RaftSimSolverLanes=8', $laneLog.Replace('8 (', '4 ('),
    $laneLog.Replace('diagnostic override', 'default'), $laneLog.Replace($archiveHash, ('b' * 64)),
    ($laneLog + $laneLog), ($laneLog + 'LogTemp: Display: RaftSim live-water solver lane limit: 4 (default)'))) {
    if (Test-RaftSimSolverLaneLog $invalid 8 $archiveHash) { throw 'Missing, conflicting or stale worker evidence accepted' }
}
foreach ($badExpected in @(0, 65)) {
    if (Test-RaftSimSolverLaneLog $laneLog $badExpected $archiveHash) { throw 'Invalid expected lane count accepted' }
}
foreach ($duplicate in @(@{ ExtraGameArgument='-RaftSimSolverLanes=4' }, @{ ExtraGameArguments=@('-RaftSimSolverLanes=8') })) {
    $rejected = $false
    try { & $source -Label 'south-fork-test-duplicate-lanes' -CookProcessId 0 -CookStartUtc 'invalid' -SolverLanes 8 @duplicate }
    catch {
        if ($_.Exception.Message -ne 'Use SolverLanes once, not a duplicate extra game argument') { throw }
        $rejected = $true
    }
    if (-not $rejected) { throw 'Duplicate worker override accepted' }
}
'PASS: worker comparison requires one runtime limit and the linked archive identity'
$frameModeFunction = @($ast.FindAll({
    param($node)
    $node -is [Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -eq 'Test-RaftSimFrameTimeModeLog'
}, $true))
if ($frameModeFunction.Count -ne 1) { throw 'Expected one production CSV timing-mode validator' }
. ([scriptblock]::Create($frameModeFunction[0].Extent.Text))
foreach ($valid in @('csv.UseLegacyFrameTime = "0"', '[time]LogConsoleManager: csv.UseLegacyFrameTime = "0" LastSetBy:Console', '[time][  0]csv.UseLegacyFrameTime = "false"')) {
    if (-not (Test-RaftSimFrameTimeModeLog $valid)) { throw 'Confirmed default frame-time mode rejected' }
}
foreach ($invalid in @('', '-ExecCmds=csv.UseLegacyFrameTime 0', 'csv.UseLegacyFrameTime = "1"',
    'csv.UseLegacyFrameTime = "0.5"', 'csv.UseLegacyFrameTime = "true"', "csv.UseLegacyFrameTime = `"0`"`ncsv.UseLegacyFrameTime = `"1`"")) {
    if (Test-RaftSimFrameTimeModeLog $invalid) { throw 'Absent/request-only/conflicting timing-mode evidence accepted' }
}
'PASS: CSV frame-time mode requires runtime confirmation, not command intent'
if (-not (Test-RaftSimFrameTimeModeLog "prefix`r`n[time][  0]csv.UseLegacyFrameTime = `"false`"`r`nnext`r`n")) {
    throw 'Actual Windows CRLF log format rejected'
}
if (Test-RaftSimFrameTimeModeLog "csv.UseLegacyFrameTime = `"false`"`r`ncsv.UseLegacyFrameTime = `"true`"`r`n") {
    throw 'Conflicting CRLF timing modes accepted'
}
# Exercise the production normalization expression without starting, suspending,
# or resuming any process. No Unreal installation or running cook is required.
$assignment = @($ast.FindAll({
    param($node)
    $node -is [Management.Automation.Language.AssignmentStatementAst] -and
    $node.Left.Extent.Text -eq '$expectedStartUtc'
}, $true))
if ($assignment.Count -ne 1) { throw 'Expected one production start-time normalization' }
$normalize = [scriptblock]::Create($assignment[0].Extent.Text + '; $expectedStartUtc')
$stamp = '2026-09-16T20:41:40.8546390Z'
$cases = @(
    [pscustomobject]@{ start_utc=$stamp },
    [pscustomobject]@{ start_utc=[datetime]::Parse($stamp, [cultureinfo]::InvariantCulture, [Globalization.DateTimeStyles]::RoundtripKind) },
    ([string]('{"start_utc":"' + $stamp + '"}') | ConvertFrom-Json)
)
foreach ($identity in $cases) {
    $normalized = & $normalize
    if ($normalized -cne $stamp) { throw 'Equivalent manifest time failed exact identity comparison' }
}
foreach ($badStamp in @('2026-09-16T20:41:40.8546391Z', '2026-09-16T20:41:41.8546390Z', '', 'invalid')) {
    $identity = [pscustomobject]@{ start_utc=$badStamp }
    if ((& $normalize) -ceq $stamp) { throw 'Changed or invalid timestamp accepted' }
}
$identity = [pscustomobject]@{ start_utc=$cases[1].start_utc.AddTicks(1) }
if ((& $normalize) -ceq $stamp) { throw 'DateTime normalization lost 100 ns identity precision' }
'PASS: exact process identity timestamps (string, DateTime, JSON, and rejection cases)'
foreach ($modes in @(
    @{ NativePerformanceGate=$true; DetailStreamingReplay=$true },
    @{ NativePerformanceGate=$true; StartupRenderReplay=$true },
    @{ DetailStreamingReplay=$true; StartupRenderReplay=$true },
    @{ NativePerformanceGate=$true; DetailStreamingReplay=$true; StartupRenderReplay=$true }
)) {
    $rejected = $false
    try {
        & $source -Label 'south-fork-test-invalid-modes' -CookProcessId 0 -CookStartUtc 'invalid' @modes
    } catch {
        if ($_.Exception.Message -ne 'Choose one capture or validation mode') { throw }
        $rejected = $true
    }
    if (-not $rejected) { throw 'Conflicting validation modes were accepted' }
}
'PASS: conflicting validation modes rejected before process access'
$rejected = $false
try {
    & $source -Label 'south-fork-test-invalid-buffer' -CookProcessId 0 -CookStartUtc 'invalid' -StartupBufferVisualization WorldNormal
} catch {
    if ($_.Exception.Message -ne 'Buffer visualization requires StartupRenderReplay; it is not an FPS capture') { throw }
    $rejected = $true
}
if (-not $rejected) { throw 'Buffer visualization was allowed in a performance capture' }
$bufferAssignment = @($ast.FindAll({
    param($node)
    $node -is [Management.Automation.Language.AssignmentStatementAst] -and
    $node.Left.Extent.Text -eq '$bufferCommands'
}, $true))
if ($bufferAssignment.Count -ne 1) { throw 'Expected one production buffer command builder' }
$buildBuffer = [scriptblock]::Create($bufferAssignment[0].Extent.Text + '; $bufferCommands')
foreach ($StartupBufferVisualization in @('', 'WorldNormal', 'Roughness', 'SceneDepth')) {
    $expected = if ($StartupBufferVisualization) { "viewmode VisualizeBuffer,r.BufferVisualizationTarget $StartupBufferVisualization," } else { '' }
    if ((& $buildBuffer) -cne $expected) { throw 'Diagnostic command ordering or ordinary capture changed' }
}
'PASS: buffer diagnostics are opt-in, ordered, and excluded from performance captures'
$logFunction = @($ast.FindAll({
    param($node)
    $node -is [Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -eq 'Test-RaftSimBufferDiagnosticLog'
}, $true))
if ($logFunction.Count -ne 1) { throw 'Expected one production buffer log validator' }
. ([scriptblock]::Create($logFunction[0].Extent.Text))
$validLog = "Set new viewmode: VisualizeBuffer`nr.BufferVisualizationTarget = ""WorldNormal"""
if (-not (Test-RaftSimBufferDiagnosticLog $validLog 'WorldNormal')) { throw 'Valid debug commands rejected' }
foreach ($invalidLog in @('', 'r.BufferVisualizationTarget = "WorldNormal"', ($validLog + "`nError: view mode not recognized: buffervisualization"), ($validLog + "`nDebug viewmodes not allowed in Test or Shipping builds."))) {
    if (Test-RaftSimBufferDiagnosticLog $invalidLog 'WorldNormal') { throw 'Unconfirmed/rejected debug commands accepted' }
}
if (Test-RaftSimBufferDiagnosticLog $validLog 'Roughness') { throw 'Wrong buffer accepted' }
'PASS: rejected, absent and wrong-buffer command evidence fails closed'
$rejected = $false
try {
    & $source -Label 'south-fork-test-invalid-normal' -CookProcessId 0 -CookStartUtc 'invalid' -StartupOpticalNormalStrength 0
} catch {
    if ($_.Exception.Message -ne 'Optical normal control requires StartupRenderReplay; it is not an FPS capture') { throw }
    $rejected = $true
}
if (-not $rejected) { throw 'Optical normal control was allowed in a performance capture' }
$normalAssignment = @($ast.FindAll({
    param($node)
    $node -is [Management.Automation.Language.AssignmentStatementAst] -and
    $node.Left.Extent.Text -eq '$normalCommands'
}, $true))
if ($normalAssignment.Count -ne 1) { throw 'Expected one production optical normal command builder' }
$buildNormal = [scriptblock]::Create($normalAssignment[0].Extent.Text + '; $normalCommands')
foreach ($StartupOpticalNormalStrength in @($null, 0.0, 0.18, 1.0)) {
    $expected = if ($null -ne $StartupOpticalNormalStrength) { 'RaftSim.WaterMaterialProbe SouthForkCurrentNormalStrength ' + $StartupOpticalNormalStrength.ToString('R', [cultureinfo]::InvariantCulture) + ' delay=0.05,' } else { '' }
    if ((& $buildNormal) -cne $expected) { throw 'Optical control changed default capture or lost its explicit value' }
}
'PASS: optical normal controls are explicit, startup-only and invariant-culture'
foreach ($taskMode in @('NativePerformanceGate','DetailStreamingReplay','StartupRenderReplay','CheckpointResetReplay')) {
    $taskModeArgs=@{}; $taskModeArgs[$taskMode]=$true; $rejected=$false
    try { & $source -Label 'south-fork-test-invalid-profile-length' -CookProcessId 0 -CookStartUtc 'invalid' -ProfileFrames 1200 @taskModeArgs }
    catch { if ($_.Exception.Message -ne 'ProfileFrames only applies to ordinary CSV capture') { throw }; $rejected=$true }
    if (-not $rejected) { throw 'CSV length changed a native/replay mode' }
}
$profileAssignment=@($ast.FindAll({param($node)
    $node -is [Management.Automation.Language.AssignmentStatementAst] -and $node.Left.Extent.Text -eq '$profileCommands'
},$true))
if ($profileAssignment.Count -ne 1) { throw 'Expected one production CSV command builder' }
$buildProfile=[scriptblock]::Create($profileAssignment[0].Extent.Text+'; $profileCommands')
$Label='south-fork-test-profile-length'
foreach ($ProfileFrames in @(300,1200,2400)) {
    if ((& $buildProfile) -cne "-ExecCmds=csv.UseLegacyFrameTime 0,csv.TargetFrameRateOverride 30,CsvCategory FMsgLogf disable,csvprofile STARTFILE=$Label,csvprofile FRAMES=$ProfileFrames") { throw 'CSV duration or explicit timing mode changed unrelated commands' }
}
$profileParam=@($ast.ParamBlock.Parameters | Where-Object {$_.Name.VariablePath.UserPath -eq 'ProfileFrames'})
if ($profileParam.Count -ne 1 -or $profileParam[0].DefaultValue.Extent.Text -ne '300') { throw 'Default profiling duration changed' }
'PASS: longer CSV histories are explicit; replay/native gates and 300-frame default unchanged'
