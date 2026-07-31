from __future__ import annotations

import importlib.util
import base64
import json
import plistlib
import stat
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "Scripts" / "release_candidate.py"
SPEC = importlib.util.spec_from_file_location("raftsim_release_candidate", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
release = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = release
SPEC.loader.exec_module(release)


def test_release_version_matches_project_configuration() -> None:
    assert release.read_project_version(REPO_ROOT) == release.RELEASE_VERSION
    assert release.read_macos_marketing_version(REPO_ROOT) == release.RELEASE_VERSION


def test_required_release_files_exist() -> None:
    missing = [
        path
        for path in release.REQUIRED_RELEASE_FILES
        if not (REPO_ROOT / path).is_file()
    ]
    assert missing == []


def test_sha256_file_matches_known_digest(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.bin"
    artifact.write_bytes(b"raftsim-release-candidate")
    assert (
        release.sha256_file(artifact)
        == "6db38c6a6795054448c6f9a9e6fc05166bdb7090ae4cf912fbff3c55170b76f7"
    )


def test_macos_package_inspection_requires_executable_and_runtime_data(
    tmp_path: Path,
) -> None:
    app = tmp_path / "SmokeEmIfYouGotEm.app"
    executable = app / "Contents" / "MacOS" / "SmokeEmIfYouGotEm"
    executable.parent.mkdir(parents=True)
    executable.write_text("#!/bin/sh\n", encoding="utf-8")
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
    with (app / "Contents" / "Info.plist").open("wb") as stream:
        plistlib.dump(
            {
                "CFBundleExecutable": "SmokeEmIfYouGotEm",
                "CFBundleShortVersionString": release.RELEASE_VERSION,
            },
            stream,
        )
    runtime = app / "Contents" / "UE" / "RaftSimRuntimeData"
    runtime.mkdir(parents=True)
    for index in range(3):
        (runtime / f"field_{index}.json").write_text("{}\n", encoding="utf-8")

    inspection = release.inspect_package(
        app, "macos", release.RELEASE_VERSION, minimum_runtime_files=3
    )
    assert inspection.executable_ready is True
    assert inspection.runtime_data_file_count == 3


def test_package_inspection_rejects_incomplete_runtime_stage(tmp_path: Path) -> None:
    app = tmp_path / "SmokeEmIfYouGotEm.app"
    executable = app / "Contents" / "MacOS" / "SmokeEmIfYouGotEm"
    executable.parent.mkdir(parents=True)
    executable.write_text("#!/bin/sh\n", encoding="utf-8")
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
    with (app / "Contents" / "Info.plist").open("wb") as stream:
        plistlib.dump(
            {
                "CFBundleExecutable": "SmokeEmIfYouGotEm",
                "CFBundleShortVersionString": release.RELEASE_VERSION,
            },
            stream,
        )
    with pytest.raises(release.ReleaseError, match="runtime-data files"):
        release.inspect_package(
            app, "macos", release.RELEASE_VERSION, minimum_runtime_files=1
        )


def test_macos_package_inspection_rejects_wrong_bundle_version(tmp_path: Path) -> None:
    app = tmp_path / "RaftSim.app"
    executable = app / "Contents" / "MacOS" / "RaftSim-Shipping"
    executable.parent.mkdir(parents=True)
    executable.write_text("#!/bin/sh\n", encoding="utf-8")
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
    with (app / "Contents" / "Info.plist").open("wb") as stream:
        plistlib.dump(
            {
                "CFBundleExecutable": "RaftSim-Shipping",
                "CFBundleShortVersionString": "5.8.0",
            },
            stream,
        )
    runtime = app / "Contents" / "UE" / "RaftSimRuntimeData"
    runtime.mkdir(parents=True)
    (runtime / "manifest.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(release.ReleaseError, match="Packaged project version"):
        release.inspect_package(
            app, "macos", release.RELEASE_VERSION, minimum_runtime_files=1
        )


def test_windows_package_inspection_finds_archived_executable_recursively(
    tmp_path: Path,
) -> None:
    package = tmp_path / "package"
    executable = (
        package
        / "Windows"
        / "SmokeEmIfYouGotEm"
        / "Binaries"
        / "Win64"
        / "SmokeEmIfYouGotEm.exe"
    )
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"exe")
    runtime = executable.parent / "RaftSimRuntimeData"
    runtime.mkdir()
    (runtime / "manifest.json").write_text("{}\n", encoding="utf-8")

    inspection = release.inspect_package(
        package, "windows", release.RELEASE_VERSION, minimum_runtime_files=1
    )
    assert Path(inspection.executable) == executable


def test_qa_report_requires_explicit_pass(tmp_path: Path) -> None:
    path = tmp_path / "qa.json"
    path.write_text(
        json.dumps({"schema": "test", "passed": True}) + "\n", encoding="utf-8"
    )
    loaded = release.load_qa_report(path)
    assert loaded["passed"] is True
    assert len(loaded["sha256"]) == 64

    path.write_text(
        json.dumps({"schema": "test", "status": "looks_good"}) + "\n", encoding="utf-8"
    )
    assert release.load_qa_report(path)["passed"] is False


def test_performance_report_requires_player_representative_qualification(
    tmp_path: Path,
) -> None:
    path = tmp_path / "performance.json"
    path.write_text(
        json.dumps(
            {
                "schema": "raftsim.m8.full_reach_performance_soak.v3",
                "passed": True,
                "performance_protocol": "offscreen_engineering_diagnostic",
                "release_performance_qualified": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    diagnostic = release.load_qa_report(path)
    assert diagnostic["passed"] is False
    assert diagnostic["release_performance_qualified"] is False
    assert diagnostic["performance_protocol"] == "offscreen_engineering_diagnostic"

    path.write_text(
        json.dumps(
            {
                "schema": "raftsim.m8.full_reach_performance_soak.v3",
                "passed": True,
                "performance_protocol": "normal_windowed_player_presentation",
                "release_performance_qualified": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    qualified = release.load_qa_report(path)
    assert qualified["passed"] is True
    assert qualified["release_performance_qualified"] is True


def test_extract_qa_report_from_packaged_stdout(tmp_path: Path) -> None:
    payload = {"schema": "raftsim.test.qa.v1", "passed": True, "cases": 60}
    encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")
    log_path = tmp_path / "packaged.log"
    log_path.write_text(
        "engine startup\n"
        f"LogTemp: Display: {release.VALIDATION_STDOUT_MARKER}{encoded}\n"
        "engine shutdown\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "qa.json"

    assert release.extract_qa_report_from_log(log_path, output_path) == payload
    assert json.loads(output_path.read_text(encoding="utf-8")) == payload


def test_extract_qa_report_rejects_missing_marker(tmp_path: Path) -> None:
    log_path = tmp_path / "packaged.log"
    log_path.write_text("engine startup only\n", encoding="utf-8")
    with pytest.raises(release.ReleaseError, match="no validation report marker"):
        release.extract_qa_report_from_log(log_path, tmp_path / "qa.json")


def test_zip_preserves_package_root(tmp_path: Path) -> None:
    package = tmp_path / "Windows"
    package.mkdir()
    (package / "SmokeEmIfYouGotEm.exe").write_bytes(b"exe")
    archive = tmp_path / "artifact.zip"
    release.create_zip(package, archive, "windows")
    import zipfile

    with zipfile.ZipFile(archive) as handle:
        assert handle.namelist() == ["Windows/SmokeEmIfYouGotEm.exe"]


def _write_release_artifact_fixture(
    tmp_path: Path,
    *,
    clean: bool = True,
    signature_status: str = "authenticode_valid",
) -> tuple[Path, Path, Path]:
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    archive = artifact_dir / "RaftSim-1.0.0-rc1-windows-x64.zip"
    archive.write_bytes(b"immutable-windows-rc")
    manifest = {
        "schema": "raftsim.m9.release_artifact_manifest.v1",
        "release_version": release.RELEASE_VERSION,
        "release_branch": release.RELEASE_BRANCH,
        "git_commit": "1" * 40,
        "source_worktree_clean": clean,
        "platform": "windows",
        "signature": {"passed": True, "status": signature_status},
        "qa_reports": [
            {"schema": "raftsim.test.qa.v1", "passed": True, "sha256": "2" * 64}
        ],
        "archive": {
            "filename": archive.name,
            "size_bytes": archive.stat().st_size,
            "sha256": release.sha256_file(archive),
        },
        "passed": True,
    }
    manifest_path = artifact_dir / "windows-x64-release-manifest.json"
    manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
    return manifest_path, artifact_dir, archive


def test_verify_artifact_manifest_locks_clean_signed_archive_bytes(
    tmp_path: Path,
) -> None:
    manifest_path, artifact_dir, archive = _write_release_artifact_fixture(tmp_path)

    verification = release.verify_artifact_manifest(
        manifest_path, artifact_dir, "windows"
    )

    assert verification["passed"] is True
    assert verification["source_worktree_clean"] is True
    assert verification["signature_status"] == "authenticode_valid"
    assert verification["archive"]["sha256"] == release.sha256_file(archive)


def test_verify_artifact_manifest_rejects_dirty_or_modified_artifact(
    tmp_path: Path,
) -> None:
    manifest_path, artifact_dir, archive = _write_release_artifact_fixture(
        tmp_path, clean=False
    )
    with pytest.raises(release.ReleaseError, match="clean worktree"):
        release.verify_artifact_manifest(manifest_path, artifact_dir, "windows")

    archive.write_bytes(b"modified-after-finalization")
    with pytest.raises(release.ReleaseError, match="byte count|SHA-256"):
        release.verify_artifact_manifest(
            manifest_path,
            artifact_dir,
            "windows",
            require_clean=False,
        )


def test_verify_artifact_manifest_rejects_wrong_signature_or_platform(
    tmp_path: Path,
) -> None:
    manifest_path, artifact_dir, _ = _write_release_artifact_fixture(
        tmp_path, signature_status="development_or_adhoc_valid_not_notarizable"
    )
    with pytest.raises(release.ReleaseError, match="authenticode_valid"):
        release.verify_artifact_manifest(manifest_path, artifact_dir, "windows")
    with pytest.raises(release.ReleaseError, match="platform"):
        release.verify_artifact_manifest(manifest_path, artifact_dir, "macos")
