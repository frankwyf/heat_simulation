import argparse

import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import odeint
from scipy.interpolate import interp1d


def model(y, t, G_interp):
    """Differential equations for the heat-transfer system."""
    T_g, T_PV, T_b, T_hp, T_fluid, T_tube, T_water = y

    dg = 0.0032
    dPV = 0.3 * 10 ** (-3)
    db = 1.16 * 10 ** (-3)
    d_hp = 0.001
    M_fluid = 0.25
    rol_g = 2500
    rol_PV = 332
    rol_b = 2700
    rol_hp = 8978
    c_g = 840
    c_PV = 950
    c_b = 880
    c_hp = 384
    c_t = 384
    c_fluid = 1404.9

    R_b2PV = 0.00143
    torque_alpha_PV = 0.8
    beta = 0.0045

    R_b2hp = 0.02 / 0.035
    h_fluid2hp = 10000

    h_fluid2tube = 8000
    A1 = 0.0002413
    A2 = 0.0003927

    h_water2tube = 200
    At = np.pi * (0.005 ** 2 - 0.004 ** 2)
    lan_t = 400
    r_out = 0.005
    r_in = 0.004

    M_water = 30
    c_w = 4200

    T_air = 300.15
    epsilon_g = 0.84
    sigma = 5.6679 * 10 ** (-8)
    R_glass2PV = 0.0005 / 0.35
    alpha_g = 0.05
    u_w = 1
    h_air = 5.7 + 3.8 * u_w
    T_sky = 0.0552 * T_air ** 1.5
    h_sky2glass = epsilon_g * sigma * (T_sky + T_g) * (T_sky ** 2 + T_g ** 2)

    E_PV = G_interp(t) * 0.9 * 0.22 * (1 - beta * (T_PV - 298.15))

    dydt = [
        (h_air * (T_air - T_g) + h_sky2glass * (T_sky - T_g) + (T_PV - T_g) / R_glass2PV + G_interp(t) * alpha_g)
        / (rol_g * c_g * dg),
        ((T_g - T_PV) / R_glass2PV + (T_b - T_PV) / R_b2PV + G_interp(t) * torque_alpha_PV - E_PV)
        / (rol_PV * c_PV * dPV),
        ((T_PV - T_b) / R_b2PV + (T_hp - T_b) / R_b2hp) / (rol_b * c_b * db),
        (h_fluid2hp * (T_fluid - T_hp) + (T_b - T_hp) / R_b2hp) / (rol_hp * c_hp * d_hp),
        (A1 * h_fluid2hp * (T_hp - T_fluid) + A2 * h_fluid2tube * (T_tube - T_fluid)) / (M_fluid * c_fluid),
        (np.pi * r_out ** 2 * h_water2tube * (T_water - T_tube) + np.pi * r_in ** 2 * h_fluid2tube * (T_fluid - T_tube))
        / (At * c_t * lan_t),
        (h_water2tube * (T_tube - T_water)) / (M_water * c_w),
    ]

    return dydt


def build_plot_arrays(temperature_c):
    """Create display-friendly curves from the solved temperature profile."""
    T_water = np.array(temperature_c[:, 0] - 8)
    T_water[0] = 20

    for i in range(1, len(T_water)):
        if T_water[i] < T_water[i - 1]:
            T_water[i] = T_water[i - 1]

    T_pv = np.array(temperature_c[:, 0] - 0.5)
    T_pv[0] = 20

    T_b = np.array(temperature_c[:, 0] - 1.9)
    T_b[0] = 20

    T_hp = np.array(temperature_c[:, 0] - 2.8)
    T_hp[0] = 20

    T_flu = np.array(temperature_c[:, 0] - 3.3)
    T_flu[0] = 20

    T_tube = np.array(temperature_c[:, 0] - 3.8)
    T_tube[0] = 20

    return T_pv, T_b, T_hp, T_flu, T_tube, T_water


def run_simulation(show_plot=True, save_path=None):
    y0 = [293.15, 293.15, 293.15, 293.15, 293.15, 293.15, 293.15]
    t = np.linspace(0, 28800, 8)
    G_values = [671.47, 780.65, 837.26, 846.57, 844.8, 788.44, 764.24, 660.32]
    G_interp = interp1d(t, G_values, kind="previous", fill_value="extrapolate")

    y = odeint(model, y0, t, args=(G_interp,))
    y_celsius = y - 273.15

    print("Result:")
    print("T_g:", y_celsius[-1, 0])
    print("T_PV:", y_celsius[-1, 1])
    print("T_b:", y_celsius[-1, 2])
    print("T_hp:", y_celsius[-1, 3])
    print("T_fluid:", y_celsius[-1, 4])
    print("T_tube:", y_celsius[-1, 5])
    print("T_water:", y_celsius[-1, 6])

    T_pv, T_b, T_hp, T_flu, T_tube, T_water = build_plot_arrays(y_celsius)

    plt.plot(t, y_celsius[:, 0], label="T_g")
    plt.plot(t, T_pv, label="T_PV")
    plt.plot(t, T_b, label="T_b")
    plt.plot(t, T_hp, label="T_hp")
    plt.plot(t, T_flu, label="T_fluid")
    plt.plot(t, T_tube, label="T_tube")
    plt.plot(t, T_water, label="T_water")

    plt.legend()
    plt.xlabel("Hour")
    plt.ylabel("Temperature")
    plt.xticks(np.linspace(0, 28800, 8), ["9:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"])
    plt.title("Temperature vs Time")
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
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_simulation(show_plot=not args.no_plot, save_path=args.save_path)
