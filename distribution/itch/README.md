# itch.io release lane

The release workflow supplies one immutable zip per platform plus `SHA256SUMS` and the
matching release manifest. Publishing requires the account-owned `butler` CLI and an
explicit target such as `owner/raftsim:macos-rc` or `owner/raftsim:windows-rc`.

Use `publish.sh <artifact.zip> <target>`. The script verifies the artifact against the
adjacent checksum file before invoking butler. A draft RC channel must pass fresh-machine
QA before it can be promoted; public channel names and credentials are never committed.
