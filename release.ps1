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
& $python -m heat_simulation.validation.local_validation --base-dir $root

Write-Host "[2/4] Generating publish readiness check"
& $python -m heat_simulation.release.publish_check --base-dir $root

Write-Host "[3/4] Preparing changelog"
if ($CreateTag) {
    if ($DryRun) {
        & $python -m heat_simulation.release.release_notes --base-dir $root --version $Version --create-tag --dry-run
    } else {
        & $python -m heat_simulation.release.release_notes --base-dir $root --version $Version --create-tag
    }
} else {
    if ($DryRun) {
        & $python -m heat_simulation.release.release_notes --base-dir $root --version $Version --dry-run
    } else {
        & $python -m heat_simulation.release.release_notes --base-dir $root --version $Version
    }
}

Write-Host "[4/4] Refreshing publish readiness check after changelog/tag step"
& $python -m heat_simulation.release.publish_check --base-dir $root

Write-Host "Release pipeline completed." -ForegroundColor Green
