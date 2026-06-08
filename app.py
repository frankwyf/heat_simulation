import json
import os

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from benchmark_runner import run_benchmark
from portfolio_text import get_text
from simulation_core import DEFAULT_IRRADIANCE, SimulationConfig, run_heat_simulation


SCENARIOS = {
    "Clear Sky / 晴天": {
        "ambient_temp_c": 27.0,
        "wind_speed": 1.0,
        "irradiance": [680, 790, 860, 900, 890, 820, 760, 680],
    },
    "Cloudy / 多云": {
        "ambient_temp_c": 24.0,
        "wind_speed": 1.8,
        "irradiance": [420, 510, 590, 640, 620, 570, 520, 450],
    },
    "High Wind / 大风": {
        "ambient_temp_c": 25.0,
        "wind_speed": 6.0,
        "irradiance": [650, 770, 840, 860, 850, 800, 740, 670],
    },
}


st.set_page_config(page_title="Industrial Heat Simulation Demo", page_icon="🔥", layout="wide")


@st.cache_data(show_spinner=False)
def load_benchmark_profiles(config_path="benchmark_profiles.json"):
    if not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

lang = st.sidebar.selectbox("Language / 语言", ["中文", "English"], index=0)
text = get_text(lang)

st.title(text.title)
st.caption(text.subtitle)

scenario_name = st.sidebar.selectbox("Scenario / 工况预设", list(SCENARIOS.keys()))
scenario = SCENARIOS[scenario_name]

with st.sidebar:
    st.header(text.sidebar_header)
    initial_temp_c = st.slider("Initial Temp (°C) / 初始温度", min_value=5.0, max_value=60.0, value=20.0, step=0.5)
    ambient_temp_c = st.slider(
        "Ambient Temp (°C) / 环境温度",
        min_value=0.0,
        max_value=50.0,
        value=float(scenario["ambient_temp_c"]),
        step=0.5,
    )
    wind_speed = st.slider(
        "Wind Speed (m/s) / 风速",
        min_value=0.0,
        max_value=12.0,
        value=float(scenario["wind_speed"]),
        step=0.1,
    )
    st.markdown("---")
    st.subheader("Irradiance (W/m²) / 辐照强度")

    default_labels = ["9:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]
    irradiance = []
    for i, (label, fallback) in enumerate(zip(default_labels, DEFAULT_IRRADIANCE)):
        preset_value = float(scenario["irradiance"][i]) if i < len(scenario["irradiance"]) else float(fallback)
        v = st.slider(f"{label}", min_value=200.0, max_value=1200.0, value=preset_value, step=5.0)
        irradiance.append(v)


tab_system, tab_optimizer, tab_showcase = st.tabs([text.tab_system, text.tab_optimizer, text.tab_showcase])

with tab_system:
    run_clicked = st.button(text.run_button, type="primary", width="stretch")

    if run_clicked:
        config = SimulationConfig(
            initial_temp_k=initial_temp_c + 273.15,
            ambient_temp_k=ambient_temp_c + 273.15,
            wind_speed=wind_speed,
            irradiance_values=irradiance,
        )

        result = run_heat_simulation(config)
        curves = result["curves"]
        final_result = result["final_result"]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("T_g", f"{final_result['T_g']:.2f} °C")
        c2.metric("T_PV", f"{final_result['T_PV']:.2f} °C")
        c3.metric("T_fluid", f"{final_result['T_fluid']:.2f} °C")
        c4.metric("T_water", f"{final_result['T_water']:.2f} °C")

        plot_df = pd.DataFrame(
            {
                "Time": result["time_labels"],
                "T_g": curves["T_g"],
                "T_PV": curves["T_PV"],
                "T_b": curves["T_b"],
                "T_hp": curves["T_hp"],
                "T_fluid": curves["T_fluid"],
                "T_tube": curves["T_tube"],
                "T_water": curves["T_water"],
            }
        )

        fig, ax = plt.subplots(figsize=(12, 5))
        for key in ["T_g", "T_PV", "T_b", "T_hp", "T_fluid", "T_tube", "T_water"]:
            ax.plot(plot_df["Time"], plot_df[key], label=key, linewidth=2)
        ax.set_xlabel("Time / 时间")
        ax.set_ylabel("Temperature (°C)")
        ax.set_title("PV-T Temperature Response")
        ax.grid(alpha=0.2)
        ax.legend(ncol=4, fontsize=8)
        st.pyplot(fig)

        st.dataframe(plot_df, width="stretch")
        csv_bytes = plot_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download CSV / 下载 CSV",
            data=csv_bytes,
            file_name="heat_simulation_result.csv",
            mime="text/csv",
            width="stretch",
        )
    else:
        st.info("Configure inputs, then run. / 请先配置参数后运行。")

