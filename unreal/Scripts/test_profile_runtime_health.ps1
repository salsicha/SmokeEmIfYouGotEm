$ErrorActionPreference = 'Stop'
$tokens = $null; $errors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile(
    (Join-Path $PSScriptRoot 'profile_south_fork_menu_launch_ps5.ps1'), [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
$functions = @($ast.FindAll({ param($node)
    $node -is [Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -eq 'Get-RaftSimRuntimeErrors'
}, $true))
if ($functions.Count -ne 1) { throw 'Expected production health parser' }
. ([scriptblock]::Create($functions[0].Extent.Text))
if (@(Get-RaftSimRuntimeErrors 'LogTemp: Display: Error: quoted status').Count) { throw 'Display line is not an error' }
$log = @(
    '[2026.09.26-17.56.53:253][ 54]LogTemp: Error: Stateful detail dispatch rejected: Invalid mean-flow depth, velocity or aeration',
    'LogTemp: Warning: warmup',
    'LogCore: Fatal: test failure'
) -join "`r`n"
$found = @(Get-RaftSimRuntimeErrors $log)
if ($found.Count -ne 2 -or $found[0] -notmatch 'dispatch rejected' -or $found[1] -notmatch 'Fatal:') {
    throw 'Runtime failure omitted from timing health gate'
}
'PASS: timestamped errors and fatal diagnostics retained; display/warning lines excluded'
