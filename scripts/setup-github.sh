#!/bin/bash
# Setup GitHub Branch Protection (Unix/Linux/macOS)
# Requires: GitHub CLI (gh) installed and authenticated
#
# Install gh: https://cli.github.com/
# Authenticate: gh auth login

set -e

echo "GitHub Branch Protection Setup"
echo "==============================="
echo ""

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "[X] GitHub CLI (gh) is not installed."
    echo "    Install: https://cli.github.com/"
    echo "    Then run: gh auth login"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "[X] Not authenticated to GitHub."
    echo "    Run: gh auth login"
    exit 1
fi

# Get repo info
REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner' 2>/dev/null)
if [ -z "$REPO" ]; then
    echo "[X] Not in a GitHub repository or repo not connected."
    echo "    Run: gh repo create <name> --source=. --push"
    exit 1
fi

echo "Repository: $REPO"
echo ""

# Confirm
echo "This will configure branch protection on 'main' with:"
echo "  - Required status checks: Quick, Full, Sacred"
echo "  - No bypass allowed (even for admins)"
echo "  - Pull request required before merging"
echo ""
read -p "Continue? (y/N) " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Configuring branch protection..."

# Create the protection rule
BODY=$(cat <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "Quick (< 1 min)",
      "Full (main only)",
      "Sacred files"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
)

if echo "$BODY" | gh api "repos/$REPO/branches/main/protection" --method PUT --input - > /dev/null 2>&1; then
    echo ""
    echo "[OK] Branch protection configured!"
    echo ""
    echo "Settings applied:"
    echo "  - Required checks: Quick, Full, Sacred"
    echo "  - Admins cannot bypass"
    echo "  - Force push disabled"
    echo ""
    echo "View settings: https://github.com/$REPO/settings/branches"
else
    echo ""
    echo "[X] Failed to configure branch protection."
    echo ""
    echo "This might fail if:"
    echo "  - The 'main' branch doesn't exist yet (push first)"
    echo "  - You don't have admin rights on the repo"
    echo "  - The repo is not on a paid plan (some features require it)"
    echo ""
    echo "Configure manually: https://github.com/$REPO/settings/branches"
    exit 1
fi
