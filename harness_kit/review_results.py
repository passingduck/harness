from __future__ import annotations

from pathlib import Path
from typing import Any

from harness_kit.queue import (
    _parse_frontmatter,
    _render_frontmatter,
    _split_frontmatter_block,
    validate_phase1_task_id,
)


REVIEW_RESULTS_ROOT = Path(".harness/runtime/review-results")
REVIEW_RESULT_FIELDS = (
    "stage",
    "verdict",
    "blocking_issues",
    "advisory_notes",
    "evidence_refs",
    "next_action",
)
LIST_FIELDS = {
    "blocking_issues",
    "advisory_notes",
    "evidence_refs",
}
VALID_VERDICTS = {
    "APPROVED",
    "CHANGES_REQUIRED",
    "ESCALATE",
}


def _review_result_path(repo_root: Path, task_id: str, stage: str) -> Path:
    safe_task_id = validate_phase1_task_id(task_id)
    safe_stage = validate_phase1_task_id(stage, "review stage")
    return repo_root / REVIEW_RESULTS_ROOT / safe_task_id / f"{safe_stage}.md"


def _validate_review_result(payload: dict[str, Any]) -> None:
    missing = [field for field in REVIEW_RESULT_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"Review result missing fields: {', '.join(missing)}")
    validate_phase1_task_id(str(payload["stage"]), "review stage")
    verdict = payload["verdict"]
    if verdict not in VALID_VERDICTS:
        raise ValueError(f"Unsupported review result verdict: {verdict}")
    for field in LIST_FIELDS:
        value = payload[field]
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise ValueError(f"Review result field {field!r} must be a list of strings.")
    next_action = payload["next_action"]
    if not isinstance(next_action, str) or not next_action:
        raise ValueError("Review result field 'next_action' must be a non-empty string.")


def write_review_result(
    repo_root: Path,
    task_id: str,
    stage: str,
    verdict: str,
    blocking_issues: list[str],
    advisory_notes: list[str],
    evidence_refs: list[str],
    next_action: str,
) -> Path:
    receipt = {
        "stage": stage,
        "verdict": verdict,
        "blocking_issues": blocking_issues,
        "advisory_notes": advisory_notes,
        "evidence_refs": evidence_refs,
        "next_action": next_action,
    }
    _validate_review_result(receipt)
    receipt_path = _review_result_path(repo_root, task_id, stage)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = _render_frontmatter(receipt, REVIEW_RESULT_FIELDS)
    receipt_path.write_text(f"{frontmatter}\n", encoding="utf-8")
    return receipt_path


def load_review_result(repo_root: Path, task_id: str, stage: str) -> dict[str, Any]:
    receipt_path = _review_result_path(repo_root, task_id, stage)
    frontmatter_text, body_text = _split_frontmatter_block(receipt_path.read_text(encoding="utf-8"))
    if body_text.strip():
        raise ValueError("Review result receipts must not include a markdown body.")
    receipt = _parse_frontmatter(frontmatter_text)
    _validate_review_result(receipt)
    if receipt["stage"] != stage:
        raise ValueError("Review result stage must match the receipt filename.")
    return receipt


def validate_review_results(
    repo_root: Path,
    task_id: str,
    required_stages: list[str],
) -> list[dict[str, Any]]:
    try:
        receipts = [load_review_result(repo_root, task_id, stage) for stage in required_stages]
    except FileNotFoundError as exc:
        raise ValueError(f"Missing required review result receipt: {exc.filename}") from exc
    unapproved = [receipt["stage"] for receipt in receipts if receipt["verdict"] != "APPROVED"]
    if unapproved:
        raise ValueError(
            "All required review results must be APPROVED: " + ", ".join(unapproved)
        )
    return receipts
