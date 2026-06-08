# Publish Readiness Check

- Generated at: 2026-06-08T13:32:29.519383
- Branch: master

## Git Health

- Working tree clean: no
- Pending changes:
  - M README.md
  -  M app.py
  - RM heat_simulation/tools/benchmark_runner.py -> heat_simulation/benchmarks/benchmark_suite.py
  - RM heat_simulation/tools/generate_portfolio_report.py -> heat_simulation/benchmarks/portfolio_report.py
  -  M heat_simulation/core/paths.py
  - RM heat_simulation/tools/release_checklist.py -> heat_simulation/release/publish_check.py
  - RM heat_simulation/tools/release_prepare.py -> heat_simulation/release/release_notes.py
  -  D heat_simulation/tools/__init__.py
  - RM heat_simulation/tools/validate_local_pipeline.py -> heat_simulation/validation/local_validation.py
  -  M release.bat
  -  M release.ps1
  -  M reports/portfolio_report.md
  - ?? heat_simulation/benchmarks/__init__.py
  - ?? heat_simulation/release/__init__.py
  - ?? heat_simulation/validation/__init__.py
  - ?? reports/publish_readiness.md

## Recent Commits

- a846925 chore: refresh release checklist after layout cleanup
- 73b9529 docs: refresh usage and report paths for new layout
- 7512756 refactor: reorganize project into package-based layout
- 19e763a feat: add snapshot validation and nonempty release guard
- 2cb0311 feat: add snapshot preview and release commit filters

## Validation

- validation_summary.json found: yes
- validation status: passed
- validated at: 2026-06-08T13:32:25.812450
- checks: py_compile, solve_cli, benchmark_quick, portfolio_report

## Ready To Publish

- ready: no