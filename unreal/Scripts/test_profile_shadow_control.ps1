$ErrorActionPreference = 'Stop'
$tokens = $null
$parseErrors = $null
$source = Join-Path $PSScriptRoot 'profile_south_fork_current_map.ps1'
$ast = [Management.Automation.Language.Parser]::ParseFile($source, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw 'Production runner must parse' }
$validator = @($ast.FindAll({ param($node)
    $node -is [Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -ceq 'Test-RaftSimShadowControlLog'
}, $true))
if ($validator.Count -ne 1) { throw 'Expected production shadow validator' }
. ([scriptblock]::Create($validator[0].Extent.Text))
$confirmed = '[time][  0]ShowFlag.DynamicShadows = "0" LastSetBy: Console'
if (-not (Test-RaftSimShadowControlLog $confirmed)) { throw 'Confirmed control rejected' }
if (-not (Test-RaftSimShadowControlLog ($confirmed+"`r`n"+$confirmed+"`r`n"))) { throw 'Consistent CRLF responses rejected' }
foreach ($invalid in @('', '-DPCVars=ShowFlag.DynamicShadows=0',
    'Setting CommandLine Device Profile CVar: [[ShowFlag.DynamicShadows:0]]',
    $confirmed.Replace('"0"','"1"'), $confirmed.Replace('"0"','"2"'),
    ($confirmed+"`n"+$confirmed.Replace('"0"','"1"')),
    ($confirmed+"`nThe ini file 'DeviceProfiles' tries to set the console variable 'ShowFlag.DynamicShadows'"))) {
    if (Test-RaftSimShadowControlLog $invalid) { throw 'Unconfirmed, rejected or conflicting shadow control accepted' }
}
foreach ($arguments in @(@{}, @{ StartupRenderReplay=$true; ExtraGameArguments=@('-DPCVars=ShowFlag.DynamicShadows=0') })) {
    $rejected = $false
    try { & $source -Label 'south-fork-test-shadow-control' -StartupDisableDynamicShadows @arguments }
    catch {
        if ($_.Exception.Message -cnotin @('Shadow control requires StartupRenderReplay; it is not an FPS capture',
            'Use StartupDisableDynamicShadows once, not an extra shadow override')) { throw }
        $rejected = $true
    }
    if (-not $rejected) { throw 'Shadow control guard failed before process access' }
}
$assignment = @($ast.FindAll({ param($node)
    $node -is [Management.Automation.Language.AssignmentStatementAst] -and
    $node.Left.Extent.Text -ceq '$shadowCommands'
}, $true))
if ($assignment.Count -ne 1) { throw 'Expected single command builder' }
$build = [scriptblock]::Create($assignment[0].Extent.Text+'; $shadowCommands')
$StartupDisableDynamicShadows = $false
if ((& $build) -cne '') { throw 'Normal capture must not override shadows' }
$StartupDisableDynamicShadows = $true
if ((& $build) -cne 'ShowFlag.DynamicShadows 0,') { throw 'Diagnostic must use console path' }
'PASS: shadow command, normal default, runtime confirmation and pre-process isolation guards'
