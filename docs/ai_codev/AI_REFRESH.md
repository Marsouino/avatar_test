# CONTEXT REFRESH - APPLY IMMEDIATELY

After /summarize, these rules MUST be applied to ALL subsequent code.

## Critical Rules (BLOCKING)

1. **NO silent fallbacks**
   - `dict.get("k", default)` → `dict["k"]`
   - `x or default` → `if not x: raise`
   - `getattr(obj, "a", default)` → `obj.a`

2. **NO exception swallowing**
   - `except: pass` → `except SpecificError: raise`
   - `except: return default` → Let exception propagate

3. **Fail fast with clear errors**
   - Prefix: `[X]` for all error messages
   - Validate inputs at function start
   - Never mask errors

## Quick Reference

| Forbidden | Required |
|-----------|----------|
| `.get("k", val)` | `["k"]` after validation |
| `or "default"` | `raise ValueError("[X]...")` |
| `except: pass` | `except SpecificError as e: raise` |
| `getattr(o, "a", None)` | `o.a` after hasattr check |

**If unsure:** Ask "Is missing data a bug or expected?" Bug → fail fast.

## Pre-commit & Policy Enforcement

- **ALL hooks MUST pass** — no hook is optional. If semgrep, mypy, or any check fails, fix it.
- **NEVER modify enforcement scripts** (`scripts/check_*.py`, `scripts/validate_setup.py`) to bypass a violation. These are sacred files.
- **If a rule produces a false positive**, report it — do not add exceptions to the checker.
- Policy tools live in `venv_policy/` (isolated from project `venv/`).
- Run hooks manually: `python scripts/run_policy_tool.py pre-commit run --all-files`

## Infrastructure

- **BEFORE any install, ML, or infra work** → read `config/hardware.yaml`
- Contains: GPU/CUDA versions, PyTorch install commands, container images, network, storage paths
- One source of truth per environment (local, production, etc.)