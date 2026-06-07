import matplotlib.pyplot as plt
import numpy as np
import math
import time
import seaborn as sns

sns.set_style("whitegrid")
np.random.seed(int(time.time())) # 设置随机数种子

num = 20000  # 每次更新温度时的迭代次数
R = 0.5    # 控制温度降低快慢， T = T * R
T_max = 20  # 初始温度
T_min = 0.01  # 下限温度

xs_bounds = [[0.1, 2], [0.1, 10], [0.1, 10], [0.1, 2]]  # x1, x2, x3, x4取值范围


def aim_function(xs):
    return 0.04811 * xs[2] * xs[3] * (xs[1] + 14) + 1.10471 * xs[0] ** 2 * xs[1]


# 定义约束条件函数
def constraint1(xs):
    if (xs[0] - xs[3]) <= 0:
        return 0
    else:
        return -10000


def constraint2(xs):
    if (2.1952 / (xs[2] ** 3 * xs[3]) - 0.25) <= 0:
        return 0
    else:
        return -10000


def constraint3(xs):
    if ((4.013 * 30 * 10 ** 6 * xs[2] * xs[3] ** 3) * (
            1 - xs[2] / 28 * math.sqrt((30 * 10 ** 6) / (48 * 10 ** 6))) / (6 * 14 ** 2)) >= 6000:
        return 0
    else:
        return -10000


def constraint4(xs):
    R = math.sqrt(xs[1] ** 2 * 0.25 + ((xs[0] + xs[2]) * 0.5) ** 2)
    M = 6000 * (xs[1] * 0.5 + 14)
    J = 2 * (math.sqrt(2) * xs[0] * xs[1] * ((xs[1] ** 2 / 12) + (xs[0] + xs[2] / 2) ** 2))
    T = 6000 / (math.sqrt(2) * xs[0] * xs[1])
    if (math.sqrt(T ** 2 + (R * M / J) ** 2 + 2 * T * R * M / J * xs[1] / 2 / R)) <= 13600:
        return 0
    else:
        return -10000


def constraint5(xs):
    if (504000 / (xs[3] * xs[2] ** 2)) <= 30000:
        return 0
    else:
        return -10000


def constraint6(xs):
    if xs[0] >= 0.125:
        return 0
    return -10000


def constraint7(xs):
    if 0.10471 * xs[0] ** 2 + 0.04811 * xs[2] * xs[3] * (xs[1] + 14) <= 5:
        return 0
    return -10000


def adjust(xs):
    # Check constraint violations
    if (
        constraint1(xs) < 0
        or constraint2(xs) < 0
        or constraint3(xs) < 0
        or constraint4(xs) < 0
        or constraint5(xs) < 0
        or constraint6(xs) < 0
        or constraint7(xs) < 0
    ):
        # Apply penalty for constraint violations
        return [
            aim_function(xs) + 10000,
            aim_function(xs) + 10000,
            aim_function(xs) + 10000,
            aim_function(xs) + 10000,
        ]
    else:
        return xs


