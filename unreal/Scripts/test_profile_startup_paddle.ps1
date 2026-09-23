$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'profile_south_fork_current_map.ps1'
$tokens = $null
$errors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($source, [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw 'Runner must parse' }
$rejected = $false
try { & $source -Label 'south-fork-test-paddle' -StartupPaddle }
catch {
    if ($_.Exception.Message -cne 'StartupPaddle requires StartupRenderReplay; it is not an ordinary FPS capture') { throw }
    $rejected = $true
}
if (-not $rejected) { throw 'Paddle option leaked into ordinary cost capture' }
$assignment = @($ast.FindAll({ param($node)
    $node -is [Management.Automation.Language.AssignmentStatementAst] -and
    $node.Left.Extent.Text -ceq '$paddleOption'
}, $true))
if ($assignment.Count -ne 1) { throw 'Expected one production option builder' }
$build = [scriptblock]::Create($assignment[0].Extent.Text+'; $paddleOption')
$StartupPaddle = $false
if ((& $build) -cne '') { throw 'Default capture must not inject input' }
$StartupPaddle = $true
if ((& $build) -cne ' paddle') { throw 'Explicit capture must use the normal crew-command path' }
'PASS: normal input unchanged; explicit capture paddle option; pre-process guard'
