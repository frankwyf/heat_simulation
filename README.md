# Heat Simulation Portfolio Project

A cleaned and open-source-ready simulation project for heat transfer modeling and metaheuristic optimization.

## Quick Start (Showcase Friendly)

### 1) Install
```bash
pip install -r requirements.txt
```

### 2) Run CLI Simulation
```bash
python solve.py --no-plot --save-path result.png
```

### 3) Run Interactive Web UI
```bash
streamlit run app.py
```

The optimizer tab supports editing `configs/benchmark_profiles.json` directly in the UI and saving updates.
Each save writes a change snapshot under `reports/profile_history/` for traceability.
You can also choose a snapshot in UI to rollback profile settings safely.
Selected snapshot details and parameter diffs can be previewed before rollback.
The preview flags `ok`, `missing`, `type-mismatch`, and `out-of-range` values before rollback.
The optimizer tab now also shows the latest benchmark snapshot summary at a glance.

### 4) Run Local Optimizer Benchmark (GA/PSO/SA)
```bash
python -m heat_simulation.tools.benchmark_runner --runs 2 --ga-iter 200 --seed 42 --profile quick
```

Artifacts will be generated under `reports/` as CSV + PNG + JSON.
Profile parameters are defined in `configs/benchmark_profiles.json` for reproducible tuning.

### 5) Generate Portfolio Markdown Report
```bash
python -m heat_simulation.tools.generate_portfolio_report
```

This generates `reports/portfolio_report.md` using the latest benchmark artifacts.

### 6) Run Full Local Validation
```bash
python -m heat_simulation.tools.validate_local_pipeline
```

This performs compile checks, CLI simulation, quick benchmark, and report generation in one command.

### 7) Generate Release Checklist
```bash
python -m heat_simulation.tools.release_checklist
```

This summarizes git status, recent commits, and validation readiness in `reports/release_checklist.md`.

### 8) Prepare Changelog And Tag
```bash
python -m heat_simulation.tools.release_prepare --version v0.2.0 --create-tag
```

Use `--dry-run` to preview changes before writing `CHANGELOG.md` or creating tag.

Auto-bump semantic version from latest tag:
```bash
python -m heat_simulation.tools.release_prepare --bump patch --dry-run
python -m heat_simulation.tools.release_prepare --bump minor --dry-run
```

Use an explicit changelog range start tag:
```bash
python -m heat_simulation.tools.release_prepare --from-tag v0.1.0 --version v0.2.0 --dry-run
```

Or use commits from recent days:
```bash
python -m heat_simulation.tools.release_prepare --since-days 30 --version v0.2.0 --dry-run
```

You can also filter by author and commit subject keyword:
```bash
python -m heat_simulation.tools.release_prepare --since-days 30 --author "isidsh" --grep "feat" --version v0.2.0 --dry-run
```

If an empty result set should fail fast:
```bash
python -m heat_simulation.tools.release_prepare --since-days 30 --author "nobody" --version v0.2.0 --dry-run --require-nonempty
```

Note: `--version` and `--bump` are mutually exclusive.
`--from-tag` and `--since-days` are mutually exclusive.

### 9) One-Command Release Pipeline (Windows)
```bash
release.bat --version v0.2.1 --dry-run
```

PowerShell variant:
```powershell
./release.ps1 -Version v0.2.1 -DryRun
```

The Web UI allows you to:
- tune ambient temperature, initial condition, and wind speed
- customize irradiance profile from 9:00-16:00
- visualize thermal responses instantly
- export results as CSV for further analysis/reporting

## Project Layout

```text
heat_simulation/
├─ app.py
├─ solve.py
├─ configs/
│  └─ benchmark_profiles.json
├─ heat_simulation/
│  ├─ core/
│  ├─ optimizers/
│  └─ tools/
├─ legacy/
│  └─ solve.m
├─ reports/
├─ release.bat
├─ release.ps1
├─ README.md
└─ requirements.txt
```

This keeps the root focused on user-facing entrypoints while moving reusable code, tooling, configuration, and legacy files into dedicated folders.

## 中文说明（Chinese）

### 项目简介
这是一个用于展示传热建模与优化算法实践的作品集项目，包含：
- 光伏-热系统温度演化仿真（Python 主程序）
- 三种经典智能优化算法实验代码：GA / PSO / SA
- 一个历史 MATLAB 版本（仅存档用途）

仓库已进行开源前清理：
- 删除与课程提交相关且不影响复现的非代码材料
- 增加依赖清单、许可证与忽略规则
- 改造主程序为命令行可运行（支持无界面环境）

