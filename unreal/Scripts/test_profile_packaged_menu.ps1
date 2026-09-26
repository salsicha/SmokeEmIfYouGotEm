$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'profile_south_fork_menu_launch_ps5.ps1'
$tokens = $null; $errors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($source, [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
$functions = @($ast.FindAll({ param($node)
    $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Get-RaftSimPackagedLaunchPaths'
}, $true))
if ($functions.Count -ne 1) { throw 'Expected production packaged-path helper' }
. ([scriptblock]::Create($functions[0].Extent.Text))
# Mock existence only; no files, engine launch or removal is needed.
function Test-Path { param($LiteralPath, $PathType)
    if ($script:missing -and $LiteralPath.EndsWith($script:missing)) { return $false }
    return $true
}
$script:missing = ''
$result = Get-RaftSimPackagedLaunchPaths 'C:/fixture' 'C:/fixture/tmp/stage/Windows'
if (-not $result.Binary.EndsWith('Binaries\Win64\SmokeEmIfYouGotEm.exe')) { throw 'Not the inner executable' }
if (-not $result.CsvDirectory.EndsWith('SmokeEmIfYouGotEm\Saved\Profiling\CSV')) { throw 'Not the packaged CSV directory' }
foreach ($path in @('C:/outside/stage', 'C:/fixture/tmp-other/stage', 'C:/fixture/tmp/../unreal')) {
    $rejected = $false
    try { $null = Get-RaftSimPackagedLaunchPaths 'C:/fixture' $path } catch { $rejected = $true }
    if (-not $rejected) { throw 'Out-of-scope stage accepted' }
}
foreach ($leaf in @('SmokeEmIfYouGotEm.exe', 'Paks')) {
    $script:missing = $leaf; $rejected = $false
    try { $null = Get-RaftSimPackagedLaunchPaths 'C:/fixture' 'C:/fixture/tmp/stage/Windows' } catch { $rejected = $true }
    if (-not $rejected) { throw 'Incomplete cooked stage accepted' }
}
'PASS: packaged inner executable, CSV root, scope and missing payload checks; profiler syntax'
