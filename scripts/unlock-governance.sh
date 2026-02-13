#!/bin/bash
# Unlock governance files (Unix/Linux/macOS)
# Removes read-only flag to allow modification
# Reads file list from .github/sacred-files.yml (single source of truth)

set -e

echo "Unlocking governance files..."
echo ""
echo "WARNING: You are unlocking protected files."
echo "Only do this if you have approval to modify governance files."
echo ""

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SACRED_FILES_PATH="$PROJECT_ROOT/.github/sacred-files.yml"

if [ ! -f "$SACRED_FILES_PATH" ]; then
    echo "[X] Sacred files list not found: $SACRED_FILES_PATH"
    exit 1
fi

# Parse YAML list items: "  - path/to/file" (with optional # comment)
SACRED_FILES=$(grep -oP '^\s+-\s+\K[^\s#]+' "$SACRED_FILES_PATH")

if [ -z "$SACRED_FILES" ]; then
    echo "[X] No sacred files found in $SACRED_FILES_PATH"
    exit 1
fi

UNLOCKED=0
NOT_FOUND=0

while IFS= read -r file; do
    full_path="$PROJECT_ROOT/$file"
    if [ -f "$full_path" ]; then
        chmod 644 "$full_path"
        echo "  [UNLOCKED] $file"
        ((UNLOCKED++))
    else
        echo "  [NOT FOUND] $file"
        ((NOT_FOUND++))
    fi
done <<< "$SACRED_FILES"

echo ""
echo "Done: $UNLOCKED files unlocked, $NOT_FOUND not found."
echo ""
echo "REMEMBER: Run ./scripts/lock-governance.sh after your changes!"
