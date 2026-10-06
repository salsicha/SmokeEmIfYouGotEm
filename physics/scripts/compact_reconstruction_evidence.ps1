# Transparent NTFS compression of one explicitly scoped, terminal diagnostic.
# No data files are deleted, renamed, rewritten or moved.
param(
    [string]$DiagnosticDirectory = 'south-fork-bank-spike-20260907',
    [string]$ReportName = 'south-fork-evidence-compression-20260912.json'
)
$ErrorActionPreference = 'Stop'
$compressionRoot = 'C:\Users\salsi\repos\SmokeEmIfYouGotEm'
if ($DiagnosticDirectory -notmatch '^[a-z0-9-]+$' -or $ReportName -notmatch '^[a-z0-9-]+\.json$') {
    throw 'Expected a literal diagnostic directory and JSON report basename'
}
$compressionTarget = [IO.Path]::GetFullPath((Join-Path $compressionRoot ('tmp\' + $DiagnosticDirectory)))
if (-not $compressionTarget.StartsWith($compressionRoot + '\tmp\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Compression target escaped generated scratch scope'
}
$compressionReport = Join-Path $compressionRoot ('tmp\' + $ReportName)
if (Test-Path -LiteralPath $compressionReport) { throw 'Existing evidence report must be preserved' }
$freeBefore = (Get-PSDrive C).Free
$compressionFiles = @(Get-ChildItem -LiteralPath $compressionTarget -Recurse -File | Sort-Object FullName)
$before = @{}
foreach ($item in $compressionFiles) {
    $before[$item.FullName] = @{ bytes=$item.Length; sha256=(Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash }
}
Write-Output "Verified original hashes for $($compressionFiles.Count) diagnostic files"
& compact.exe /C "/S:$compressionTarget" /A /Q
if ($LASTEXITCODE -ne 0) { throw "NTFS compression returned $LASTEXITCODE; inspect before resuming" }
$afterFiles = @(Get-ChildItem -LiteralPath $compressionTarget -Recurse -File | Sort-Object FullName)
if ($afterFiles.Count -ne $compressionFiles.Count) { throw 'File inventory changed during compression' }
foreach ($item in $afterFiles) {
    if (-not $before.ContainsKey($item.FullName) -or $before[$item.FullName].bytes -ne $item.Length -or
        $before[$item.FullName].sha256 -ne (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash) {
        throw "Diagnostic contents changed: $($item.FullName)"
    }
}
$report = [ordered]@{
    target=$compressionTarget
    method='Transparent NTFS filesystem compression; paths and logical bytes unchanged'
    file_count=$afterFiles.Count
    all_sha256_unchanged=$true
    files_deleted=0
    free_bytes_before=$freeBefore
    free_bytes_after=(Get-PSDrive C).Free
    source_files=$before
}
[IO.File]::WriteAllText($compressionReport, ($report | ConvertTo-Json -Depth 5))
[pscustomobject]$report | Select-Object target,file_count,all_sha256_unchanged,files_deleted,free_bytes_before,free_bytes_after | ConvertTo-Json -Compress
