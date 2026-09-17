$ErrorActionPreference = 'Stop'
$tokens = $null
$parseErrors = $null
$source = Join-Path $PSScriptRoot 'profile_south_fork_current_map.ps1'
$ast = [Management.Automation.Language.Parser]::ParseFile($source, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw 'Profiling script must parse without errors' }
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
