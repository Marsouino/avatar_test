#!/usr/bin/env python3
"""Multi-venv test runner.

Reads config/venvs.yaml and runs pytest in each module's venv.
Each module is tested in isolation — no single venv needs all deps.

Usage:
    python scripts/run_all_tests.py                  # Run all modules
    python scripts/run_all_tests.py --module core     # Run one module
    python scripts/run_all_tests.py --module pose     # Run one module
    python scripts/run_all_tests.py --verbose         # Show pytest output

Config: config/venvs.yaml
"""

import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
VENVS_CONFIG = PROJECT_ROOT / "config" / "venvs.yaml"


def parse_venvs_config() -> dict[str, dict[str, str]]:
    """Parse config/venvs.yaml without PyYAML.

    Extracts module entries under 'modules:' section.
    Each module has: venv, requirements, tests.
    """
    if not VENVS_CONFIG.exists():
        raise FileNotFoundError(
            f"[X] Venvs config not found: {VENVS_CONFIG}. "
            "This file is required for multi-venv testing."
        )

    content = VENVS_CONFIG.read_text(encoding="utf-8")
    modules: dict[str, dict[str, str]] = {}

    # Simple YAML parser for our specific format
    current_module: str | None = None
    in_modules_section = False

    for line in content.splitlines():
        stripped = line.strip()

        # Skip comments and empty lines
        if not stripped or stripped.startswith("#"):
            continue

        # Detect sections
        if stripped == "modules:":
            in_modules_section = True
            continue
        elif not line.startswith(" ") and not line.startswith("\t"):
            # New top-level key — exit modules section
            in_modules_section = False
            current_module = None
            continue

        if not in_modules_section:
            continue

        # Module name (2-space indent, ends with :)
        module_match = re.match(r"^  (\w+):$", line)
        if module_match:
            current_module = module_match.group(1)
            modules[current_module] = {}
            continue

        # Module property (4-space indent)
        if current_module:
            prop_match = re.match(r"^    (\w+):\s*(.+)$", line)
            if prop_match:
                key = prop_match.group(1)
                value = prop_match.group(2).strip().strip('"').strip("'")
                # Skip comments after value
                if "#" in value:
                    value = value[:value.index("#")].strip()
                modules[current_module][key] = value

    return modules


def resolve_python(venv_name: str) -> Path:
    """Find the Python executable in a venv."""
    venv_path = PROJECT_ROOT / venv_name

    # Windows
    python_exe = venv_path / "Scripts" / "python.exe"
    if python_exe.exists():
        return python_exe

    # Unix
    python_bin = venv_path / "bin" / "python"
    if python_bin.exists():
        return python_bin

    raise FileNotFoundError(
        f"[X] Python not found in venv '{venv_name}' ({venv_path}). "
        f"Run init_project to create it, or install manually."
    )


def run_tool_in_venv(
    python: Path,
    cmd_args: list[str],
    verbose: bool = False,
) -> tuple[bool, str]:
    """Run a command via a venv's Python. Returns (passed, output)."""
    cmd = [str(python), *cmd_args]
    result = subprocess.run(
        cmd,
        capture_output=not verbose,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    output = ""
    if not verbose and result.stdout:
        output = result.stdout.strip()
    return result.returncode == 0, output


def run_module_checks(
    module_name: str,
    module_config: dict[str, str],
    verbose: bool = False,
) -> list[tuple[bool, str]]:
    """Run pytest + mypy for a single module in its venv."""
    venv_name = module_config.get("venv")
    tests_dir = module_config.get("tests")

    if not venv_name:
        raise RuntimeError(f"[X] Module '{module_name}' has no 'venv' defined in config.")
    if not tests_dir:
        raise RuntimeError(f"[X] Module '{module_name}' has no 'tests' defined in config.")

    tests_path = PROJECT_ROOT / tests_dir
    if not tests_path.exists():
        return [(True, f"[SKIP] {module_name}: tests dir '{tests_dir}' not found")]

    python = resolve_python(venv_name)
    results: list[tuple[bool, str]] = []

    # 1. pytest
    pytest_args = ["-m", "pytest", str(tests_path), "-q", "--tb=short"]
    if verbose:
        pytest_args.append("-v")
    passed, output = run_tool_in_venv(python, pytest_args, verbose)
    if passed:
        summary = f" ({output.splitlines()[-1]})" if output else ""
        results.append((True, f"[OK] {module_name} pytest{summary}"))
    else:
        error_info = f"\n{output}" if output else ""
        results.append((False, f"[FAIL] {module_name} pytest{error_info}"))

    # 2. mypy
    mypy_args = ["-m", "mypy", "src/", str(tests_path), "--config-file", "pyproject.toml"]
    passed, output = run_tool_in_venv(python, mypy_args, verbose)
    if passed:
        results.append((True, f"[OK] {module_name} mypy"))
    else:
        error_info = f"\n{output}" if output else ""
        results.append((False, f"[FAIL] {module_name} mypy{error_info}"))

    return results


def main() -> int:
    """Main entry point."""
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    # Parse --module filter
    target_module: str | None = None
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--module" and i + 1 <= len(sys.argv) - 1:
            target_module = sys.argv[i + 1]

    modules = parse_venvs_config()
    if not modules:
        raise RuntimeError("[X] No modules found in config/venvs.yaml.")

    if target_module:
        if target_module not in modules:
            print(f"[X] Module '{target_module}' not found. Available: {', '.join(modules)}")
            return 1
        modules = {target_module: modules[target_module]}

    print("=" * 60)
    print("MULTI-VENV TEST RUNNER (pytest + mypy)")
    print("=" * 60)
    print()

    total_passed = 0
    total_failed = 0
    all_results: list[str] = []

    for module_name, module_config in modules.items():
        check_results = run_module_checks(module_name, module_config, verbose)
        for passed, message in check_results:
            all_results.append(message)
            if passed:
                total_passed += 1
            else:
                total_failed += 1

    # Summary
    print()
    for r in all_results:
        print(f"  {r}")

    print()
    print("=" * 60)
    total = total_passed + total_failed
    if total_failed == 0:
        print(f"RESULT: ALL CHECKS PASSED ({total_passed}/{total})")
    else:
        print(f"RESULT: {total_failed} CHECK(S) FAILED ({total_passed}/{total})")
    print("=" * 60)

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