### 环境要求
- Python 3.10+

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行主程序
```bash
python solve.py --no-plot --save-path result.png
```

参数说明：
- `--no-plot`：不弹出图形窗口（适合服务器/CI）
- `--save-path`：将结果图像保存到指定路径
- `--initial-temp-c`：设置初始温度（摄氏度）
- `--ambient-temp-c`：设置环境温度（摄氏度）
- `--wind-speed`：设置风速（m/s）

### 运行交互式 UI（推荐用于作品展示）
```bash
streamlit run app.py
```

交互式 UI 功能：
- 调整环境参数并即时查看温度响应曲线
- 自定义全天辐照输入，展示工况变化分析能力
- 导出 CSV 结果，便于论文/汇报二次处理

### 运行本地算法基准对比
```bash
python -m heat_simulation.tools.benchmark_runner --runs 2 --ga-iter 200 --seed 42 --profile quick
```

报告将输出到 `reports/`，包含：
- 明细 CSV
- 汇总 CSV
- 对比图 PNG
- 元信息 JSON

`configs/benchmark_profiles.json` 用于管理 quick/standard 的参数配置，方便版本化追踪调参。
每次在 UI 保存配置时，会在 `reports/profile_history/` 生成参数差异快照。
也支持在 UI 中选择快照执行回滚。
回滚前可先在 UI 预览快照保存时间和参数变更明细。
预览中会标记 `ok`、`missing`、`type-mismatch`、`out-of-range` 状态，便于先发现异常参数。
优化器页也会展示最近一次 benchmark 的摘要，便于快速回顾结果。

### 生成作品集报告（Markdown）
```bash
python -m heat_simulation.tools.generate_portfolio_report
```

将自动读取最新一次 benchmark 的结果，生成 `reports/portfolio_report.md`。

### 一键执行本地稳定性验证
```bash
python -m heat_simulation.tools.validate_local_pipeline
```

会依次执行编译检查、CLI 仿真、quick benchmark 与报告生成。

### 生成发布检查清单
```bash
python -m heat_simulation.tools.release_checklist
```

会汇总 git 状态、最近提交与验证结果，生成 `reports/release_checklist.md`。

### 生成变更日志并准备本地 Tag
```bash
python -m heat_simulation.tools.release_prepare --version v0.2.0 --create-tag
```

可先用 `--dry-run` 预览，不写文件、不创建 tag。

也支持根据最新 tag 自动递增版本：
```bash
python -m heat_simulation.tools.release_prepare --bump patch --dry-run
python -m heat_simulation.tools.release_prepare --bump minor --dry-run
```

也可以指定 changelog 的起始 tag：
```bash
python -m heat_simulation.tools.release_prepare --from-tag v0.1.0 --version v0.2.0 --dry-run
```

也可以仅使用最近 N 天的提交生成 changelog：
```bash
python -m heat_simulation.tools.release_prepare --since-days 30 --version v0.2.0 --dry-run
```

也支持按作者和提交标题关键词筛选：
```bash
python -m heat_simulation.tools.release_prepare --since-days 30 --author "isidsh" --grep "feat" --version v0.2.0 --dry-run
```

如果希望筛选结果为空时直接失败：
```bash
python -m heat_simulation.tools.release_prepare --since-days 30 --author "nobody" --version v0.2.0 --dry-run --require-nonempty
```

注意：`--version` 和 `--bump` 不能同时使用。
`--from-tag` 和 `--since-days` 不能同时使用。

### Windows 一键发布流水线
```bash
release.bat --version v0.2.1 --dry-run
```

PowerShell 版本：
```powershell
./release.ps1 -Version v0.2.1 -DryRun
```

### 目录结构
- `app.py`: Streamlit 展示入口
- `solve.py`: CLI 仿真入口
- `configs/`: benchmark 配置文件
- `heat_simulation/core/`: 共享模型和文案
- `heat_simulation/optimizers/`: GA / PSO / SA 实现
- `heat_simulation/tools/`: benchmark、报告、验证、发布工具
- `legacy/solve.m`: 历史 MATLAB 版本

---

## 日本語説明（Japanese）

### 概要
本リポジトリは、伝熱シミュレーションと最適化アルゴリズムの実装例をまとめたポートフォリオ向けプロジェクトです。

含まれる内容：
- PV-T 系の温度変化シミュレーション（Python メイン）
- 3 種類の最適化アルゴリズム実験コード（GA / PSO / SA）
- MATLAB の旧版スクリプト（参考用）

