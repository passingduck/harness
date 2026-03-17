from pathlib import Path


def iter_template_files(root: Path) -> list[Path]:
    return sorted(
        [path for path in root.rglob("*") if path.is_file()],
        key=lambda path: path.relative_to(root).as_posix(),
    )


def iter_skill_files(root: Path) -> list[Path]:
    return iter_template_files(root)


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def render_text(template: str, project_name: str) -> str:
    return template.replace("{{project_name}}", project_name)
