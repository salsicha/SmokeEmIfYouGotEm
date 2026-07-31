#!/usr/bin/env python3
"""Build and verify reproducible RaftSim release-candidate metadata.

This tool deliberately separates evidence from aspiration. It can finalize a package
only when the package exists, contains the shipping executable and staged runtime data,
has an acceptable platform signature, and every supplied packaged-QA report passes.
Unavailable platform lanes are recorded by the tracked M9 manifest; they are never
silently promoted by this script.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import configparser
import hashlib
import json
import os
import plistlib
import shutil
import stat
import subprocess
import sys
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

RELEASE_VERSION = "1.0.0-rc1"
RELEASE_BRANCH = "release/1.0"
PRODUCT_NAME = "SmokeEmIfYouGotEm"
MINIMUM_RUNTIME_DATA_FILES = 600
VALIDATION_STDOUT_MARKER = "RAFTSIM_VALIDATION_JSON_BASE64="
REQUIRED_RELEASE_FILES = (
    "CHANGELOG.md",
    "CREDITS.md",
    "LICENSE",
    "LICENSE-CONTENT.md",
    "NOTICE.md",
    "docs/release/install-and-first-run.md",
    "docs/release/known-issues.md",
    "docs/release/patch-and-rollback.md",
    "docs/release/privacy-and-crash-reporting.md",
    "docs/release/support.md",
    "docs/presskit/README.md",
    "distribution/itch/README.md",
    "distribution/steam/README.md",
)


class ReleaseError(RuntimeError):
    """A release candidate cannot be finalized."""


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class PackageInspection:
    platform: str
    package_root: str
    executable: str
    package_file_count: int
    runtime_data_file_count: int
    executable_present: bool
    executable_ready: bool
    project_version: str
    project_version_matches: bool


@dataclass(frozen=True)
class SignatureInspection:
    policy: str
    passed: bool
    status: str
    authority: str
    detail: str


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def run_command(command: Sequence[str], cwd: Path | None = None) -> CommandResult:
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return CommandResult(
        command=list(command),
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_project_version(repo_root: Path) -> str:
    path = repo_root / "unreal" / "Config" / "DefaultGame.ini"
    parser = configparser.ConfigParser(strict=False)
    parser.optionxform = str
    parser.read(path, encoding="utf-8")
    section = "/Script/EngineSettings.GeneralProjectSettings"
    if not parser.has_option(section, "ProjectVersion"):
        raise ReleaseError(f"ProjectVersion is missing from {path}")
    return parser.get(section, "ProjectVersion").strip()


def read_macos_marketing_version(repo_root: Path) -> str:
    path = repo_root / "unreal" / "Config" / "DefaultEngine.ini"
    parser = configparser.ConfigParser(strict=False)
    parser.optionxform = str
    parser.read(path, encoding="utf-8")
    section = "/Script/MacRuntimeSettings.MacRuntimeSettings"
    if not parser.has_option(section, "VersionInfo"):
        raise ReleaseError(f"macOS VersionInfo is missing from {path}")
    return parser.get(section, "VersionInfo").strip()


def git_value(repo_root: Path, *args: str) -> str:
    result = run_command(("git", *args), cwd=repo_root)
    if result.returncode != 0:
        raise ReleaseError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def source_audit(
    repo_root: Path, expected_branch: str = RELEASE_BRANCH
) -> dict[str, Any]:
    version = read_project_version(repo_root)
    macos_marketing_version = read_macos_marketing_version(repo_root)
    branch = git_value(repo_root, "branch", "--show-current")
    commit = git_value(repo_root, "rev-parse", "HEAD")
    dirty_lines = git_value(repo_root, "status", "--porcelain").splitlines()
    missing = [
        relative
        for relative in REQUIRED_RELEASE_FILES
        if not (repo_root / relative).is_file()
    ]
    return {
        "schema": "raftsim.m9.source_release_audit.v1",
        "release_version": version,
        "release_version_matches": version == RELEASE_VERSION,
        "macos_marketing_version": macos_marketing_version,
        "macos_marketing_version_matches": macos_marketing_version == RELEASE_VERSION,
        "branch": branch,
        "branch_matches": branch == expected_branch,
        "commit": commit,
        "worktree_clean": not dirty_lines,
        "dirty_path_count": len(dirty_lines),
        "required_release_file_count": len(REQUIRED_RELEASE_FILES),
        "missing_release_files": missing,
        "passed": version == RELEASE_VERSION
        and macos_marketing_version == RELEASE_VERSION
        and branch == expected_branch
        and not missing,
    }


def sha256_file(path: Path, block_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(block_size):
            digest.update(chunk)
    return digest.hexdigest()


def iter_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    yield from (path for path in root.rglob("*") if path.is_file())


def find_executable(package_root: Path, platform: str) -> Path:
    if platform == "macos":
        plist_path = package_root / "Contents" / "Info.plist"
        if plist_path.is_file():
            try:
                with plist_path.open("rb") as stream:
                    executable_name = plistlib.load(stream).get("CFBundleExecutable")
                if executable_name:
                    return package_root / "Contents" / "MacOS" / str(executable_name)
            except (OSError, plistlib.InvalidFileException):
                pass
        return package_root / "Contents" / "MacOS" / PRODUCT_NAME
    candidates = (
        package_root / f"{PRODUCT_NAME}.exe",
        package_root / "Windows" / f"{PRODUCT_NAME}.exe",
        package_root / "Win64" / f"{PRODUCT_NAME}.exe",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    recursive = sorted(package_root.rglob(f"{PRODUCT_NAME}.exe"))
    if recursive:
        return recursive[0]
    return candidates[0]


def packaged_project_version(package_root: Path, platform: str, fallback: str) -> str:
    if platform != "macos":
        return fallback
    plist_path = package_root / "Contents" / "Info.plist"
    if not plist_path.is_file():
        return fallback
    try:
        with plist_path.open("rb") as stream:
            payload = plistlib.load(stream)
    except (OSError, plistlib.InvalidFileException):
        return fallback
    return str(payload.get("CFBundleShortVersionString") or fallback)


def inspect_package(
    package_root: Path,
    platform: str,
    expected_version: str,
    minimum_runtime_files: int = MINIMUM_RUNTIME_DATA_FILES,
) -> PackageInspection:
    package_root = package_root.resolve()
    if not package_root.exists():
        raise ReleaseError(f"Package root does not exist: {package_root}")
    executable = find_executable(package_root, platform)
    files = list(iter_files(package_root))
    runtime_files = [path for path in files if "RaftSimRuntimeData" in path.parts]
    executable_present = executable.is_file()
    executable_ready = executable_present and (
        platform == "windows" or bool(executable.stat().st_mode & stat.S_IXUSR)
    )
    # A missing macOS bundle version is a failed package contract, not an
    # opportunity to substitute the source version being checked.
    version_fallback = "" if platform == "macos" else expected_version
    package_version = packaged_project_version(package_root, platform, version_fallback)
    inspection = PackageInspection(
        platform=platform,
        package_root=str(package_root),
        executable=str(executable),
        package_file_count=len(files),
        runtime_data_file_count=len(runtime_files),
        executable_present=executable_present,
        executable_ready=executable_ready,
        project_version=package_version,
        project_version_matches=package_version == expected_version,
    )
    if not executable_ready:
        raise ReleaseError(
            f"Shipping executable is missing or not runnable: {executable}"
        )
    if len(runtime_files) < minimum_runtime_files:
        raise ReleaseError(
            f"Only {len(runtime_files)} runtime-data files staged; expected at least "
            f"{minimum_runtime_files}"
        )
    if not inspection.project_version_matches:
        raise ReleaseError(
            f"Packaged project version {inspection.project_version!r} does not match "
            f"{expected_version!r}"
        )
    return inspection


def _codesign_authority(detail: str) -> str:
    for line in detail.splitlines():
        if line.startswith("Authority="):
            return line.partition("=")[2].strip()
        if line.startswith("Signature="):
            return line.partition("=")[2].strip()
    return "unknown"


def inspect_macos_signature(package_root: Path, policy: str) -> SignatureInspection:
    verify = run_command(
        ("codesign", "--verify", "--deep", "--strict", "--verbose=2", str(package_root))
    )
    detail_result = run_command(("codesign", "-d", "--verbose=4", str(package_root)))
    detail = "\n".join(
        part for part in (detail_result.stdout, detail_result.stderr) if part
    ).strip()
    authority = _codesign_authority(detail)
    valid = verify.returncode == 0
    is_distribution = "Developer ID Application" in detail
    if policy == "defer":
        passed = True
        status = "verification_deferred"
    elif policy == "distribution":
        passed = valid and is_distribution
        status = "developer_id_valid" if passed else "developer_id_required"
    else:
        passed = valid
        status = "valid" if valid else "invalid"
        if valid and not is_distribution:
            status = "development_or_adhoc_valid_not_notarizable"
    return SignatureInspection(policy, passed, status, authority, detail[-4000:])


def inspect_windows_signature(
    package_root: Path, executable: Path, policy: str
) -> SignatureInspection:
    if policy == "defer":
        return SignatureInspection(policy, True, "verification_deferred", "unknown", "")
    if os.name != "nt":
        return SignatureInspection(
            policy,
            False,
            "windows_signature_requires_windows_host",
            "unknown",
            "Authenticode verification was not executed on a Windows host.",
        )
    escaped = str(executable).replace("'", "''")
    command = (
        "powershell",
        "-NoProfile",
        "-Command",
        f"$s=Get-AuthenticodeSignature -LiteralPath '{escaped}'; "
        "$s | Select-Object Status,StatusMessage,SignerCertificate | ConvertTo-Json -Depth 4",
    )
    result = run_command(command)
    detail = result.stdout.strip() or result.stderr.strip()
    valid = result.returncode == 0 and '"Status": 0' in detail
    return SignatureInspection(
        policy,
        valid,
        "authenticode_valid" if valid else "authenticode_invalid",
        "windows_authenticode",
        detail[-4000:],
    )


def inspect_signature(
    package_root: Path,
    executable: Path,
    platform: str,
    policy: str,
) -> SignatureInspection:
    if platform == "macos":
        return inspect_macos_signature(package_root, policy)
    return inspect_windows_signature(package_root, executable, policy)


def load_qa_report(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseError(f"Invalid QA report {path}: {exc}") from exc
    schema = payload.get("schema", "unknown")
    passed = payload.get("passed") is True
    release_performance_qualified: bool | None = None
    if schema == "raftsim.m8.full_reach_performance_soak.v3":
        release_performance_qualified = (
            payload.get("release_performance_qualified") is True
        )
        passed = passed and release_performance_qualified
    report = {
        "path": str(path.resolve()),
        "schema": schema,
        "passed": passed,
        "sha256": sha256_file(path),
    }
    if release_performance_qualified is not None:
        report["release_performance_qualified"] = release_performance_qualified
        report["performance_protocol"] = payload.get(
            "performance_protocol", "missing"
        )
    return report


def verify_artifact_manifest(
    manifest_path: Path,
    artifact_dir: Path,
    expected_platform: str,
    *,
    require_clean: bool = True,
    require_distribution_signature: bool = True,
) -> dict[str, Any]:
    """Verify that a downloaded RC archive is the immutable artifact in its manifest."""
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseError(
            f"Invalid release artifact manifest {manifest_path}: {exc}"
        ) from exc
    if manifest.get("schema") != "raftsim.m9.release_artifact_manifest.v1":
        raise ReleaseError("Release artifact manifest schema is not supported")
    if manifest.get("passed") is not True:
        raise ReleaseError("Release artifact manifest is not passing")
    if manifest.get("release_version") != RELEASE_VERSION:
        raise ReleaseError("Release artifact version does not match the release lock")
    if manifest.get("release_branch") != RELEASE_BRANCH:
        raise ReleaseError("Release artifact branch does not match the release lock")
    if manifest.get("platform") != expected_platform:
        raise ReleaseError(
            f"Release artifact platform {manifest.get('platform')!r} does not match "
            f"{expected_platform!r}"
        )
    commit = manifest.get("git_commit")
    if not isinstance(commit, str) or len(commit) != 40:
        raise ReleaseError("Release artifact commit is missing or malformed")
    source_clean = manifest.get("source_worktree_clean") is True
    if require_clean and not source_clean:
        raise ReleaseError("Release artifact was not built from a clean worktree")

    signature = manifest.get("signature")
    if not isinstance(signature, dict) or signature.get("passed") is not True:
        raise ReleaseError("Release artifact signature did not pass")
    expected_signature_status = (
        "developer_id_valid" if expected_platform == "macos" else "authenticode_valid"
    )
    if (
        require_distribution_signature
        and signature.get("status") != expected_signature_status
    ):
        raise ReleaseError(
            f"Release artifact requires {expected_signature_status}, got "
            f"{signature.get('status')!r}"
        )

    qa_reports = manifest.get("qa_reports")
    if not isinstance(qa_reports, list) or not qa_reports:
        raise ReleaseError("Release artifact has no packaged-QA evidence")
    if any(
        not isinstance(report, dict) or report.get("passed") is not True
        for report in qa_reports
    ):
        raise ReleaseError("Release artifact contains a failing packaged-QA report")

    archive = manifest.get("archive")
    if not isinstance(archive, dict):
        raise ReleaseError("Release artifact archive record is missing")
    filename = archive.get("filename")
    if not isinstance(filename, str) or Path(filename).name != filename:
        raise ReleaseError("Release artifact archive filename is unsafe or malformed")
    resolved_artifact_dir = artifact_dir.resolve()
    archive_path = (resolved_artifact_dir / filename).resolve()
    if archive_path.parent != resolved_artifact_dir:
        raise ReleaseError("Release artifact archive escapes the artifact directory")
    if not archive_path.is_file():
        raise ReleaseError(f"Release archive is missing: {archive_path}")
    expected_size = archive.get("size_bytes")
    if (
        not isinstance(expected_size, int)
        or archive_path.stat().st_size != expected_size
    ):
        raise ReleaseError("Release archive byte count does not match its manifest")
    expected_sha = archive.get("sha256")
    actual_sha = sha256_file(archive_path)
    if not isinstance(expected_sha, str) or actual_sha != expected_sha:
        raise ReleaseError("Release archive SHA-256 does not match its manifest")

    return {
        "schema": "raftsim.m9.release_artifact_verification.v1",
        "manifest": str(manifest_path.resolve()),
        "manifest_sha256": sha256_file(manifest_path),
        "release_version": manifest["release_version"],
        "release_branch": manifest["release_branch"],
        "git_commit": commit,
        "source_worktree_clean": source_clean,
        "platform": expected_platform,
        "signature_status": signature.get("status"),
        "qa_report_count": len(qa_reports),
        "archive": {
            "path": str(archive_path),
            "size_bytes": expected_size,
            "sha256": actual_sha,
        },
        "passed": True,
    }


def extract_qa_report_from_log(log_path: Path, output_path: Path) -> dict[str, Any]:
    """Recover a packaged QA report emitted through an inherited stdout handle.

    Sandboxed macOS applications can write their own container, but a release
    shell may be denied direct access to that container by host privacy policy.
    Stdout is already opened by the parent process, so it is a reliable,
    sandbox-compatible evidence channel on local machines and CI runners.
    """
    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        raise ReleaseError(f"Unable to read packaged QA log {log_path}: {exc}") from exc
    encoded_reports = [
        line.split(VALIDATION_STDOUT_MARKER, 1)[1].strip()
        for line in lines
        if VALIDATION_STDOUT_MARKER in line
    ]
    if not encoded_reports:
        raise ReleaseError(
            f"Packaged QA log contains no validation report marker: {log_path}"
        )
    try:
        decoded = base64.b64decode(encoded_reports[-1], validate=True).decode("utf-8")
        payload = json.loads(decoded)
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReleaseError(f"Invalid encoded QA report in {log_path}: {exc}") from exc
    if (
        not isinstance(payload, dict)
        or "schema" not in payload
        or "passed" not in payload
    ):
        raise ReleaseError(
            f"Encoded QA report has no schema/passed contract: {log_path}"
        )
    write_json(output_path, payload)
    return payload


def create_zip(package_root: Path, archive_path: Path, platform: str) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    if platform == "macos" and shutil.which("ditto"):
        result = run_command(
            (
                "ditto",
                "-c",
                "-k",
                "--sequesterRsrc",
                "--keepParent",
                str(package_root),
                str(archive_path),
            )
        )
        if result.returncode != 0:
            raise ReleaseError(result.stderr.strip() or "ditto archive failed")
        return
    with zipfile.ZipFile(
        archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        root_parent = package_root.parent
        for path in sorted(iter_files(package_root)):
            archive.write(path, path.relative_to(root_parent))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )


def finalize(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = args.repo_root.resolve()
    source = source_audit(repo_root, args.expected_branch)
    if not source["passed"]:
        raise ReleaseError(
            "Source release audit failed: "
            + json.dumps(
                {
                    "version": source["release_version"],
                    "branch": source["branch"],
                    "missing": source["missing_release_files"],
                }
            )
        )
    if not source["worktree_clean"] and not args.allow_dirty:
        raise ReleaseError(
            "Release source worktree is dirty; pass --allow-dirty only for milestone validation"
        )

    inspection = inspect_package(
        args.package_root,
        args.platform,
        RELEASE_VERSION,
        args.minimum_runtime_files,
    )
    signature = inspect_signature(
        args.package_root.resolve(),
        Path(inspection.executable),
        args.platform,
        args.signature_policy,
    )
    if not signature.passed:
        raise ReleaseError(f"Platform signature failed: {signature.status}")

    qa_reports = [load_qa_report(path) for path in args.qa_report]
    if not qa_reports:
        raise ReleaseError("At least one packaged QA report is required")
    failed_reports = [report["path"] for report in qa_reports if not report["passed"]]
    if failed_reports:
        raise ReleaseError(f"Packaged QA failed: {failed_reports}")

    platform_slug = "macos-arm64" if args.platform == "macos" else "windows-x64"
    archive_name = f"RaftSim-{RELEASE_VERSION}-{platform_slug}.zip"
    archive_path = args.output_dir.resolve() / archive_name
    if not args.skip_archive:
        create_zip(args.package_root.resolve(), archive_path, args.platform)
    if not archive_path.is_file():
        raise ReleaseError(f"Release archive was not created: {archive_path}")

    archive_sha = sha256_file(archive_path)
    manifest = {
        "schema": "raftsim.m9.release_artifact_manifest.v1",
        "generated_utc": utc_now(),
        "release_version": RELEASE_VERSION,
        "release_branch": source["branch"],
        "git_commit": source["commit"],
        "source_worktree_clean": source["worktree_clean"],
        "platform": args.platform,
        "architecture": "arm64" if args.platform == "macos" else "x86_64",
        "configuration": args.configuration,
        "package": asdict(inspection),
        "signature": asdict(signature),
        "qa_reports": qa_reports,
        "archive": {
            "path": str(archive_path),
            "filename": archive_path.name,
            "size_bytes": archive_path.stat().st_size,
            "sha256": archive_sha,
        },
        "passed": True,
    }
    manifest_path = args.output_dir.resolve() / f"{platform_slug}-release-manifest.json"
    write_json(manifest_path, manifest)
    sums_path = args.output_dir.resolve() / "SHA256SUMS"
    existing = {}
    if sums_path.is_file():
        for line in sums_path.read_text(encoding="utf-8").splitlines():
            digest, _, name = line.partition("  ")
            if digest and name:
                existing[name] = digest
    existing[archive_path.name] = archive_sha
    sums_path.write_text(
        "".join(f"{existing[name]}  {name}\n" for name in sorted(existing)),
        encoding="utf-8",
    )
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=repository_root())
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit = subparsers.add_parser(
        "audit-source", help="Validate tracked RC source state"
    )
    audit.add_argument("--expected-branch", default=RELEASE_BRANCH)
    audit.add_argument("--output", type=Path)

    extract = subparsers.add_parser(
        "extract-qa-log", help="Extract a sandboxed packaged-QA report from stdout"
    )
    extract.add_argument("--log", type=Path, required=True)
    extract.add_argument("--output", type=Path, required=True)

    final = subparsers.add_parser(
        "finalize", help="Verify and archive a built RC package"
    )
    final.add_argument("--platform", choices=("macos", "windows"), required=True)
    final.add_argument("--package-root", type=Path, required=True)
    final.add_argument("--output-dir", type=Path, required=True)
    final.add_argument("--configuration", default="Shipping")
    final.add_argument("--expected-branch", default=RELEASE_BRANCH)
    final.add_argument(
        "--signature-policy",
        choices=("any-valid", "distribution", "defer"),
        default="any-valid",
    )
    final.add_argument("--qa-report", type=Path, action="append", default=[])
    final.add_argument(
        "--minimum-runtime-files", type=int, default=MINIMUM_RUNTIME_DATA_FILES
    )
    final.add_argument("--allow-dirty", action="store_true")
    final.add_argument("--skip-archive", action="store_true", help=argparse.SUPPRESS)

    verify = subparsers.add_parser(
        "verify-artifact",
        help="Verify a signed RC manifest and the exact downloaded archive it names",
    )
    verify.add_argument("--manifest", type=Path, required=True)
    verify.add_argument("--artifact-dir", type=Path, required=True)
    verify.add_argument("--platform", choices=("macos", "windows"), required=True)
    verify.add_argument("--output", type=Path)
    verify.add_argument("--allow-dirty", action="store_true")
    verify.add_argument("--allow-nondistribution", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "audit-source":
            payload = source_audit(args.repo_root.resolve(), args.expected_branch)
            if args.output:
                write_json(args.output, payload)
            print(json.dumps(payload, indent=2))
            return 0 if payload["passed"] else 2
        if args.command == "extract-qa-log":
            payload = extract_qa_report_from_log(args.log, args.output)
            print(
                json.dumps(
                    {
                        "schema": payload.get("schema"),
                        "passed": payload.get("passed") is True,
                        "output": str(args.output.resolve()),
                    },
                    indent=2,
                )
            )
            return 0 if payload.get("passed") is True else 2
        if args.command == "verify-artifact":
            payload = verify_artifact_manifest(
                args.manifest.resolve(),
                args.artifact_dir.resolve(),
                args.platform,
                require_clean=not args.allow_dirty,
                require_distribution_signature=not args.allow_nondistribution,
            )
            if args.output:
                write_json(args.output, payload)
            print(json.dumps(payload, indent=2))
            return 0
        payload = finalize(args)
        print(json.dumps(payload, indent=2))
        return 0
    except ReleaseError as exc:
        print(f"release candidate failure: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
