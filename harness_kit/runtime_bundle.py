from pathlib import Path


RUNTIME_BUNDLE_ROOT = Path("scripts/harness/runtime/harness_kit")
VENDORED_RUNTIME_MODULES = [
    Path("__init__.py"),
    Path("cli.py"),
    Path("memory.py"),
    Path("queue.py"),
    Path("review_pack.py"),
    Path("worktree.py"),
]


def iter_runtime_bundle(repo_root: Path) -> list[tuple[Path, Path]]:
    package_root = repo_root / "harness_kit"
    bundle: list[tuple[Path, Path]] = []
    for rel_path in VENDORED_RUNTIME_MODULES:
        bundle.append((package_root / rel_path, RUNTIME_BUNDLE_ROOT / rel_path))
    return bundle
