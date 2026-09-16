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
$rejected = $false
try {
    & $source -Label 'south-fork-test-invalid-modes' -CookProcessId 0 -CookStartUtc 'invalid' -NativePerformanceGate -DetailStreamingReplay
} catch {
    if ($_.Exception.Message -ne 'Choose one native validation mode') { throw }
    $rejected = $true
}
if (-not $rejected) { throw 'Conflicting validation modes were accepted' }
'PASS: conflicting validation modes rejected before process access'
