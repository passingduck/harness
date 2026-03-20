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
    claim_parser = sub.add_parser("claim-task")
    claim_parser.add_argument("--repo-root", required=True)
    claim_parser.add_argument("--task", required=True)

    open_parser = sub.add_parser("open-worktree")
    open_parser.add_argument("--repo-root", required=True)
    open_parser.add_argument("--task-id", required=True)
    open_parser.add_argument("--branch", required=True)
    open_parser.add_argument(
        "--cleanup-policy",
        choices=["preserve", "delete"],
        default="preserve",
    )

    close_parser = sub.add_parser("close-worktree")
    close_parser.add_argument("--repo-root", required=True)
    close_parser.add_argument("--task-id", required=True)
    close_parser.add_argument("--mode", required=True, choices=["preserve", "delete"])
    close_parser.add_argument(
        "--worker-status",
        required=True,
        choices=["DONE", "DONE_WITH_CONCERNS", "NEEDS_CONTEXT", "BLOCKED"],
    )

    refresh_parser = sub.add_parser("refresh-memory")
    refresh_parser.add_argument("--repo-root", required=True)
    refresh_parser.add_argument(
        "--changed-path",
        dest="changed_paths",
        action="append",
        required=True,
    )

    review_result_parser = sub.add_parser("write-review-result")
    review_result_parser.add_argument("--repo-root", required=True)
    review_result_parser.add_argument("--task-id", required=True)
    review_result_parser.add_argument("--stage", required=True)
    review_result_parser.add_argument(
        "--verdict",
        required=True,
        choices=["APPROVED", "CHANGES_REQUIRED", "ESCALATE"],
    )
    review_result_parser.add_argument(
        "--blocking-issue",
        dest="blocking_issues",
        action="append",
        default=[],
    )
    review_result_parser.add_argument(
        "--advisory-note",
        dest="advisory_notes",
        action="append",
        default=[],
    )
    review_result_parser.add_argument(
        "--evidence-ref",
        dest="evidence_refs",
        action="append",
        default=[],
    )
    review_result_parser.add_argument("--next-action", required=True)

    review_pack_parser = sub.add_parser("build-review-pack")
    review_pack_parser.add_argument("--repo-root", required=True)
    review_pack_parser.add_argument(
        "--type",
        dest="review_type",
        choices=["commit", "pr"],
        required=True,
    )
    review_pack_parser.add_argument("--task-id")
    review_pack_parser.add_argument("--title", required=True)
    review_pack_parser.add_argument(
        "--changed-path",
        dest="changed_paths",
        action="append",
        required=True,
    )
    review_pack_parser.add_argument(
        "--verification-command",
        dest="verification_commands",
        action="append",
        required=True,
    )
    review_pack_parser.add_argument("--promote-to")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    repo_root = Path(getattr(args, "repo_root", ".")).resolve()
    if args.command == "init":
        from harness_kit.scaffold import init_project

        init_project(Path(args.target), args.project_name)
    elif args.command == "claim-task":
        from harness_kit.queue import claim_task

        task_path = Path(args.task)
        if not task_path.is_absolute():
            task_path = repo_root / task_path
        claimed_task, context_pack = claim_task(
            task_path=task_path,
            repo_root=repo_root,
        )
        print(claimed_task)
        print(context_pack)
    elif args.command == "open-worktree":
        from harness_kit.worktree import open_worktree

        print(
            open_worktree(
                repo_root=repo_root,
                task_id=args.task_id,
                branch_name=args.branch,
                cleanup_policy=args.cleanup_policy,
            )
        )
    elif args.command == "close-worktree":
        from harness_kit.worktree import close_worktree

        moved_task, record = close_worktree(
            repo_root=repo_root,
            task_id=args.task_id,
            mode=args.mode,
            worker_status=args.worker_status,
        )
        if moved_task is not None:
            print(moved_task)
        print(record)
    elif args.command == "refresh-memory":
        from harness_kit.memory import refresh_memory

        for guide in refresh_memory(
            repo_root=repo_root,
            changed_paths=args.changed_paths,
        ):
            print(guide)
    elif args.command == "write-review-result":
        from harness_kit.review_results import write_review_result

        print(
            write_review_result(
                repo_root=repo_root,
                task_id=args.task_id,
                stage=args.stage,
                verdict=args.verdict,
                blocking_issues=args.blocking_issues,
                advisory_notes=args.advisory_notes,
                evidence_refs=args.evidence_refs,
                next_action=args.next_action,
            )
        )
    elif args.command == "build-review-pack":
        from harness_kit.review_pack import build_review_pack, promote_review_pack

        draft = build_review_pack(
            repo_root=repo_root,
            review_type=args.review_type,
            title=args.title,
            changed_paths=args.changed_paths,
            verification_commands=args.verification_commands,
            task_id=args.task_id,
        )
        print(draft)
        if args.promote_to:
            print(
                promote_review_pack(
                    repo_root=repo_root,
                    draft_path=draft.relative_to(repo_root),
                    promote_to=Path(args.promote_to),
                    task_id=args.task_id,
                )
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
