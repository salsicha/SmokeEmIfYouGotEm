# Radial preference: partial repair, still unqualified

September28 UTC, resumed after a temporary repository write grant. Scope remains
the full reconstruction queue; South Fork is unfinished and candidate OFF.

## Applied changes

Scoped elevation applied the radial dry-witness preference in
RaftSimStoredBankContour.h and extended audit_stored_bank_contour.py to bind
15 cases, including original frame342/source23259 and414/source19466 from
shared-reserve-live-v1 (SHA9b8e68b71b25ef793b4cda668593dc82d73731475e09962c893dc5ee7188d1f3).
Native failure diagnostics now include the inner-fan orientation. No source
donors, width/sign/partition gates or normal candidate defaults were changed.

The17 Python audit controls passed. The fresh v2 recipe built successfully in
57.41s, then native qualification FAILED:19 successes/one failure, exit255.
The previous case0 failure is cleared; cases0..9 constructed complete native
contours and reached the subsequent fixture. Case10 fails before new cases13/14
or the full export. This is not15-case exact certification or scene delivery.

Receipt: tmp/certified-bank-normal-band-v2-20260928-process.json.
Native log: tmp/certified-bank-normal-band-v2-20260928-native.log.

## Remaining discontinuity

Case10 fails with both bounded and full searches at stage1:

```
P=(0.229892578125,0.000107421875)
Q=(0.23029296874999999,0.0001171875)
outer radial order lower bound=2.2020339965819607e-06
band triangle bounds=9.5570179386018489e-09,-5.9351664697067503e-07
inner fan order lower bound=-0.00022499738354968889
whole wet segment and whole dry fan signs both prove
```

Individual radial preference is insufficient: general neighbor selection now
admits candidates whose dry witness requires a nonradial direction, creating a
discontinuity with neighboring radial witnesses. Next restore radial dry-sign
qualification in the general HasSignedNeighbor search, six near-axis reserve
trials and final neighbor selection. Keep the nonradial alternative for the
whole-endcap search, and require all final geometric certificates. This proposal
is not a proved complete fix. The attempted three-line correction FAILED TO
WRITE; it did not land. No v3 recipe/build was launched.

## Coordination and current limits

The original Chilko map-import process and following P4 process were allowed
to exit before the v2 build; their files were not edited by this work. A later
check found a separate UnrealEditor process5596 and one changed frozen source:
RaftSimAutomation/Private/Tests/RaftSimTroublemakerMapTest.cpp. Its change time
relative to qualification is not established, so do not claim a globally
unchanged source qualification. South Fork target header/auditor inputs did
not change after the build. Preserve the unrelated work and avoid replacing
shared binaries while the editor is live.

The repository grant shown in the preceding user-question turn was absent from
the resumed permission profile. Scoped elevation allowed the first edits but
the subsequent header write failed. No ACL changes or bypasses were attempted.
Persistent repository write access is still needed for continued editing.

Normal v27 executable SHA remains
82e139184dbd93c46ebf7c0419e49da850db003d0aab4071ac35bba5dd65bcd0.
Protected WaterSurfaceTest.cpp remains
d9abdd3643882d192e41af879eef023ed1e58f12a39d26698e42cb0f0773e8f3.
No game package, cook, live South Fork replay, performance acceptance, source
deletion, solver activation, commit or push resulted from this attempt.
