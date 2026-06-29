# South Fork GeoClaw AMR 2-3 References

This directory stores normalized GeoClaw reference fixtures for the South Fork
American Chili Bar to Coloma validation matrix.

The fixtures are generated from the shared 2.5D South Fork scenario family with:

- AMR min level: 2
- AMR max level: 3
- Fixed-grid output frames: 5
- Grid: 72 x 32
- Duration: 8 seconds

Only normalized comparison artifacts belong here. Full GeoClaw app directories,
compiled executables, raw `_output` files, and local C++ comparison outputs should
stay under ignored `outputs/` directories.

See `fixture_registry.json` for the flow-band inventory, validation stats, and
reproduction commands.
