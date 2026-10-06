$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'profile_south_fork_current_map.ps1'
$tokens = $null
$errors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($source, [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw 'Runner must parse' }
foreach ($case in @(
    @{ Args = @{ StartupHighSide = $true }; Error = 'StartupHighSide requires StartupRenderReplay; it is not an ordinary FPS capture' },
    @{ Args = @{ StartupHighSide = $true; StartupRenderReplay = $true; StartupPaddle = $true }; Error = 'Choose one startup crew command' }
)) {
    $rejected = $false
    try { $arguments = $case.Args; & $source -Label 'south-fork-test-high-side' @arguments }
    catch { if ($_.Exception.Message -cne $case.Error) { throw }; $rejected = $true }
    if (-not $rejected) { throw 'Invalid high-side capture was not rejected before launching' }
}
$assignment = @($ast.FindAll({ param($node)
    $node -is [Management.Automation.Language.AssignmentStatementAst] -and
    $node.Left.Extent.Text -ceq '$highSideOption'
}, $true))
if ($assignment.Count -ne 1) { throw 'Expected one production option builder' }
$build = [scriptblock]::Create($assignment[0].Extent.Text+'; $highSideOption')
$StartupHighSide = $false
if ((& $build) -cne '') { throw 'Default capture must not inject input' }
$StartupHighSide = $true
if ((& $build) -cne ' highside') { throw 'Explicit capture must use the normal crew-command path' }
'PASS: high-side option, unchanged default, mutually exclusive commands and pre-process guards'

foreach ($replay in @('StartupRenderReplay','DetailStreamingReplay','CheckpointResetReplay','NativePerformanceGate')) {
    $rejected=$false
    try { $arguments=@{ProfileHighSide=$true};$arguments[$replay]=$true; & $source -Label 'south-fork-test-high-side' @arguments }
    catch { if($_.Exception.Message -cne 'ProfileHighSide requires an ordinary CSV run without replay, recording or other input'){throw};$rejected=$true }
    if(-not $rejected){throw 'Mixed recording/profile command was accepted'}
}
$assignment=@($ast.FindAll({param($node)
    $node -is [Management.Automation.Language.AssignmentStatementAst] -and $node.Left.Extent.Text -ceq '$profileCrewCommands'
},$true))
if($assignment.Count -ne 1){throw 'Expected one input-only profile command builder'}
$build=[scriptblock]::Create($assignment[0].Extent.Text+'; $profileCrewCommands')
$ProfileHighSide=$false
if((& $build) -cne ''){throw 'Ordinary cost default must not issue commands'}
$ProfileHighSide=$true
if((& $build) -cne 'RaftSim.ProfileHighSide,'){throw 'Profile probe must issue only the normal command'}
'PASS: isolated input-only high-side cost option and replay guards'
