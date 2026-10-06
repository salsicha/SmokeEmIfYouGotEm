$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'profile_south_fork_current_map.ps1'
$tokens = $null
$errors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($source, [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw 'Runner must parse' }
foreach ($case in @(
    @{ Args=@{StartupCrewOverboard=$true}; Error='StartupCrewOverboard requires render replay without other crew input' },
    @{ Args=@{StartupCrewOverboard=$true;StartupRenderReplay=$true;StartupPaddle=$true}; Error='StartupCrewOverboard requires render replay without other crew input' },
    @{ Args=@{StartupCrewOverboard=$true;StartupRenderReplay=$true;StartupHighSide=$true}; Error='StartupCrewOverboard requires render replay without other crew input' },
    @{ Args=@{ProfileCrewOverboard=$true;ProfileHighSide=$true}; Error='ProfileCrewOverboard requires an ordinary CSV run without other input' },
    @{ Args=@{ProfileCrewOverboard=$true;StartupRenderReplay=$true}; Error='ProfileCrewOverboard requires an ordinary CSV run without other input' },
    @{ Args=@{ProfileCrewOverboard=$true;NativePerformanceGate=$true}; Error='ProfileCrewOverboard requires an ordinary CSV run without other input' },
    @{ Args=@{ProfileCrewOverboard=$true;DetailStreamingReplay=$true}; Error='ProfileCrewOverboard requires an ordinary CSV run without other input' },
    @{ Args=@{ProfileCrewOverboard=$true;CheckpointResetReplay=$true}; Error='ProfileCrewOverboard requires an ordinary CSV run without other input' }
)) {
    $rejected=$false
    try { $arguments=$case.Args; & $source -Label 'south-fork-test-overboard' @arguments }
    catch { if ($_.Exception.Message -cne $case.Error) { throw }; $rejected=$true }
    if (-not $rejected) { throw 'Invalid input mix was not rejected before process access' }
}
foreach ($name in @('$overboardOption','$profileCrewCommands')) {
    $assignments=@($ast.FindAll({param($node)
        $node -is [Management.Automation.Language.AssignmentStatementAst] -and $node.Left.Extent.Text -ceq $name
    },$true))
    if ($assignments.Count -ne 1) { throw 'Expected one production input builder' }
    $build=[scriptblock]::Create($assignments[0].Extent.Text+'; '+$name)
    $StartupCrewOverboard=$false; $ProfileCrewOverboard=$false; $ProfileHighSide=$false
    if ((& $build) -cne '') { throw 'Default must not inject a swimmer' }
    $StartupCrewOverboard=$true; $ProfileCrewOverboard=$true
    $expected=if($name -ceq '$overboardOption'){' overboard'}else{'RaftSim.ProfileCrewOverboard,'}
    if ((& $build) -cne $expected) { throw 'Explicit drill must use the input-only command' }
}
'PASS: eight pre-process guards, unchanged default and explicit motion/cost overboard inputs'
