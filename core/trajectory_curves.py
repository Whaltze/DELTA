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
        self.is_animating = False # 改名为 is_animating，因为实际执行在下位机


        self.transition_params = {
        'enabled': True,          # 是否启用过渡
        'num_points': 50,         # 过渡轨迹点数
        'duration': 1.0,          # 过渡持续时间（秒）
        'speed_factor': 0.5       # 过渡段速度因子
    }
         
        # 用于本地UI和仿真器更新的定时器
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._animate_next_point)
        self.current_anim_index = 0
        self.animation_speed = 1.0 # 动画倍率
        
        # 工作空间限位 (根据 Delta 430mm 臂长调整)
        # Z轴通常工作在 -350 到 -500 之间
        self.workspace_limits = {
            'x_min': -250, 'x_max': 250,
            'y_min': -250, 'y_max': 250,
            'z_min': -590, 'z_max': -390 
        }
        # 滑块限位
        self.slider_limits = {
            'min': -337,
            'max': -30
        }
        
        # 话题定义
        self.TOPIC_ROBOT_COMMAND = "card/0/position/control/curve"
    def set_transition_params(self, enabled=True, num_points=50, duration=1.0, speed_factor=0.5):
        """配置过渡轨迹参数"""
        self.transition_params.update({
            'enabled': enabled,
            'num_points': num_points,
            'duration': duration,
            'speed_factor': speed_factor
        })
        self.log_signal.emit(f"过渡参数已更新: {self.transition_params}")
        
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
    
    # ================== 轨迹生成 (参数已固化为适宜数值) ==================

    def generate_gate_curve(self):
        """生成门型曲线 (高密度插补)"""
        # 参数固化：确保在安全空间内
        width = 150.0
        height = 80.0
        base_z = -550.0 # 安全高度
        num_points = 1000 # 增加点数以获得丝滑效果
        
        trajectory = []
        # 分段生成，总点数分配给各段
        segment_points = num_points // 4
        
        # 1. 左侧上升
        p1 = [-width/2, 0, base_z]
        p2 = [-width/2, 0, base_z + height] # 注意：Z轴向上是正方向增加（虽然是负数）
        trajectory.extend(self.planner.linear_trajectory(p1, p2, segment_points))
        
        # 2. 顶部横移
        p3 = [width/2, 0, base_z + height]
        trajectory.extend(self.planner.linear_trajectory(p2, p3, segment_points))
        
        # 3. 右侧下降
        p4 = [width/2, 0, base_z]
        trajectory.extend(self.planner.linear_trajectory(p3, p4, segment_points))
        
        # 4. 底部返回
        trajectory.extend(self.planner.linear_trajectory(p4, p1, segment_points))
        
        return np.array(trajectory)
    
    def generate_flower_curve(self):
        """生成花朵曲线"""
        petals = 5
        radius = 80.0  # 减小半径防止超出
        base_z = -550.0
        height_variation = 40.0
        num_points = 1000 # 高密度
        
        trajectory = []
        theta = np.linspace(0, 2 * np.pi, num_points)
        
        for t in theta:
            r = radius * np.cos(petals * t)
            x = r * np.cos(t)
            y = r * np.sin(t)
            # Z轴随花瓣波动
            z = base_z + height_variation * np.sin(petals * 2 * t)
            trajectory.append([x, y, z])
        
        return np.array(trajectory)
    
    def generate_lame_curve(self):
        """生成Lame曲线 (超椭圆)"""
        a = 100.0
        b = 80.0
        n = 4 # 矩形圆角效果
        base_z = -550.0
        num_points = 1000
        
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
    
    def generate_helix_curve(self):
        """生成螺旋线"""
        radius = 70.0
        pitch = 30.0 # 螺距
        turns = 3
        base_z = -440.0 # 起始高度较高，向下螺旋
        num_points = 1000
        
        trajectory = []
        # 生成往复螺旋（下去再上来）以形成闭环或更长的展示
        theta = np.linspace(0, turns * 2 * np.pi, num_points // 2)
        
        # 下降螺旋
        for t in theta:
            x = radius * np.cos(t)
            y = radius * np.sin(t)
            z = base_z - (pitch * t) / (2 * np.pi)
            trajectory.append([x, y, z])
            
        # 简单反向回原点 (直线插补返回)
        if trajectory:
            last_p = trajectory[-1]
            first_p = trajectory[0]
            return_path = self.planner.linear_trajectory(last_p, first_p, num_points // 2)
            trajectory.extend(return_path)
        
        return np.array(trajectory)

    # ================== 通用生成接口 ==================
    def generate_curve(self, curve_type, **kwargs):
        """根据类型生成轨迹"""
        try:
            trajectory = None
            if curve_type == "门型曲线":
                trajectory = self.generate_gate_curve()
            elif curve_type == "花朵":
                trajectory = self.generate_flower_curve()
            elif curve_type == "Lame曲线":
                trajectory = self.generate_lame_curve()
            elif curve_type == "螺旋线":
                trajectory = self.generate_helix_curve()
            else:
                self.log_signal.emit(f"未知的曲线类型: {curve_type}")
                return None
            
            # 校验轨迹有效性
            if trajectory is not None:
                valid_traj = []
                for idx, point in enumerate(trajectory):
                    # 1. 检查工作空间
                    if not self._check_limits(point):
                        self.log_signal.emit(f"警告: 点 {idx} 超出软限位 {point}，已裁剪")
                        continue # 或者做裁剪处理
                        
                    # 2. 检查逆运动学解
                    sliders = self.kinematics.inverse_kinematics(point)
                    if sliders is None:
                        self.log_signal.emit(f"错误: 点 {idx} 逆解失败 (超出机械臂范围)")
                        return None
                    
                    valid_traj.append(point)
                
                self.current_trajectory = valid_traj
                self.trajectory_generated.emit(self.current_trajectory)
                self.log_signal.emit(f"生成 {curve_type} 轨迹成功，共 {len(self.current_trajectory)} 个插补点")
                return self.current_trajectory
                
        except Exception as e:
            self.log_signal.emit(f"生成轨迹异常: {str(e)}")
            return None

    def _check_limits(self, point):
        x, y, z = point
        lim = self.workspace_limits
        if not (lim['x_min'] <= x <= lim['x_max']): return False
        if not (lim['y_min'] <= y <= lim['y_max']): return False
        if not (lim['z_min'] <= z <= lim['z_max']): return False
        return True

    # ================== 执行逻辑 (发送 + 仿真) ==================
    def start_execution(self, mqtt_handler, simulator_window, ui_callback, speed_factor=1.0):
        """
        执行轨迹：发送指令给下位机，并启动本地动画
        """
        if not self.current_trajectory:
            self.log_signal.emit("请先生成轨迹！")
            return False
            
        self.mqtt_handler = mqtt_handler
        
        # 1. 发送给下位机 (一次性发送)
        if self.mqtt_handler and self.mqtt_handler.is_connected:
            # 计算最大速度 mm/s (假设基准速度 200mm/s * 比例)
            max_vel = 20.0 * speed_factor
            
            success = self.mqtt_handler.send_curve_trajectory(self.current_trajectory, max_vel)
            if not success:
                self.log_signal.emit("发送轨迹指令失败")
                return False
        else:
            self.log_signal.emit("仿真模式：未连接设备，仅演示动画")

        # 2. 启动本地 UI/仿真器 动画
        # 即使下位机瞬间收到了所有点，上位机也需要慢慢画出来给用户看
        self.is_animating = True
        self.current_anim_index = 0
        
        # 计算定时器间隔，模拟真实运动速度
        # 假设点很密集，我们不需要每一帧都更新UI，否则UI会卡死
        # 我们以固定频率 (例如 30ms) 更新一次动画
        self.animation_timer.start(30) 
        
        return True

    # 在 TrajectoryCurves 类中添加以下方法

    def generate_transition_trajectory(self, start_pos, end_pos, num_points=50):
        """
        生成从当前位置到轨迹起点的直线过渡轨迹
        
        参数:
        start_pos (list): 当前位置 [x, y, z]
        end_pos (list): 轨迹起点 [x, y, z]
        num_points (int): 插补点数
        
        返回:
        np.ndarray: 过渡轨迹点数组
        """
        try:
            # 检查起点和终点是否在工作空间内
            if not self._check_limits(start_pos):
                self.log_signal.emit(f"警告: 当前位置 {start_pos} 超出工作空间")
                return None
                
            if not self._check_limits(end_pos):
                self.log_signal.emit(f"警告: 轨迹起点 {end_pos} 超出工作空间")
                return None
            
            # 生成直线轨迹
            transition_traj = self.planner.linear_trajectory(start_pos, end_pos, num_points)
            
            # 验证所有点都在工作空间内
            valid_traj = []
            for idx, point in enumerate(transition_traj):
                if self._check_limits(point):
                    valid_traj.append(point)
                else:
                    self.log_signal.emit(f"警告: 过渡轨迹点 {idx} 超出限位 {point}")
                    return None
            
            self.log_signal.emit(f"生成过渡轨迹: 从 {start_pos} 到 {end_pos}, 共 {len(valid_traj)} 个点")
            return np.array(valid_traj)
            
        except Exception as e:
            self.log_signal.emit(f"生成过渡轨迹失败: {str(e)}")
            return None

    def start_execution_with_transition(self, mqtt_handler, simulator_window, current_pos, speed_factor=1.0):
        """
        执行带过渡的轨迹：先执行直线过渡，再执行原轨迹
        
        参数:
        mqtt_handler: MQTT处理器
        simulator_window: 仿真器窗口
        current_pos (list): 当前机器人位置 [x, y, z]
        speed_factor: 速度因子
        """
        if not self.current_trajectory:
            self.log_signal.emit("请先生成轨迹！")
            return False
        
        try:
            # 1. 生成过渡轨迹
            trajectory_start = self.current_trajectory[0]
            transition_traj = self.generate_transition_trajectory(current_pos, trajectory_start)
            
            if transition_traj is None:
                self.log_signal.emit("无法生成过渡轨迹，直接执行原轨迹")
                return self.start_execution(mqtt_handler, simulator_window, None, speed_factor)
            else:
                self.start_execution(mqtt_handler, simulator_window, None, speed_factor)
                
            # 2. 合并轨迹（过渡 + 原轨迹）
            full_trajectory = np.vstack([transition_traj, self.current_trajectory])
            
            # 3. 在仿真器中显示完整轨迹
            if simulator_window:
                simulator_window.set_trajectory(full_trajectory)
            
            # 4. 启动动画（包含过渡段）
            self.is_animating = True
            self.current_anim_index = 0
            self.full_execution_trajectory = full_trajectory  # 保存完整轨迹
            
            # 计算动画速度（过渡段使用较慢速度）
            transition_duration = 1.0  # 过渡段持续时间（秒）
            total_points = len(full_trajectory)
            transition_points = len(transition_traj)
            
            # 调整动画间隔
            self.animation_timer.start(30)  # 30ms更新一次
            
            self.log_signal.emit(f"开始执行带过渡的轨迹: 过渡段 {transition_points} 点 + 原轨迹 {len(self.current_trajectory)} 点")
            
            return True
            
        except Exception as e:
            self.log_signal.emit(f"执行带过渡轨迹失败: {str(e)}")
            return False

    # 修改动画更新方法
    def _animate_next_point(self):
        """本地动画更新循环（支持过渡轨迹）"""
        if not self.is_animating:
            self.animation_timer.stop()
            return
            
        # 每次步进数
        step = 3  # 过渡段使用较小步长，使运动更平滑
        
        self.current_anim_index += step
        
        # 检查是否使用完整轨迹（包含过渡）
        trajectory_to_use = getattr(self, 'full_execution_trajectory', self.current_trajectory)
        
        if self.current_anim_index >= len(trajectory_to_use):
            # 动画结束
            self.stop_execution()
            self.execution_completed.emit(True)
            return
            
        # 获取当前点
        point = trajectory_to_use[self.current_anim_index]
        sliders = self.kinematics.inverse_kinematics(point)
        
        if sliders is not None:
            # 触发UI更新信号
            self.ui_update_signal.emit(point, sliders)
            
            # 触发仿真器更新
            self.simulator_update_signal.emit(point)
            
            # 触发进度条
            self.execution_progress.emit(self.current_anim_index, len(trajectory_to_use))
            
            # 添加日志区分过渡段和原轨迹
            if hasattr(self, 'full_execution_trajectory') and self.current_anim_index < len(self.full_execution_trajectory) - len(self.current_trajectory):
                if self.current_anim_index % 10 == 0:  # 每10个点记录一次
                    self.log_signal.emit(f"过渡段: {self.current_anim_index}/{len(self.full_execution_trajectory)}")

    def stop_execution(self):
        """停止动画"""
        self.is_animating = False
        self.animation_timer.stop()
        self.log_signal.emit("轨迹显示结束")