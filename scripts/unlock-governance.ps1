# Unlock governance files (Windows)
# Removes read-only flag to allow modification
# Reads file list from .github/sacred-files.yml (single source of truth)

$ErrorActionPreference = "Stop"

Write-Host "Unlocking governance files..." -ForegroundColor Yellow
Write-Host ""
Write-Host "WARNING: You are unlocking protected files." -ForegroundColor Red
Write-Host "Only do this if you have approval to modify governance files." -ForegroundColor Red
Write-Host ""

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

$unlocked = 0
$notFound = 0

foreach ($file in $sacredFiles) {
    $fullPath = Join-Path $projectRoot $file
    if (Test-Path $fullPath) {
        attrib -R $fullPath
        Write-Host "  [UNLOCKED] $file" -ForegroundColor Yellow
        $unlocked++
    } else {
        Write-Host "  [NOT FOUND] $file" -ForegroundColor Gray
        $notFound++
    }
}

Write-Host ""
Write-Host "Done: $unlocked files unlocked, $notFound not found." -ForegroundColor Cyan
Write-Host ""
Write-Host "REMEMBER: Run .\scripts\lock-governance.ps1 after your changes!" -ForegroundColor Red
