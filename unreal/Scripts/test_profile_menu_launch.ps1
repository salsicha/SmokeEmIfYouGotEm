$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'profile_south_fork_current_map.ps1'
$tokens = $null
$errors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($source, [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
foreach ($name in @('Get-RaftSimLaunchPrefix', 'Get-RaftSimPostTravelCsvLeaf')) {
    $functions = @($ast.FindAll({ param($node)
        $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $name
    }, $true))
    if ($functions.Count -ne 1) { throw "Expected one production function: $name" }
    . ([scriptblock]::Create($functions[0].Extent.Text))
}
$prefix = @(Get-RaftSimLaunchPrefix 'test.uproject' $true)
if ($prefix.Count -ne 1 -or $prefix[0] -ne 'test.uproject') { throw 'Menu launch must use project default map' }
$prefix = @(Get-RaftSimLaunchPrefix 'test.uproject' $false)
if ($prefix.Count -ne 2 -or $prefix[1] -ne '/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach') { throw 'Direct-map mode changed' }
$lines = @(
    'LogLoad: LoadMap: /Game/RaftSim/Maps/L_RaftSimBoot?Name=Player',
    'LogTemp: Display: RaftSim.MenuScreen: showing main (7 run buttons)',
    'LogLoad: LoadMap: /Game/RaftSim/Maps/L_SouthForkAmerican_FullReach',
    'LogTemp: Display: RaftSim post-travel CSV event: world=/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach.L_SouthForkAmerican_FullReach world_s=5.028',
    'LogTemp: Display: RaftSim post-travel CSV capture: frames=1200',
    'LogCsvProfiler: Display: Capture Ended. Writing CSV to file : ../../Saved/Profiling/CSV/Profile(20260926_010000).csv'
)
$valid = $lines -join "`r`n"
if ((Get-RaftSimPostTravelCsvLeaf $valid 1200) -ne 'Profile(20260926_010000).csv') { throw 'Ordered travel receipt rejected' }
$invalid = @(
    ($lines[1..5] -join "`r`n"),
    ($valid + "`r`n" + $lines[0]),
    (($lines[1], $lines[0], $lines[2], $lines[3], $lines[4], $lines[5]) -join "`r`n"),
    $valid.Replace('frames=1200', 'frames=300'),
    $valid.Replace('Profile(20260926_010000)', 'bad name'),
    $valid.Replace('world=/Game/RaftSim/Maps/L_SouthForkAmerican_FullReach.', 'world=/Game/RaftSim/Maps/L_RaftSimBoot.')
)
foreach ($log in $invalid) {
    $rejected = $false
    try { $null = Get-RaftSimPostTravelCsvLeaf $log 1200 } catch { $rejected = $true }
    if (-not $rejected) { throw 'Invalid travel receipt accepted' }
}
foreach ($conflict in @(
    @{StartupRenderReplay=$true}, @{NativePerformanceGate=$true}, @{DetailStreamingReplay=$true},
    @{CheckpointResetReplay=$true}, @{ProfileHighSide=$true}, @{ProfileCrewOverboard=$true},
    @{ReviewStationM=0}, @{SolverLanes=4}, @{ExtraGameArgument='-test'}, @{ExtraGameArguments=@('-test')}
)) {
    $rejected = $false
    try { & $source -Label south-fork-menu-test -NormalMenuLaunch -NoCookWorkload @conflict }
    catch {
        if ($_.Exception.Message -ne 'NormalMenuLaunch requires an ordinary unmodified post-travel CSV run') { throw }
        $rejected = $true
    }
    if (-not $rejected) { throw 'Conflicting menu mode accepted' }
}
'PASS: menu launch prefix, ordered post-travel receipts, invalid receipts and conflicting modes'
