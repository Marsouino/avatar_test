#!/usr/bin/env python3
"""Test that Semgrep rules detect all expected violations.

This script creates temporary Python files with known violations,
runs Semgrep against them, and verifies that each violation is detected.

It does NOT verify which specific rule matched — only that the pattern
is blocked. This is intentional: if the pattern is blocked, it's blocked,
regardless of which rule caught it.

Usage:
    python scripts/test_policy.py

Exit codes:
    0 - All violations detected (PASS)
    1 - Some violations not detected (FAIL)
"""

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple


class Violation(NamedTuple):
    """A code violation that should be detected by Semgrep."""

    name: str
    code: str
    description: str


# =============================================================================
# ALL VIOLATIONS TO TEST
# =============================================================================

VIOLATIONS: list[Violation] = [
    # =========================================================================
    # Silent fallback with dict.get()
    # =========================================================================
    Violation(
        name="dict_get_simple",
        code="""
def load():
    config = {"a": 1}
    return config.get("key", "default")
""",
        description="Basic dict.get() with default",
    ),
    Violation(
        name="dict_get_numeric",
        code="""
def load():
    params = {}
    timeout = params.get("timeout", 30)
    return timeout
""",
        description="dict.get() with numeric default",
    ),
    Violation(
        name="dict_get_none",
        code="""
def load():
    data = {}
    value = data.get("key", None)
    return value
""",
        description="dict.get() with None default",
    ),
    Violation(
        name="dict_get_empty_string",
        code="""
def load():
    config = {}
    name = config.get("name", "")
    return name
""",
        description="dict.get() with empty string default",
    ),
    Violation(
        name="dict_get_empty_list",
        code="""
def load():
    config = {}
    items = config.get("items", [])
    return items
""",
        description="dict.get() with empty list default",
    ),
    Violation(
        name="dict_get_empty_dict",
        code="""
def load():
    config = {}
    nested = config.get("nested", {})
    return nested
""",
        description="dict.get() with empty dict default",
    ),
    Violation(
        name="dict_get_false",
        code="""
def load():
    config = {}
    enabled = config.get("enabled", False)
    return enabled
""",
        description="dict.get() with False default",
    ),
    Violation(
        name="dict_get_chained",
        code="""
def load():
    config = {"nested": {}}
    value = config.get("nested", {}).get("key", "default")
    return value
""",
        description="Chained dict.get() calls",
    ),
    # =========================================================================
    # Silent fallback with `or`
    # =========================================================================
    Violation(
        name="or_string",
        code="""
def process(name):
    return name or "anonymous"
""",
        description="or with string fallback",
    ),
    Violation(
        name="or_numeric",
        code="""
def process(count):
    return count or 0
""",
        description="or with numeric fallback",
    ),
    Violation(
        name="or_list",
        code="""
def process(items):
    return items or []
""",
        description="or with list fallback",
    ),
    Violation(
        name="or_dict",
        code="""
def process(config):
    return config or {}
""",
        description="or with dict fallback",
    ),
    Violation(
        name="or_assignment",
        code="""
def process(value):
    result = value or "default"
    return result
""",
        description="or fallback in assignment",
    ),
    Violation(
        name="or_in_return",
        code="""
def get_name(user):
    return user.name or "Unknown"
""",
        description="or fallback with attribute access",
    ),
    # =========================================================================
    # Silent fallback with getattr()
    # =========================================================================
    Violation(
        name="getattr_string",
        code="""
def get_value(obj):
    return getattr(obj, "attr", "default")
""",
        description="getattr with string default",
    ),
    Violation(
        name="getattr_none",
        code="""
def get_value(obj):
    return getattr(obj, "attr", None)
""",
        description="getattr with None default",
    ),
    Violation(
        name="getattr_numeric",
        code="""
def get_value(obj):
    return getattr(obj, "count", 0)
""",
        description="getattr with numeric default",
    ),
    Violation(
        name="getattr_callable",
        code="""
def get_method(obj):
    return getattr(obj, "method", lambda: None)
""",
        description="getattr with callable default",
    ),
    # =========================================================================
    # Bare except - Catching all exceptions
    # =========================================================================
    Violation(
        name="bare_except_pass",
        code="""
def risky():
    try:
        something()
    except:
        pass
""",
        description="Bare except with pass",
    ),
    Violation(
        name="bare_except_return",
        code="""
def risky():
    try:
        return load()
    except:
        return None
""",
        description="Bare except with return",
    ),
    Violation(
        name="bare_except_log",
        code="""
def risky():
    try:
        process()
    except:
        print("error")
""",
        description="Bare except with print",
    ),
    # =========================================================================
    # Broad except with pass - Catching Exception and ignoring
    # =========================================================================
    Violation(
        name="exception_pass",
        code="""
def risky():
    try:
        x = 1
        y = 2
    except Exception:
        pass
""",
        description="except Exception with pass",
    ),
    Violation(
        name="exception_as_pass",
        code="""
def risky():
    try:
        x = 1
        y = 2
    except Exception as e:
        pass
""",
        description="except Exception as e with pass",
    ),
    # =========================================================================
    # Except returning default values
    # =========================================================================
    Violation(
        name="except_return_none",
        code="""
def load():
    try:
        return read_file()
    except Exception:
        return None
""",
        description="except returning None",
    ),
    Violation(
        name="except_return_empty_string",
        code="""
def load():
    try:
        return read_file()
    except Exception:
        return ""
""",
        description="except returning empty string",
    ),
    Violation(
        name="except_return_empty_list",
        code="""
def load():
    try:
        return read_items()
    except Exception:
        return []
""",
        description="except returning empty list",
    ),
    Violation(
        name="except_return_empty_dict",
        code="""
def load():
    try:
        return read_config()
    except Exception:
        return {}
""",
        description="except returning empty dict",
    ),
    Violation(
        name="except_return_zero",
        code="""
def load():
    try:
        return get_count()
    except Exception:
        return 0
""",
        description="except returning zero",
    ),
    Violation(
        name="except_return_false",
        code="""
def check():
    try:
        return validate()
    except Exception:
        return False
""",
        description="except returning False",
    ),
    # =========================================================================
    # Star imports
    # =========================================================================
    Violation(
        name="star_import",
        code="""
from os import *

def test():
    pass
""",
        description="Basic star import",
    ),
    Violation(
        name="star_import_module",
        code="""
from pathlib import *

path = Path(".")
""",
        description="Star import from pathlib",
    ),
    # =========================================================================
    # Legacy naming patterns
    # =========================================================================
    Violation(
        name="legacy_function",
        code="""
def process_legacy():
    pass
""",
        description="Function with 'legacy' in name",
    ),
    Violation(
        name="old_class",
        code="""
class OldHandler:
    pass
""",
        description="Class with 'Old' prefix",
    ),
    Violation(
        name="deprecated_function",
        code="""
def deprecated_handler():
    pass
""",
        description="Function with 'deprecated' in name",
    ),
    Violation(
        name="v1_function",
        code="""
def get_data_v1():
    pass
""",
        description="Function with version suffix",
    ),
    # =========================================================================
    # hasattr with else fallback
    # =========================================================================
    Violation(
        name="hasattr_ternary",
        code="""
def get_value(obj):
    return obj.attr if hasattr(obj, "attr") else "default"
""",
        description="hasattr in ternary with fallback",
    ),
    # =========================================================================
    # Anti-bypass rules - Detect attempts to silence warnings
    # =========================================================================
    Violation(
        name="noqa_on_dict_get",
        code="""
def load():
    x = config.get("key", "default")  # noqa
    return x
""",
        description="# noqa on .get() - suspicious bypass",
    ),
    Violation(
        name="noqa_on_or_fallback",
        code="""
def load(x):
    return x or "default"  # noqa
""",
        description="# noqa on 'or' fallback - suspicious bypass",
    ),
    Violation(
        name="noqa_on_getattr",
        code="""
def load(obj):
    return getattr(obj, "x", None)  # noqa
""",
        description="# noqa on getattr - suspicious bypass",
    ),
    Violation(
        name="noqa_on_except",
        code="""
def load():
    try:
        x = 1
    except Exception:  # noqa
        pass
""",
        description="# noqa on except - suspicious bypass",
    ),
    # NOTE: # nosemgrep cannot be detected BY Semgrep (it respects the directive).
    # Use scripts/check_nosemgrep.py (now a pre-commit hook) to detect these.
    Violation(
        name="blanket_noqa",
        code="""
def load():
    x = some_long_line_that_exceeds_limit_and_has_issues()  # noqa
    return x
""",
        description="Blanket # noqa without specific codes",
    ),
]


