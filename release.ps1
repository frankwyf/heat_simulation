param(
    [string]$Version = "v0.2.1",
    [string]$BaseDir = ".",
    [switch]$CreateTag,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path $BaseDir
$python = Join-Path $root ".venv/Scripts/python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

Write-Host "[1/4] Running local validation"
& $python "$(Join-Path $root 'validate_local_pipeline.py')" --base-dir $root

Write-Host "[2/4] Generating release checklist"
& $python "$(Join-Path $root 'release_checklist.py')" --base-dir $root

Write-Host "[3/4] Preparing changelog"
if ($CreateTag) {
    if ($DryRun) {
        & $python "$(Join-Path $root 'release_prepare.py')" --base-dir $root --version $Version --create-tag --dry-run
    } else {
        & $python "$(Join-Path $root 'release_prepare.py')" --base-dir $root --version $Version --create-tag
    }
} else {
    if ($DryRun) {
        & $python "$(Join-Path $root 'release_prepare.py')" --base-dir $root --version $Version --dry-run
    } else {
        & $python "$(Join-Path $root 'release_prepare.py')" --base-dir $root --version $Version
    }
}

Write-Host "[4/4] Refreshing checklist after changelog/tag step"
& $python "$(Join-Path $root 'release_checklist.py')" --base-dir $root

Write-Host "Release pipeline completed." -ForegroundColor Green