公開準備として、不要ファイルの整理、依存関係定義、ライセンス追加、実行しやすい CLI 化を実施しています。

### 動作環境
- Python 3.10+

### 依存関係インストール
```bash
pip install -r requirements.txt
```

### 実行方法
```bash
python solve.py --no-plot --save-path result.png
```

オプション：
- `--no-plot`: GUI ウィンドウを開かずに実行
- `--save-path`: 出力図を保存

### インタラクティブ UI
```bash
streamlit run app.py
```

---

## English

### Overview
This repository is a portfolio-ready project focused on heat-transfer simulation and optimization experiments.

It includes:
- A PV-T thermal simulation entrypoint in Python
- Three optimization experiment scripts: GA, PSO, and SA
- A legacy MATLAB script for reference

The project has been cleaned for open-source release with:
- Unnecessary non-code artifacts removed
- Reproducible dependency file added
- License and .gitignore added
- CLI-friendly simulation execution

### Requirements
- Python 3.10+

### Install
```bash
pip install -r requirements.txt
```

### Run
```bash
python solve.py --no-plot --save-path result.png
```

Options:
- `--no-plot`: run without opening a GUI window
- `--save-path`: save the generated figure
- `--initial-temp-c`: initial temperature in Celsius
- `--ambient-temp-c`: ambient temperature in Celsius
- `--wind-speed`: wind speed in m/s

### Interactive UI
```bash
streamlit run app.py
```

The UI is designed for open-source portfolio demos and technical interviews.

### Local Benchmark Pipeline
```bash
python -m heat_simulation.tools.benchmark_runner --runs 2 --ga-iter 200 --seed 42 --profile quick
```

This generates report artifacts in `reports/` for reproducible algorithm comparison.
Use `--profile standard` for heavier runs.
Profile settings are versioned in `configs/benchmark_profiles.json`.
Every UI save creates a diff snapshot in `reports/profile_history/`.
You can rollback profile settings from snapshot history directly in the UI.
The selected snapshot preview shows saved time and parameter-level diffs before rollback.
The preview also marks `ok`, `missing`, `type-mismatch`, and `out-of-range` validation states.
The optimizer tab also shows the latest benchmark snapshot summary.

### Generate Portfolio Report
```bash
python -m heat_simulation.tools.generate_portfolio_report
```

This creates `reports/portfolio_report.md` from the latest benchmark metadata.

### Full Local Validation
```bash
python -m heat_simulation.tools.validate_local_pipeline
```

Runs compile checks, CLI simulation, quick benchmark, and report generation in one reproducible step.

### Generate Release Checklist
```bash
python -m heat_simulation.tools.release_checklist
```

Generates `reports/release_checklist.md` with git and validation readiness info.

### Prepare Changelog And Tag
```bash
python -m heat_simulation.tools.release_prepare --version v0.2.0 --create-tag
```

Add `--dry-run` for preview-only mode.

You can also auto-bump from latest semantic tag:
```bash
python -m heat_simulation.tools.release_prepare --bump patch --dry-run
python -m heat_simulation.tools.release_prepare --bump minor --dry-run
```

You can pin an explicit range start tag:
```bash
python -m heat_simulation.tools.release_prepare --from-tag v0.1.0 --version v0.2.0 --dry-run
```

`--version` and `--bump` are mutually exclusive.

### One-Command Release Pipeline (Windows)
```bash
release.bat --version v0.2.1 --dry-run
```

PowerShell variant:
```powershell
./release.ps1 -Version v0.2.1 -DryRun
```

## Notes
- The optimization scripts are research-style experiments and may take longer to run.
- For fast validation, use `solve.py`.

## Project Entry Points
- `solve.py`: command-line simulation entrypoint
- `app.py`: interactive showcase UI entrypoint
- `heat_simulation/core/simulation_core.py`: reusable simulation engine used by both CLI and UI
- `configs/benchmark_profiles.json`: versioned benchmark parameter profiles (quick/standard)
- `heat_simulation/tools/benchmark_runner.py`: reproducible local benchmark and report generator
- `heat_simulation/tools/generate_portfolio_report.py`: generate markdown report for portfolio presentation
- `heat_simulation/tools/validate_local_pipeline.py`: one-command local validation workflow
- `heat_simulation/tools/release_checklist.py`: generate publish readiness checklist from git + validation status
- `heat_simulation/tools/release_prepare.py`: generate changelog section and optional local release tag
- `release.bat`: one-command release pipeline for Windows CMD
- `release.ps1`: one-command release pipeline for PowerShell
