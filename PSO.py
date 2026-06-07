import math
import random
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib as mpl
import time

sns.set_style("whitegrid")
mpl.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体
mpl.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题

# '设定随机种子，每次生成一样随机数'
# random.seed(10)

'随机生成[0,1]之间的随机数'


# 定义评估函数
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


class PSO:
    """
       参数表
       w：惯量权重，0.5
       c1,c2：加速系数，1.5
       r1,r2：[0，1]区间随机数
       pre：模型结果向量，这里假设只有两个模型
       X：融合系数，[0,1]，即粒子位置
       sum：真实label之和
       gbest：全局最优位置向量，引导收敛
       pbest：个体最优位置向量
       f1_list：粒子的最佳函数评估结果
       f2_list：粒子的函数评估结果
    """

    def __init__(self):
        self.pop = 500
        self.w = 0.5
        self.c1 = 1.5
        self.c2 = 1.5
        self.sum = 311  # 真实label之和
        self.x = np.zeros((self.pop, 4), dtype=float)  # 个体最佳位置
        self.v = np.zeros((self.pop, 4))  # 速度
        self.pbest = self.x  # 个体经历的最佳位置
        self.gbest = np.zeros((1, 4))  # 全局最佳位置
        self.f1_list = []
        self.f2_list = []
        self.r = self.x.shape[0]
        self.c = self.x.shape[1]

        self.gbest_hist = []
        for i in range(self.pop):
            self.x[i][0] = random.uniform(100, 2000) / 1000
            self.x[i][1] = random.uniform(1, 100) / 10
            self.x[i][2] = random.uniform(1, 100) / 10
            self.x[i][3] = random.uniform(1, 20) / 10
            # 如果超出范围，重新生成
            while constraint1(self.x[i]) < 0 or constraint2(self.x[i]) < 0 or constraint3(self.x[i]) < 0 or constraint4(
                    self.x[i]) < 0 or constraint5(self.x[i]) < 0 or constraint6(self.x[i]) < 0 or constraint7(
                self.x[i]) < 0:
                self.x[i][0] = random.uniform(100, 2000) / 1000
                self.x[i][1] = random.uniform(1, 100) / 10
                self.x[i][2] = random.uniform(1, 100) / 10
                self.x[i][3] = random.uniform(1, 20) / 10

    def fun(self, X):
        '计算评估函数'
        f_list = []
        for i in range(self.pop):
            f_list.append(aim_function(self.x[i]) - constraint1(self.x[i]) - constraint2(self.x[i]) - constraint3(
                self.x[i]) - constraint4(self.x[i]) - constraint5(self.x[i]) - constraint6(self.x[i]) - constraint7(
                self.x[i]))
            X[i] = self.x[i]
        return f_list

    # 计算适应度函数(全局最优)
    def m1(self):
        min = 65535
        self.f1_list = self.fun(self.x)
        for i in range(len(self.f1_list)):
            if self.f1_list[i] > 5:
                # 重新生成，检查是否符合约束条件
                self.x[i][0] = random.uniform(100, 2000) / 1000
                self.x[i][1] = random.uniform(1, 100) / 10
                self.x[i][2] = random.uniform(1, 100) / 10
                self.x[i][3] = random.uniform(1, 20) / 10
                while constraint1(self.x[i]) < 0 or constraint2(self.x[i]) < 0 or constraint3(self.x[i]) < 0 or constraint4(
                        self.x[i]) < 0 or constraint5(self.x[i]) < 0 or constraint6(self.x[i]) < 0 or constraint7(self.x[i]) < 0:
                    self.x[i][0] = random.uniform(100, 2000) / 1000
                    self.x[i][1] = random.uniform(1, 100) / 10
                    self.x[i][2] = random.uniform(1, 100) / 10
                    self.x[i][3] = random.uniform(1, 20) / 10
            if self.f1_list[i] < min:  # 寻找最小值
                min = self.f1_list[i]
                k = i  # 记录最佳下标
        self.gbest = self.pbest[k]

    def m2(self):
        '粒子速度和位置更新'
        for i in range(self.r):
            vtmp1 = []
            for j in range(self.c):
                r1 = random.random()
                r2 = random.random()
                vtmp2 = self.w * self.v[i][j] + \
                        self.c1 * r1 * (self.pbest[i][j] - self.x[i][j]) + \
                        self.c2 * r2 * (self.gbest[j] - self.x[i][j])
                if i == 0 and vtmp2 < 0.1:
                    vtmp2 = 0.1
                elif i == 0 and vtmp2 > 2:
                    vtmp2 = 2
                if i == 1 and vtmp2 < 0.1:
                    vtmp2 = 0.1
                elif i == 1 and vtmp2 > 10:
                    vtmp2 = 10
                if i == 2 and vtmp2 < 0.1:
                    vtmp2 = 0.1
                elif i == 2 and vtmp2 > 10:
                    vtmp2 = 10
                if i == 3 and vtmp2 < 0.1:
                    vtmp2 = 0.1
                elif i == 3 and vtmp2 > 2:
                    vtmp2 = 2
                vtmp1.append(vtmp2)
            self.x[i] = self.x[i] + np.array(vtmp1)



    # 计算适应度函数(个体最优)
    def m3(self):
        self.f2_list = self.fun(self.x)
        for i in range(self.r):
            if self.f2_list[i] < self.f1_list[i]:
                self.f1_list[i] = self.f2_list[i]
                self.pbest[i] = self.x[i]
        min = 65535
        for i in range(self.r):
            #　如果评价函数大于5，重新开始
            if self.f1_list[i] > 5:
                # 重新生成，检查是否符合约束条件
                self.x[i][0] = random.uniform(100, 2000) / 1000
                self.x[i][1] = random.uniform(1, 100) / 10
                self.x[i][2] = random.uniform(1, 100) / 10
                self.x[i][3] = random.uniform(1, 20) / 10
                while constraint1(self.x[i]) < 0 or constraint2(self.x[i]) < 0 or constraint3(self.x[i]) < 0 or constraint4(
                        self.x[i]) < 0 or constraint5(self.x[i]) < 0 or constraint6(self.x[i]) < 0 or constraint7(self.x[i]) < 0:
                    self.x[i][0] = random.uniform(100, 2000) / 1000
                    self.x[i][1] = random.uniform(1, 100) / 10
                    self.x[i][2] = random.uniform(1, 100) / 10
                    self.x[i][3] = random.uniform(1, 20) / 10

            if self.f1_list[i] < min:
                min = self.f1_list[i]
                k = i
        self.gbest = self.pbest[k]

    def run(self):
        print("PSO算法开始运行：")
        # 记录开始时间
        start_time = time.time()
        self.m1()
        # 种群大小
        for i in range(100):
            self.m2()
            self.m3()
            print(self.gbest)
            t = abs(aim_function(self.gbest))
            # 如果评价函数大于5，重新开始
            print(aim_function(self.x[i]))
            self.gbest_hist.append(t)
        # 记录结束时间
        end_time = time.time()
        # 计算算法的运行时间
        run_time = end_time - start_time

        plt.plot(self.gbest_hist)
        # 在图上添加文字说明
        plt.title("PSO算法--迭代次数与最佳评估函数值的关系" + "\n" + "最佳评估函数值为：" + str(self.gbest_hist[-1]))
        plt.xlabel("迭代次数" + "运行时间为：" + str(run_time))
        plt.ylabel("最佳评估函数值" + "\n" + "平均值：" + str(np.mean(self.gbest_hist)))
        plt.show()
        return run_time


