$ErrorActionPreference = 'Stop'
$tokens = $null; $errors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile(
    (Join-Path $PSScriptRoot 'profile_south_fork_menu_launch_ps5.ps1'), [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
foreach ($name in @('Get-RaftSimDetailEdgeMode', 'Test-RaftSimProfileWorkload')) {
    $nodes = @($ast.FindAll({ param($node)
        $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $name
    }, $true))
    if ($nodes.Count -ne 1) { throw "Expected production helper: $name" }
    . ([scriptblock]::Create($nodes[0].Extent.Text))
}
$normal = '[2026.09.28][ 12]LogTemp: Display: Crest selective detail edges: enabled=1 legacy_override=0; original shoreline points, profile tolerance and physics retained'
$legacy = $normal.Replace('enabled=1 legacy_override=0;', 'enabled=0 legacy_override=1;')
foreach ($control in @($false, $true)) {
    $valid = if ($control) { $legacy } else { $normal }
    $mode = Get-RaftSimDetailEdgeMode ($valid+"`r`n"+$valid) $control
    if ($mode.selective_enabled -eq $control -or $mode.legacy_override -ne $control -or $mode.confirmed_reports -ne 2) {
        throw 'Runtime mode was not retained faithfully'
    }
    foreach ($invalid in @('', '-RaftSimLegacyDetailEdges', ($normal+"`n"+$legacy),
        $valid.Replace('enabled=', 'enabled=9'), $valid.Replace('Display:', 'Warning:'),
        $valid.Replace('legacy_override=', 'legacy_override=9'))) {
        $rejected = $false
        try { $null = Get-RaftSimDetailEdgeMode $invalid $control } catch { $rejected = $true }
        if (-not $rejected) { throw 'Unconfirmed or conflicting runtime mode accepted' }
    }
    $opposite = if ($control) { $normal } else { $legacy }
    $rejected = $false
    try { $null = Get-RaftSimDetailEdgeMode $opposite $control } catch { $rejected = $true }
    if (-not $rejected) { throw 'Opposite runtime mode accepted' }
}
foreach ($work in @(
    @{Name='python.exe';CommandLine='python -u unreal/Plugins/SEIYGECore/python/scripts/audit_south_fork_prescribed_physical_transport.py'},
    @{Name='pythonw.exe';CommandLine='python -m audit_south_fork_affine_front_metric'},
    @{Name='UnrealEditor-Cmd.exe';CommandLine='editor'},
    @{Name='dotnet.exe';CommandLine='UnrealBuildTool'},
    @{Name='raftsim_cartesian_cook.exe';CommandLine='cook'})) {
    if (-not (Test-RaftSimProfileWorkload $work)) { throw 'Competing workload omitted' }
}
if (Test-RaftSimProfileWorkload @{Name='python.exe';CommandLine='python unrelated.py'}) { throw 'Unrelated Python blocked' }
# Execute the production argument branch too; no process launch is involved.
$branches = @($ast.FindAll({ param($node)
    $node -is [Management.Automation.Language.IfStatementAst] -and
    $node.Clauses[0].Item1.Extent.Text -ceq '$LegacyDetailEdges'
}, $true))
if ($branches.Count -ne 1) { throw 'Expected one detail-edge argument branch' }
$argumentBuilder = [scriptblock]::Create('$gameArgs = @(''-game''); '+$branches[0].Extent.Text+'; ,$gameArgs')
foreach ($control in @($false, $true)) {
    $LegacyDetailEdges = $control
    $actual = & $argumentBuilder
    $expectedCount = if ($control) { 2 } else { 1 }
    if ($actual.Count -ne $expectedCount -or $actual[0] -cne '-game') { throw 'Unexpected game arguments' }
    if ($control -and $actual[1] -cne '-RaftSimLegacyDetailEdges') { throw 'Missing legacy-edge control argument' }
}
# Evaluate the actual normal_configuration expression, not a test duplicate.
$tables = @($ast.FindAll({ param($node) $node -is [Management.Automation.Language.HashtableAst] }, $true))
$values = @($tables | ForEach-Object { $_.KeyValuePairs } | Where-Object { $_.Item1.Value -eq 'normal_configuration' })
if ($values.Count -ne 1) { throw 'Expected one normal-configuration receipt field' }
$expression = [scriptblock]::Create($values[0].Item2.Extent.Text)
$DiagnosticExecCmds = ''; $LegacyBreakingSearch = $false; $LegacyDetailEdges = $false
if (-not (& $expression)) { throw 'Normal default misclassified' }
$LegacyDetailEdges = $true
if (& $expression) { throw 'Detail-edge control mislabeled normal' }
$LegacyDetailEdges = $false; $LegacyBreakingSearch = $true
if (& $expression) { throw 'Breaking-search control mislabeled normal' }
$LegacyBreakingSearch = $false; $DiagnosticExecCmds = 'r.Shadow.Virtual.Enable 0'
if (& $expression) { throw 'Quality override mislabeled normal' }
'PASS: actual runtime mode, conflicting evidence, control receipt and workload isolation'
