from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIGS_DIR = PROJECT_ROOT / "configs"
REPORTS_DIR = PROJECT_ROOT / "reports"
PROFILE_HISTORY_DIR = REPORTS_DIR / "profile_history"
LEGACY_DIR = PROJECT_ROOT / "legacy"
DEFAULT_BENCHMARK_PROFILE_PATH = CONFIGS_DIR / "benchmark_profiles.json"
DEFAULT_BENCHMARK_PROFILE_RELATIVE = "configs/benchmark_profiles.json"
BENCHMARK_META_GLOB = str(REPORTS_DIR / "benchmark_meta_*.json")
PORTFOLIO_REPORT_PATH = REPORTS_DIR / "portfolio_report.md"
PUBLISH_READINESS_PATH = REPORTS_DIR / "publish_readiness.md"
