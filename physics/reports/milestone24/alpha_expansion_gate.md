# Milestone 24 Alpha Expansion Gate

Decision: `PASS_GATE_CONTRACT_AND_BLOCK_UNVALIDATED_ALPHA_PROMOTION`

The source-controlled alpha expansion gate is now in place at `unreal/Content/RaftSim/Automation/alpha_expansion_gate.json`.

The gate requires four lanes before any playable alpha expansion can be promoted:

- Automated content validation.
- Physics regression replay.
- River-source provenance checks.
- Playable end-to-end river-section runs.

This report passes the gate contract only. It does not unlock alpha promotion yet.

South Fork is the first candidate once the gate lanes pass. Colorado and Pacuare remain planning-only until their placeholder source, hydrology, guide-review, geospatial, protected-area, and field-media blockers are replaced with reviewed evidence.
