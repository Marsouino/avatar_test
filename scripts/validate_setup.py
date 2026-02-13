#!/usr/bin/env python3
"""Validate that the project is correctly configured.

Run this after cloning the template to ensure everything is set up properly.
Can be called from any Python — resolves venv paths explicitly.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

SACRED_FILES_PATH = Path(".github/sacred-files.yml")


def find_venv_bin(project_root: Path, venv_name: str) -> Path:
    """Return the bin/Scripts directory for a named venv."""
    venv_root = project_root / venv_name
    if not venv_root.exists():
        raise FileNotFoundError(
            f"[X] Venv '{venv_name}' not found at {venv_root}. "
            "Run init_project to create it."
        )
    scripts_dir = venv_root / "Scripts"  # Windows
    if scripts_dir.exists():
        return scripts_dir
    bin_dir = venv_root / "bin"  # Unix
    if bin_dir.exists():
        return bin_dir
    raise FileNotFoundError(
        f"[X] No bin/Scripts directory in {venv_root}."
    )


def venv_cmd(project_root: Path, venv_name: str, tool: str) -> str:
    """Resolve a tool to its full path inside a specific venv."""
    bin_dir = find_venv_bin(project_root, venv_name)
    # Windows: look for .exe
    exe = bin_dir / f"{tool}.exe"
    if exe.exists():
        return str(exe)
    # Unix: no extension
    cmd = bin_dir / tool
    if cmd.exists():
        return str(cmd)
    raise FileNotFoundError(
        f"[X] '{tool}' not found in {venv_name} ({bin_dir}). "
        f"Run: {venv_name}/pip install {tool}"
    )


def run_command(cmd: list[str], capture: bool = True) -> tuple[int, str]:
    """Run a command and return (exit_code, output)."""
    result = subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
    )
    if not capture:
        return result.returncode, ""
    output = result.stdout + result.stderr
    return result.returncode, output


def load_sacred_files(project_root: Path) -> list[str]:
    """Load sacred file paths from .github/sacred-files.yml.

    Parses lines matching '  - path/to/file' (with optional # comment).
    No PyYAML dependency needed — format is simple and stable.
    """
    sacred_path = project_root / SACRED_FILES_PATH
    if not sacred_path.exists():
        raise FileNotFoundError(
            f"[X] Sacred files list not found: {sacred_path}. "
            "This file is required for governance enforcement."
        )
    content = sacred_path.read_text(encoding="utf-8")
    # Match YAML list items: "  - path/to/file" with optional "# comment"
    pattern = re.compile(r"^\s+-\s+([^\s#]+)", re.MULTILINE)
    files = pattern.findall(content)
    if not files:
        raise RuntimeError(
            f"[X] No sacred files found in {sacred_path}. File may be malformed."
        )
    return files


def check_mark(passed: bool) -> str:
    """Return a check mark or X."""
    return "[OK]" if passed else "[FAIL]"


def main() -> int:
    """Run all validation checks."""
    project_root = Path(__file__).parent.parent
    checks_passed = 0
    checks_failed = 0

    print("=" * 60)
    print("PROJECT SETUP VALIDATION")
    print("=" * 60)
    print()

    # 1a. Check both venvs exist
    print("Checking virtual environments...")
    venv_exists = (project_root / "venv").exists()
    venv_policy_exists = (project_root / "venv_policy").exists()
    print(f"  {check_mark(venv_exists)} Project venv (venv/)")
    print(f"  {check_mark(venv_policy_exists)} Policy venv (venv_policy/)")
    if venv_exists and venv_policy_exists:
        checks_passed += 1
    else:
        checks_failed += 1
        print("    -> Run: .\\scripts\\init_project.ps1 (Windows) or ./scripts/init_project.sh (Unix)")

    # 1b. Check pre-commit hooks installed
    print("\nChecking pre-commit hooks...")
    hooks_dir = project_root / ".git" / "hooks" / "pre-commit"
    hooks_installed = hooks_dir.exists()
    print(f"  {check_mark(hooks_installed)} Pre-commit hooks installed")
    if hooks_installed:
        checks_passed += 1
    else:
        checks_failed += 1
        print("    -> Run: pre-commit install (from venv_policy)")

    # 2. Check sacred files are locked (read-only)
    print("\nChecking sacred files permissions...")
    sacred_files = load_sacred_files(project_root)
    all_locked = True
    for file in sacred_files:
        path = project_root / file
        if path.exists():
            is_locked = not os.access(path, os.W_OK)
            if not is_locked:
                all_locked = False
                print(f"  [WARN] {file} is NOT locked")

    if all_locked:
        print(f"  {check_mark(True)} Sacred files are locked")
        checks_passed += 1
    else:
        print(f"  {check_mark(False)} Some sacred files are not locked")
        print(
            "    -> Run: scripts/lock-governance.ps1 (Windows) or scripts/lock-governance.sh (Unix)"
        )
        checks_failed += 1

    # 3. Check Semgrep rules are valid (venv_policy)
    print("\nChecking Semgrep rules...")
    code, output = run_command(
        [venv_cmd(project_root, "venv_policy", "semgrep"),
         "--validate", "--config", ".semgrep/rules/"]
    )
    semgrep_valid = code == 0
    print(f"  {check_mark(semgrep_valid)} Semgrep rules are valid")
    if not semgrep_valid:
        checks_failed += 1
        print(f"    -> Error: {output[:200]}")
    else:
        checks_passed += 1

    # 4. Check tests pass (venv — project deps + pytest)
    print("\nRunning tests...")
    code, output = run_command(
        [venv_cmd(project_root, "venv", "pytest"), "tests/", "-q", "--tb=no"]
    )
    tests_pass = code == 0
    if tests_pass:
        lines = output.strip().split("\n")
        if not lines:
            raise RuntimeError("[X] pytest produced no output")
        print(f"  {check_mark(True)} Tests pass ({lines[-1]})")
        checks_passed += 1
    else:
        print(f"  {check_mark(False)} Tests fail")
        print("    -> Run: pytest tests/ -v")
        checks_failed += 1

    # 5. Check coverage (venv — reporting only, no gate)
    print("\nChecking test coverage...")
    code, output = run_command(
        [venv_cmd(project_root, "venv", "pytest"),
         "tests/", "--cov=src", "--cov-report=term-missing", "-q", "--tb=no"]
    )
    if code == 0:
        print(f"  {check_mark(True)} Coverage report generated")
        checks_passed += 1
    else:
        print(f"  {check_mark(False)} Coverage report failed")
        checks_failed += 1

    # 6. Check Ruff (venv_policy)
    print("\nChecking code style...")
    code, _ = run_command(
        [venv_cmd(project_root, "venv_policy", "ruff"),
         "check", "src/", "tests/", "--quiet"]
    )
    ruff_ok = code == 0
    print(f"  {check_mark(ruff_ok)} Ruff check passes")
    if ruff_ok:
        checks_passed += 1
    else:
        checks_failed += 1
        print("    -> Run: ruff check --fix .")

    # Summary
    print()
    print("=" * 60)
    total = checks_passed + checks_failed
    if checks_failed == 0:
        print(f"RESULT: ALL CHECKS PASSED ({checks_passed}/{total})")
    else:
        print(f"RESULT: {checks_failed} CHECK(S) FAILED ({checks_passed}/{total})")
    print("=" * 60)

    return 0 if checks_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
