#!/usr/bin/env python3
"""Custom linter for fail-fast patterns.

Detects patterns that Semgrep doesn't catch well:
- Functions with dict parameters but no validation
- Functions with too many default parameters
- Public functions without any raise statements

Usage:
    python scripts/check_fail_fast.py src/
    python scripts/check_fail_fast.py src/core/module.py
"""

import ast
import sys
from pathlib import Path


class FailFastChecker(ast.NodeVisitor):
    """AST visitor that checks for fail-fast violations."""

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.violations: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        """Check function definitions for fail-fast patterns."""
        # Skip private/magic methods
        if node.name.startswith("_"):
            self.generic_visit(node)
            return

        # Skip test functions
        if node.name.startswith("test"):
            self.generic_visit(node)
            return

        # Check 1: Too many defaults (more than 50% of params have defaults)
        self._check_excessive_defaults(node)

        # Check 2: Dict parameter without validation
        self._check_dict_without_validation(node)

        # Check 3: No validation at all (no raise in function)
        self._check_has_validation(node)

        self.generic_visit(node)

    def _check_excessive_defaults(self, node: ast.FunctionDef) -> None:
        """Warn if more than 50% of parameters have defaults.

        Exception: single optional parameter with `| None = None` is a valid
        API pattern (e.g. `def run(self, ctx: X | None = None)`). This is not
        a sign of lax defaults — it's explicit optionality.
        """
        args = node.args
        total_params = len(args.args) + len(args.posonlyargs) + len(args.kwonlyargs)

        # Skip if no params or just self
        if total_params <= 1:
            return

        # Count defaults
        num_defaults = len(args.defaults) + len(args.kw_defaults)
        # kw_defaults can have None for params without defaults
        num_defaults = sum(1 for d in args.kw_defaults if d is not None) + len(args.defaults)

        # Exclude 'self' from count
        effective_params = total_params
        if args.args and args.args[0].arg == "self":
            effective_params -= 1

        # Skip: single param with | None = None (valid optional API pattern)
        if effective_params == 1 and num_defaults == 1:
            param = args.args[-1] if args.args else None
            if param and param.annotation:
                ann_str = ast.unparse(param.annotation)
                if "None" in ann_str:
                    return

        if effective_params > 0 and num_defaults / effective_params > 0.5:
            self.violations.append(
                f"{self.filename}:{node.lineno}: "
                f"[!] Function '{node.name}' has {num_defaults}/{effective_params} "
                f"parameters with defaults (>50%). Consider making some required."
            )

    def _check_dict_without_validation(self, node: ast.FunctionDef) -> None:
        """Warn if function takes dict but doesn't validate it."""
        # Check if any parameter is annotated as dict
        has_dict_param = False
        for arg in node.args.args:
            if arg.annotation:
                ann_str = ast.unparse(arg.annotation)
                if "dict" in ann_str.lower():
                    has_dict_param = True
                    break

        if not has_dict_param:
            return

        # Check if function body has validation (raise or 'not in')
        has_validation = False
        for child in ast.walk(node):
            if isinstance(child, ast.Raise):
                has_validation = True
                break
            if isinstance(child, ast.Compare):
                for op in child.ops:
                    if isinstance(op, ast.NotIn | ast.In):
                        has_validation = True
                        break

        if not has_validation:
            self.violations.append(
                f"{self.filename}:{node.lineno}: "
                f"[!] Function '{node.name}' takes dict but has no validation. "
                f"Add: if 'key' not in dict: raise ValueError(...)"
            )

    def _check_has_validation(self, node: ast.FunctionDef) -> None:
        """Info if public function has no raise statements at all.

        Currently disabled - uncomment to enable this check.
        """
        # Only check functions with >3 lines of body
        if len(node.body) <= 3:
            return

        # Disabled: This is informational only, not enforced
        # To enable, uncomment:
        #
        # has_raise = False
        # for child in ast.walk(node):
        #     if isinstance(child, ast.Raise):
        #         has_raise = True
        #         break
        # if not has_raise:
        #     self.violations.append(
        #         f"{self.filename}:{node.lineno}: "
        #         f"[?] Function '{node.name}' has no raise statements."
        #     )
        pass


def check_file(filepath: Path) -> list[str]:
    """Check a single Python file for violations."""
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError as e:
        return [f"{filepath}: [X] Syntax error: {e}"]

    checker = FailFastChecker(str(filepath))
    checker.visit(tree)
    return checker.violations


def check_path(path: Path) -> list[str]:
    """Check a file or directory recursively."""
    violations: list[str] = []

    if path.is_file():
        if path.suffix == ".py":
            violations.extend(check_file(path))
    elif path.is_dir():
        for pyfile in path.rglob("*.py"):
            # Skip test files
            if "test" in pyfile.name or "conftest" in pyfile.name:
                continue
            violations.extend(check_file(pyfile))

    return violations


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python check_fail_fast.py <path> [path2] ...")
        print("       python check_fail_fast.py src/")
        return 1

    all_violations: list[str] = []

    for arg in sys.argv[1:]:
        path = Path(arg)
        if not path.exists():
            print(f"[X] Path not found: {path}")
            return 1
        all_violations.extend(check_path(path))

    if all_violations:
        print("Fail-fast pattern violations found:\n")
        for v in all_violations:
            print(f"  {v}")
        print(f"\nTotal: {len(all_violations)} violation(s)")
        return 1
    else:
        print("[OK] No fail-fast violations found")
        return 0


if __name__ == "__main__":
    sys.exit(main())
