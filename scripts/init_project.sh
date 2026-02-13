#!/bin/bash
# Initialize Project from Template
# =================================
# Run this script after cloning/creating from template.
# It sets up TWO virtual environments:
#   - venv/        : project dependencies (ML libs, etc.)
#   - venv_policy/ : policy-as-code tools (semgrep, ruff, mypy, pytest, pre-commit)
#
# Usage: ./scripts/init_project.sh

set -e

echo "============================================================"
echo "  AI Co-Development Template - Project Initialization"
echo "============================================================"
echo ""

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Step 1: Create project virtual environment
echo "[1/7] Creating project virtual environment (venv/)..."
if [ -d "$PROJECT_ROOT/venv" ]; then
    echo "  [SKIP] venv/ already exists"
else
    python3 -m venv "$PROJECT_ROOT/venv"
    echo "  [OK] venv/ created"
fi

# Step 2: Create policy virtual environment
echo ""
echo "[2/7] Creating policy virtual environment (venv_policy/)..."
if [ -d "$PROJECT_ROOT/venv_policy" ]; then
    echo "  [SKIP] venv_policy/ already exists"
else
    python3 -m venv "$PROJECT_ROOT/venv_policy"
    echo "  [OK] venv_policy/ created"
fi

# Step 3: Install project dependencies
echo ""
echo "[3/7] Installing project dependencies (venv/)..."
"$PROJECT_ROOT/venv/bin/python" -m pip install -q --upgrade pip
"$PROJECT_ROOT/venv/bin/pip" install -q -r "$PROJECT_ROOT/requirements.txt"
echo "  [OK] Project dependencies installed"

# Step 4: Install policy tools
echo ""
echo "[4/7] Installing policy tools (venv_policy/)..."
"$PROJECT_ROOT/venv_policy/bin/python" -m pip install -q --upgrade pip
"$PROJECT_ROOT/venv_policy/bin/pip" install -q -r "$PROJECT_ROOT/requirements-policy.txt"
echo "  [OK] Policy tools installed"

# Step 5: Install pre-commit hooks (using policy venv)
echo ""
echo "[5/7] Installing pre-commit hooks..."
"$PROJECT_ROOT/venv_policy/bin/pre-commit" install
echo "  [OK] Pre-commit hooks installed"

# Step 6: Lock governance files
echo ""
echo "[6/7] Locking governance files..."
chmod +x "$PROJECT_ROOT/scripts/"*.sh
"$PROJECT_ROOT/scripts/lock-governance.sh"

# Step 7: Validate setup
echo ""
echo "[7/7] Validating setup..."
"$PROJECT_ROOT/venv_policy/bin/python" "$PROJECT_ROOT/scripts/validate_setup.py"

echo ""
echo "============================================================"
echo "  Setup Complete!"
echo "============================================================"
echo ""
echo "Virtual environments:"
echo "  venv/        : Project dependencies (activate for development)"
echo "  venv_policy/ : Policy tools (used automatically by pre-commit)"
echo ""
echo "Next steps:"
echo "  1. Activate project venv: source venv/bin/activate"
echo "  2. Fill out PROJECT_BRIEF.md with your project vision"
echo "  3. Start a Cursor chat session"
echo ""
echo "To initialize AI assistant:"
echo "  @docs/ai_codev/AI_CONTEXT_FULL.md"
echo "  @PROJECT_BRIEF.md"
echo "  (Let the AI ask clarifying questions before coding)"
echo ""
echo "To refresh context after long conversations:"
echo "  /summarize"
echo "  @docs/ai_codev/AI_REFRESH.md"
echo ""
