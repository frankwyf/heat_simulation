@echo off
setlocal

set VERSION=v0.2.1
set BASEDIR=.
set CREATETAG=0
set DRYRUN=0

:parse
if "%~1"=="" goto run
if /I "%~1"=="--version" (
  set VERSION=%~2
  shift
  shift
  goto parse
)
if /I "%~1"=="--base-dir" (
  set BASEDIR=%~2
  shift
  shift
  goto parse
)
if /I "%~1"=="--create-tag" (
  set CREATETAG=1
  shift
  goto parse
)
if /I "%~1"=="--dry-run" (
  set DRYRUN=1
  shift
  goto parse
)
shift
goto parse

:run
set PY=%BASEDIR%\.venv\Scripts\python.exe
if not exist "%PY%" set PY=python

echo [1/4] Running local validation
"%PY%" -m heat_simulation.tools.validate_local_pipeline --base-dir "%BASEDIR%" || goto fail

echo [2/4] Generating release checklist
"%PY%" -m heat_simulation.tools.release_checklist --base-dir "%BASEDIR%" || goto fail

echo [3/4] Preparing changelog
if %CREATETAG%==1 (
  if %DRYRUN%==1 (
    "%PY%" -m heat_simulation.tools.release_prepare --base-dir "%BASEDIR%" --version %VERSION% --create-tag --dry-run || goto fail
  ) else (
    "%PY%" -m heat_simulation.tools.release_prepare --base-dir "%BASEDIR%" --version %VERSION% --create-tag || goto fail
  )
) else (
  if %DRYRUN%==1 (
    "%PY%" -m heat_simulation.tools.release_prepare --base-dir "%BASEDIR%" --version %VERSION% --dry-run || goto fail
  ) else (
    "%PY%" -m heat_simulation.tools.release_prepare --base-dir "%BASEDIR%" --version %VERSION% || goto fail
  )
)

echo [4/4] Refreshing release checklist
"%PY%" -m heat_simulation.tools.release_checklist --base-dir "%BASEDIR%" || goto fail

echo Release pipeline completed.
exit /b 0

:fail
echo Release pipeline failed.
exit /b 1
