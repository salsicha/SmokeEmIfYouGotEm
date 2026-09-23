from pathlib import Path

import pytest

from raftsim.editor_source_layout import (
    EDITOR_PRIVATE_RELATIVE_PATH,
    PHOTOREAL_MATERIAL_MEMBERS,
    BASE_MATERIAL_MEMBERS,
    read_base_material_source,
    read_photoreal_material_source,
)


SOURCE_SETS = (
    (PHOTOREAL_MATERIAL_MEMBERS, read_photoreal_material_source),
    (BASE_MATERIAL_MEMBERS, read_base_material_source),
)


def populate(root: Path, members):
    folder = root / EDITOR_PRIVATE_RELATIVE_PATH / "Materials"
    folder.mkdir(parents=True)
    for member in members:
        (folder / member).write_text("sentinel:" + member, encoding="utf-8")
    return folder


@pytest.mark.parametrize("members,reader", SOURCE_SETS)
def test_material_source_set_is_explicit_and_ordered(tmp_path, members, reader):
    folder = populate(tmp_path, members)
    (folder / "UnrelatedWater.cpp").write_text("unrelated", encoding="utf-8")
    assert reader(tmp_path) == "\n".join(
        "sentinel:" + member for member in members
    )


@pytest.mark.parametrize("members,reader,missing", [
    (members, reader, missing) for members, reader in SOURCE_SETS for missing in members
])
def test_missing_material_member_is_not_hidden_by_another_source(tmp_path, members, reader, missing):
    folder = populate(tmp_path, members)
    (folder / missing).unlink()
    (folder / "UnrelatedWater.cpp").write_text("sentinel:" + missing, encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        reader(tmp_path)
