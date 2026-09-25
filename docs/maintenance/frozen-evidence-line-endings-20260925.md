# Frozen South Fork text evidence: exact-byte recovery

Three historical artifacts failed byte hashes solely due to CRLF instead of LF.
Two C++ files had checkout conversion; the JSON manifest contained CRLF in its
LFS object itself. Converting only CRLF to LF reproduced the existing review
hash exactly before each write. No expected digest, content, assertion or review
acceptance flag changed:

- RaftSimEditorSouthForkMaterial.cpp: 165 CRLF sequences; recovered SHA256
  6f4c8fd7542b63fd43473e9e8d7c4a4ea3fa69d4baf006d9523f8805b76603bd.
- RaftSimEditorSouthForkOrganicTerrainTest.cpp: 124 CRLF sequences; recovered
  5ac7ef38b7b59a7720cfb5dd4852b272c8c004e754f4399c55ab9eeb7fe1fd4c.
- landscape_candidate_manifest_american_south_fork.json: 220 CRLF sequences;
  recovered 4d319cef8f1f632b13a55570d1e789512a4ccd54f2a7abc8725a3e231f7f7d1a.

Exact-path Git attributes now pin text/eol=lf for the two C++ files. The manifest
retains LFS/-text ownership with the recovered original LF object committed.
No global newline
policy or binary/source-data transformation was applied. Tests hash raw bytes,
not normalized content, and check the effective Git checkout policy. All three
new checks pass. The combined South Fork organic-terrain suite is7passed/1failed
(`tmp/south-fork-frozen-line-endings-20260925.xml`). Its existing immutable gate
now proceeds past the first recovered artifact and still rejects the materially
changed MaterialsBase.cpp. Other changed historical source, assets and captures
remain unreconciled; no blanket normalization/release acceptance is claimed.

This restores reproducibility, not river geometry, rendering, physics or normal
play. No build, cook, staged executable replacement or GitHub push occurred.
Physical game input validation separately awaits computer-use app approval;
its timed-out launch was not retried or bypassed.
