# trajectory_curves.py
# -*- coding: utf-8 -*-
"""
轨迹曲线生成模块
实现门型曲线、花朵曲线、Lame曲线等多种轨迹
"""

import numpy as np
import math
from PySide6.QtCore import QObject, Signal, QTimer
from kinematics.trajectory import TrajectoryPlanner
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

class TrajectoryCurves(QObject):
    """
    轨迹曲线生成和执行类
    支持多种预定义轨迹，并实现实时更新
    """
    
    # 信号定义
    trajectory_generated = Signal(list)  # 轨迹生成完成信号
    execution_progress = Signal(int, int)  # 执行进度信号 (当前点, 总点数)
    execution_completed = Signal(bool)  # 执行完成信号
    log_message = Signal(str)  # 日志消息信号
    
    def __init__(self, kinematics, parent=None):
        super().__init__(parent)
        self.kinematics = kinematics
        self.planner = TrajectoryPlanner()
        self.current_trajectory = []
        self.is_executing = False
        self.execution_timer = QTimer()
        self.execution_timer.timeout.connect(self._execute_next_point)
        self.current_execution_index = 0
        
    def generate_gate_curve(self, width=200, height=150, base_z=-300, num_points=100):
        """
        生成门型曲线轨迹
        形状类似门框：从底部左侧开始，向上到顶部，横向到右侧，再向下到底部右侧
        """
        trajectory = []
        
        # 左侧上升段
        left_up = self.planner.linear_trajectory(
            [-width/2, 0, base_z], 
            [-width/2, 0, base_z - height], 
            num_points//4
        )
        trajectory.extend(left_up)
        
        # 顶部横移段
        top_move = self.planner.linear_trajectory(
            [-width/2, 0, base_z - height], 
            [width/2, 0, base_z - height], 
            num_points//4
        )
        trajectory.extend(top_move)
        
        # 右侧下降段
        right_down = self.planner.linear_trajectory(
            [width/2, 0, base_z - height], 
            [width/2, 0, base_z], 
            num_points//4
        )
        trajectory.extend(right_down)
        
        # 底部返回段（可选）
        bottom_return = self.planner.linear_trajectory(
            [width/2, 0, base_z], 
            [-width/2, 0, base_z], 
            num_points//4
        )
        trajectory.extend(bottom_return)
        
        return np.array(trajectory)
    
    def generate_flower_curve(self, petals=6, radius=100, base_z=-300, height_variation=50, num_points=200):
        """
        生成花朵曲线轨迹
        使用玫瑰线方程：r = a * cos(k * θ)
        """
        trajectory = []
        
        # 生成角度序列
        theta = np.linspace(0, 2 * np.pi, num_points)
        
        for i, t in enumerate(theta):
            # 玫瑰线方程
            r = radius * np.cos(petals * t)
            
            # 转换为笛卡尔坐标
            x = r * np.cos(t)
            y = r * np.sin(t)
            
            # 添加高度变化，使花朵有立体感
            z = base_z - height_variation * (0.5 + 0.5 * np.sin(petals * 2 * t))
            
            trajectory.append([x, y, z])
        
        return np.array(trajectory)
    
    def generate_lame_curve(self, a=150, b=100, n=4, base_z=-300, num_points=150):
        """
        生成Lame曲线（超椭圆）轨迹
        方程：|x/a|^n + |y/b|^n = 1
        """
        trajectory = []
        
        # 生成角度序列
        theta = np.linspace(0, 2 * np.pi, num_points)
        
        for t in theta:
            # Lame曲线参数方程
            cos_t = np.cos(t)
            sin_t = np.sin(t)
            
            # 避免除零错误
            sign_cos = 1 if cos_t >= 0 else -1
            sign_sin = 1 if sin_t >= 0 else -1
            
            x = a * sign_cos * (abs(cos_t) ** (2/n))
            y = b * sign_sin * (abs(sin_t) ** (2/n))
            z = base_z
            
            trajectory.append([x, y, z])
        
        return np.array(trajectory)
    
    def generate_3d_helix_curve(self, radius=100, pitch=50, turns=3, base_z=-300, num_points=200):
        """
        生成3D螺旋线轨迹（额外功能）
        """
        trajectory = []
        
        # 生成角度序列
        theta = np.linspace(0, turns * 2 * np.pi, num_points)
        
        for i, t in enumerate(theta):
            x = radius * np.cos(t)
            y = radius * np.sin(t)
            z = base_z - (pitch * t) / (2 * np.pi)
            
            trajectory.append([x, y, z])
        
        return np.array(trajectory)
    
    def generate_curve(self, curve_type, **params):
        """
        根据类型生成轨迹曲线
        """
        try:
            if curve_type == "门型曲线":
                trajectory = self.generate_gate_curve(**params)
            elif curve_type == "花朵":
                trajectory = self.generate_flower_curve(**params)
            elif curve_type == "Lame曲线":
                trajectory = self.generate_lame_curve(**params)
            elif curve_type == "螺旋线":
                trajectory = self.generate_3d_helix_curve(**params)
            else:
                self.log_message.emit(f"未知的曲线类型: {curve_type}")
                return None
            
            self.current_trajectory = trajectory.tolist()
            self.trajectory_generated.emit(self.current_trajectory)
            self.log_message.emit(f"生成{curve_type}轨迹，共{len(trajectory)}个点")
            
            return trajectory
            
        except Exception as e:
            self.log_message.emit(f"生成轨迹失败: {str(e)}")
            return None
    
    def start_execution(self, motion_controller, simulator_window, update_callback, speed_factor=1.0):
        """
        开始执行轨迹
        motion_controller: 运动控制器
        simulator_window: 仿真窗口
        update_callback: UI更新回调函数
        speed_factor: 速度因子
        """
        if not self.current_trajectory:
            self.log_message.emit("错误: 没有可执行的轨迹")
            return False
        
        if self.is_executing:
            self.log_message.emit("警告: 轨迹正在执行中")
            return False
        
        self.is_executing = True
        self.current_execution_index = 0
        self.motion_controller = motion_controller
        self.simulator_window = simulator_window
        self.update_callback = update_callback
        self.speed_factor = speed_factor
        
        # 启动定时器执行轨迹
        interval = int(50 / speed_factor)  # 根据速度因子调整执行间隔
        self.execution_timer.start(interval)
        
        self.log_message.emit("开始执行轨迹")
        return True
    
    def _execute_next_point(self):
        """
        执行下一个轨迹点
        """
        if not self.is_executing or self.current_execution_index >= len(self.current_trajectory):
            self.stop_execution()
            self.execution_completed.emit(True)
            return
        
        try:
            # 获取当前目标点
            target_point = self.current_trajectory[self.current_execution_index]
            x, y, z = target_point
            
            # 计算滑块位置
            sliders_z = self.kinematics.inverse_kinematics([x, y, z])
            
            if sliders_z is not None:
                # 更新仿真器
                if self.simulator_window:
                    self.simulator_window.update_by_sliders(sliders_z)
                
                # 更新UI
                if self.update_callback:
                    self.update_callback([x, y, z], sliders_z)
                
                # 控制实际运动
                if self.motion_controller and self.motion_controller.is_connected:
                    self.motion_controller.move_to_xyz(x, y, z, wait=False)
                
                # 发送进度信号
                self.execution_progress.emit(
                    self.current_execution_index + 1, 
                    len(self.current_trajectory)
                )
            
            self.current_execution_index += 1
            
        except Exception as e:
            self.log_message.emit(f"执行轨迹点失败: {str(e)}")
            self.stop_execution()
            self.execution_completed.emit(False)
    
    def stop_execution(self):
        """
        停止执行轨迹
        """
        self.is_executing = False
        self.execution_timer.stop()
        self.log_message.emit("轨迹执行已停止")
    
    def visualize_trajectory(self, trajectory, title="轨迹可视化"):
        """
        可视化轨迹
        """
        try:
            fig = plt.figure(figsize=(12, 8))
            ax = fig.add_subplot(111, projection='3d')
            
            # 绘制轨迹
            trajectory = np.array(trajectory)
            ax.plot(trajectory[:, 0], trajectory[:, 1], trajectory[:, 2], 
                   'b-', linewidth=2, label='轨迹')
            
            # 标记起点和终点
            ax.scatter(trajectory[0, 0], trajectory[0, 1], trajectory[0, 2], 
                      c='green', s=100, label='起点')
            ax.scatter(trajectory[-1, 0], trajectory[-1, 1], trajectory[-1, 2], 
                      c='red', s=100, label='终点')
            
            # 设置标签和标题
            ax.set_xlabel('X (mm)')
            ax.set_ylabel('Y (mm)')
            ax.set_zlabel('Z (mm)')
            ax.set_title(title)
            ax.legend()
            ax.grid(True)
            
            # 设置视角
            ax.view_init(elev=20, azim=45)
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            self.log_message.emit(f"可视化失败: {str(e)}")
    def enhanced_visualization(self, trajectory, curve_type, show_workspace=True):
        """
        增强的轨迹可视化功能
        """
        try:
            fig = plt.figure(figsize=(15, 10))
            
            # 3D轨迹图
            ax1 = fig.add_subplot(221, projection='3d')
            trajectory = np.array(trajectory)
            ax1.plot(trajectory[:, 0], trajectory[:, 1], trajectory[:, 2], 
                    'b-', linewidth=2, label='轨迹')
            ax1.scatter(trajectory[0, 0], trajectory[0, 1], trajectory[0, 2], 
                    c='green', s=100, label='起点')
            ax1.scatter(trajectory[-1, 0], trajectory[-1, 1], trajectory[-1, 2], 
                    c='red', s=100, label='终点')
            
            # 显示工作空间边界（可选）
            if show_workspace:
                self._draw_workspace_boundary(ax1)
            
            ax1.set_xlabel('X (mm)')
            ax1.set_ylabel('Y (mm)')
            ax1.set_zlabel('Z (mm)')
            ax1.set_title(f'{curve_type} - 3D轨迹')
            ax1.legend()
            ax1.grid(True)
            
            # XY投影
            ax2 = fig.add_subplot(222)
            ax2.plot(trajectory[:, 0], trajectory[:, 1], 'b-', linewidth=2)
            ax2.scatter(trajectory[0, 0], trajectory[0, 1], c='green', s=100, label='起点')
            ax2.scatter(trajectory[-1, 0], trajectory[-1, 1], c='red', s=100, label='终点')
            ax2.set_xlabel('X (mm)')
            ax2.set_ylabel('Y (mm)')
            ax2.set_title('XY平面投影')
            ax2.grid(True)
            ax2.axis('equal')
            ax2.legend()
            
            # XZ投影
            ax3 = fig.add_subplot(223)
            ax3.plot(trajectory[:, 0], trajectory[:, 2], 'b-', linewidth=2)
            ax3.scatter(trajectory[0, 0], trajectory[0, 2], c='green', s=100, label='起点')
            ax3.scatter(trajectory[-1, 0], trajectory[-1, 2], c='red', s=100, label='终点')
            ax3.set_xlabel('X (mm)')
            ax3.set_ylabel('Z (mm)')
            ax3.set_title('XZ平面投影')
            ax3.grid(True)
            ax3.legend()
            
            # 速度和加速度分析
            ax4 = fig.add_subplot(224)
            self._plot_velocity_analysis(ax4, trajectory)
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            self.log_message.emit(f"增强可视化失败: {str(e)}")

    def _draw_workspace_boundary(self, ax):
        """绘制工作空间边界"""
        try:
            # 简化的工作空间边界（圆形）
            theta = np.linspace(0, 2*np.pi, 50)
            max_radius = 200  # 假设最大工作半径
            workspace_x = max_radius * np.cos(theta)
            workspace_y = max_radius * np.sin(theta)
            workspace_z = np.full_like(theta, -300)
            
            ax.plot(workspace_x, workspace_y, workspace_z, 'r--', alpha=0.3, label='工作空间边界')
            
        except Exception as e:
            print(f"绘制工作空间边界失败: {e}")

    def _plot_velocity_analysis(self, ax, trajectory):
        """绘制速度分析图"""
        try:
            # 计算速度
            velocities = []
            for i in range(1, len(trajectory)):
                dist = np.linalg.norm(trajectory[i] - trajectory[i-1])
                velocities.append(dist)
            
            if velocities:
                ax.plot(velocities, 'g-', linewidth=2)
                ax.set_xlabel('轨迹点')
                ax.set_ylabel('速度 (mm/step)')
                ax.set_title('速度分析')
                ax.grid(True)
                
                # 添加统计信息
                mean_vel = np.mean(velocities)
                max_vel = np.max(velocities)
                ax.axhline(y=mean_vel, color='r', linestyle='--', label=f'平均速度: {mean_vel:.2f}')
                ax.axhline(y=max_vel, color='orange', linestyle='--', label=f'最大速度: {max_vel:.2f}')
                ax.legend()
            
        except Exception as e:
            print(f"速度分析失败: {e}")
