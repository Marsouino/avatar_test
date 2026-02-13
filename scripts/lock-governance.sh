#!/bin/bash
# Lock governance files (Unix/Linux/macOS)
# Makes sacred files read-only to prevent accidental modification
# Reads file list from .github/sacred-files.yml (single source of truth)

set -e

echo "Locking governance files..."

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

LOCKED=0
NOT_FOUND=0

while IFS= read -r file; do
    full_path="$PROJECT_ROOT/$file"
    if [ -f "$full_path" ]; then
        chmod 444 "$full_path"
        echo "  [LOCKED] $file"
        ((LOCKED++))
    else
        echo "  [NOT FOUND] $file"
        ((NOT_FOUND++))
    fi
done <<< "$SACRED_FILES"

echo ""
echo "Done: $LOCKED files locked, $NOT_FOUND not found."
echo ""
echo "To modify these files, run: ./scripts/unlock-governance.sh"
