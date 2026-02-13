#!/usr/bin/env python3
"""Detect # nosemgrep bypass comments in the codebase.

Semgrep cannot detect # nosemgrep comments because it respects them.
This script uses simple text search to find unauthorized bypasses.

Usage:
    python scripts/check_nosemgrep.py [path]
    python scripts/check_nosemgrep.py src/
    python scripts/check_nosemgrep.py  # defaults to src/ and tests/
"""

import re
import sys
from pathlib import Path

# Patterns to detect
BYPASS_PATTERNS = [
    (r"#\s*nosemgrep", "# nosemgrep - Semgrep bypass"),
    (r"#\s*noqa\s*$", "# noqa (blanket) - silences all warnings"),
    (r"#\s*type:\s*ignore\s*$", "# type: ignore (blanket) - silences all type errors"),
    (r"#\s*pylint:\s*disable\s*=\s*all", "# pylint: disable=all - blanket disable"),
]

# Files/paths to exclude from checking
EXCLUDE_PATTERNS = [
    r"\.git/",
    r"__pycache__/",
    r"\.pyc$",
    r"venv/",
    r"\.venv/",
    r"node_modules/",
    r"\.md$",  # Documentation can mention these patterns
    r"test_.*\.py$",  # Test files may use type: ignore intentionally
    r"conftest\.py$",  # Test config may use type: ignore
]


def should_exclude(path: Path) -> bool:
    """Check if path should be excluded."""
    path_str = str(path)
    return any(re.search(pattern, path_str) for pattern in EXCLUDE_PATTERNS)


def check_file(file_path: Path) -> list[tuple[int, str, str]]:
    """Check a file for bypass patterns.

    Returns list of (line_number, line_content, pattern_description).
    """
    violations = []

    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as e:
        raise RuntimeError(f"[X] Cannot read file {file_path}: {e}") from e
    except UnicodeDecodeError as e:
        raise RuntimeError(f"[X] Cannot decode file {file_path}: {e}") from e

    for line_num, line in enumerate(content.splitlines(), start=1):
        for pattern, description in BYPASS_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                violations.append((line_num, line.strip(), description))
                break  # Only report once per line

    return violations


def check_directory(dir_path: Path) -> dict[Path, list[tuple[int, str, str]]]:
    """Check all Python files in a directory."""
    results: dict[Path, list[tuple[int, str, str]]] = {}

    for file_path in dir_path.rglob("*.py"):
        if should_exclude(file_path):
            continue

        violations = check_file(file_path)
        if violations:
            results[file_path] = violations

    return results


def main() -> int:
    """Run the bypass detector."""
    # Determine paths to check
    if len(sys.argv) > 1:
        paths = [Path(arg) for arg in sys.argv[1:]]
    else:
        paths = [Path("src"), Path("tests")]

    print("=" * 70)
    print("BYPASS COMMENT DETECTOR")
    print("=" * 70)
    print()

    all_violations: dict[Path, list[tuple[int, str, str]]] = {}

    for path in paths:
        if not path.exists():
            print(f"[SKIP] Path does not exist: {path}")
            continue

        if path.is_file():
            violations = check_file(path)
            if violations:
                all_violations[path] = violations
        else:
            results = check_directory(path)
            all_violations.update(results)

    # Report results
    if not all_violations:
        print("[OK] No bypass comments detected")
        print()
        print("=" * 70)
        return 0

    total_violations = sum(len(v) for v in all_violations.values())
    print(f"[WARN] Found {total_violations} bypass comment(s) in {len(all_violations)} file(s):")
    print()

    for file_path, violations in sorted(all_violations.items()):
        print(f"  {file_path}:")
        for line_num, line_content, description in violations:
            print(f"    Line {line_num}: {description}")
            print(f"      {line_content[:60]}...")
        print()

    print("=" * 70)
    print()
    print("To fix:")
    print("  1. Remove the bypass comment")
    print("  2. Fix the underlying issue that triggered the warning")
    print("  3. If truly necessary, document in .github/sacred-files.yml")
    print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
