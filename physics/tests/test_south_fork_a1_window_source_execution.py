import hashlib
import json
import shutil
from pathlib import Path

from raftsim.south_fork_a1_window_source_execution import (
    FULL_REACH_WINDOW_SOURCE_PULL_EXECUTION_PLAN_RELATIVE_PATH,
    build_south_fork_a1_window_source_pull_execution_plan,
    execute_south_fork_a1_window_source_pulls,
)
from raftsim.south_fork_a1_window_source_pulls import (
    FULL_REACH_WINDOW_SOURCE_PULL_PLAN_RELATIVE_PATH,
)
from raftsim.south_fork_a1_window_source_status import (
    FULL_REACH_WINDOW_SOURCE_PULL_STATUS_RELATIVE_PATH,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_execution_plan() -> dict:
    return json.loads(
        (REPO_ROOT / FULL_REACH_WINDOW_SOURCE_PULL_EXECUTION_PLAN_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )


def test_south_fork_a1_window_source_execution_plan_is_reproducible():
    generated = build_south_fork_a1_window_source_pull_execution_plan(REPO_ROOT)
    committed = _load_execution_plan()

    assert generated == committed
    assert committed["schema"] == "raftsim.south_fork.a1_window_source_pull_execution_plan.v1"
    assert committed["status"] == "ready_to_execute_review_gated_source_downloads"
    assert committed["production_promoted"] is False


def test_south_fork_a1_window_source_execution_plan_covers_official_dem_and_naip_tasks():
    plan = _load_execution_plan()
    summary = plan["summary"]
    tasks = plan["tasks"]

    assert summary["task_count"] == 12
    assert summary["terrain_task_count"] == 6
    assert summary["aerial_task_count"] == 6
    assert summary["destination_missing_count"] == 12
    assert {task["role"] for task in tasks} == {"terrain_dem", "aerial_imagery"}
    assert all(task["official_export_url"].startswith("https://") for task in tasks)
    assert all(task["lfs_tracking_required"] is True for task in tasks)
    assert all(task["production_promoted"] is False for task in tasks)


def test_south_fork_a1_full_reach_window_png_sources_are_lfs_tracked():
    attributes = (REPO_ROOT / ".gitattributes").read_text(encoding="utf-8")
    plan = _load_execution_plan()

    assert "*.tif filter=lfs" in attributes
    assert "physics/data/real_world/*/production_corridor/full_reach_windows/**/*.png filter=lfs" in attributes
    assert "physics/data/real_world/*/production_corridor/full_reach_windows/**/*.png" in plan[
        "policy"
    ]["lfs_patterns_required"]


def test_south_fork_a1_window_source_executor_downloads_selected_file_and_refreshes_status(tmp_path):
    _copy_required_inputs(tmp_path)
    content = b"fake official dem bytes"
    report = execute_south_fork_a1_window_source_pulls(
        tmp_path,
        window_ids={"chili_bar_existing_pilot_0_2500m"},
        roles={"terrain_dem"},
        opener=FakeOpener(content),
    )
    status = json.loads((tmp_path / FULL_REACH_WINDOW_SOURCE_PULL_STATUS_RELATIVE_PATH).read_text())
    first_window = status["windows"][0]

    assert report["status"] == "completed"
    assert report["summary"]["downloaded_count"] == 1
    assert report["summary"]["failed_count"] == 0
    assert report["results"][0]["sha256"] == hashlib.sha256(content).hexdigest()
    assert first_window["terrain_dem"]["present"] is True
    assert first_window["terrain_dem"]["sha256"] == hashlib.sha256(content).hexdigest()
    assert status["summary"]["present_source_file_count"] == 1
    assert status["summary"]["missing_source_file_count"] == 11


def _copy_required_inputs(tmp_path: Path) -> None:
    for relative in (
        FULL_REACH_WINDOW_SOURCE_PULL_PLAN_RELATIVE_PATH,
        FULL_REACH_WINDOW_SOURCE_PULL_STATUS_RELATIVE_PATH,
    ):
        source = REPO_ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    pilot_manifest = (
        "physics/data/real_world/south_fork_american_chili_bar/"
        "production_corridor/chili_bar_reach_0_2500m/manifest.json"
    )
    target = tmp_path / pilot_manifest
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO_ROOT / pilot_manifest, target)


class FakeResponse:
    def __init__(self, content: bytes):
        self._content = content
        self._offset = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self, size: int = -1) -> bytes:
        if self._offset >= len(self._content):
            return b""
        if size < 0:
            size = len(self._content) - self._offset
        start = self._offset
        self._offset = min(len(self._content), self._offset + size)
        return self._content[start:self._offset]


class FakeOpener:
    def __init__(self, content: bytes):
        self.content = content

    def __call__(self, request, timeout: int):
        assert request.full_url.startswith("https://")
        assert timeout == 60
        return FakeResponse(self.content)
