# Exact normal candidates: not promoted

Two native candidates were tested against actual South Fork mesh copies.
Neither establishes a performance improvement suitable for default delivery.
Both have been removed from production source; the original normal code and
class layout are restored. Candidate source/tests, DLLs and logs remain in
ignored `tmp/active-crest-normals-v2-20260916` and the v1 directory.

V1 builds compact lists of affected vertices and required faces, retaining
coarse neighbouring-face contributions. It matches every vertex attribute in
80 actual mesh pairs, but all80 require incidence rebuilds. Median candidate /
original timing ratios are1.09330 and1.13587 in the two alternating call orders:
slower, despite fewer face-normal evaluations. Do not promote this algorithm.

V2 uses the original full incidence ordering and a single parallel phase over
affected vertices. Each vertex recomputes its incident cross products rather
than waiting for a separate all-face phase. Its native regression passes
47,068 three-way vertex comparisons over28 changing meshes against both the
original serial and current parallel implementations, with no tolerance.
Coverage includes changing heights, reversed winding, repeated/degenerate
corners, dry/rewet, resets, source-prefix changes and invalid-input rejection.
A coarse-neighbour test separately proves its contribution is retained.

The actual V2 game comparison also completes80 exact pairs, with79 incidence
rebuilds. But timings depend on order:

| Candidate order | Original median ms | Candidate median ms | Median paired ratio | Candidate wins |
| --- | ---: | ---: | ---: | ---: |
| Second | 1.827350 | 1.727849 | 0.933182 | 29/40 |
| First | 1.867650 | 1.931949 | 1.017172 | 15/40 |

This is not enough evidence to replace the current path. The package and
full-domain solver were concurrently active; neither timing run measures
uncontended frame rate. Tests use copies of actual submitted positions,
indices and attributes, with the exact clipped-source prefix, before buffer
reserve. They do NOT replace displayed meshes, run the production call site,
advance physics or capture the pre-normal input at that call site. Synthetic
native tests cover unprocessed inputs separately. No30FPS acceptance follows.

## Evidence

- Native v1 session73967 exit0; actual v1 session44129 exit0.
- Native v2 and actual v2 run sequentially in session40353, exit0.
- V1 DLL SHA256 `ef236c2d6ef5f0facdba0a7144a6fc396fac6cab7ec1eec92b849001bf05c3f8`.
- V2 DLL SHA256 `fcd5caec0dbffa773932c1bcac5e89c99002666495a68d71f3dd279403609625`.
- V1 `play-pairs-v1.log` SHA256
  `7d5f5f10779eec5f660ae783491b3cd4713f4821980e195bf50edd2b671ade12`.
- V2 `play-pairs-v2.log` SHA256
  `036f354a7f406624c057e2f49ff915d4333731094ce4d91483bde22a01508cb7`.
- V2 `native-tests/index.json` SHA256
  `9e060156d83ea4f791f46b8e18312d9052a9d4beea6f45139da980ba8183198c`.
- Archived V2 header SHA256
  `d807829369c9ad1cff5a0e97449e36964caee1b7107e0864939095f1009b1a22`;
  test SHA256 `4687ce6d3b42d115270b4e2185dc9359063acb2a86fb161f6ecc382e5ef36272`.

The first isolated module link failed because the old project DLL did not
export a new inspection accessor. Explicitly inlining that accessor fixed the
isolated link; no project binary was replaced. Initial source-write failures
were transient; a nonmutating write-handle check and subsequent patch succeeded.
The inspection accessor was removed with the candidate after testing.

All22 original project binaries/manifests match their pre-test hashes. The464
protected scene/source identities still comprise462 unchanged files plus the
two previously verified CPU-retention-only revisions, with no mismatches.
No saved map, material, geometry, scenario, profile or physics change was made.
Keep the source/model work and normal-play delivery requirements open; see the
[matched bed playback](equal-age-bed-playback.md) for the useful visual result.
