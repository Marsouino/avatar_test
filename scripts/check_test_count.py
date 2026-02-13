#!/usr/bin/env python3
"""Test count ratchet — policy as code.

Ensures the number of tests never decreases between commits.
Detects silent test removal (e.g. LLM deleting tests to make things pass).

Counts tests via AST parsing (def test_*), NOT pytest --collect-only.
This makes it independent of any project venv — runs from venv_policy.

Usage:
    python scripts/check_test_count.py              # Check against baseline
    python scripts/check_test_count.py --update      # Force-update baseline (explicit reset)

Baseline file: tests/.test_count_baseline
"""

import ast
import sys
from pathlib import Path

BASELINE_FILE = Path("tests/.test_count_baseline")
TESTS_DIR = Path("tests")


def count_tests_in_file(filepath: Path) -> int:
    """Count test functions (def test_*) in a Python file via AST."""
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError:
        # File has syntax errors — don't count, don't crash
        # (semgrep/ruff will catch syntax errors separately)
        return 0

    count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith("test_"):
            count += 1
    return count


def count_all_tests() -> int:
    """Count all test functions across all test files."""
    if not TESTS_DIR.exists():
        return 0

    total = 0
    for pyfile in TESTS_DIR.rglob("test_*.py"):
        total += count_tests_in_file(pyfile)
    return total


def read_baseline() -> int:
    """Read baseline count. Returns 0 if no baseline exists yet."""
    if not BASELINE_FILE.exists():
        return 0
    content = BASELINE_FILE.read_text(encoding="utf-8").strip()
    if not content:
        return 0
    if not content.isdigit():
        raise RuntimeError(
            f"[X] Invalid baseline file content: '{content}'. Expected a number."
        )
    return int(content)


def write_baseline(count: int) -> None:
    """Write the baseline file."""
    BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_FILE.write_text(f"{count}\n", encoding="utf-8")


def main() -> int:
    """Main entry point."""
    force_update = "--update" in sys.argv

    current_count = count_all_tests()
    baseline = read_baseline()

    if force_update:
        write_baseline(current_count)
        print(f"[OK] Baseline updated: {baseline} -> {current_count}")
        return 0

    if current_count < baseline:
        print(
            f"[X] Test count regression detected!\n"
            f"    Baseline: {baseline} tests\n"
            f"    Current:  {current_count} tests\n"
            f"    Delta:    {current_count - baseline}\n"
            f"\n"
            f"    If this is intentional (refactoring, test consolidation),\n"
            f"    update the baseline explicitly:\n"
            f"        python scripts/check_test_count.py --update"
        )
        return 1

    if current_count > baseline:
        write_baseline(current_count)
        print(f"[OK] Test count increased: {baseline} -> {current_count} (baseline updated)")
        return 0

    print(f"[OK] Test count stable: {current_count} tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
