from pathlib import Path

import pytest

from raftsim.editor_source_layout import (
    EDITOR_PRIVATE_RELATIVE_PATH,
    LANDSCAPE_FOLIAGE_MEMBERS,
    LandscapeFoliageSourceSet,
    read_landscape_foliage_source,
)


def populate(root):
    directory = root / EDITOR_PRIVATE_RELATIVE_PATH / 'Landscape'
    directory.mkdir(parents=True)
    for name in LANDSCAPE_FOLIAGE_MEMBERS:
        (directory / name).write_text('sentinel:'+name, encoding='utf-8')
    (directory / 'Unrelated.cpp').write_text('not a biome member', encoding='utf-8')
    return directory


def test_exact_members_only_in_explicit_order(tmp_path):
    populate(tmp_path)
    expected = '\n'.join('sentinel:'+name for name in LANDSCAPE_FOLIAGE_MEMBERS)
    assert read_landscape_foliage_source(tmp_path) == expected
    assert LandscapeFoliageSourceSet(tmp_path).read_text(encoding='UTF_8') == expected
    assert 'not a biome member' not in expected


@pytest.mark.parametrize('missing', LANDSCAPE_FOLIAGE_MEMBERS)
def test_missing_member_cannot_silently_pass(tmp_path, missing):
    directory = populate(tmp_path)
    (directory / missing).unlink()
    with pytest.raises(FileNotFoundError):
        read_landscape_foliage_source(tmp_path)


def test_reader_rejects_other_encodings(tmp_path):
    with pytest.raises(ValueError, match='UTF-8'):
        LandscapeFoliageSourceSet(tmp_path).read_text(encoding='latin-1')


def test_every_implementation_and_private_header_meets_original_limit():
    root = Path(__file__).resolve().parents[2]
    for name in LANDSCAPE_FOLIAGE_MEMBERS:
        source = root / EDITOR_PRIVATE_RELATIVE_PATH / 'Landscape' / name
        assert len(source.read_text(encoding='utf-8').splitlines()) <= 3000


def test_placement_order_and_callback_type_contracts_remain_explicit():
    root = Path(__file__).resolve().parents[2]
    path = root / EDITOR_PRIVATE_RELATIVE_PATH / 'Landscape' / 'RaftSimEditorLandscapeFoliagePlacement.cpp'
    source = path.read_text(encoding='utf-8')
    assert source.index('AddPacuarePlacements(Context, Queries)') < source.index('AddZambeziLaunchPlacements(Context, Queries)')
    assert source.index('AddZambeziLaunchPlacements(Context, Queries)') < source.index('const int32 ExpectedFoliageInstanceCount')
    assert source.count('static_assert(std::is_same_v<decltype(') == 6
