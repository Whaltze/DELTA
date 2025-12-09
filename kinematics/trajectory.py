# -*- coding: utf-8 -*-
# trajectory.py
# Delta机器人轨迹规划类，参考BezierTrack类实现

import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

# 设置中文字体
try:
    matplotlib.rcParams['font.family'] = 'AR PL UKai CN'
    # plt.rc("font",family="AR PL UKai CN")
    matplotlib.rcParams['axes.unicode_minus'] = False
except:
    pass


class TrajectoryPlanner:
    """
    为机器人生成轨迹点序列。
    支持线性、圆形和贝塞尔曲线轨迹插补。
    参考BezierTrack类实现贝塞尔曲线轨迹规划。
    """

    def __init__(self, acc=100, max_speed=1000, interval=0.1, h=10, b=30, d=60):
        """
        初始化轨迹规划器。

        参数:
        acc (float): 加速度，默认100 mm/s²
        max_speed (float): 最大速度，默认1000 mm/s
        interval (float): 散点序列时间间隔，默认0.1 s
        h (float): 最小竖直偏移，默认10 mm
        b (float): 轨迹偏移高度，默认30 mm
        d (float): 曲线水平最大偏移，默认60 mm
        """
        assert acc > 0
        assert max_speed > 0
        assert interval > 0
        assert h > 0
        assert b > 0
        assert d > 0

        self.__acc = acc
        self.__max_speed = max_speed
        self.__interval = interval
        self.__h = h
        self.__b = b
        self.__d = d

        # 计算最小加速距离
        min_acc_distance = max_speed ** 2 / (2 * acc)
        if min_acc_distance > h:
            min_acc_distance = h
            self.__max_speed = math.sqrt(2 * acc * min_acc_distance)  # 更新最大速度

        self.__min_acc_distance = min_acc_distance

    def linear_trajectory(self, start_pos, end_pos, num_points=100):
        """
        生成两点之间的线性插补轨迹。

        参数:
        start_pos (np.ndarray or list): 起始点坐标 [x, y, z]。
        end_pos (np.ndarray or list): 终点坐标 [x, y, z]。
        num_points (int): 插补点的数量，包含起始点。

        返回:
        np.ndarray: 一个 (num_points, 3) 的数组，包含轨迹上的所有点。
        """
        start_pos = np.array(start_pos)
        end_pos = np.array(end_pos)
        
        # 使用np.linspace在每个维度上生成均匀分布的点
        x_points = np.linspace(start_pos[0], end_pos[0], num_points)
        y_points = np.linspace(start_pos[1], end_pos[1], num_points)
        z_points = np.linspace(start_pos[2], end_pos[2], num_points)
        
        # 将各维度的点组合成轨迹
        trajectory = np.vstack((x_points, y_points, z_points)).T
        
        return trajectory

    def circular_trajectory(self, center, start_pos, end_angle, plane='xy', num_points=100):
        """
        生成空间圆弧轨迹。

        参数:
        center (np.ndarray or list): 圆心坐标 [cx, cy, cz]。
        start_pos (np.ndarray or list): 圆弧起始点坐标 [x, y, z]。
        end_angle (float): 圆弧扫过的总角度 (弧度)。正值表示逆时针，负值表示顺时针。
        plane (str): 圆弧所在的平面，可选 'xy', 'yz', 'xz'。
        num_points (int): 插补点的数量，包含起始点。

        返回:
        np.ndarray: 一个 (num_points, 3) 的数组，包含轨迹上的所有点。
        """
        center = np.array(center)
        start_pos = np.array(start_pos)
        
        # 计算半径和起始角度
        radius_vec = start_pos - center
        
        if plane.lower() == 'xy':
            radius = np.sqrt(radius_vec[0]**2 + radius_vec[1]**2)
            start_angle = np.arctan2(radius_vec[1], radius_vec[0])
            z_const = center[2]
        elif plane.lower() == 'yz':
            radius = np.sqrt(radius_vec[1]**2 + radius_vec[2]**2)
            start_angle = np.arctan2(radius_vec[2], radius_vec[1])
            x_const = center[0]
        elif plane.lower() == 'xz':
            radius = np.sqrt(radius_vec[2]**2 + radius_vec[0]**2)
            start_angle = np.arctan2(radius_vec[0], radius_vec[2])
            y_const = center[1]
        else:
            raise ValueError("平面参数必须是 'xy', 'yz', 或 'xz' 之一。")

        if radius < 1e-6:
            raise ValueError("起始点与圆心重合，无法定义圆弧。")

        # 生成角度序列
        angles = np.linspace(start_angle, start_angle + end_angle, num_points)
        
        # 根据平面计算轨迹点
        trajectory = np.zeros((num_points, 3))
        if plane.lower() == 'xy':
            trajectory[:, 0] = center[0] + radius * np.cos(angles)
            trajectory[:, 1] = center[1] + radius * np.sin(angles)
            trajectory[:, 2] = z_const
        elif plane.lower() == 'yz':
            trajectory[:, 0] = x_const
            trajectory[:, 1] = center[1] + radius * np.cos(angles)
            trajectory[:, 2] = center[2] + radius * np.sin(angles)
        elif plane.lower() == 'xz':
            trajectory[:, 0] = center[0] + radius * np.sin(angles)
            trajectory[:, 1] = y_const
            trajectory[:, 2] = center[2] + radius * np.cos(angles)
            
        return trajectory

    def bezier_trajectory(self, start_x, start_y, start_z, target_x, target_y, target_z, show_plot=False):
        """
        生成贝塞尔曲线轨迹（参考BezierTrack类的update方法）。
        
        参数:
        start_x, start_y, start_z (float): 起点坐标
        target_x, target_y, target_z (float): 终点坐标
        show_plot (bool): 是否显示3D轨迹图，默认False
        
        返回:
        list[tuple[float, float, float]]: 轨迹点列表，每个元素为(x, y, z)元组
        """
        A = np.array([start_x, start_y, start_z])  # 起点
        H = np.array([target_x, target_y, target_z])  # 终点

        end_z = max(start_z, target_z)
        B = np.array([start_x, start_y, end_z + self.__h])
        C = np.array([start_x, start_y, end_z + self.__b])
        G = np.array([target_x, target_y, end_z + self.__h])
        BG = H - A

        norm_BG = np.linalg.norm(BG)
        curve_scaling = min(self.__d / norm_BG, 0.5) if norm_BG > 0 else 0.5

        # 计算D点的位置
        D = np.array([
            A[0] + (H[0] - A[0]) * curve_scaling,
            A[1] + (H[1] - A[1]) * curve_scaling,
            end_z + self.__b
        ])

        # 计算F点，与D点对称
        F = np.array([H[0], H[1], end_z + self.__b])

        # 计算E点的位置
        E = np.array([
            H[0] + (A[0] - H[0]) * curve_scaling,
            H[1] + (A[1] - H[1]) * curve_scaling,
            end_z + self.__b
        ])

        # 定义控制点序列
        P0 = B
        P1 = C
        P2 = D

        Q0 = E
        Q1 = F
        Q2 = G

        # 生成曲线部分
        def curve(__P0, __P1, __P2):
            # 如果所有点在同一垂直线上，直接返回直线段
            if (__P0[0] == __P1[0] == __P2[0] and __P0[1] == __P1[1] == __P2[1]):
                return [], [], []

            def curve_S(t):
                return np.linalg.norm(2 * ((1 - t) * (__P1 - __P0) + t * (__P2 - __P1)))

            def curve_L(t):
                # 高斯求积
                weight = [[0.5688888888888889, 0.0000000000000000],
                          [0.4786286704993665, -0.5384693101056831],
                          [0.4786286704993665, 0.5384693101056831],
                          [0.2369268850561891, -0.9061798459386640],
                          [0.2369268850561891, 0.9061798459386640]]

                return 0.5 * t * sum([w * curve_S(0.5 * t * (x + 1)) for w, x in weight])

            def curve_invert_L(l, t_init=0.5):
                t1 = t_init

                while True:
                    t2 = t1 - (curve_L(t1) - l) / curve_S(t1)
                    if math.fabs(t1 - t2) < 1e-14:
                        break

                    t2 = max(0, min(1, t2))  # 确保t2在[0, 1]范围内

                    t1 = t2

                return t2

            curve_length = curve_L(1)
            point_count = max(int(curve_length // (self.__max_speed * self.__interval)), 1)

            curve_x, curve_y, curve_z = [], [], []
            __t_values = [curve_invert_L(curve_length * t, t) for t in np.arange(1, point_count + 1) / point_count]
            for t in __t_values:
                # 计算曲线上的点 (二次贝塞尔曲线)
                P_t_1 = (1 - t) * __P0 + t * __P1
                P_t_2 = (1 - t) * __P1 + t * __P2
                P_t_3 = (1 - t) * P_t_1 + t * P_t_2

                curve_x.append(P_t_3[0])
                curve_y.append(P_t_3[1])
                curve_z.append(P_t_3[2])

            return curve_x, curve_y, curve_z

        # 计算第一段曲线上的点 (二次贝塞尔曲线)
        curveX1, curveY1, curveZ1 = curve(P0, P1, P2)

        # 计算第二段曲线上的点
        curveX2, curveY2, curveZ2 = curve(Q0, Q1, Q2)

        # 变速部分
        lineZt = [0.5 * self.__acc * t ** 2 for t in np.arange(0, self.__max_speed / self.__acc, self.__interval)]

        # 竖直上升部分 (A到B)
        lineXAB, lineYAB, lineZAB = [], [], []

        up_distance = np.linalg.norm(B - A)

        # 加速部分
        for s in lineZt:
            scaling = s / up_distance if up_distance > 0 else 0
            lineXAB.append(A[0] + (B[0] - A[0]) * scaling)
            lineYAB.append(A[1] + (B[1] - A[1]) * scaling)
            lineZAB.append(A[2] + (B[2] - A[2]) * scaling)

        # 匀速部分
        up_last_distance = max(up_distance - lineZt[-1] if lineZt else up_distance, 0)
        up_last_count = max(int(up_last_distance // (self.__max_speed * self.__interval)), 0)

        if up_last_count > 0:
            t_values = np.arange(1, up_last_count + 1) / up_last_count
            lineXAB += [A[0] + (B[0] - A[0]) * (up_last_distance / up_distance) * t for t in t_values]
            lineYAB += [A[1] + (B[1] - A[1]) * (up_last_distance / up_distance) * t for t in t_values]
            lineZAB += [A[2] + lineZt[-1] + (B[2] - A[2]) * (up_last_distance / up_distance) * t for t in t_values]

        # 水平移动部分 (D到E)
        move_distance = np.linalg.norm(E - D)
        point_count = max(int(move_distance // (self.__max_speed * self.__interval)), 0)

        lineXDE, lineYDE, lineZDE = [], [], []
        if point_count > 0:
            t_values = np.arange(0, point_count) / point_count
            lineXDE = [D[0] + (E[0] - D[0]) * t for t in t_values]
            lineYDE = [D[1] + (E[1] - D[1]) * t for t in t_values]
            lineZDE = [D[2] + (E[2] - D[2]) * t for t in t_values]

        # 竖直下降部分 (G到H)
        lineXGH, lineYGH, lineZGH = [], [], []

        down_distance = np.linalg.norm(H - G)

        # 匀速部分
        down_last_distance = max(down_distance - lineZt[-1] if lineZt else down_distance, 0)
        down_last_count = max(int(math.ceil(down_last_distance / (self.__max_speed * self.__interval))), 0)

        if down_last_count > 0:
            t_values = np.arange(0, down_last_count) / down_last_count * (down_last_distance / down_distance)
            lineXGH += [G[0] + (H[0] - G[0]) * t for t in t_values]
            lineYGH += [G[1] + (H[1] - G[1]) * t for t in t_values]
            lineZGH += [G[2] + (H[2] - G[2]) * t for t in t_values]

        # 减速部分
        for s in lineZt[::-1]:
            scaling = s / down_distance if down_distance > 0 else 0
            lineXGH.append(H[0] + (G[0] - H[0]) * scaling)
            lineYGH.append(H[1] + (G[1] - H[1]) * scaling)
            lineZGH.append(H[2] + (G[2] - H[2]) * scaling)

        # 合并所有点形成完整轨迹
        fullX = lineXAB + curveX1 + lineXDE + ([E[0]] if len(lineXDE) == 0 or (len(lineXDE) > 0 and abs(lineXDE[-1] - E[0]) > 1e-6) else []) + curveX2 + lineXGH
        fullY = lineYAB + curveY1 + lineYDE + ([E[1]] if len(lineYDE) == 0 or (len(lineYDE) > 0 and abs(lineYDE[-1] - E[1]) > 1e-6) else []) + curveY2 + lineYGH
        fullZ = lineZAB + curveZ1 + lineZDE + ([E[2]] if len(lineZDE) == 0 or (len(lineZDE) > 0 and abs(lineZDE[-1] - E[2]) > 1e-6) else []) + curveZ2 + lineZGH

        # 确保所有列表长度一致
        min_len = min(len(fullX), len(fullY), len(fullZ))
        fullX = fullX[:min_len]
        fullY = fullY[:min_len]
        fullZ = fullZ[:min_len]

        # 创建3D图形（可选）
        if show_plot:
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')

            # 绘制轨迹
            ax.scatter(fullX, fullY, fullZ, c='b', marker='o', s=20)

            # 添加标签和标题
            ax.set_title('三维贝塞尔曲线')
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')

            # 设置视角
            ax.view_init(elev=20, azim=35)
            plt.tight_layout()
            plt.show()

        # 返回轨迹点列表
        full_points = [(x, y, z) for x, y, z in zip(fullX, fullY, fullZ)]
        return full_points


# ================== 使用示例 ==================
if __name__ == '__main__':
    planner = TrajectoryPlanner()

    # --- 线性轨迹测试 ---
    print("--- 线性轨迹测试 ---")
    start_point = [0, 0, -200]
    end_point = [100, 50, -250]
    linear_path = planner.linear_trajectory(start_point, end_point, num_points=10)
    print(f"从 {start_point} 到 {end_point} 的线性轨迹 (前5个点):")
    print(linear_path[:5])

    # --- 圆形轨迹测试 ---
    print("\n--- XY平面圆形轨迹测试 ---")
    center_point = [0, 0, -250]
    arc_start_point = [100, 0, -250]
    total_angle = np.pi  # 180度
    circular_path_xy = planner.circular_trajectory(center_point, arc_start_point, total_angle, plane='xy', num_points=10)
    print(f"从 {arc_start_point} 开始，绕 {center_point} 旋转 {np.rad2deg(total_angle)} 度的XY平面圆弧轨迹 (前5个点):")
    print(circular_path_xy[:5])
    
    print("\n--- YZ平面圆形轨迹测试 ---")
    center_point_yz = [50, 0, -250]
    arc_start_point_yz = [50, 100, -250]
    total_angle_yz = -np.pi / 2  # -90度
    circular_path_yz = planner.circular_trajectory(center_point_yz, arc_start_point_yz, total_angle_yz, plane='yz', num_points=10)
    print(f"从 {arc_start_point_yz} 开始，绕 {center_point_yz} 旋转 {np.rad2deg(total_angle_yz)} 度的YZ平面圆弧轨迹 (前5个点):")
    print(circular_path_yz[:5])

    # --- 贝塞尔曲线轨迹测试 ---
    print("\n--- 贝塞尔曲线轨迹测试 ---")
    bezier_path = planner.bezier_trajectory(0, 0, -360, 0, 120, -500, show_plot=False)
    print(f"贝塞尔曲线轨迹点数: {len(bezier_path)}")
    print(f"前5个点: {bezier_path[:5]}")
