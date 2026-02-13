# AI Co-Development Template

A Python project template that implements the **Policy as Code** paradigm for AI-assisted development.

## Philosophy

This template embodies a development approach where:

- **Human** defines WHAT (specs, tests, contracts)
- **AI** implements HOW (code)
- **CI** verifies automatically (enforcement)

### Core Principles

| Principle | Description |
|-----------|-------------|
| **Fail Fast** | Errors must be visible immediately, not hidden |
| **Zero Silent Fallback** | No `.get(key, default)`, no `x or default` |
| **Zero Exception Swallowing** | No `except: pass`, no `except: return default` |
| **Policy as Code** | Rules are verified automatically by CI, not by human review |

### Enforcement Layers

| Layer | Tool | What it catches |
|-------|------|-----------------|
| Static Analysis | Semgrep | Silent fallback patterns in code |
| Type Checking | Mypy + beartype | Type errors at analysis and runtime |
| Architecture | ValidatedProcessor | Forces validation before processing |
| Testing | pytest fail-fast tests | Verifies functions raise on bad input |
| Custom Linter | check_fail_fast.py | Dict params without validation |

## Quick Start

### Option A: Automated Setup (Recommended)

```bash
# 1. Create from template on GitHub, then clone
git clone https://github.com/YOUR_USERNAME/my-project
cd my-project

# 2. Run initialization script
# Windows:
.\scripts\init_project.ps1

# Unix/macOS:
chmod +x scripts/*.sh
./scripts/init_project.sh

# 3. Give context to AI assistant
# In Cursor: @docs/ai_codev/AI_CONTEXT_FULL.md
```

The init script will:
- Create two virtual environments (`venv/` for project, `venv_policy/` for enforcement tools)
- Install project dependencies and policy tools separately
- Install pre-commit hooks (from `venv_policy/`)
- Lock governance files
- Validate the setup

### Option B: Manual Setup

<details>
<summary>Click to expand manual steps</summary>

#### 1. Clone this template

```bash
git clone https://github.com/YOUR_USERNAME/ai-codev-template my-project
cd my-project
rm -rf .git
git init
```

#### 2. Rename the project

Search and replace `project-name` with your project name in:
- `pyproject.toml` (line 2)

#### 3. Set up the environments

```bash
# Create virtual environments
python -m venv venv
python -m venv venv_policy

# Install project dependencies
venv/Scripts/pip install -r requirements.txt      # Windows
# venv/bin/pip install -r requirements.txt        # Unix

# Install policy tools
venv_policy/Scripts/pip install -r requirements-policy.txt  # Windows
# venv_policy/bin/pip install -r requirements-policy.txt    # Unix
```

#### 4. Install pre-commit hooks

```bash
venv_policy/Scripts/pre-commit install   # Windows
# venv_policy/bin/pre-commit install     # Unix
```

#### 5. Lock governance files

```bash
# Windows
.\scripts\lock-governance.ps1

# Unix/macOS
chmod +x scripts/*.sh
./scripts/lock-governance.sh
```

#### 6. Validate setup

```bash
python scripts/validate_setup.py
```

</details>

### (Optional) Setup GitHub branch protection

If you're using GitHub, configure branch protection to enforce the CI checks:

```bash
# Windows
.\scripts\setup-github.ps1

# Unix/macOS
chmod +x scripts/setup-github.sh
./scripts/setup-github.sh
```

Or configure manually in GitHub → Settings → Branches → Add rule:

| Setting | Value |
|---------|-------|
| Branch name pattern | `main` |
| Require status checks | ✅ Yes |
| Status checks required | `Quick (< 1 min)`, `Full (main only)`, `Sacred files` |
| Require branches up to date | ✅ Yes |
| Do not allow bypassing | ✅ Yes (even admins) |

## Project Structure

```
my-project/
├── .cursor/rules/           # AI guidance rules (Cursor IDE)
├── .github/
│   ├── workflows/           # CI/CD pipelines
│   ├── ISSUE_TEMPLATE/      # Issue templates
│   └── sacred-files.yml     # Protected files list
├── .semgrep/rules/          # Code quality rules
├── src/
│   ├── core/base/           # Abstract Base Classes (contracts)
│   ├── models/              # Pydantic data models
│   └── utils/               # Shared utilities
├── tests/
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── config/
│   ├── hardware.yaml        # GPU/CUDA/infra config
│   └── venvs.yaml           # Module-to-venv mapping
├── scripts/                 # Utility & enforcement scripts
└── docs/
    ├── ai_codev/            # AI co-development documentation
    └── architecture_suggestions/  # Proven architecture patterns
```

## Governance

### Sacred Files

Some files are protected and cannot be modified without explicit approval:

| Category | Files |
|----------|-------|
| Governance Rules | `.semgrep/rules/*`, `.cursor/rules/*` |
| Project Config | `pyproject.toml`, `tests/conftest.py` |
| Meta-Protection | `.github/workflows/*`, `.pre-commit-config.yaml` |

