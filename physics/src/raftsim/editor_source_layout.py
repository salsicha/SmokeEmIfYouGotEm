from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


EDITOR_PRIVATE_RELATIVE_PATH = Path("unreal/Plugins/RaftSim/Source/RaftSimEditor/Private")
EDITOR_PUBLIC_RELATIVE_PATH = Path("unreal/Plugins/RaftSim/Source/RaftSimEditor/Public")

RIVER_BUILD_TARGETS = (
    ("american_south_fork", "L_SouthForkAmerican_PhysicalCorridorCandidate"),
    ("colorado_river", "L_ColoradoGrandCanyon_PhysicalCorridorCandidate"),
    ("pacuare", "L_Pacuare_SourceLandscapeCandidate"),
    ("zambezi_batoka_gorge", "L_ZambeziBatokaGorge_PhysicalCorridorCandidate"),
    ("futaleufu_terminator", "L_FutaleufuTerminator_PhysicalCorridorCandidate"),
    ("chilko_river_lava_canyon", "L_ChilkoRiver_PhysicalCorridorCandidate"),
)


@dataclass(frozen=True)
class EditorImplementationSourceSet:
    repo_root: Path

    def read_text(self, encoding: str = "utf-8") -> str:
        if encoding.lower().replace("_", "-") != "utf-8":
            raise ValueError("RaftSim editor source aggregation supports UTF-8 only")
        return read_raftsim_editor_source(self.repo_root)


def editor_implementation_paths(repo_root: Path) -> list[Path]:
    private_root = repo_root / EDITOR_PRIVATE_RELATIVE_PATH
    return sorted(private_root.rglob("*.cpp"), key=lambda path: path.relative_to(private_root).as_posix())


def read_raftsim_editor_source(repo_root: Path) -> str:
    chunks = []
    for path in editor_implementation_paths(repo_root):
        relative = path.relative_to(repo_root).as_posix()
        chunks.append(f"\n// RAFTSIM_EDITOR_SOURCE_FILE: {relative}\n")
        chunks.append(path.read_text(encoding="utf-8"))
    return "".join(chunks)


def _registered_console_commands(source: str) -> list[dict[str, str | None]]:
    assignment_pattern = re.compile(
        r"(?P<member>[A-Za-z0-9_]+)\s*=\s*MakeUnique<FAutoConsoleCommand>\s*\(\s*"
        r'TEXT\("(?P<command>RaftSim\.[^"]+)"\)',
        re.MULTILINE,
    )
    matches = list(assignment_pattern.finditer(source))
    commands = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else min(len(source), match.end() + 1400)
        block = source[match.start() : end]
        handler_match = re.search(r"&FRaftSimEditorModule::(?P<handler>[A-Za-z0-9_]+)", block)
        commands.append(
            {
                "command": match.group("command"),
                "member": match.group("member"),
                "handler": handler_match.group("handler") if handler_match else None,
            }
        )
    return commands


def _startup_flags(source: str) -> list[str]:
    return sorted(
        set(
            re.findall(
                r'FParse::Param\s*\([^;]+?TEXT\("(RaftSim[A-Za-z0-9_]+)"\)',
                source,
                flags=re.DOTALL,
            )
        )
    )


def build_editor_source_inventory(repo_root: Path) -> dict[str, Any]:
    paths = editor_implementation_paths(repo_root)
    source = read_raftsim_editor_source(repo_root)
    commands = _registered_console_commands(source)
    river_targets = [
        {
            "river_id": river_id,
            "map_package_token": map_token,
            "river_id_present": f'TEXT("{river_id}")' in source,
            "map_package_present": map_token in source,
        }
        for river_id, map_token in RIVER_BUILD_TARGETS
    ]
    return {
        "schema": "raftsim.editor.source_inventory.v1",
        "implementation_files": [
            {
                "path": path.relative_to(repo_root).as_posix(),
                "line_count": len(path.read_text(encoding="utf-8").splitlines()),
            }
            for path in paths
        ],
        "implementation_file_count": len(paths),
        "implementation_line_count": sum(
            len(path.read_text(encoding="utf-8").splitlines()) for path in paths
        ),
        "registered_console_command_count": len(commands),
        "registered_console_commands": commands,
        "startup_flags": _startup_flags(source),
        "river_build_targets": river_targets,
        "all_river_build_targets_present": all(
            target["river_id_present"] and target["map_package_present"] for target in river_targets
        ),
    }


def render_editor_source_inventory_markdown(inventory: dict[str, Any]) -> str:
    lines = [
        "# RaftSim Editor Source Inventory",
        "",
        f"Implementation files: **{inventory['implementation_file_count']}**. ",
        f"Implementation lines: **{inventory['implementation_line_count']}**. ",
        f"Registered console commands: **{inventory['registered_console_command_count']}**.",
        "",
        "## Source Files",
        "",
        "| File | Lines |",
        "| --- | ---: |",
    ]
    for source_file in inventory["implementation_files"]:
        lines.append(f"| `{source_file['path']}` | {source_file['line_count']} |")
    lines.extend(
        [
            "",
            "## Registered Commands",
            "",
            "| Command | Owning member | Handler |",
            "| --- | --- | --- |",
        ]
    )
    for command in inventory["registered_console_commands"]:
        lines.append(
            f"| `{command['command']}` | `{command['member']}` | "
            f"`{command['handler'] or 'lambda'}` |"
        )
    lines.extend(
        [
            "",
            "## River Build Paths",
            "",
            "| River id | Candidate map | Present |",
            "| --- | --- | --- |",
        ]
    )
    for target in inventory["river_build_targets"]:
        present = target["river_id_present"] and target["map_package_present"]
        lines.append(
            f"| `{target['river_id']}` | `{target['map_package_token']}` | "
            f"{'yes' if present else 'no'} |"
        )
    lines.extend(
        [
            "",
            "## Startup Flags",
            "",
            *[f"- `{flag}`" for flag in inventory["startup_flags"]],
            "",
        ]
    )
    return "\n".join(lines)
