# Lock governance files (Windows)
# Makes sacred files read-only to prevent accidental modification
# Reads file list from .github/sacred-files.yml (single source of truth)

$ErrorActionPreference = "Stop"

Write-Host "Locking governance files..." -ForegroundColor Yellow

$projectRoot = Split-Path -Parent $PSScriptRoot
$sacredFilesPath = Join-Path $projectRoot ".github\sacred-files.yml"

if (-Not (Test-Path $sacredFilesPath)) {
    Write-Host "[X] Sacred files list not found: $sacredFilesPath" -ForegroundColor Red
    exit 1
}

# Parse YAML list items: "  - path/to/file" (with optional # comment)
$sacredFiles = Get-Content $sacredFilesPath | ForEach-Object {
    if ($_ -match '^\s+-\s+([^\s#]+)') {
        $matches[1]
    }
}

if (-Not $sacredFiles) {
    Write-Host "[X] No sacred files found in $sacredFilesPath" -ForegroundColor Red
    exit 1
}

$locked = 0
$notFound = 0

foreach ($file in $sacredFiles) {
    $fullPath = Join-Path $projectRoot $file
    if (Test-Path $fullPath) {
        attrib +R $fullPath
        Write-Host "  [LOCKED] $file" -ForegroundColor Green
        $locked++
    } else {
        Write-Host "  [NOT FOUND] $file" -ForegroundColor Gray
        $notFound++
    }
}

Write-Host ""
Write-Host "Done: $locked files locked, $notFound not found." -ForegroundColor Cyan
Write-Host ""
Write-Host "To modify these files, run: .\scripts\unlock-governance.ps1" -ForegroundColor Yellow