See `.github/sacred-files.yml` for the complete and authoritative list.

### Modifying Sacred Files

1. Run `scripts/unlock-governance.ps1` (Windows) or `scripts/unlock-governance.sh` (Unix)
2. Make your changes
3. Create a dedicated PR explaining the need
4. Run `scripts/lock-governance.ps1` or `scripts/lock-governance.sh`

## CI/CD

Three validation jobs run automatically:

| Job | Trigger | Duration | Checks |
|-----|---------|----------|--------|
| **Quick** | Every push | < 1 min | Ruff, Semgrep, Unit tests |
| **Full** | PR to main | < 5 min | All tests, Coverage report, Type check |
| **Sacred** | PR to main | < 30s | No sacred files modified |

## Pytest Markers

| Marker | Usage | Description |
|--------|-------|-------------|
| `@pytest.mark.fail_fast` | Required for validation tests | Tests that verify functions raise on invalid input |
| `@pytest.mark.slow` | Optional | Tests that take longer to run |
| `@pytest.mark.integration` | Optional | Integration tests |

```bash
# Run only fail-fast tests
pytest -m fail_fast

# Run everything except slow tests
pytest -m "not slow"
```

## Commands

```bash
# Run all tests (multi-venv, each module in its own venv)
python scripts/run_all_tests.py
python scripts/run_all_tests.py --module core    # Single module

# Run pre-commit hooks (static analysis from venv_policy)
python scripts/run_policy_tool.py pre-commit run --all-files

# Validate project setup
python scripts/validate_setup.py

# Lock/unlock governance files
.\scripts\lock-governance.ps1    # Windows
./scripts/lock-governance.sh     # Unix

# Setup GitHub branch protection
.\scripts\setup-github.ps1       # Windows
./scripts/setup-github.sh        # Unix
```

## AI Co-Development

### Starting a Session

1. Fill out `PROJECT_BRIEF.md` with your project vision
2. In Cursor chat: `@docs/ai_codev/AI_CONTEXT_FULL.md`
3. Then: `@PROJECT_BRIEF.md`
4. Let the AI ask clarifying questions before coding

### Refreshing Context (Long Conversations)

When the conversation gets long (10+ exchanges), the AI may "forget" the rules.

**In Cursor chat:**
```
/summarize
@docs/ai_codev/AI_REFRESH.md
```

This compresses the context and re-injects the critical rules at the end (where AI attention is highest).

### Key Rules for the AI

- **Never** use silent fallbacks (`.get(key, default)`)
- **Never** swallow exceptions (`except: pass`)
- **Always** validate inputs at the start of functions
- **Always** ask before modifying tests or contracts

### Documentation

- `docs/ai_codev/PHILOSOPHY.md` - Code rules
- `docs/ai_codev/WORKFLOW.md` - How to work together
- `docs/ai_codev/TESTING.md` - Testing strategy
- `docs/ai_codev/AI_CONTEXT_FULL.md` - Full context for AI
- `docs/ai_codev/AI_REFRESH.md` - Quick refresh after /summarize

### Architecture Suggestions

Proven architecture patterns to reference in your `PROJECT_BRIEF.md`:

- `docs/architecture_suggestions/DAG_PIPELINE.md` - DAG Pipeline with Nodes/Providers/Backends

## Examples

### StrictModel (Pydantic)

```python
from src.models.base import StrictModel

class UserConfig(StrictModel):
    name: str
    age: int

# Strict validation - no silent coercion
config = UserConfig(name="Alice", age=30)  # ✅ OK
config = UserConfig(name="Alice", age="30")  # ❌ ValidationError
```

### ValidatedProcessor (Architecture-enforced validation)

```python
from src.core.base.validated import ValidatedProcessor

class ImageProcessor(ValidatedProcessor[ImageInput, ImageOutput]):
    def validate(self, inputs: ImageInput) -> None:
        if not inputs.path.exists():
            raise ValueError(f"[X] Image not found: {inputs.path}")

    def process(self, inputs: ImageInput) -> ImageOutput:
        # Only called if validate() passes
        return transform(inputs)

# Usage: processor.run(inputs) → validates then processes
```

### Runtime Type Checking (beartype)

```python
from beartype import beartype

@beartype
def process(name: str, count: int) -> str:
    return name * count

process("hello", 3)     # ✅ OK
process("hello", "3")   # ❌ RuntimeError (not just mypy warning)
```

### Abstract Base Class (Contract)

```python
from src.core.base.example import Processor

class MyProcessor(Processor[InputData, OutputData]):
    @property
    def name(self) -> str:
        return "my_processor"

    def process(self, data: InputData) -> OutputData:
        # Validate first (fail-fast)
        if not data.is_valid:
            raise ValueError("[X] data.is_valid must be True")
        # Then process
        return OutputData(result=transform(data))
```

## License

All rights reserved.
