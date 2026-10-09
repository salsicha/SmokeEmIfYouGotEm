# Keeps the project folder inside its disk budget.
#
#   .\tools\cleanup\project_space.ps1            # report only
#   .\tools\cleanup\project_space.ps1 -Apply     # also prune Git LFS and archive cold tmp/ folders
#
# Budget: the project folder stays under -BudgetGB (900 GB, well inside 1 TB)
# and its drive keeps -DriveReserveGB free. Nothing is deleted outright:
# old Git LFS versions are pruned only once GitHub confirms it holds them
# (git lfs prune --verify-remote), and cold tmp/ run folders are moved,
# verified, to a compressed archive on another drive (archive_tmp_dirs.ps1),
# which can be deleted by hand when no longer wanted.
param(
    [switch]$Apply,
    [double]$BudgetGB = 900,
    [double]$DriveReserveGB = 100,
    [double]$ColdDays = 7,
    [string]$ArchiveRoot = 'C:\SmokeEmIfYouGotEm-archive\tmp'
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
function Get-TreeBytes([string]$Path) {
    $out = robocopy $Path NULL /L /S /NJH /BYTES /NFL /NDL /NC /XJ /R:0 /W:0
    [double]((($out | Select-String '^\s*Bytes\s*:' | Select-Object -First 1).ToString() -split '\s+' |
        Where-Object { $_ -match '^\d+$' } | Select-Object -First 1))
}
$total = 0.0
$parts = foreach ($item in Get-ChildItem -LiteralPath $root -Force) {
    $bytes = if ($item.PSIsContainer) { Get-TreeBytes $item.FullName } else { [double]$item.Length }
    $total += $bytes
    [pscustomobject]@{ Name = $item.Name; GB = [math]::Round($bytes / 1GB, 1) }
}
$drive = Get-PSDrive ($root.Substring(0, 1))
'Project {0:N1} GB of {1:N0} GB budget; drive {2}: {3:N1} GB free (reserve {4:N0} GB)' -f ($total / 1GB), $BudgetGB, $drive.Name, ($drive.Free / 1GB), $DriveReserveGB
$parts | Where-Object GB -ge 1 | Sort-Object GB -Descending | Format-Table -AutoSize | Out-String
$python = @(
    'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe',
    (Get-Command py.exe -ErrorAction SilentlyContinue).Source
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $python) { throw 'No Python found (Unreal Engine 5.8 ships one).' }
$cold = @(& $python (Join-Path $PSScriptRoot 'select_cold_tmp.py') --days $ColdDays --summary)
'{0} cold tmp/ folders (older than {1} days, unreferenced by current plans or scripts)' -f $cold.Count, $ColdDays
$over = ($total / 1GB -gt $BudgetGB) -or ($drive.Free / 1GB -lt $DriveReserveGB)
if ($over) { 'OVER BUDGET: run with -Apply, or archive further by hand.' }
if (-not $Apply) { return }
Push-Location $root
try { git lfs prune --verify-remote } finally { Pop-Location }
if ($cold.Count) {
    $list = Join-Path ([IO.Path]::GetTempPath()) ('cold-tmp-{0}.txt' -f (Get-Date -Format 'yyyyMMddHHmmss'))
    $cold | Set-Content -Encoding utf8 $list
    New-Item -ItemType Directory -Force $ArchiveRoot | Out-Null
    compact /c /i /q $ArchiveRoot | Out-Null
    & (Join-Path $PSScriptRoot 'archive_tmp_dirs.ps1') -ListFile $list -ArchiveRoot $ArchiveRoot
}
