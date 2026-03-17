from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


VALID_STATES = (
    "backlog",
    "ready",
    "in_progress",
    "review",
    "blocked",
    "done",
)
VALID_TRANSITIONS = {
    "backlog": {"ready"},
    "ready": {"in_progress"},
    "in_progress": {"review", "blocked", "ready"},
    "review": {"in_progress", "done"},
    "blocked": {"ready"},
    "done": set(),
}
QUEUE_FRONTMATTER_FIELDS = [
    "id",
    "title",
    "status",
    "priority",
    "owner_role",
    "model_hint",
    "worktree",
    "parent_spec",
    "parent_plan",
    "why_this_task_exists",
    "owned_paths",
    "required_reads",
    "disallowed_edits",
    "docs_to_update",
    "constraints",
    "verification_commands",
    "expected_report_schema",
    "review_stages",
    "dependencies",
]
BODY_SECTION_FIELDS = ("task_text", "acceptance_criteria", "non_goals")
LIST_FIELDS = {
    "owned_paths",
    "required_reads",
    "disallowed_edits",
    "docs_to_update",
    "constraints",
    "verification_commands",
    "expected_report_schema",
    "review_stages",
    "dependencies",
}
STRING_FIELDS = {
    "id",
    "title",
    "status",
    "priority",
    "owner_role",
    "model_hint",
    "parent_spec",
    "parent_plan",
    "why_this_task_exists",
}
CONTEXT_PACK_FIELDS = (
    "task_text",
    "why_this_task_exists",
    "owned_paths",
    "required_reads",
    "disallowed_edits",
    "constraints",
    "verification_commands",
    "expected_report_schema",
)


@dataclass
class QueueTask:
    path: Path
    frontmatter: dict[str, Any]
    sections: dict[str, str]

    @property
    def state(self) -> str:
        return str(self.frontmatter["status"])


def _split_frontmatter_block(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("Queue item must start with a frontmatter block.")
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            frontmatter = "\n".join(lines[1:index])
            body = "\n".join(lines[index + 1 :])
            return frontmatter, body
    raise ValueError("Queue item frontmatter block is not terminated.")


def _parse_scalar(raw_value: str) -> Any:
    if raw_value == "null":
        return None
    if raw_value == "true":
        return True
    if raw_value == "false":
        return False
    if raw_value == "[]":
        return []
    return raw_value


def _parse_frontmatter(frontmatter_text: str) -> dict[str, Any]:
    frontmatter: dict[str, Any] = {}
    lines = frontmatter_text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if ":" not in line:
            raise ValueError(f"Invalid frontmatter line: {line!r}")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        if value == "":
            items: list[str] = []
            index += 1
            while index < len(lines) and lines[index].startswith("  - "):
                items.append(lines[index][4:])
                index += 1
            frontmatter[key] = items
            continue
        frontmatter[key] = _parse_scalar(value)
        index += 1
    return frontmatter


def _render_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value)


def _render_frontmatter(frontmatter: dict[str, Any], field_order: list[str] | tuple[str, ...]) -> str:
    lines = ["---"]
    seen: set[str] = set()
    for field in field_order:
        if field not in frontmatter:
            continue
        seen.add(field)
        value = frontmatter[field]
        if isinstance(value, list):
            if value:
                lines.append(f"{field}:")
                for item in value:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"{field}: []")
        else:
            lines.append(f"{field}: {_render_scalar(value)}")
    for field in sorted(frontmatter.keys() - seen):
        value = frontmatter[field]
        if isinstance(value, list):
            if value:
                lines.append(f"{field}:")
                for item in value:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"{field}: []")
        else:
            lines.append(f"{field}: {_render_scalar(value)}")
    lines.append("---")
    return "\n".join(lines)