def main():
    # 记录开始时间
    start_time = time.time()
    count = 0  # 记录迭代次数

    # 随机生成初始状态
    xs = [np.random.uniform(xs_bounds[i][0], xs_bounds[i][1]) for i in range(4)]

    # 计算初始状态的目标函数值
    Best_A = aim_function(xs)

    # 用于存储每次迭代后的最优目标函数值
    Best_array = []

    # 用于存储每次迭代后的温度值
    T_array = []

    # 初始化温度为最大温度
    T = T_max

    # 迭代直到温度达到最小温度
    while T > T_min:
        count += 1
        # 对每个变量进行更新状态
        for i in range(num):
            # 生成新的状态
            xs_temp = [np.random.uniform(xs_bounds[i][0], xs_bounds[i][1]) for i in range(4)]

            # 对生成的状态进行边界限制
            for j in range(4):
                if xs_temp[j] < xs_bounds[j][0]:
                    xs_temp[j] = xs_bounds[j][0]
                elif xs_temp[j] > xs_bounds[j][1]:
                    xs_temp[j] = xs_bounds[j][1]

            # 判断新状态是否违反约束条件
            if (
                    constraint1(xs_temp) < 0
                    or constraint2(xs_temp) < 0
                    or constraint3(xs_temp) < 0
                    or constraint4(xs_temp) < 0
                    or constraint5(xs_temp) < 0
                    or constraint6(xs_temp) < 0
                    or constraint7(xs_temp) < 0
            ):
                # 如果违反约束条件，进行惩罚或调整
                xs_temp = adjust(xs_temp)

            # 计算新状态的目标函数值
            current = aim_function(xs_temp)

            # 计算目标函数值的变化量
            dE = Best_A - current

            # 判断是否接受新状态
            if dE >= 0:
                # 如果目标函数值减小，则接受新状态
                Best_A = current
                xs = xs_temp
            else:
                # 如果目标函数值增加，则根据概率决定是否接受新状态, 概率公式为exp(-dE/T)
                if math.exp(dE / T) > np.random.uniform(0, 1):
                    Best_A = current
                    xs = xs_temp

        # 如果此时的评估大于1.785且温度小于初始温度的0.1%，则升高温度
        if Best_A > 1.76 and T < T_max * 0.001:
            # 升高温度
            T = T * 1.00001
        else:
            # 降低温度
            T = R * T

        # 存储每次迭代后的温度值
        T_array.append(T)

        # 存储每次迭代后的最优目标函数值
        Best_array.append(Best_A)

        # 如果迭代次数超过150次且最优目标函数值小于1.8,停止迭代
        if count > 100 and Best_A < 1.78:
            T = T_min
        # 如果迭代次数超过200次且最优目标函数值小于1.81,停止迭代
        elif count > 200 and Best_A < 1.79:
            T = T_min
        # 如果迭代次数超过300次且最优目标函数值小于1.82,停止迭代
        elif count > 300 and Best_A < 1.80:
            T = T_min
        # 如果迭代次数超过400次且最优目标函数值小于1.83,停止迭代
        elif count > 400 and Best_A < 1.83:
            T = T_min
        # 如果迭代次数超过500次，停止迭代
        elif count > 500:
            T = T_min


    # 记录结束时间
    end_time = time.time()
    # 计算程序运行时间
    time_consume= end_time - start_time
    print("程序运行时间：", time_consume, "s")
    # 绘制目标函数值和温度的变化曲线
    Plot(Best_array, T_array)

    # 返回最优的目标函数值和对应的变量值
    return Best_A, xs, time_consume


def Plot(Best_array, T_array):
    # 绘制目标函数值和温度的变化曲线
    plt.figure(1)
    x_num = [i+1 for i in range(len(Best_array))]
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.title('SA--退火温度变化情况' + "\n平均值 " + str(np.mean(T_array)) + " 方差 " + str(np.var(T_array)))
    plt.xlabel('迭代次数(次): ' + str(x_num[-1]))
    plt.ylabel('温度（最小值）' + str(T_array[-1]))
    plt.plot(x_num, T_array, 'r')

    plt.figure(2)
    plt.plot(x_num, Best_array)
    plt.title('评估函数值收敛情况（最小值）' + str(Best_array[-1]) + " 最大值 " + str(np.max(Best_array)))
    plt.xlabel('迭代次数(次): ' + str(x_num[-1]) + " 方差 " + str(np.var(Best_array)))
    plt.ylabel('目标函数值' + " 平均值 " + str(np.mean(Best_array)))

    plt.show()


if __name__ == '__main__':
    N = 20  # 运行次数
    Bests = []
    xs = []
    consume = [] # 运行时间
    for _ in range(N):
        y, x, t_consume= main()
        Bests.append(y)
        xs.append(x)
        consume.append(t_consume)

    Avg = np.mean(Bests)
    Best = np.min(Bests)
    Worst = np.max(Bests)
    Var = np.var(Bests)
    print("坐标：", xs)
    print("\nAVG: ", Avg,
          "\nBest: ", Best,
          "\nWorst: ", Worst,
          "\nVar: ", Var)

    # 绘制最小值的分布情况折线图和运行时间
    # 两个子图分别表示最小值的分布情况折线图和运行时间
    plt.figure(4)
    plt.subplot(1, 2, 1)
    plt.plot([i for i in range(N)], Bests, 'r')
    plt.title('适应度函数值分布情况\n' + "平均值 " + str(np.mean(Bests)) + "\n 最小值 " + str(np.min(Bests)))
    plt.ylabel('适应度函数值' + " 方差 " + str(np.var(Bests)))
    plt.xlabel('迭代次数')
    plt.subplot(1, 2, 2)
    plt.plot([i for i in range(N)], consume)
    plt.title('运行时间分布情况\n' + "平均值 " + str(np.mean(consume)) + "\n 最小值 " + str(np.min(consume)))
    plt.ylabel('运行时间' + " 方差 " + str(np.var(consume)))
    plt.xlabel('迭代次数')

    plt.show()