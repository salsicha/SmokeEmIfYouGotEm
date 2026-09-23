$ErrorActionPreference = 'Stop'
$tokens = $null
$parseErrors = $null
$source = Join-Path $PSScriptRoot 'profile_south_fork_current_map.ps1'
$ast = [Management.Automation.Language.Parser]::ParseFile($source, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw 'Production runner must parse' }
$branches = @($ast.FindAll({
    param($node)
    $node -is [Management.Automation.Language.IfStatementAst] -and
    $node.Clauses[0].Item1.Extent.Text -ceq '$NoCookWorkload' -and
    $node.Extent.Text.Contains('NoCookWorkload cannot carry a cook identity')
}, $true))
if ($branches.Count -ne 1) { throw 'Expected one production cook identity/absence branch' }
$productionBranch = [scriptblock]::Create(@'
    param([int]$CookProcessId=0, [string]$CookStartUtc='', [switch]$NoCookWorkload,
          [string]$CookExecutable='', [switch]$FakeLiveCook)
    # Only the query is mocked. Execute the actual production guards; a valid
    # cook identity is not supplied, so no real OS handle can be obtained.
    function Get-Process { param($Name, $ErrorAction)
        if ($Name -cne 'raftsim_cartesian_cook') { throw 'Unexpected process query' }
        if ($FakeLiveCook) { [pscustomobject]@{ Id=123 } }
    }
    $owned = @()
'@ + "`n" + $branches[0].Extent.Text + "`n" + @'
    if ($owned.Count) { throw 'Absent cook must not produce an owned process' }
'@)
& $productionBranch -NoCookWorkload
foreach ($arguments in @(
    @{ NoCookWorkload=$true; CookProcessId=123 },
    @{ NoCookWorkload=$true; CookStartUtc='2026-09-23T00:00:00Z' },
    @{ NoCookWorkload=$true; CookExecutable='tmp/stale/raftsim_cartesian_cook.exe' },
    @{ NoCookWorkload=$true; FakeLiveCook=$true },
    @{}, @{ CookProcessId=123 }, @{ CookStartUtc='2026-09-23T00:00:00Z' }
)) {
    $rejected = $false
    try { & $productionBranch @arguments }
    catch {
        if ($_.Exception.Message -cnotin @('NoCookWorkload cannot carry a cook identity',
            'NoCookWorkload requires no running Cartesian cook',
            'Supply an exact live cook identity or explicit NoCookWorkload')) { throw }
        $rejected = $true
    }
    if (-not $rejected) { throw ('Ambiguous, incomplete or conflicting cook state accepted: '+($arguments | ConvertTo-Json -Compress)) }
}
'PASS: explicit no-cook mode and seven incompatible/ambiguous state rejections'
