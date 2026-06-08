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

### 4) Run Local Optimizer Benchmark (GA/PSO/SA)
```bash
python benchmark_runner.py --runs 2 --ga-iter 200 --seed 42 --profile quick
```

Artifacts will be generated under `reports/` as CSV + PNG + JSON.

### 5) Generate Portfolio Markdown Report
```bash
python generate_portfolio_report.py
```

This generates `reports/portfolio_report.md` using the latest benchmark artifacts.

### 6) Run Full Local Validation
```bash
python validate_local_pipeline.py
```

This performs compile checks, CLI simulation, quick benchmark, and report generation in one command.

The Web UI allows you to:
- tune ambient temperature, initial condition, and wind speed
- customize irradiance profile from 9:00-16:00
- visualize thermal responses instantly
- export results as CSV for further analysis/reporting

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
python benchmark_runner.py --runs 2 --ga-iter 200 --seed 42 --profile quick
```

报告将输出到 `reports/`，包含：
- 明细 CSV
- 汇总 CSV
- 对比图 PNG
- 元信息 JSON

### 生成作品集报告（Markdown）
```bash
python generate_portfolio_report.py
```

将自动读取最新一次 benchmark 的结果，生成 `reports/portfolio_report.md`。

### 一键执行本地稳定性验证
```bash
python validate_local_pipeline.py
```

会依次执行编译检查、CLI 仿真、quick benchmark 与报告生成。

### 目录结构
- `solve.py`: 主仿真入口（推荐）
- `GA.py`: 遗传算法实验脚本
- `PSO.py`: 粒子群算法实验脚本
- `SA.py`: 模拟退火算法实验脚本
- `solve.m`: 历史 MATLAB 版本

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
python benchmark_runner.py --runs 2 --ga-iter 200 --seed 42 --profile quick
```

This generates report artifacts in `reports/` for reproducible algorithm comparison.
Use `--profile standard` for heavier runs.

### Generate Portfolio Report
```bash
python generate_portfolio_report.py
```

This creates `reports/portfolio_report.md` from the latest benchmark metadata.

### Full Local Validation
```bash
python validate_local_pipeline.py
```

Runs compile checks, CLI simulation, quick benchmark, and report generation in one reproducible step.

## Notes
- The optimization scripts are research-style experiments and may take longer to run.
- For fast validation, use `solve.py`.

## Project Entry Points
- `solve.py`: command-line simulation entrypoint
- `app.py`: interactive showcase UI entrypoint
- `simulation_core.py`: reusable simulation engine used by both CLI and UI
- `benchmark_runner.py`: reproducible local benchmark and report generator
- `generate_portfolio_report.py`: generate markdown report for portfolio presentation
- `validate_local_pipeline.py`: one-command local validation workflow
