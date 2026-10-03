# Parser-only adversarial frame fixtures, not native FPS evidence.
$ErrorActionPreference='Stop'
foreach($pair in @(
    @('profile_reference_map_ps5.ps1','passes_20fps_goal'),
    @('profile_south_fork_menu_launch_ps5.ps1','healthy_timing_passes')
)){
    $tokens=$null;$errors=$null
    $ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot $pair[0]),[ref]$tokens,[ref]$errors)
    if($errors.Count){throw 'Profiler AST invalid'}
    $expressions=@($ast.FindAll({param($node)
        $node -is [Management.Automation.Language.HashtableAst]
    },$true) | ForEach-Object {
        foreach($entry in $_.KeyValuePairs){if($entry.Item1.Extent.Text -eq $pair[1]){$entry.Item2.Extent.Text}}
    })
    if($expressions.Count -ne 1){throw 'Expected exactly one timing gate'}
    $gate=[scriptblock]::Create($expressions[0])
    $runtimeErrors=@();$p95=40.0
    $window=@(40.0)*240
    if(-not (& $gate)){throw 'Finite under-budget fixture must pass'}
    $window[120]=50.001
    if(& $gate){throw 'One slow frame cannot pass via p95 or a 100ms hitch threshold'}
    $window[120]=50.0
    if(-not (& $gate)){throw 'Exact 20 FPS budget should pass'}
    $runtimeErrors=@('LogTemp: Error: fixture')
    if(& $gate){throw 'Engine error cannot pass a fast timing fixture'}
}
'PASS: both production profiling gates reject one frame below 20 FPS and runtime errors'
