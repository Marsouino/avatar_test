# Initialize Project from Template
# =================================
# Run this script after cloning/creating from template.
# It sets up TWO virtual environments:
#   - venv/        : project dependencies (ML libs, etc.)
#   - venv_policy/ : policy-as-code tools (semgrep, ruff, mypy, pytest, pre-commit)
#
# Usage: .\scripts\init_project.ps1

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  AI Co-Development Template - Project Initialization" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = Split-Path -Parent $PSScriptRoot

# Step 1: Create project virtual environment
Write-Host "[1/7] Creating project virtual environment (venv/)..." -ForegroundColor Yellow
if (Test-Path "$projectRoot\venv") {
    Write-Host "  [SKIP] venv/ already exists" -ForegroundColor Gray
} else {
    python -m venv "$projectRoot\venv"
    Write-Host "  [OK] venv/ created" -ForegroundColor Green
}

# Step 2: Create policy virtual environment
Write-Host ""
Write-Host "[2/7] Creating policy virtual environment (venv_policy/)..." -ForegroundColor Yellow
if (Test-Path "$projectRoot\venv_policy") {
    Write-Host "  [SKIP] venv_policy/ already exists" -ForegroundColor Gray
} else {
    python -m venv "$projectRoot\venv_policy"
    Write-Host "  [OK] venv_policy/ created" -ForegroundColor Green
}

# Step 3: Install project dependencies
Write-Host ""
Write-Host "[3/7] Installing project dependencies (venv/)..." -ForegroundColor Yellow
& "$projectRoot\venv\Scripts\python.exe" -m pip install -q --upgrade pip
& "$projectRoot\venv\Scripts\pip.exe" install -q -r "$projectRoot\requirements.txt"
Write-Host "  [OK] Project dependencies installed" -ForegroundColor Green

# Step 4: Install policy tools
Write-Host ""
Write-Host "[4/7] Installing policy tools (venv_policy/)..." -ForegroundColor Yellow
& "$projectRoot\venv_policy\Scripts\python.exe" -m pip install -q --upgrade pip
& "$projectRoot\venv_policy\Scripts\pip.exe" install -q -r "$projectRoot\requirements-policy.txt"
Write-Host "  [OK] Policy tools installed" -ForegroundColor Green

# Step 5: Install pre-commit hooks (using policy venv)
Write-Host ""
Write-Host "[5/7] Installing pre-commit hooks..." -ForegroundColor Yellow
& "$projectRoot\venv_policy\Scripts\pre-commit.exe" install
Write-Host "  [OK] Pre-commit hooks installed" -ForegroundColor Green

# Step 6: Lock governance files
Write-Host ""
Write-Host "[6/7] Locking governance files..." -ForegroundColor Yellow
& "$PSScriptRoot\lock-governance.ps1"

# Step 7: Validate setup
Write-Host ""
Write-Host "[7/7] Validating setup..." -ForegroundColor Yellow
& "$projectRoot\venv_policy\Scripts\python.exe" "$projectRoot\scripts\validate_setup.py"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Virtual environments:" -ForegroundColor Yellow
Write-Host "  venv/        : Project dependencies (activate for development)" -ForegroundColor White
Write-Host "  venv_policy/ : Policy tools (used automatically by pre-commit)" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Activate project venv: .\venv\Scripts\Activate" -ForegroundColor White
Write-Host "  2. Fill out PROJECT_BRIEF.md with your project vision" -ForegroundColor White
Write-Host "  3. Start a Cursor chat session" -ForegroundColor White
Write-Host ""
Write-Host "To initialize AI assistant:" -ForegroundColor Yellow
Write-Host "  @docs/ai_codev/AI_CONTEXT_FULL.md" -ForegroundColor White
Write-Host "  @PROJECT_BRIEF.md" -ForegroundColor White
Write-Host "  (Let the AI ask clarifying questions before coding)" -ForegroundColor Gray
Write-Host ""
Write-Host "To refresh context after long conversations:" -ForegroundColor Yellow
Write-Host "  /summarize" -ForegroundColor White
Write-Host "  @docs/ai_codev/AI_REFRESH.md" -ForegroundColor White
Write-Host ""
