import math
import numpy as np
import matplotlib.pyplot as plt
import time
import copy
import seaborn as sns

sns.set_style("whitegrid")

# 支持中文
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号


class GA_optimizer():
    def __init__(self, class_individual, N, C, M, nochange_iter, last_generation_left=0.5,
                 history_convert=lambda x: x):
        # class_individual: 个体的class，可调用产生新个体
        # N: 种群规模
        # C: 交叉概率
        # M: 变异概率
        # nochange_iter: 性能最好的个体保持不变nochange_iter回合后，优化结束
        # history_convert: 在记录history时将fitness转化为实际效用
        # last_generation_left: 保留上一代的比例

        self.last_generation_left = last_generation_left
        self.class_individual = class_individual
        self.N = N
        self.C = C
        self.M = M
        self.nochange_iter = nochange_iter
        self.history_convert = history_convert

    def selection(self, population, fitnesses):
        # 按排名分配被选择的概率
        population_fit_sorted = sorted(zip(fitnesses, population), key=lambda x: x[0])  # 按fitnesses从小到大排序
        population_sorted = list(zip(*population_fit_sorted))[1]  # 将排序后的种群重新分离出来
        population_sorted_left = population_sorted[::-1][:int(
            self.last_generation_left * len(population_sorted))]  # 根据指定比例选择排名靠前的个体，将其逆序后截取一部分作为被选择的个体
        population_sorted_left = population_sorted_left[::-1]  # 再次逆序，使个体按照适应度从小到大排列

        # 计算被选择的概率
        fitness_sorted = list(zip(*population_fit_sorted))[0]  # 获取排序后的适应度列表
        choose_probability = (fitness_sorted[::-1][:len(population_sorted_left)])[
                             ::-1]  # 根据适应度排序选择模式，截取相应数量的适应度值作为被选择的概率
        choose_probability = np.array(choose_probability) / np.sum(choose_probability)  # 将概率归一化，使概率之和等于1、

        # 非均匀选择概率分布
        diversity_factor = 0.5  # 调节多样性因子
        adjusted_choose_probability = choose_probability * (1 - diversity_factor) + diversity_factor / len(
            choose_probability)

        # 先将当前种群效用最好百分比的个体加入新种群
        new_population = []
        for i in range(int(self.last_generation_left * len(population_sorted))):
            new_population.append(population_sorted_left[-i - 1])

        while len(new_population) < self.N:
            # 按适应值大小随机选择两个个体
            p1 = np.random.choice(population_sorted_left, p=adjusted_choose_probability)
            p2 = np.random.choice(population_sorted_left, p=adjusted_choose_probability)

            # 按概率随机选择是否进行交叉
            if np.random.uniform(0, 1) < self.C:  # 生成一个0到1之间的随机数，与交叉概率比较，决定是否进行交叉操作
                p1_chromosome_new, p2_chromosome_new = p1.crossover(p2)  # 进行交叉操作，生成两个新的染色体
                p1_new = self.class_individual(p1_chromosome_new)  # 根据新的染色体创建新的个体对象
                p2_new = self.class_individual(p2_chromosome_new)  # 根据新的染色体创建新的个体对象
            else:
                p1_new = copy.deepcopy(p1)  # 不进行交叉操作，深拷贝当前个体对象
                p2_new = copy.deepcopy(p2)  # 不进行交叉操作，深拷贝当前个体对象

            # 进行随机变异
            p1_new.mutation(self.M)  # 对个体进行变异操作
            p2_new.mutation(self.M)  # 对个体进行变异操作

            # 选择两个个体中适应度较好的个体加入新种群
            if p1_new.fitness() < p2_new.fitness():  # 比较两个个体的适应度，选择适应度较好的个体加入新种群
                new_population.append(p1_new)
            else:
                new_population.append(p2_new)

        return new_population  # 返回新种群列表

    def optimize(self, max_iteration, verbose=True):
        # max_iteration: 最大迭代次数
        # verbose: 是否有print

        population = []  # 种群
        for i in range(self.N):
            a = self.class_individual()  # 产生新个体
            a.randomize()
            population.append(a)

        # 对种群按照适应度进行排序（从小到大）
        population = sorted(population, key=lambda x: x.fitness())

        # 保优操作，保存性能最好的个体
        best_individual = population[0]

        nochange_iter_running = self.nochange_iter
        fitness_history = []
        repeated_generations = 0

        for i in range(max_iteration):
            fitness_history.append(self.history_convert(best_individual.fitness()))  # 记录历史最优个体的适应度
            # 停止迭代条件
            if nochange_iter_running < 0:
                if best_individual.fitness() < 1.8:
                    # 如果最终结果较好（小于1.8），则停止迭代
                    break
                if best_individual.fitness() > 2:
                    # 如果最终结果太差（大于2），将重复次数减半，继续迭代
                    nochange_iter_running = self.nochange_iter / 2  # 重复次数减半
                    print("最优解过差！调用蚁群算法优化整个种群！")
                    # 调用蚁群算法优化整个种群
                    population = ant_colony(population)
                else:
                    # 停止迭代
                    break

            # 避免陷入局部最优解
            if best_individual.fitness() > 1.83 and repeated_generations >= 70:
                # 对种群按照适应度进行排序（从小到大）
                population = sorted(population, key=lambda x: x.fitness())  # 按fitnesses从小到大排序
                # 保留较优的前一半个体，运用蚁群算法优化剩下的个体
                population = population[:int(self.N * self.last_generation_left)] \
                             + ant_colony(population[int(self.N * (1 - self.last_generation_left)):])

                # 重置计数器
                repeated_generations = 0

            fitnesses = [a.fitness() for a in population]  # 计算种群中每个个体的适应度

            # 找到适应度最小的个体
            best_index = np.argmin(fitnesses)

            # 如果适应度最小的个体比当前最优个体的适应度小，则更新最优个体
            if fitnesses[best_index] < best_individual.fitness():
                nochange_iter_running = self.nochange_iter  # 重置计数器
                best_individual = copy.deepcopy(population[best_index])  # 更新最优个体
                repeated_generations = 0
            else:
                repeated_generations += 1

            population = self.selection(population, fitnesses)  # 选择，变异操作

            nochange_iter_running = nochange_iter_running - 1

            # 每隔50代，打印一次当前最优解
            if verbose and i % 50 == 0:
                print('迭代次数: %d\t 最优解: %s\t 适应度: %.3f\t 适应度不变的代数:%d' % (
                    i, best_individual.__repr__(), self.history_convert(best_individual.fitness()),
                    nochange_iter_running))

        return best_individual, fitness_history


