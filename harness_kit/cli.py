import argparse
import importlib.util
from pathlib import Path


def has_scaffold_support() -> bool:
    return importlib.util.find_spec("harness_kit.scaffold") is not None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="harness-kit")
    sub = parser.add_subparsers(dest="command")
    if has_scaffold_support():
        init_parser = sub.add_parser("init")
        init_parser.add_argument("--target", required=True)
        init_parser.add_argument("--project-name", required=True)
    for name in [
        "claim-task",
        "open-worktree",
        "close-worktree",
        "refresh-memory",
        "build-review-pack",
    ]:
        sub.add_parser(name)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "init":
        from harness_kit.scaffold import init_project

        init_project(Path(args.target), args.project_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
