from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import subprocess

from harness_kit.runtime_bundle import iter_runtime_bundle
from harness_kit.template_loader import iter_skill_files, iter_template_files, load_text, render_text


def _file_mode(path: Path) -> int:
    return path.stat().st_mode & 0o777


def _write_text_file(path: Path, content: str, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if mode is not None:
        path.chmod(mode)


def _copy_rendered_surface(source_root: Path, target_root: Path, project_name: str) -> None:
    if not source_root.exists():
        return
    for source_path in iter_template_files(source_root):
        rel_path = source_path.relative_to(source_root)
        target_path = target_root / rel_path
        rendered = render_text(load_text(source_path), project_name)
        _write_text_file(target_path, rendered, _file_mode(source_path))


def _copy_skill_surface(source_root: Path, target_root: Path) -> None:
    if not source_root.exists():
        return
    for source_path in iter_skill_files(source_root):
        rel_path = source_path.relative_to(source_root)
        target_path = target_root / rel_path
        _write_text_file(target_path, load_text(source_path), _file_mode(source_path))


def _copy_runtime_bundle(source_root: Path, target_root: Path) -> list[str]:
    fileset: list[str] = []
    for source_path, rel_target_path in iter_runtime_bundle(source_root):
        target_path = target_root / rel_target_path
        _write_text_file(target_path, load_text(source_path), _file_mode(source_path))
        fileset.append(rel_target_path.as_posix())
    return fileset


def _git_output(repo_root: Path, args: list[str], default: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return default
    return proc.stdout.strip() or default


def _write_provenance(source_root: Path, target_root: Path, runtime_fileset: list[str]) -> Path:
    source_remote = _git_output(source_root, ["config", "--get", "remote.origin.url"], "local")
    source_branch = _git_output(source_root, ["rev-parse", "--abbrev-ref", "HEAD"], "unknown")
    source_commit = _git_output(source_root, ["rev-parse", "HEAD"], "unknown")
    provenance = target_root / "third_party" / "harness-source.txt"
    content = (
        f"source_remote: {source_remote}\n"
        f"source_branch: {source_branch}\n"
        f"source_commit: {source_commit}\n"
        f"runtime_bundle_fileset: {','.join(runtime_fileset)}\n"
        f"synced_at: {datetime.now(UTC).isoformat()}\n"
    )
    _write_text_file(provenance, content)
    return provenance


def sync_project(source_root: Path, target_root: Path, project_name: str | None = None) -> Path:
    source_root = source_root.resolve()
    target_root = target_root.resolve()
    target_root.mkdir(parents=True, exist_ok=True)
    resolved_project_name = project_name or target_root.name

    _copy_rendered_surface(
        source_root / "templates" / "project" / "scripts" / "harness",
        target_root / "scripts" / "harness",
        resolved_project_name,
    )
    _copy_rendered_surface(
        source_root / "templates" / "project" / ".harness" / "policies",
        target_root / ".harness" / "policies",
        resolved_project_name,
    )
    _copy_rendered_surface(
        source_root / "templates" / "project" / ".harness" / "templates",
        target_root / ".harness" / "templates",
        resolved_project_name,
    )
    _copy_skill_surface(source_root / "skills", target_root / "skills")
    runtime_fileset = _copy_runtime_bundle(source_root, target_root)
    return _write_provenance(source_root, target_root, runtime_fileset)