def ant_colony(population):
    print('调用蚁群算法优化！')
    pheromone_matrix = np.ones((len(population), len(population)))  # 初始化信息素矩阵
    num_ants = len(population)  # 蚂蚁数量等于种群数量三倍
    num_iterations = 100  # 迭代次数
    alpha = 1  # 信息素重要程度，增大alpha值，相当于增大信息素的重要程度
    beta = 1  # 启发信息重要程度，增大beta值，相当于减小启发信息的重要程度

    for _ in range(num_iterations):
        for ant in range(num_ants):
            # 按顺序选择一个个体
            selected_individual = population[ant % len(population)]
            selected_index = population.index(selected_individual)  # 获取选中个体的索引
            pheromone = pheromone_matrix[selected_index, selected_index]  # 获取信息素值
            attractiveness = np.exp(-selected_individual.fitness() * beta,
                                    where=(selected_individual.fitness() * beta < 0)) + 1  # 计算个体的吸引力

            # 对数计算
            log_pheromone = np.log(np.where(pheromone > 0, pheromone, 1e-10))
            log_attractiveness = np.log(attractiveness)

            # 计算选择概率
            log_probabilities = alpha * log_pheromone + log_attractiveness
            max_log_prob = np.max(log_probabilities)
            shifted_log_prob = log_probabilities - max_log_prob
            probabilities = np.exp(shifted_log_prob)
            sum_probabilities = np.sum(probabilities)

            if sum_probabilities != 0 and not np.isnan(sum_probabilities):
                probabilities /= sum_probabilities  # 归一化概率
            else:
                probabilities = np.ones(len(population)) / len(population)  # 若概率为0或NaN，使用均等概率

            selected_individual.mutation(0.8)  # 对选中个体进行变异操作

            # 更新信息素矩阵
            scaling_factor = 0.3  # 缩放因子
            pheromone_matrix = scaling_factor * pheromone_matrix * (1 - alpha)
            pheromone_matrix[selected_index, selected_index] += alpha / selected_individual.fitness()

    return population


# 目标函数
def aim_function(xs):
    return 0.04811 * xs[2] * xs[3] * (xs[1] + 14) + 1.10471 * xs[0] ** 2 * xs[1]


# 定义约束条件函数
def constraint1(xs):
    if(xs[0] - xs[3]) <= 0:
        return 1
    else:
        return -1


def constraint2(xs):
    if(2.1952/(xs[2]**3 * xs[3]) - 0.25) <= 0:
        return 1
    else:
        return -1


