import argparse

import matplotlib.pyplot as plt

from simulation_core import SimulationConfig, run_heat_simulation


def run_simulation(config: SimulationConfig, show_plot=True, save_path=None):
    result = run_heat_simulation(config=config)
    curves = result["curves"]
    time_seconds = result["time_seconds"]
    time_labels = result["time_labels"]

    print("Result:")
    for key, value in result["final_result"].items():
        print(f"{key}: {value:.4f}")

    plt.plot(time_seconds, curves["T_g"], label="T_g")
    plt.plot(time_seconds, curves["T_PV"], label="T_PV")
    plt.plot(time_seconds, curves["T_b"], label="T_b")
    plt.plot(time_seconds, curves["T_hp"], label="T_hp")
    plt.plot(time_seconds, curves["T_fluid"], label="T_fluid")
    plt.plot(time_seconds, curves["T_tube"], label="T_tube")
    plt.plot(time_seconds, curves["T_water"], label="T_water")

    plt.legend()
    plt.xlabel("Hour")
    plt.ylabel("Temperature (C)")
    plt.xticks(time_seconds, time_labels)
    plt.title("PV-T Temperature vs Time")
    plt.grid()

    if save_path:
        plt.savefig(save_path, dpi=200, bbox_inches="tight")
        print(f"Plot saved to: {save_path}")

    if show_plot:
        plt.show()
    else:
        plt.close()


def parse_args():
    parser = argparse.ArgumentParser(description="Heat transfer simulation for a PV-T collector.")
    parser.add_argument("--no-plot", action="store_true", help="Run simulation without opening a plot window.")
    parser.add_argument("--save-path", default=None, help="Optional path to save the result figure.")
    parser.add_argument("--initial-temp-c", type=float, default=20.0, help="Initial panel/fluid temperature in Celsius.")
    parser.add_argument("--ambient-temp-c", type=float, default=27.0, help="Ambient air temperature in Celsius.")
    parser.add_argument("--wind-speed", type=float, default=1.0, help="Wind speed in m/s.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    simulation_config = SimulationConfig(
        initial_temp_k=args.initial_temp_c + 273.15,
        ambient_temp_k=args.ambient_temp_c + 273.15,
        wind_speed=max(0.0, args.wind_speed),
    )
    run_simulation(config=simulation_config, show_plot=not args.no_plot, save_path=args.save_path)
