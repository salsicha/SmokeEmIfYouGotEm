# A finalized file is capture evidence, not decoded motion or an FPS pass.
function Get-RaftSimStartupMotionEvidence {
    param([Parameter(Mandatory=$true)][string]$LogText,
          [Parameter(Mandatory=$true)][string]$VideoRoot)
    $records = [regex]::Matches($LogText, 'RaftSim recording saved: (.+\.mp4) \((\d+) source_frames, ([\d.]+) s; encoder may repeat frames to preserve duration\)')
    if ($records.Count -ne 1) { throw 'Exactly one finalized startup recording required' }
    $record = $records[0]
    $frames = [long]::Parse($record.Groups[2].Value, [Globalization.CultureInfo]::InvariantCulture)
    $seconds = [double]::Parse($record.Groups[3].Value, [Globalization.CultureInfo]::InvariantCulture)
    if ($frames -lt 2 -or -not [double]::IsFinite($seconds) -or $seconds -le 0) { throw 'Positive duration and multiple actual source frames required' }
    $root = [IO.Path]::GetFullPath($VideoRoot).TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    $path = [IO.Path]::GetFullPath($record.Groups[1].Value)
    if (-not $path.StartsWith($root, [StringComparison]::OrdinalIgnoreCase) -or
        -not (Test-Path -LiteralPath $path -PathType Leaf) -or (Get-Item -LiteralPath $path).Length -eq 0) {
        throw 'Nonempty recording inside the project VideoCaptures directory required'
    }
    return [ordered]@{
        path=$path; sha256=(Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant()
        source_frames=$frames; duration_seconds=$seconds
        encoder_may_repeat_frames=$true; fully_decoded=$false; performance_accepted=$false; visual_accepted=$false
    }
}
