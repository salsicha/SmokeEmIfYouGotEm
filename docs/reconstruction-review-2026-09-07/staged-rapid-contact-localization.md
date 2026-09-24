# Staged rapid contact localization — September 24

Supporting diagnosis only, not new playable reconstruction or acceptance.
The previous staged motion review localized a near-stall beside a large rock.
This follow-through identifies the actual sampled collision source without
altering source geometry, contact response, water, or solver modes.

The existing read-only `RaftSimGroundContactAudit` observer records39 vertical
corrections; engine exit0. Every observation belongs to
`SourceMatched20260917/SM_SourceMatchedGround`, original actor
`StaticMeshActor_UAID_04421A89ABE5ED0003_2136936984`. Every resampled height
matches the solver float. The observer records only corrections >=5mm, at
most64; these39 are not a complete contact ledger. The run did not fill that
cap. Maximum recorded correction1.268496cm; their sum31.715146cm is accumulated
correction, NOT net raft rise or measured energy gain.

Independent XY/barycentric lookup against the hash-verified archived mesh
locates all39 on triangles whose THREE vertex authority values are5 (inferred
flank). This was not inferred from native face numbers: source triangles were
selected by containing XY and independently checked against height and upward
world normal. Maximum height error0.0000639804cm; maximum normal vector
difference6.04091e-7. All39 recovered source face IDs also match the recorded
native IDs. No missing lookup or mixed-authority face.

Near the observed turn,11 corrections at9.71–11.41s occur on source face599292,
source-local east2.926..3.021m/north2.332..2.513m. Subsequent faces198090 and
600011 also have entirely inferred-flank vertices. This directs follow-up
toward inferred-flank/contact-response qualification, NOT deleting a captured
cap or repairing a mismatched collision asset. It does not prove that all
forces causing the turn are ground contact, that the inferred flank is
geographically wrong, or that experimental contact paths are safe to promote.

Evidence:

- `tmp/audit-staged-troublemaker-contact-20260924.py` and matching `.log`.
- `tmp/staged-troublemaker-contact-20260924.json`, SHA256
  `221b79e1c188116690849d8d30b1df074e139032dd25929abee9111d8a660f6e`.
- `tmp/localize-staged-contact-20260924.py` and
  `tmp/staged-troublemaker-contact-localized-20260924.json`.
- Original mesh SHA256:
  `8edf8a7fbfb675a22ac6736db600a3300f018f1c9037b1c0674bc1c376cfcca7`.
- Staged executable SHA256:
  `6194fed46b8dbf4a37c9948112cdc54052ed96dbc792ded7bfc1f8cc3bc04ddd`.

Both owned processes are terminal0. No continuous/full-hull contact override
was supplied; normal performance remains unaccepted. South Fork remains first
unfinished; Colorado, Pacuare and Futaleufu stay queued. Do not repeat this
identity lookup absent changed evidence. A documentation append to the previous
review was denied by filesystem permissions; this separate record preserves
the result without changing those permissions.
