# Steam release lane

Steam account IDs, app IDs, depot IDs, and credentials are external release authority.
The tracked VDF files are templates and cannot upload until the owner supplies those IDs
through a private build workspace.

1. Replace `__STEAM_APP_ID__`, `__STEAM_DEPOT_ID__`, `__CONTENT_ROOT__`, and
   `__BUILD_OUTPUT__` in copies of the templates outside Git.
2. Place the verified Windows or macOS RC package under the content root.
3. Run SteamCMD with the account-owned build command.
4. Keep the build on an internal `rc` branch until the matching manifest, checksum,
   fresh-machine QA, platform QA, and M10 acceptance pass.

Never commit Steam credentials or promote a build whose executable signature, archive
hash, or packaged QA report differs from the release manifest.
