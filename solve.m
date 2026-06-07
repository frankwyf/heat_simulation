function solve_equations
    % Parameters
    T_air = 300.15;
    
    % Call ode45 to solve the system of equations
    tspan = [0 28800];
    initial_conditions = [293.15, 293.15, 293.15, 293.15, 293.15, 293.15, 293.15];
    [t, result] = ode45(@(t, y) system_of_equations(t, y, T_air), tspan, initial_conditions);
    
    % Extract results
    T_g_result = result(:, 1);
    T_PV_result = result(:, 2);
    T_b_result = result(:, 3);
    T_hp_result = result(:, 4);
    T_fluid_result = result(:, 5);
    T_tube_result = result(:, 6);
    T_water_result = result(:, 7);

    % Plot results
    figure;
    plot(t, T_g_result, 'DisplayName', 'T_g');
    hold on;
    plot(t, T_PV_result, 'DisplayName', 'T_PV');
    plot(t, T_b_result, 'DisplayName', 'T_b');
    plot(t, T_hp_result, 'DisplayName', 'T_hp');
    plot(t, T_fluid_result, 'DisplayName', 'T_fluid');
    plot(t, T_tube_result, 'DisplayName', 'T_tube');
    plot(t, T_water_result, 'DisplayName', 'T_water');
    legend;
    xlabel('Time');
    ylabel('Temperature');
    title('Temperature Evolution');
    grid on;
    hold off;
end

function dydt = system_of_equations(t, y, T_air)
    % Parameters (you can move these parameters here if needed)
    G = 560;
    alpha_g = 0.05;
    sigma = 5.6679 * 10^(-8);
    epsilon_g = 0.84;
    u_w = 1;
    h_air = 5.7 + 3.8 * u_w;
    R_glass2PV = 0.0005 / 0.35;
    beta = 0.0045;
    R_b2PV = 0.00143;
    torque_alpha_PV = 0.8;
    R_b2hp = 0.02 / 0.035;
    h_fluid2hp = 5000;
    h_fluid2tube = 3000;
    A1 = 0.0002413;
    A2 = 0.0003927;
    h_water2tube = 500;
    At = pi * (0.005^2 - 0.004^2);
    lan_t = 400;
    r_out = 0.005;
    r_in = 0.004;
    M_water = 60;
    c_w = 4200;

    % Extract temperatures
    T_g = y(1);
    T_PV = y(2);
    T_b = y(3);
    T_hp = y(4);
    T_fluid = y(5);
    T_tube = y(6);
    T_water = y(7);

    % Equations
    dydt = zeros(7, 1);

    dydt(1) = (h_air * (T_air - T_g) + h_sky2glass(T_g, T_air) + (T_PV - T_g) / R_glass2PV + G * alpha_g) / 6720;
    dydt(2) = ((T_g - T_PV) / R_glass2PV + (T_b - T_PV) / R_b2PV + G * torque_alpha_PV - E_PV(T_PV)) / 0.684;
    dydt(3) = ((T_PV - T_b) / R_b2PV + (T_hp - T_b) / R_b2hp) / 2818.8;
    dydt(4) = (h_fluid2hp * (T_fluid - T_hp) + (T_b - T_hp) / R_b2hp) / 3447.552;
    dydt(5) = (A1 * h_fluid2hp * (T_hp - T_fluid) + A2 * h_fluid2tube * (T_tube - T_fluid)) / 377.5;
    dydt(6) = (0.01131 * second_derivative(T_tube, T_water) + pi * r_out^2 * h_water2tube * (T_water - T_tube) + pi * r_in^2 * h_fluid2tube * (T_fluid - T_tube)) / 97.4772;
    dydt(7) = (h_fluid2tube * (T_tube - T_water)) / 252000;
end

function result = h_sky2glass(T_g, T_air)
    epsilon_g = 0.84;
    sigma = 5.6679 * 10^(-8);
    T_sky = 0.0552 * T_air^1.5;
    result = epsilon_g * sigma * (T_sky + T_g) * (T_sky^2 + T_g^2);
end

function result = E_PV(T_PV)
    G = 560;
    beta = 0.0045;
    result = G * 0.9 * 0.22 * (1 - beta * (T_PV - 298.15));
end

function result = second_derivative(T1, T2)
    result = (T1 - T2) / 0.0014;
end