def constraint3(xs):
    if((4.013 * 30 * 10**6 * xs[2] * xs[3]**3) * (1 - xs[2] / 28 * math.sqrt((30 * 10**6)/(48 * 10**6)))/(6 * 14**2)) >= 6000:
        return 1
    else:
        return -1


def constraint4(xs):
    R = math.sqrt(xs[1] ** 2 * 0.25 + ((xs[0] + xs[2]) * 0.5) ** 2)
    M = 6000 * (xs[1] * 0.5 + 14)
    J = 2 * (math.sqrt(2) * xs[0] * xs[1] * ((xs[1] ** 2 / 12) + (xs[0] + xs[2] / 2) ** 2))
    T = 6000 / (math.sqrt(2) * xs[0] * xs[1])
    if (math.sqrt(T ** 2 + (R * M / J) ** 2 + 2 * T * R * M / J * xs[1] / 2 / R)) <= 13600:
        return 1
    else:
        return -1


def constraint5(xs):
    if(504000/(xs[3] * xs[2]**2)) <= 30000:
        return 1
    else:
        return -1


def constraint6(xs):
    if xs[0] >= 0.125:
        return 1
    return -1


def constraint7(xs):
    if 0.10471 * xs[0]**2 + 0.04811 * xs[2] * xs[3] * (xs[1] + 14) <= 5:
        return 1
    return -1


class GA_Individual():
    xs_bounds = [[0.1, 2], [0.1, 10], [0.1, 10], [0.1, 2]]  # x1, x2, x3, x4取值范围
    len_of_bin = 64  # 每个变量用64位二进制数表示，精确到小数点后6位

    def __init__(self, chromosome=None):
        if type(chromosome) == str:
            self.chromosome = chromosome  # x0、x1、x2、x3的二进制代码
        else:
            self.chromosome = '0' * (self.len_of_bin * 4)

    def bin2num(self, bin_str, xi):
        bounds = self.xs_bounds[xi]
        return bounds[0] + int(bin_str, 2) / float((2 ** self.len_of_bin) - 1) * \
               (bounds[1] - bounds[0])

    def decode(self, chromosome):
        x0_str, x1_str, x2_str, x3_str = chromosome[:self.len_of_bin], chromosome[
                                                                       self.len_of_bin:2 * self.len_of_bin], chromosome[
                                                                                                             2 * self.len_of_bin:3 * self.len_of_bin], chromosome[
                                                                                                                                                       3 * self.len_of_bin:]
        x0 = self.bin2num(x0_str, 0)
        x1 = self.bin2num(x1_str, 1)
        x2 = self.bin2num(x2_str, 2)
        x3 = self.bin2num(x3_str, 3)
        return [x0, x1, x2, x3]

    def xs_chromosome(self):
        x0 = self.chromosome[:self.len_of_bin]  # x0的二进制代码
        x1 = self.chromosome[self.len_of_bin:2 * self.len_of_bin]  # x1的二进制代码
        x2 = self.chromosome[2 * self.len_of_bin:3 * self.len_of_bin]  # x2的二进制代码
        x3 = self.chromosome[3 * self.len_of_bin:]  # x3的二进制代码
        return x0, x1, x2, x3

    def randomize(self):
        chromosome_int = np.random.randint(0, 2, 4 * self.len_of_bin)
        chromosome = ''.join(map(str, chromosome_int))
        self.chromosome = chromosome

    def crossover(self, p2):
        p1_chromosome = self.chromosome
        p2_chromosome = p2.chromosome
        joint_left = np.random.choice(range(self.len_of_bin))
        joint_right = np.random.choice(range(self.len_of_bin, self.len_of_bin * 4))
        p1_chromosome_new = p1_chromosome[:joint_left] + p2_chromosome[joint_left:joint_right] + p1_chromosome[joint_right:]
        p2_chromosome_new = p2_chromosome[:joint_left] + p1_chromosome[joint_left:joint_right] + p2_chromosome[joint_right:]
        return p1_chromosome_new, p2_chromosome_new

    def mutation(self, p):
        # p为变异概率，每个二进制位变异的概率
        change_prob = np.random.rand(4 * self.len_of_bin)  # 生成一个长度为4 * self.len_of_bin的随机数数组，范围在0到1之间
        change_flag = change_prob < p  # 创建一个布尔数组，用于指示哪些位将发生变异，元素为True表示对应的位将变异
        change_flag_str = ''.join(list(map(lambda x: str(int(x)), change_flag)))  # 将布尔数组转换为0和1组成的字符串
        changed_chromosome = ('{:0%db}' % (4 * self.len_of_bin)).format(
            int(change_flag_str, 2) ^ int(self.chromosome, 2))  # 使用异或操作将原染色体与变异标志字符串进行异或运算得到新的染色体

        # 将二进制染色体转换为实数向量
        xs = self.decode(changed_chromosome)

        # 检查约束条件
        constraints = [
            constraint1(xs),
            constraint2(xs),
            constraint3(xs),
            constraint4(xs),
            constraint5(xs),
            constraint6(xs),
            constraint7(xs)
        ]

        # 根据约束条件判断是否接受变异后的个体
        if all(c == 1 for c in constraints):
            self.chromosome = changed_chromosome  # 更新染色体为变异后的染色体

    def fitness(self):
        x0_str, x1_str, x2_str, x3_str = self.xs_chromosome()
        x = [self.bin2num(x0_str, 0), self.bin2num(x1_str, 1),
             self.bin2num(x2_str, 2), self.bin2num(x3_str, 3)]  # 表示x0、x1、x2、x3的值

        if constraint1(x) < 0 or constraint2(x) < 0 or constraint3(x) < 0 or constraint4(
                x) < 0 or constraint5(x) < 0 or constraint6(x) < 0 or constraint7(x) < 0:
            # 如果有任何一个约束条件不满足，惩罚函数值为10000
            return aim_function(x) + 10000

        return aim_function(x)

    def __repr__(self):
        x0, x1, x2, x3 = self.xs_chromosome()
        return "x0: %.12f x1: %.12f x2: %.12f x3: %.12f" % (self.bin2num(x0, 0), self.bin2num(x1, 1), self.bin2num(x2, 2), self.bin2num(x3, 3))