# =============================================================================
# TEST RUNNER
# =============================================================================


def find_semgrep() -> str:
    """Resolve semgrep executable from venv_policy."""
    project_root = Path(__file__).parent.parent
    for subdir in ["Scripts", "bin"]:
        for name in ["semgrep.exe", "semgrep"]:
            path = project_root / "venv_policy" / subdir / name
            if path.exists():
                return str(path)
    raise FileNotFoundError(
        "[X] semgrep not found in venv_policy. "
        "Run init_project to install policy tools."
    )


def run_semgrep(file_path: Path) -> tuple[int, str]:
    """Run Semgrep on a file and return (exit_code, output)."""
    result = subprocess.run(
        [
            find_semgrep(),
            "--config=.semgrep/rules/",
            str(file_path),
            "--error",
            "--quiet",
            "--metrics=off",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    stdout = result.stdout if result.stdout else ""
    stderr = result.stderr if result.stderr else ""
    return result.returncode, stdout + stderr


def test_violation(violation: Violation, temp_dir: Path) -> bool:
    """Test that a violation is detected by Semgrep.

    Returns True if violation was detected (PASS), False otherwise (FAIL).
    """
    # Create temp file - NOT named test_*.py to avoid exclusion rules
    file_path = temp_dir / f"check_{violation.name}.py"
    file_path.write_text(violation.code, encoding="utf-8")

    # Run Semgrep
    exit_code, output = run_semgrep(file_path)

    # Violation detected if exit_code != 0
    detected = exit_code != 0

    return detected


def main() -> int:
    """Run all policy tests."""
    print("=" * 70)
    print("POLICY AS CODE - VIOLATION DETECTION TESTS")
    print("=" * 70)
    print()

    passed = 0
    failed = 0
    failed_violations: list[Violation] = []

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        for violation in VIOLATIONS:
            detected = test_violation(violation, temp_path)

            if detected:
                print(f"  [OK] {violation.name}: {violation.description}")
                passed += 1
            else:
                print(f"  [FAIL] {violation.name}: {violation.description}")
                print("         NOT DETECTED!")
                failed += 1
                failed_violations.append(violation)

    # Summary
    print()
    print("=" * 70)
    total = passed + failed

    if failed == 0:
        print(f"RESULT: ALL {total} VIOLATIONS DETECTED")
        print("=" * 70)
        return 0
    else:
        print(f"RESULT: {failed}/{total} VIOLATIONS NOT DETECTED")
        print()
        print("Failed violations:")
        for v in failed_violations:
            print(f"  - {v.name}")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
