from dataclasses import dataclass


@dataclass
class I18NText:
    title: str
    subtitle: str
    sidebar_header: str
    run_button: str
    tab_system: str
    tab_optimizer: str
    tab_showcase: str


TEXT_ZH = I18NText(
    title="工业传热仿真展示台",
    subtitle="PV-T 系统热行为仿真 + 交互参数探索，适合开源项目演示与工程作品集展示",
    sidebar_header="仿真参数",
    run_button="运行仿真",
    tab_system="系统热仿真",
    tab_optimizer="优化算法对比",
    tab_showcase="作品集展示建议",
)


TEXT_EN = I18NText(
    title="Industrial Heat Simulation Studio",
    subtitle="Interactive PV-T thermal simulation and optimization benchmarking for open-source portfolio demos",
    sidebar_header="Simulation Controls",
    run_button="Run Simulation",
    tab_system="System Simulation",
    tab_optimizer="Optimizer Benchmark",
    tab_showcase="Portfolio Tips",
)


def get_text(lang: str) -> I18NText:
    if lang == "English":
        return TEXT_EN
    return TEXT_ZH
