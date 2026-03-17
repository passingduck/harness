import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="harness-kit")
    sub = parser.add_subparsers(dest="command")
    for name in [
        "init",
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
    parser.parse_args()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
