# -*- coding: utf-8 -*-
"""
轨迹曲线生成模块（适配新架构）
"""

import numpy as np
import math
from PySide6.QtCore import QObject, Signal, QTimer
from kinematics.trajectory import TrajectoryPlanner
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

class TrajectoryCurves(QObject):
    """
    轨迹曲线生成和执行模块
    适配新架构，支持UI更新和仿真器更新
    """
    
    # 信号定义
    log_signal = Signal(str)                    # 日志信号
    ui_update_signal = Signal(list, list)       # UI更新信号 (动平台坐标, 滑块坐标)
    simulator_update_signal = Signal(list)      # 仿真器更新信号 (动平台坐标)
    execution_progress = Signal(int, int)       # 执行进度信号
    execution_completed = Signal(bool)          # 执行完成信号
    trajectory_generated = Signal(list)         # 轨迹生成完成信号
    
    def __init__(self, kinematics, mqtt_handler=None, simulator_window=None, parent=None):
        super().__init__(parent)
        self.kinematics = kinematics
        self.mqtt_handler = mqtt_handler
        self.simulator_window = simulator_window
        self.planner = TrajectoryPlanner()
        self.current_trajectory = []
        self.is_executing = False
        self.execution_timer = QTimer()
        self.execution_timer.timeout.connect(self._execute_next_point)
        self.current_execution_index = 0
        
        # 工作空间限位
        self.workspace_limits = {
            'x_min': -200, 'x_max': 200,
            'y_min': -200, 'y_max': 200,
            'z_min': -337, 'z_max': 0
        }
        
        # 滑块限位
        self.slider_limits = {
            'min': -337,
            'max': -30
        }
        
        # 话题定义
        self.TOPIC_ROBOT_COMMAND = "card/0/robot/in/command"
    
    def update_current_position(self, position):
        """
        更新当前机器人位置
        """
        if isinstance(position, np.ndarray):
            position = position.tolist()
        self.current_robot_pos = list(position)
    
    def check_workspace_limits(self, position):
        """检查工作空间限位"""
        try:
            x, y, z = position
            if x < self.workspace_limits['x_min'] or x > self.workspace_limits['x_max']:
                return False, f"X轴超出范围: {x:.1f}"
            if y < self.workspace_limits['y_min'] or y > self.workspace_limits['y_max']:
                return False, f"Y轴超出范围: {y:.1f}"
            if z < self.workspace_limits['z_min'] or z > self.workspace_limits['z_max']:
                return False, f"Z轴超出范围: {z:.1f}"
            return True, ""
        except Exception as e:
            return False, f"检查工作空间限位失败: {str(e)}"
    
    def generate_gate_curve(self, width=200, height=150, base_z=-500, num_points=100):
        """生成门型曲线轨迹"""
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
        
        # 底部返回段
        bottom_return = self.planner.linear_trajectory(
            [width/2, 0, base_z], 
            [-width/2, 0, base_z], 
            num_points//4
        )
        trajectory.extend(bottom_return)
        
        return np.array(trajectory)
    
    def generate_flower_curve(self, petals=6, radius=100, base_z=-500, height_variation=50, num_points=200):
        """生成花朵曲线轨迹"""
        trajectory = []
        theta = np.linspace(0, 2 * np.pi, num_points)
        
        for t in theta:
            r = radius * np.cos(petals * t)
            x = r * np.cos(t)
            y = r * np.sin(t)
            z = base_z - height_variation * (0.5 + 0.5 * np.sin(petals * 2 * t))
            trajectory.append([x, y, z])
        
        return np.array(trajectory)
    
    def generate_lame_curve(self, a=150, b=100, n=4, base_z=-500, num_points=150):
        """生成Lame曲线轨迹"""
        trajectory = []
        theta = np.linspace(0, 2 * np.pi, num_points)
        
        for t in theta:
            cos_t = np.cos(t)
            sin_t = np.sin(t)
            sign_cos = 1 if cos_t >= 0 else -1
            sign_sin = 1 if sin_t >= 0 else -1
            
            x = a * sign_cos * (abs(cos_t) ** (2/n))
            y = b * sign_sin * (abs(sin_t) ** (2/n))
            z = base_z
            trajectory.append([x, y, z])
        
        return np.array(trajectory)
    
    def generate_helix_curve(self, radius=100, pitch=50, turns=3, base_z=-500, num_points=200):
        """生成螺旋线轨迹"""
        trajectory = []
        theta = np.linspace(0, turns * 2 * np.pi, num_points)
        
        for t in theta:
            x = radius * np.cos(t)
            y = radius * np.sin(t)
            z = base_z - (pitch * t) / (2 * np.pi)
            trajectory.append([x, y, z])
        
        return np.array(trajectory)
    
    def generate_curve(self, curve_type, **params):
        """
        根据类型生成轨迹曲线
        
        参数:
        curve_type (str): 曲线类型
        **params: 曲线参数
        
        返回:
        np.ndarray: 轨迹点数组
        """
        try:
            if curve_type == "门型曲线":
                trajectory = self.generate_gate_curve(**params)
            elif curve_type == "花朵":
                trajectory = self.generate_flower_curve(**params)
            elif curve_type == "Lame曲线":
                trajectory = self.generate_lame_curve(**params)
            elif curve_type == "螺旋线":
                trajectory = self.generate_helix_curve(**params)
            else:
                self.log_signal.emit(f"未知的曲线类型: {curve_type}")
                return None
            
            # 检查轨迹限位
            for point in trajectory:
                valid, msg = self.check_workspace_limits(point)
                if not valid:
                    self.log_signal.emit(f"轨迹点超出工作空间: {msg}")
                    return None
                    
                sliders = self.kinematics.inverse_kinematics(point)
                if sliders is None:
                    self.log_signal.emit(f"轨迹点不可达: ({point[0]:.1f}, {point[1]:.1f}, {point[2]:.1f})")
                    return None
            
            self.current_trajectory = trajectory.tolist()
            self.trajectory_generated.emit(self.current_trajectory)
            self.log_signal.emit(f"生成{curve_type}轨迹，共{len(trajectory)}个点")
            
            return trajectory
            
        except Exception as e:
            self.log_signal.emit(f"生成轨迹失败: {str(e)}")
            return None
    
    def start_execution(self, speed=50.0, simulator_enabled=False):
        """
        开始执行轨迹
        
        参数:
        speed (float): 移动速度 (mm/s)
        simulator_enabled (bool): 是否启用仿真器
        
        返回:
        bool: 启动是否成功
        """
        if not self.current_trajectory:
            self.log_signal.emit("错误: 没有可执行的轨迹")
            return False
        
        if self.is_executing:
            self.log_signal.emit("警告: 轨迹正在执行中")
            return False
        
        self.is_executing = True
        self.current_execution_index = 0
        self.execution_speed = speed
        self.simulator_enabled = simulator_enabled
        
        # 计算执行间隔
        total_distance = 0
        for i in range(1, len(self.current_trajectory)):
            p1 = np.array(self.current_trajectory[i-1])
            p2 = np.array(self.current_trajectory[i])
            total_distance += np.linalg.norm(p2 - p1)
        
        if total_distance > 0 and self.execution_speed > 0:
            total_time = total_distance / self.execution_speed
            interval = int((total_time * 1000) / len(self.current_trajectory))
            interval = max(10, min(100, interval))
        else:
            interval = 50
        
        # 启动定时器执行轨迹
        self.execution_timer.start(interval)
        
        self.log_signal.emit(f"开始执行轨迹，共{len(self.current_trajectory)}个点")
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
            target_point = self.current_trajectory[self.current_execution_index]
            x, y, z = target_point
            
            # 计算滑块位置
            sliders = self.kinematics.inverse_kinematics([x, y, z])
            
            if sliders is not None:
                # 发送更新信号
                self.ui_update_signal.emit([x, y, z], sliders)
                
                if self.simulator_enabled:
                    self.simulator_update_signal.emit([x, y, z])
                
                # 控制实际运动
                if self.mqtt_handler and self.mqtt_handler.is_connected:
                    # 发送MQTT指令
                    import time, json
                    robot_data = {
                        "header": {
                            "stamp": time.time(),
                            "frame_id": "robot_base"
                        },
                        "type": "move_xyz",
                        "position": {
                            "x": round(float(x), 3),
                            "y": round(float(y), 3),
                            "z": round(float(z), 3)
                        },
                        "motion_type": "trajectory",
                        "interpolation": "linear",
                        "velocity": self.execution_speed
                    }
                    
                    json_str = json.dumps(robot_data, indent=2)
                    self.mqtt_handler.client.publish(self.TOPIC_ROBOT_COMMAND, json_str, qos=0)
                
                # 发送进度信号
                self.execution_progress.emit(
                    self.current_execution_index + 1, 
                    len(self.current_trajectory)
                )
            
            self.current_execution_index += 1
            
        except Exception as e:
            self.log_signal.emit(f"执行轨迹点失败: {str(e)}")
            self.stop_execution()
            self.execution_completed.emit(False)
    
    def stop_execution(self):
        """停止执行轨迹"""
        self.is_executing = False
        self.execution_timer.stop()
        self.log_signal.emit("轨迹执行已停止")
    
    def set_workspace_limits(self, x_min, x_max, y_min, y_max, z_min, z_max):
        """设置工作空间限位"""
        self.workspace_limits = {
            'x_min': float(x_min), 'x_max': float(x_max),
            'y_min': float(y_min), 'y_max': float(y_max),
            'z_min': float(z_min), 'z_max': float(z_max)
        }
    
    def set_slider_limits(self, min_limit, max_limit):
        """设置滑块限位"""
        self.slider_limits['min'] = float(min_limit)
        self.slider_limits['max'] = float(max_limit)