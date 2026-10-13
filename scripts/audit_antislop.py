"""Reject U+2013 and U+2014 in tracked project text and source files."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".git", ".venv", "node_modules", "__pycache__", "dist", "build"}
SCOPED_ROOTS = ("src", "web", "docs", "specs", "tests", "scripts")
FORBIDDEN = {"\u2013", "\u2014"}


def main() -> int:
    violations: list[str] = []
    scoped_paths = [root for name in SCOPED_ROOTS if (root := ROOT / name).exists()]
    for path in (item for root in scoped_paths for item in root.rglob("*")):
        if not path.is_file() or any(part in EXCLUDED for part in path.relative_to(ROOT).parts):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_number, line in enumerate(content.splitlines(), start=1):
            if any(char in line for char in FORBIDDEN):
                violations.append(f"{path.relative_to(ROOT)}:{line_number}")
    if violations:
        print("Caracteres U+2013/U+2014 encontrados:")
        print("\n".join(violations))
        return 1
    print("Politica Antislop U+2013/U+2014: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
