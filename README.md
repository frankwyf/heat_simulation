# Heat Simulation Portfolio Project

A cleaned and open-source-ready simulation project for heat transfer modeling and metaheuristic optimization.

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

## Notes
- The optimization scripts are research-style experiments and may take longer to run.
- For fast validation, use `solve.py`.
