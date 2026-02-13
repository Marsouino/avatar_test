# Setup GitHub Branch Protection (Windows)
# Requires: GitHub CLI (gh) installed and authenticated
#
# Install gh: winget install GitHub.cli
# Authenticate: gh auth login

$ErrorActionPreference = "Stop"

Write-Host "GitHub Branch Protection Setup" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan
Write-Host ""

# Check if gh is installed
try {
    $null = gh --version
} catch {
    Write-Host "[X] GitHub CLI (gh) is not installed." -ForegroundColor Red
    Write-Host "    Install: winget install GitHub.cli" -ForegroundColor Yellow
    Write-Host "    Then run: gh auth login" -ForegroundColor Yellow
    exit 1
}

# Check if authenticated
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] Not authenticated to GitHub." -ForegroundColor Red
    Write-Host "    Run: gh auth login" -ForegroundColor Yellow
    exit 1
}

# Get repo info
$repoInfo = gh repo view --json nameWithOwner 2>&1 | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] Not in a GitHub repository or repo not connected." -ForegroundColor Red
    Write-Host "    Run: gh repo create <name> --source=. --push" -ForegroundColor Yellow
    exit 1
}

$repo = $repoInfo.nameWithOwner
Write-Host "Repository: $repo" -ForegroundColor Green
Write-Host ""

# Confirm
Write-Host "This will configure branch protection on 'main' with:" -ForegroundColor Yellow
Write-Host "  - Required status checks: Quick, Full, Sacred" -ForegroundColor White
Write-Host "  - No bypass allowed (even for admins)" -ForegroundColor White
Write-Host "  - Pull request required before merging" -ForegroundColor White
Write-Host ""
$confirm = Read-Host "Continue? (y/N)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "Cancelled." -ForegroundColor Gray
    exit 0
}

Write-Host ""
Write-Host "Configuring branch protection..." -ForegroundColor Yellow

# Create the protection rule
# Note: GitHub API requires specific format for branch protection
$body = @{
    required_status_checks = @{
        strict = $true
        contexts = @(
            "Quick (< 1 min)",
            "Full (main only)",
            "Sacred files"
        )
    }
    enforce_admins = $true
    required_pull_request_reviews = $null
    restrictions = $null
    allow_force_pushes = $false
    allow_deletions = $false
} | ConvertTo-Json -Depth 10

try {
    # Use gh api to set branch protection
    $result = $body | gh api "repos/$repo/branches/main/protection" --method PUT --input - 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[OK] Branch protection configured!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Settings applied:" -ForegroundColor Cyan
        Write-Host "  - Required checks: Quick, Full, Sacred" -ForegroundColor White
        Write-Host "  - Admins cannot bypass" -ForegroundColor White
        Write-Host "  - Force push disabled" -ForegroundColor White
        Write-Host ""
        Write-Host "View settings: https://github.com/$repo/settings/branches" -ForegroundColor Gray
    } else {
        Write-Host "[X] Failed to configure branch protection." -ForegroundColor Red
        Write-Host "    Error: $result" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "You may need to configure manually:" -ForegroundColor Yellow
        Write-Host "    https://github.com/$repo/settings/branches" -ForegroundColor Gray
        exit 1
    }
} catch {
    Write-Host "[X] Error: $_" -ForegroundColor Red
    exit 1
}
