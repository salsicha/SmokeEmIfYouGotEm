#pragma once

// Python is an editor authoring facility, not a gameplay dependency. In an
// editor-hosted -game process, mounted editor content still contains Python
// startup scripts while Editor module classes are intentionally unavailable.
// Keep editor/PIE, commandlets and packaged builds outside this policy.
namespace RaftSimPythonStartupPolicy
{
constexpr bool DisableDefault(const bool EditorBuild, const bool RunningGame, const bool Commandlet)
{
    return EditorBuild && RunningGame && !Commandlet;
}
}
