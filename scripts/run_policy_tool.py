#!/usr/bin/env python3
"""Cross-platform wrapper to run tools from venv_policy.

Used by pre-commit hooks to find and execute policy tools (semgrep, mypy, pytest, etc.)
regardless of the OS (Windows Scripts/ vs Unix bin/).

Usage:
    python scripts/run_policy_tool.py <tool> [args...]
    python scripts/run_policy_tool.py semgrep --config=.semgrep/rules/ src/
    python scripts/run_policy_tool.py python -m mypy src/
    python scripts/run_policy_tool.py python scripts/check_fail_fast.py src/
    python scripts/run_policy_tool.py python -m pytest tests/unit/ -q
"""

import subprocess
import sys
from pathlib import Path

POLICY_VENV = Path(__file__).parent.parent / "venv_policy"


def get_policy_bin_dir() -> Path:
    """Return the venv_policy bin/Scripts directory."""
    scripts_dir = POLICY_VENV / "Scripts"  # Windows
    if scripts_dir.exists():
        return scripts_dir
    bin_dir = POLICY_VENV / "bin"  # Unix
    if bin_dir.exists():
        return bin_dir
    raise FileNotFoundError(
        f"[X] Policy venv not found at {POLICY_VENV}. "
        "Run: .\\scripts\\init_project.ps1 (Windows) or ./scripts/init_project.sh (Unix)"
    )


def resolve_tool(name: str) -> str:
    """Resolve a tool name to its full path in venv_policy."""
    bin_dir = get_policy_bin_dir()

    # "python" → resolve to venv_policy's python
    if name == "python":
        for candidate in ["python.exe", "python3.exe", "python", "python3"]:
            path = bin_dir / candidate
            if path.exists():
                return str(path)
        raise FileNotFoundError(
            f"[X] Python not found in policy venv ({bin_dir})."
        )

    # Other tools: look for exact name and .exe variant
    exe = bin_dir / f"{name}.exe"
    if exe.exists():
        return str(exe)
    cmd = bin_dir / name
    if cmd.exists():
        return str(cmd)
    raise FileNotFoundError(
        f"[X] '{name}' not found in policy venv ({bin_dir}). "
        f"Run: venv_policy pip install {name}"
    )


def main() -> int:
    """Run a tool from venv_policy with the given arguments."""
    if len(sys.argv) < 2:
        print("[X] Usage: python scripts/run_policy_tool.py <tool> [args...]")
        return 1

    tool_name = sys.argv[1]
    tool_path = resolve_tool(tool_name)
    tool_args = sys.argv[2:]

    result = subprocess.run([tool_path, *tool_args])
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())

