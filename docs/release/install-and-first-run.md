# Install and first run

RaftSim 1.0 targets flat-screen single-player play on macOS Apple Silicon and Windows
x64. Release archives include the game, cooked Unreal content, and the complete staged
runtime-data tree used by the live water solver. No separate content download is needed.

## macOS Apple Silicon

1. Verify the archive against `SHA256SUMS` with `shasum -a 256 -c SHA256SUMS`.
2. Expand `RaftSim-1.0.0-rc1-macos-arm64.zip` into an Applications or Games folder.
3. Open `SmokeEmIfYouGotEm.app`.
4. During development-signed RC testing, macOS may require Control-click → Open. A public
   1.0 package must instead carry a Developer ID signature and notarization ticket.

## Windows x64

1. Verify the archive with `Get-FileHash -Algorithm SHA256` and compare it with
   `SHA256SUMS`.
2. Extract `RaftSim-1.0.0-rc1-windows-x64.zip` to a writable Games folder.
3. Run `SmokeEmIfYouGotEm.exe`.
4. The public build must show a valid Authenticode signature. Do not bypass a SmartScreen
   warning for an unsigned or mismatched artifact.

## First-run checks

- The main menu must appear without an editor, repository checkout, or network access.
- Select Training Eddy, paddle once, issue ALL FORWARD and STOP, and return to the menu.
- Change one display/accessibility setting, quit normally, reopen, and confirm it persists.
- Start a South Fork Free Run and confirm water, crew, controls, HUD, and audio initialize.

Save data is stored in the normal Unreal per-user application-data location. Removing the
game does not remove saves; follow [patch and rollback](patch-and-rollback.md) before
manually deleting them.
