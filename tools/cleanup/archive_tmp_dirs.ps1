# Moves project tmp/ run folders to an archive outside the project, freeing
# the project drive without destroying anything. Each folder is copied in
# full, verified by file count and bytes, and only then removed from tmp/.
# A manifest line per folder is appended to <ArchiveRoot>\archive-manifest.tsv.
param(
    [Parameter(Mandatory = $true)][string]$ListFile,
    [string]$ArchiveRoot = 'C:\SmokeEmIfYouGotEm-archive\tmp',
    [string]$ProjectTmp = (Join-Path $PSScriptRoot '..\..\tmp'),
    [double]$ArchiveDriveReserveGB = 60
)
$ErrorActionPreference = 'Stop'
$ProjectTmp = (Resolve-Path $ProjectTmp).Path
New-Item -ItemType Directory -Force $ArchiveRoot | Out-Null
$manifest = Join-Path $ArchiveRoot 'archive-manifest.tsv'
function Measure-Tree([string]$Path) {
    $out = robocopy $Path NULL /L /S /NJH /BYTES /NFL /NDL /NC /XJ /R:0 /W:0
    $num = { param($label) (($out | Select-String "^\s*${label}\s*:" | Select-Object -First 1).ToString() -split '\s+' |
        Where-Object { $_ -match '^\d+$' } | Select-Object -First 1) }
    [pscustomobject]@{ Files = [int64](& $num 'Files'); Bytes = [int64](& $num 'Bytes') }
}
foreach ($name in Get-Content $ListFile | Where-Object { $_.Trim() }) {
    $name = $name.Trim()
    if ($name -match '[\/]|\.\.') { Write-Output "skip (not a plain folder name): $name"; continue }
    $src = Join-Path $ProjectTmp $name
    if (-not (Test-Path -LiteralPath $src -PathType Container)) { Write-Output "skip (missing): $name"; continue }
    $before = Measure-Tree $src
    $free = (Get-PSDrive ($ArchiveRoot.Substring(0, 1))).Free
    if ($free - $before.Bytes -lt $ArchiveDriveReserveGB * 1GB) { Write-Output "stop: archive drive would fall below its reserve before $name"; break }
    $dst = Join-Path $ArchiveRoot $name
    robocopy $src $dst /E /COPY:DAT /DCOPY:T /R:1 /W:1 /MT:8 /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { Write-Output "FAILED copy (robocopy $LASTEXITCODE): $name"; continue }
    $after = Measure-Tree $dst
    if ($after.Files -ne $before.Files -or $after.Bytes -ne $before.Bytes) {
        Write-Output "FAILED verify: $name src=$($before.Files)/$($before.Bytes) dst=$($after.Files)/$($after.Bytes)"; continue
    }
    Remove-Item -LiteralPath $src -Recurse -Force
    "{0}`t{1}`t{2}`t{3}" -f (Get-Date -Format s), $name, $before.Files, $before.Bytes | Add-Content -Encoding utf8 $manifest
    Write-Output ("archived {0} ({1:N2} GB, {2} files)" -f $name, ($before.Bytes / 1GB), $before.Files)
}