def _parse_body_sections(body_text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    section_headings = {f"## {name}": name for name in BODY_SECTION_FIELDS}
    current_name: str | None = None
    current_lines: list[str] = []
    for line in body_text.splitlines():
        section_name = section_headings.get(line.strip())
        if section_name is not None:
            if current_name is not None:
                sections[current_name] = "\n".join(current_lines).strip()
            current_name = section_name
            current_lines = []
            continue
        if current_name is not None:
            current_lines.append(line)
    if current_name is not None:
        sections[current_name] = "\n".join(current_lines).strip()
    return sections


def _render_body_sections(sections: dict[str, str]) -> str:
    blocks: list[str] = []
    for section_name, content in sections.items():
        blocks.append(f"## {section_name}\n{content.strip()}")
    return "\n\n".join(blocks).rstrip() + "\n"


def _validate_frontmatter(frontmatter: dict[str, Any]) -> None:
    missing = [field for field in QUEUE_FRONTMATTER_FIELDS if field not in frontmatter]
    if missing:
        raise ValueError(f"Queue item missing frontmatter fields: {', '.join(missing)}")
    for field in STRING_FIELDS:
        value = frontmatter[field]
        if not isinstance(value, str) or not value:
            raise ValueError(f"Queue field {field!r} must be a non-empty string.")
    status = frontmatter["status"]
    if not isinstance(status, str) or status not in VALID_STATES:
        raise ValueError("Queue field 'status' must be a valid queue state.")
    worktree = frontmatter["worktree"]
    if worktree is not None and (not isinstance(worktree, str) or not worktree):
        raise ValueError("Queue field 'worktree' must be null or a non-empty string.")
    for field in LIST_FIELDS:
        value = frontmatter[field]
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise ValueError(f"Queue field {field!r} must be a list of strings.")


def _validate_sections(sections: dict[str, str]) -> None:
    missing = [field for field in BODY_SECTION_FIELDS if not sections.get(field)]
    if missing:
        raise ValueError(f"Queue item missing body sections: {', '.join(missing)}")


def load_task(task_path: Path) -> QueueTask:
    frontmatter_text, body_text = _split_frontmatter_block(task_path.read_text(encoding="utf-8"))
    frontmatter = _parse_frontmatter(frontmatter_text)
    _validate_frontmatter(frontmatter)
    sections = _parse_body_sections(body_text)
    _validate_sections(sections)
    directory_state = task_path.parent.name
    if directory_state not in VALID_STATES:
        raise ValueError(f"Unsupported queue state directory: {directory_state}")
    frontmatter["status"] = directory_state
    return QueueTask(path=task_path, frontmatter=frontmatter, sections=sections)


def write_task(task_path: Path, frontmatter: dict[str, Any], sections: dict[str, str]) -> None:
    task_path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter_text = _render_frontmatter(frontmatter, QUEUE_FRONTMATTER_FIELDS)
    body_text = _render_body_sections(sections)
    task_path.write_text(f"{frontmatter_text}\n{body_text}", encoding="utf-8")


def move_task(task_path: Path, new_state: str) -> Path:
    if new_state not in VALID_STATES:
        raise ValueError(f"Unsupported queue state: {new_state}")
    task = load_task(task_path)
    if new_state not in VALID_TRANSITIONS[task.state]:
        raise ValueError(f"Invalid queue transition: {task.state} -> {new_state}")
    queue_root = task.path.parent.parent
    target_path = queue_root / new_state / task.path.name
    frontmatter = dict(task.frontmatter)
    frontmatter["status"] = new_state
    write_task(target_path, frontmatter, task.sections)
    if task.path != target_path and task.path.exists():
        task.path.unlink()
    return target_path


def render_context_pack(task: QueueTask) -> str:
    lines = ["# Context Pack", ""]
    for field in CONTEXT_PACK_FIELDS:
        lines.append(f"## {field}")
        lines.append("")
        if field == "task_text":
            lines.append(task.sections[field])
        else:
            value = task.frontmatter[field]
            if isinstance(value, list):
                if value:
                    lines.extend(f"- {item}" for item in value)
                else:
                    lines.append("- none")
            else:
                lines.append(str(value))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def claim_task(task_path: Path, repo_root: Path) -> tuple[Path, Path]:
    task = load_task(task_path)
    if task.state != "ready":
        raise ValueError("Only ready tasks can be claimed.")
    frontmatter = dict(task.frontmatter)
    frontmatter["worktree"] = frontmatter["id"]
    write_task(task.path, frontmatter, task.sections)
    claimed_path = move_task(task.path, "in_progress")
    claimed_task = load_task(claimed_path)
    context_pack_path = (
        repo_root / ".harness" / "runtime" / "context-packs" / f"{frontmatter['id']}.md"
    )
    context_pack_path.parent.mkdir(parents=True, exist_ok=True)
    context_pack_path.write_text(render_context_pack(claimed_task), encoding="utf-8")
    return claimed_path, context_pack_path


def find_task_path(repo_root: Path, task_id: str) -> Path | None:
    queue_root = repo_root / ".harness" / "runtime" / "queue"
    for state in VALID_STATES:
        candidate = queue_root / state / f"{task_id}.md"
        if candidate.is_file():
            return candidate
    return None