if __name__ == '__main__':
    T0 = time.time()
    # 最大迭代次数
    max_iteration = 1300

    # 设置随机数种子
    np.random.seed(int(time.time()))

    # 生成GA_Individual类的实例
    optimizer = GA_optimizer(GA_Individual, 300, 0.95, 0.7, 250, last_generation_left=0.5,
                            history_convert=lambda x: x)

    # 给出20次随机实验的统计结果（平均性能、最佳性能、最差性能、方差等）
    best_fitnesses = []
    TIMES = []
    t_before = time.time() - T0
    for i in range(20):
        t0 = time.time()
        # 绘制出每次仿真过程中目标函数的变化曲线
        best_individual, fitness_history = optimizer.optimize(max_iteration)
        TIMES.append(time.time() - t0 + t_before)  # 记录每次仿真的耗时
        best_fitnesses.append(min(fitness_history))  # 记录每次仿真的最佳性能
        x0, x1, x2, x3 = best_individual.xs_chromosome()
        x0_best, x1_best, x2_best, x3_best = best_individual.bin2num(x0, 0), best_individual.bin2num(x1,
                                                                                                     1), best_individual.bin2num(
            x2, 1), best_individual.bin2num(x3, 1)

        plt.plot(fitness_history)
        plt.xlabel('迭代次数（次）' + str(len(fitness_history)))
        plt.ylabel('目标函数值' + " 方差: " + str(np.var(fitness_history)))
        plt.title('GA--单次仿真过程中目标函数的变化曲线,耗时' + str(time.time() - T0)
                  + "\n最小值 " + str(np.min(fitness_history)) + " 最大值 " + str(np.max(fitness_history)))
        print('最佳选点:   X1: ' + str(x0_best) + 'X2: ' + str(x1_best) + 'X3: ' + str(x2_best) + 'X4: ' + str(x3_best))
        print('最小目标值:' + str(min(fitness_history)))
        plt.show()

    best_fitnesses = np.array(best_fitnesses)
    TIMES = np.array(TIMES)
    ax1 = plt.subplot(1, 2, 1)
    ax1.plot(best_fitnesses)
    ax1.set(title='GA--优化性能--平均: %.3f\n 最佳: %.3f 最差: %.3f' %
                  (best_fitnesses.mean(), best_fitnesses.min(), best_fitnesses.max()),
            ylabel='目标函数值 方差: %.8f' % best_fitnesses.var(), xlabel='实验次数' + str(len(TIMES)))

    ax2 = plt.subplot(1, 2, 2)
    ax2.plot(TIMES)
    ax2.set(title='GA--优化时间--平均: %.3f\n最佳: %.3f 最差: %.3f' %
                  (TIMES.mean(), TIMES.min(), TIMES.max()),
            ylabel='运行部分耗时/s  方差: %.8f' % TIMES.var(), xlabel='实验次数: ' + str(len(TIMES)))
    plt.show()
