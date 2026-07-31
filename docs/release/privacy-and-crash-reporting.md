# Privacy and crash reporting

RaftSim 1.0 is offline-first. It does not require an account, does not upload gameplay
telemetry, and does not enable microphone or speech recognition in the flat-screen 1.0
scope. Keyboard and gamepad commands provide complete control parity.

Unreal may write local logs, configuration, save games, screenshots requested by the
player, and crash diagnostics under the operating system's per-user application-data
directory. The project does not automatically transmit those files. A player may attach
them voluntarily to a support report after reviewing them for personal information.

Distribution services such as GitHub, itch.io, or Steam apply their own account,
download, and crash-reporting policies outside the game process. Store listings must link
their current policies and must not claim that RaftSim collects data it does not collect.

Release QA retains only build version, platform, hardware description, frame timing,
memory, solver timing, deterministic hashes, and pass/fail results. Human names, account
identifiers, voice recordings, and precise player location are not part of RC reports.
