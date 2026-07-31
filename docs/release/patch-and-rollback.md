# Patch, rollback, and save compatibility

Release builds use semantic versions. The `release/1.0` branch accepts only verified
release fixes; feature work returns to `main`. Hotfix branches use
`release/1.0-hotfix/<issue>` and merge back into both branches after validation.

## Patch procedure

1. Reproduce the defect and add the narrowest automated regression that proves it.
2. Implement the fix without changing scoring-critical physics unless the full hydraulic,
   raft/contact, replay, and packaged matrix gates are rerun.
3. Increment the patch or RC suffix in `DefaultGame.ini` and `CHANGELOG.md`.
4. Build both platform packages from the same commit.
5. Rerun packaged QA, fresh-profile startup, save migration, checksums, signature checks,
   and platform performance lanes.
6. Publish immutable archives and manifests; never replace an artifact under an existing
   version label.

## Save policy

The current save schema is version 3. Migration is additive: legacy completion, scores,
settings, and bindings are normalized into the current schema. Patch builds must never
downgrade or silently discard a newer save. Before installing an RC, copy the platform's
`Saved/SaveGames` directory. A rollback may read the same schema but must not write if its
code does not understand a higher `SaveVersion`.

## Recovery

If startup fails after a patch, preserve the crash log and save directory, launch with a
fresh OS user/profile to separate install failure from user data, then restore the prior
immutable archive whose checksum appears in its release manifest. Do not delete the only
copy of a failing save; it is required for a migration regression fixture.