with tab_optimizer:
    st.write("Run local benchmark for GA/PSO/SA and generate reproducible report artifacts.")
    profile_config_path = st.text_input("Profile Config Path", value="benchmark_profiles.json")
    profiles = load_benchmark_profiles(profile_config_path)

    if profiles:
        st.caption("Benchmark profile settings")
        profile_rows = []
        all_keys = sorted({k for p in profiles.values() for k in p.keys()})
        for profile_name, settings in profiles.items():
            row = {"profile": profile_name}
            for key in all_keys:
                row[key] = settings.get(key)
            profile_rows.append(row)
        profile_df = pd.DataFrame(profile_rows)
        st.dataframe(profile_df, width="stretch")
    else:
        st.warning("Profile config file not found. Benchmark will use internal defaults.")

    profile = st.selectbox("Benchmark Profile", ["quick", "standard"], index=0)
    runs = st.slider("Runs Per Algorithm", min_value=1, max_value=5, value=2, step=1)
    ga_iter = st.slider("GA Max Iterations", min_value=80, max_value=500, value=200, step=20)
    seed = st.number_input("Base Seed", min_value=1, max_value=99999, value=42, step=1)
    runtime_cap = st.slider("Per-Algorithm Runtime Cap (s)", min_value=1, max_value=60, value=12, step=1)

    if profiles and "quick" in profiles and "standard" in profiles:
        st.caption("quick vs standard delta")
        quick_cfg = profiles["quick"]
        standard_cfg = profiles["standard"]
        delta_rows = []
        for key in sorted(set(quick_cfg.keys()) | set(standard_cfg.keys())):
            q = quick_cfg.get(key)
            s = standard_cfg.get(key)
            delta_rows.append({"parameter": key, "quick": q, "standard": s})
        st.dataframe(pd.DataFrame(delta_rows), width="stretch")

    if st.button("Run Benchmark / 运行基准对比", width="stretch"):
        with st.spinner("Benchmark running..."):
            artifacts = run_benchmark(
                runs_per_algo=int(runs),
                max_iteration_ga=int(ga_iter),
                base_seed=int(seed),
                profile=profile,
                max_runtime_s=float(runtime_cap),
                profile_config_path=profile_config_path,
            )

        summary_df = pd.read_csv(artifacts["summary_csv"])
        st.success("Benchmark completed.")
        st.dataframe(summary_df, width="stretch")

        st.image(artifacts["plot_png"], caption="Benchmark Chart")

        for label, path in artifacts.items():
            with open(path, "rb") as f:
                st.download_button(
                    label=f"Download {label}",
                    data=f.read(),
                    file_name=path.split("/")[-1],
                    width="stretch",
                )

with tab_showcase:
    st.markdown(
        """
### Portfolio Narrative Template
- Industrial modeling: This project models multi-layer PV-T thermal dynamics with physically interpretable parameters.
- Engineering workflow: One simulation core is reused by CLI, web UI, and benchmark pipeline.
- Optimization depth: GA/PSO/SA are benchmarked locally with reproducible seeds and exported reports.
- Open-source readiness: users can reproduce results through clear docs and downloadable artifacts.

### 建议你在面试中这样讲
- 我把模型从单脚本改为“核心计算 + 多入口”的工程结构。
- 我补了交互式 UI 让非算法背景评审也能快速理解工况影响。
- 我增加了本地可复现 benchmark，让算法对比不仅是截图而是有数据和报告。
"""
    )