if __name__ == "__main__":
    pso = PSO()
    pso.run()

    # 重复运行多次，记录每一次的最优解和运行时间
    best = []
    times = []
    solutions = []
    for i in range(20):
        pso = PSO()
        x = pso.run()
        # 记录最优评估函数值
        best.append(pso.gbest_hist[-1])
        # 记录每次的最优解
        solutions.append(pso.gbest)
        times.append(x)
        print("第%d次运行的最优解为：%s" % (i + 1, pso.gbest),"第%d次运行的评估函数值：%s" % (i + 1, pso.gbest_hist[-1]), "运行时间为：%s" % x)

    # 画出每一次评估函数值和运行时间的变化曲线（一张图上）
    plt.figure(figsize=(10, 5))
    plt.subplot(121)
    plt.plot(best)
    plt.title("每次运行的最优评估函数值" + "（最小值）" + str(best[-1]) + "\n" + "最大值：" + str(max(best)))
    plt.xlabel("运行次数" + str(len(best)))
    plt.ylabel("最优评估函数值(平均值):" + str(np.mean(best)))
    plt.subplot(122)
    plt.plot(times)
    plt.title("每次运行的运行时间 (平均值):" + str(np.mean(times)) + "s" + "\n" + "最大值：" + str(max(times)) + "s")
    plt.xlabel("运行次数" + str(len(best)))
    plt.ylabel("运行时间 (最小值):" + str(times[-1]) + "s")
    plt.show()
