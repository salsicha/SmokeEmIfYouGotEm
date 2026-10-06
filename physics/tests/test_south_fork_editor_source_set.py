from pathlib import Path

import pytest

from raftsim.editor_source_layout import (
    EDITOR_PRIVATE_RELATIVE_PATH,
    read_south_fork_full_reach_source,
)


MEMBERS = (
    "RaftSimEditorSouthForkFullReach.cpp",
    "RaftSimEditorSouthForkFullReachInternal.h",
    "RaftSimEditorSouthForkFullReachHelpers.cpp",
    "RaftSimEditorSouthForkSupportExport.cpp",
)


def make_sources(root):
    folder = root / EDITOR_PRIVATE_RELATIVE_PATH / "Environment"
    folder.mkdir(parents=True)
    for index, name in enumerate(MEMBERS):
        (folder / name).write_text(f"member_{index}", encoding="utf-8")
    (folder / "AnotherRiver.cpp").write_text("unrelated", encoding="utf-8")
    return folder


def test_full_reach_source_reader_includes_each_explicit_member_only(tmp_path):
    make_sources(tmp_path)
    assert read_south_fork_full_reach_source(tmp_path) == "\n".join(
        f"member_{index}" for index in range(len(MEMBERS))
    )


@pytest.mark.parametrize("missing", MEMBERS)
def test_full_reach_source_reader_rejects_missing_members(tmp_path, missing):
    folder = make_sources(tmp_path)
    (folder / missing).unlink()
    with pytest.raises(FileNotFoundError):
        read_south_fork_full_reach_source(tmp_path)


def test_split_full_reach_implementations_and_header_are_bounded():
    root = Path(__file__).resolve().parents[2]
    folder = root / EDITOR_PRIVATE_RELATIVE_PATH / "Environment"
    for name in MEMBERS:
        assert len((folder / name).read_text(encoding="utf-8").splitlines()) <= 3000
    main = (folder / MEMBERS[0]).read_text(encoding="utf-8")
    assert '#include "Environment/RaftSimEditorSouthForkFullReachInternal.h"' in main
    assert "BuildSouthForkFullReachEnvironment" in main
    assert "CaptureSettledSouthForkFullReachEnvironment" in main
