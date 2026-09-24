# Lossless diagnostic storage recovery

2026-09-24. The early breaking-gate gameplay comparison hit Zen HTTP507 with
about1.16GB free. It was cancelled, not accepted. No competing cook or game was
live when recovery began.

Applied Windows NTFS compression only to183 generated `.npy` files under the
resolved exact directory:
tmp/control-ablation-15000to18000s-workers8-v1-20260923.
This is a terminal hydraulic diagnostic, not installed runtime data or captured
source evidence. Each file's SHA256 was calculated immediately before and
after compression; all183matched. Logical bytes remain7,879,857,024.
Deleted files:0. Filenames and readable content remain unchanged.

C: free bytes before1,158,606,848; after5,973,544,960. Other system activity may
also affect available space, so this is an observed free-space change rather
than a sum of allocated-file sizes. Script:
tmp/compress-terminal-diagnostic-arrays-20260924.ps1, terminal exit0.
Compression is reversible with NTFS decompression when enough space exists.

Installed UE BaseEngine.ini configures Zen's low-disk threshold at2,147,483,648
bytes. The fresh benchmark retry checks at least3GiB before each run and
refuses further comparison if its log contains Insufficient Storage. The
original failed log is preserved. No geometry, physics, water quality or
acceptance thresholds changed; this recovery is not a playable improvement.
