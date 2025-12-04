# -*- coding: utf-8 -*-
# visualizer.py

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  # 保持3D支持


class TrajectoryVisualizer:
    """
    使用 Matplotlib 对机器人轨迹进行可视化（位置 + 正逆解分析）。
    """

    def __init__(self):
        """
        初始化可视化工具。
        设置绘图风格和中文字体支持。
        """
        # 尝试设置中文字体，如果失败则回退
        try:
            # plt.rc("font",family="AR PL UKai CN") ###修改了这一行
            plt.rc("font",family="AR PL UKai CN")
            # plt.rcParams['font.sans-serif'] = ['AR PL UKai CN']  # 'SimHei' 没有
            plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示为方块的问题
        except Exception as e:
            print(f"警告: 设置中文字体失败, 图表标签可能显示不正常。错误: {e}")
            print("请确保系统中安装了 'AR PL UKai CN' 字体, 或修改为其他可用的中文字体。")

    # ================== 轨迹可视化 ==================
    def plot_3d_trajectory(self, trajectory_points, title="3D 末端轨迹"):
        """
        绘制末端在工作空间中的三维轨迹。

        参数:
        - trajectory_points: np.ndarray, 形状 (N,3)，每行为 [x,y,z]
        """
        if not isinstance(trajectory_points, np.ndarray) or trajectory_points.ndim != 2 or trajectory_points.shape[1] != 3:
            print("错误: 轨迹数据格式不正确，应为 (N, 3) 的 Numpy 数组。")
            return

        fig = plt.figure(figsize=(8, 7))
        ax = fig.add_subplot(111, projection="3d")

        ax.plot(
            trajectory_points[:, 0],
            trajectory_points[:, 1],
            trajectory_points[:, 2],
            marker=".",
            markersize=2,
            linestyle="-",
        )

        # 标记起点和终点
        ax.scatter(
            trajectory_points[0, 0],
            trajectory_points[0, 1],
            trajectory_points[0, 2],
            c="green",
            s=80,
            label="起点",
        )
        ax.scatter(
            trajectory_points[-1, 0],
            trajectory_points[-1, 1],
            trajectory_points[-1, 2],
            c="red",
            s=80,
            label="终点",
        )

        ax.set_xlabel("X轴 (mm)")
        ax.set_ylabel("Y轴 (mm)")
        ax.set_zlabel("Z轴 (mm)")
        ax.set_title(title)
        ax.legend()
        ax.grid(True)

        plt.tight_layout()
        plt.show()

    # ================== 正逆解 + 误差分析 ==================
    def plot_kinematics_analysis(
        self,
        trajectory_points,
        kinematics,
        time_interval_s,
        title="Delta 机器人正逆解分析",
    ):
        """
        对给定末端轨迹进行正逆解分析，并绘制关节角与误差随时间变化的曲线。

        参数:
        - trajectory_points: np.ndarray, 形状 (N,3)，末端采样轨迹
        - kinematics: DeltaKinematics 实例
        - time_interval_s: 采样时间间隔 (秒)
        """
        if not isinstance(trajectory_points, np.ndarray) or trajectory_points.ndim != 2 or trajectory_points.shape[1] != 3:
            print("错误: 轨迹数据格式不正确，应为 (N, 3) 的 Numpy 数组。")
            return

        num_points = len(trajectory_points)
        time_axis = np.arange(num_points) * time_interval_s

        # 预分配数组
        joint_angles = np.full((num_points, 3), np.nan)  # 弧度
        joint_angles_deg = np.full((num_points, 3), np.nan)  # 角度
        fk_positions = np.full((num_points, 3), np.nan)
        error_norm = np.full(num_points, np.nan)

        # 逐点做逆解 + 正解，并计算误差
        for i, P in enumerate(trajectory_points):
            thetas = kinematics.inverse_kinematics(P)
            if thetas is None:
                continue  # 不可达点保持 NaN

            joint_angles[i, :] = thetas
            joint_angles_deg[i, :] = np.rad2deg(thetas)

            P_fk = kinematics.forward_kinematics(thetas)
            if P_fk is None:
                continue
            fk_positions[i, :] = P_fk
            error_norm[i] = float(np.linalg.norm(P_fk - P))

        # 绘制图像：1) 关节角度  2) 末端误差
        fig, axs = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
        fig.suptitle(title, fontsize=16)

        # 关节角度曲线
        labels = ["θ1", "θ2", "θ3"]
        colors = ["r", "g", "b"]
        for j in range(3):
            axs[0].plot(
                time_axis,
                joint_angles_deg[:, j],
                color=colors[j],
                label=f"{labels[j]} (deg)",
            )
        axs[0].set_ylabel("关节角度 (deg)")
        axs[0].legend()
        axs[0].grid(True)

        # 末端正逆解误差
        axs[1].plot(time_axis, error_norm, color="m", label="|P_fk - P_ref|")
        axs[1].set_xlabel("时间 (s)")
        axs[1].set_ylabel("末端位置误差 (mm)")
        axs[1].legend()
        axs[1].grid(True)

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.show()
        
    def plot_realtime_trajectory(self, trajectory_points, title="实时轨迹"):
        """实时显示轨迹"""
        if not isinstance(trajectory_points, np.ndarray) or trajectory_points.ndim != 2 or trajectory_points.shape[1] != 3:
            print("错误: 轨迹数据格式不正确")
            return

        plt.ion()  # 开启交互模式
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection="3d")
        
        # 初始化轨迹线
        line, = ax.plot([], [], [], 'b-', linewidth=2)
        ax.set_xlabel("X轴 (mm)")
        ax.set_ylabel("Y轴 (mm)")
        ax.set_zlabel("Z轴 (mm)")
        ax.set_title(title)
        
        # 设置坐标轴范围
        margin = 50
        ax.set_xlim(trajectory_points[:, 0].min()-margin, trajectory_points[:, 0].max()+margin)
        ax.set_ylim(trajectory_points[:, 1].min()-margin, trajectory_points[:, 1].max()+margin)
        ax.set_zlim(trajectory_points[:, 2].min()-margin, trajectory_points[:, 2].max()+margin)
        
        # 实时更新
        for i in range(len(trajectory_points)):
            line.set_data(trajectory_points[:i+1, 0], trajectory_points[:i+1, 1])
            line.set_3d_properties(trajectory_points[:i+1, 2])
            plt.pause(0.01)
        
        plt.ioff()
        plt.show()
    # ================== 使用示例 (独立运行时) ==================
if __name__ == "__main__":
    # 仅用于单独测试，本项目中由 core/trajectory_exec 调用
    from kinematics.trajectory import TrajectoryPlanner
    from kinematics.kinematics import DeltaKinematics

    # 机器人参数
    side_sp = 300.0
    side_ep = 100.0
    L_upper = 150.0
    l_lower = 300.0
    sp_dist = side_sp / (2 * np.sqrt(3))
    ep_dist = side_ep / (2 * np.sqrt(3))
    kin = DeltaKinematics(sp=sp_dist, ep=ep_dist, L=L_upper, l=l_lower)

    planner = TrajectoryPlanner()
    start = [0, 0, -200]
    end = [80, 50, -260]
    test_traj = planner.linear_trajectory(start, end, num_points=200)

    vis = TrajectoryVisualizer()
    print("显示三维轨迹图...")
    vis.plot_3d_trajectory(test_traj, title="测试: 线性轨迹")

    print("显示正逆解分析图...")
    dt = 0.02
    vis.plot_kinematics_analysis(test_traj, kin, dt, title="测试: 线性轨迹 正逆解分析")
