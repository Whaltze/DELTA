# p2p_move_module.py - 增强仿真动画版

import numpy as np
from PySide6.QtCore import QObject, Signal, QTimer
import traceback
import time
import json

class P2PMoveModule(QObject):
    """
    Delta机器人点到点直线运动模块 - 增强仿真动画版
    使用初始坐标话题和末端坐标话题，进行轨迹验证
    并在仿真器中显示平滑的动画过程
    """
    
    # 定义信号
    log_signal = Signal(str)                    # 日志信号
    ui_update_signal = Signal(list, list)       # UI更新信号 (动平台坐标, 滑块坐标)
    simulator_update_signal = Signal(list)      # 仿真器更新信号 (动平台坐标)
    execution_progress = Signal(int, int)       # 执行进度信号 (当前点, 总点数)
    execution_completed = Signal(bool)          # 执行完成信号
    trajectory_verified = Signal(list)          # 轨迹验证完成信号
    animation_update = Signal(list, list)       # 动画更新信号 (动平台坐标, 滑块坐标)
    
    def __init__(self, mqtt_handler, kinematics, simulator_window=None):
        """
        初始化P2P点动模块
        
        参数:
        mqtt_handler: MQTT通信处理器
        kinematics: 运动学计算对象
        simulator_window: 仿真器窗口对象
        """
        super().__init__()
        self.mqtt_handler = mqtt_handler
        self.kinematics = kinematics
        self.simulator_window = simulator_window
        
        # 轨迹规划器
        from kinematics.trajectory import TrajectoryPlanner
        self.planner = TrajectoryPlanner()
        
        # 当前机器人位置（需要从外部更新）
        self.current_robot_pos = [0.0, 0.0, -410.0]
        
        # 轨迹执行参数
        self.current_trajectory = []
        self.is_executing = False
        self.is_animating = False
        
        # 动画定时器
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._animation_step)
        self.animation_speed = 50.0  # 动画速度 (mm/s)
        self.animation_index = 0
        self.animation_trajectory = []
        self.animation_interval = 50  # 动画更新间隔 (ms)
        
        # 默认参数
        self.default_speed = 50.0  # 默认速度 (mm/s)
        
        # 工作空间限位 (单位：mm)
        self.workspace_limits = {
            'x_min': -200,
            'x_max': 200,
            'y_min': -200,
            'y_max': 200,
            'z_min': -590,
            'z_max': -390
        }
        
        # 滑块限位 (单位：mm)
        self.slider_limits = {
            'min': -337,
            'max': -30
        }
        
        # 话题定义
        self.TOPIC_P2P_INITIAL = "card/0/position/control/p2p_initial"  # 初始坐标话题
        self.TOPIC_P2P_TARGET = "card/0/position/control/p2p"          # 末端坐标话题
        self.TOPIC_ROBOT_COMMAND = "card/0/robot/in/command"           # 机器人命令话题
        
        self.log_signal.emit("P2P点动模块初始化完成")
    
    def update_current_position(self, position):
        """
        更新当前机器人位置
        
        参数:
        position (list): 当前位置 [x, y, z]
        """
        if isinstance(position, np.ndarray):
            position = position.tolist()
        self.current_robot_pos = list(position)
    
    def check_workspace_limits(self, position):
        """
        检查位置是否在工作空间范围内
        
        参数:
        position (list): 位置 [x, y, z]
        
        返回:
        bool: 是否在限位范围内
        str: 错误信息（如果超出限位）
        """
        try:
            x, y, z = position
            
            if x < self.workspace_limits['x_min']:
                return False, f"X轴超出下限: {x:.1f} < {self.workspace_limits['x_min']}"
            if x > self.workspace_limits['x_max']:
                return False, f"X轴超出上限: {x:.1f} > {self.workspace_limits['x_max']}"
            if y < self.workspace_limits['y_min']:
                return False, f"Y轴超出下限: {y:.1f} < {self.workspace_limits['y_min']}"
            if y > self.workspace_limits['y_max']:
                return False, f"Y轴超出上限: {y:.1f} > {self.workspace_limits['y_max']}"
            if z < self.workspace_limits['z_min']:
                return False, f"Z轴超出下限: {z:.1f} < {self.workspace_limits['z_min']}"
            if z > self.workspace_limits['z_max']:
                return False, f"Z轴超出上限: {z:.1f} > {self.workspace_limits['z_max']}"
            
            return True, ""
        except Exception as e:
            return False, f"检查工作空间限位失败: {str(e)}"
    
    def check_slider_limits(self, sliders):
        """
        检查滑块位置是否在限位范围内
        
        参数:
        sliders (list): 滑块位置 [s1, s2, s3]
        
        返回:
        bool: 是否在限位范围内
        str: 错误信息（如果超出限位）
        """
        try:
            for i, pos in enumerate(sliders):
                if pos < self.slider_limits['min']:
                    return False, f"滑块{i+1}超出下限: {pos:.1f} < {self.slider_limits['min']}"
                if pos > self.slider_limits['max']:
                    return False, f"滑块{i+1}超出上限: {pos:.1f} > {self.slider_limits['max']}"
            return True, ""
        except Exception as e:
            return False, f"检查滑块限位失败: {str(e)}"
    
    def generate_and_validate_trajectory(self, start_pos, end_pos, num_points=50):
        """
        生成并验证轨迹
        
        参数:
        start_pos (list): 起点坐标 [x, y, z]
        end_pos (list): 终点坐标 [x, y, z]
        num_points (int): 插补点数
        
        返回:
        tuple: (是否成功, 轨迹点列表, 错误信息)
        """
        try:
            # 1. 检查起点和终点限位
            valid_start, start_msg = self.check_workspace_limits(start_pos)
            if not valid_start:
                return False, [], f"起点限位警告: {start_msg}"
                
            valid_end, end_msg = self.check_workspace_limits(end_pos)
            if not valid_end:
                return False, [], f"终点限位警告: {end_msg}"
            
            # 2. 生成线性轨迹
            trajectory = self.planner.linear_trajectory(start_pos, end_pos, num_points)
            
            # 3. 检查轨迹上每个点是否可达且符合限位
            invalid_points = []
            valid_trajectory = []
            
            for i, point in enumerate(trajectory):
                # 检查工作空间限位
                valid_ws, ws_msg = self.check_workspace_limits(point)
                if not valid_ws:
                    invalid_points.append(f"点{i}: {ws_msg}")
                    continue
                
                # 计算逆运动学
                sliders = self.kinematics.inverse_kinematics(point)
                if sliders is None:
                    invalid_points.append(f"点{i}: 不可达 ({point[0]:.1f}, {point[1]:.1f}, {point[2]:.1f})")
                    continue
                    
                # 检查滑块限位
                valid_slider, slider_msg = self.check_slider_limits(sliders)
                if not valid_slider:
                    invalid_points.append(f"点{i}: {slider_msg}")
                    continue
                
                # 点有效，加入轨迹
                valid_trajectory.append(point)
            
            if invalid_points:
                error_msg = f"轨迹验证失败，{len(invalid_points)}个点有问题:\n" + "\n".join(invalid_points[:5])
                if len(invalid_points) > 5:
                    error_msg += f"\n... 共{len(invalid_points)}个错误点"
                return False, [], error_msg
            
            return True, valid_trajectory, "轨迹验证通过"
            
        except Exception as e:
            return False, [], f"轨迹生成失败: {str(e)}"
    
    def send_p2p_initial_position(self, position):
        """
        发送初始坐标到话题
        
        参数:
        position (list): 初始坐标 [x, y, z]
        
        返回:
        bool: 是否成功
        """
        if not self.mqtt_handler or not self.mqtt_handler.is_connected:
            self.log_signal.emit("未连接到MQTT Broker，无法发送初始坐标")
            return False
        
        payload = {
            "x": float(position[0]),
            "y": float(position[1]),
            "z": float(position[2])
        }
        
        try:
            self.mqtt_handler.client.publish(self.TOPIC_P2P_INITIAL, json.dumps(payload), qos=1)
            self._log_p2p_message("初始坐标", payload)
            self.log_signal.emit(f"初始坐标已发送: X={position[0]:.1f}, Y={position[1]:.1f}, Z={position[2]:.1f}")
            return True
        except Exception as e:
            self.log_signal.emit(f"发送初始坐标失败: {str(e)}")
            return False
    
    def send_p2p_target_position(self, position, speed=None):
        """
        发送末端坐标到话题
        
        参数:
        position (list): 末端坐标 [x, y, z]
        speed (float): 移动速度 (可选)
        
        返回:
        bool: 是否成功
        """
        if not self.mqtt_handler or not self.mqtt_handler.is_connected:
            self.log_signal.emit("未连接到MQTT Broker，无法发送末端坐标")
            return False
        
        payload = {
            "x": float(position[0]),
            "y": float(position[1]),
            "z": float(position[2])
        }
        
        # 添加速度参数（如果提供）
        if speed is not None:
            payload["velocity"] = float(speed)
        
        try:
            self.mqtt_handler.client.publish(self.TOPIC_P2P_TARGET, json.dumps(payload), qos=1)
            self._log_p2p_message("末端坐标", payload)
            
            speed_msg = f", 速度={speed:.1f}mm/s" if speed is not None else ""
            self.log_signal.emit(f"末端坐标已发送: X={position[0]:.1f}, Y={position[1]:.1f}, Z={position[2]:.1f}{speed_msg}")
            return True
        except Exception as e:
            self.log_signal.emit(f"发送末端坐标失败: {str(e)}")
            return False
    
    def start_trajectory_animation(self, trajectory, animation_speed=None):
        """
        开始轨迹动画
        
        参数:
        trajectory (list): 轨迹点列表
        animation_speed (float): 动画速度 (mm/s)
        
        返回:
        bool: 动画是否成功启动
        """
        if not trajectory or len(trajectory) < 2:
            self.log_signal.emit("错误: 无效的轨迹点")
            return False
        
        if self.is_animating:
            self.stop_animation()
        
        self.animation_trajectory = trajectory
        self.animation_index = 0
        
        # 设置动画速度
        if animation_speed is not None:
            self.animation_speed = animation_speed
        
        # 计算动画间隔
        self._calculate_animation_interval(trajectory, self.animation_speed)
        
        # 启动动画定时器
        self.is_animating = True
        self.animation_timer.start(self.animation_interval)
        
        self.log_signal.emit(f"开始轨迹动画，共{len(trajectory)}个点，速度={self.animation_speed:.1f}mm/s")
        return True
    
    def _calculate_animation_interval(self, trajectory, speed):
        """
        根据轨迹和速度计算动画间隔
        
        参数:
        trajectory (list): 轨迹点列表
        speed (float): 动画速度 (mm/s)
        """
        if len(trajectory) < 2:
            self.animation_interval = 100  # 默认100ms
            return
        
        # 计算总距离
        total_distance = 0
        for i in range(1, len(trajectory)):
            p1 = np.array(trajectory[i-1])
            p2 = np.array(trajectory[i])
            total_distance += np.linalg.norm(p2 - p1)
        
        # 计算总时间
        if speed > 0:
            total_time = total_distance / speed * 1000  # 转换为毫秒
        else:
            total_time = 2000  # 默认2秒
        
        # 计算每个点之间的间隔
        if len(trajectory) > 1:
            self.animation_interval = max(10, min(100, int(total_time / (len(trajectory) - 1))))
        else:
            self.animation_interval = 50
        
        self.log_signal.emit(f"动画参数: 总距离={total_distance:.1f}mm, 间隔={self.animation_interval}ms")
    
    def _animation_step(self):
        """
        动画步进，更新当前位置到下一个轨迹点
        """
        if not self.is_animating or self.animation_index >= len(self.animation_trajectory):
            self.stop_animation()
            return
        
        try:
            # 获取当前目标点
            target_point = self.animation_trajectory[self.animation_index]
            
            # 计算滑块位置
            sliders = self.kinematics.inverse_kinematics(target_point)
            
            if sliders is not None:
                # 发送动画更新信号
                self.animation_update.emit(target_point, sliders)
                
                # 更新UI
                self.ui_update_signal.emit(target_point, sliders)
                
                # 更新仿真器
                if self.simulator_window:
                    self.simulator_update_signal.emit(target_point)
                
                # 更新当前位置
                self.current_robot_pos = list(target_point)
                
                # 发送进度信号
                self.execution_progress.emit(
                    self.animation_index + 1, 
                    len(self.animation_trajectory)
                )
            else:
                self.log_signal.emit(f"警告: 轨迹点{self.animation_index}不可达")
            
            self.animation_index += 1
            
            # 检查是否完成
            if self.animation_index >= len(self.animation_trajectory):
                self.log_signal.emit("轨迹动画完成")
                self.execution_completed.emit(True)
                self.stop_animation()
                
        except Exception as e:
            self.log_signal.emit(f"动画步进失败: {str(e)}")
            self.stop_animation()
    
    def stop_animation(self):
        """
        停止动画
        """
        self.is_animating = False
        if self.animation_timer.isActive():
            self.animation_timer.stop()
        self.log_signal.emit("轨迹动画已停止")
    
    def move_p2p_with_validation(self, start_pos, end_pos, num_points=50, speed=None, 
                                simulator_enabled=False, update_ui=True, animate_trajectory=True):
        """
        执行带验证的P2P直线运动（带平滑动画）
        
        参数:
        start_pos (list): 起点坐标 [x, y, z]
        end_pos (list): 终点坐标 [x, y, z]
        num_points (int): 插补点数（用于验证和动画）
        speed (float): 移动速度
        simulator_enabled (bool): 是否启用仿真器
        update_ui (bool): 是否更新UI
        animate_trajectory (bool): 是否进行轨迹动画
        
        返回:
        bool: 操作是否成功
        """
        try:
            self.log_signal.emit("开始P2P直线运动验证...")
            
            # 1. 生成并验证轨迹
            success, trajectory, message = self.generate_and_validate_trajectory(
                start_pos, end_pos, num_points
            )
            
            if not success:
                self.log_signal.emit(f"轨迹验证失败: {message}")
                return False
            
            self.log_signal.emit(f"轨迹验证通过: {len(trajectory)}个点全部有效")
            
            # 2. 设置当前轨迹
            self.current_trajectory = trajectory
            
            # 3. 发送初始坐标
            initial_success = self.send_p2p_initial_position(start_pos)
            if not initial_success:
                return False
            
            # 4. 更新UI到起点位置
            if update_ui:
                start_sliders = self.kinematics.inverse_kinematics(start_pos)
                if start_sliders is not None:
                    self.ui_update_signal.emit(start_pos, start_sliders)
                    self.current_robot_pos = list(start_pos)
            
            # 5. 更新仿真器显示轨迹
            if simulator_enabled and self.simulator_window:
                # 传递完整轨迹给仿真器显示
                self.simulator_window.set_trajectory(trajectory)
                # 立即更新到起点位置
                self.simulator_window.update_robot_state(start_pos)
            
            # 6. 发送末端坐标（触发实际运动）
            target_success = self.send_p2p_target_position(end_pos, speed)
            if not target_success:
                return False
            
            # 7. 触发轨迹验证完成信号
            self.trajectory_verified.emit(trajectory)
            
            # 8. 开始轨迹动画（如果启用）
            if animate_trajectory and simulator_enabled and trajectory:
                animation_speed = speed if speed is not None else self.default_speed
                self.start_trajectory_animation(trajectory, animation_speed)
            elif update_ui:
                # 如果不动画，直接更新到终点
                end_sliders = self.kinematics.inverse_kinematics(end_pos)
                if end_sliders is not None:
                    self.ui_update_signal.emit(end_pos, end_sliders)
                    self.current_robot_pos = list(end_pos)
                    
                    if simulator_enabled and self.simulator_window:
                        self.simulator_window.update_robot_state(end_pos)
            
            self.log_signal.emit(f"P2P直线运动指令已发送: {start_pos} -> {end_pos}")
            
            return True
            
        except Exception as e:
            self.log_signal.emit(f"P2P运动失败: {str(e)}")
            traceback.print_exc()
            return False
    
    def move_p2p(self, start_pos, end_pos, num_points=50, speed=None, simulator_enabled=False):
        """
        执行点到点直线运动（兼容旧接口）
        
        参数:
        start_pos (list): 起点坐标 [x, y, z]
        end_pos (list): 终点坐标 [x, y, z]
        num_points (int): 插补点数
        speed (float): 移动速度 (可选)
        simulator_enabled (bool): 是否启用仿真器
        
        返回:
        bool: 操作是否成功
        """
        return self.move_p2p_with_validation(
            start_pos, end_pos, num_points, speed, simulator_enabled, 
            update_ui=True, animate_trajectory=True
        )
    
    def move_to_position_p2p(self, target_pos, num_points=50, speed=None, simulator_enabled=False):
        """
        从当前位置移动到目标位置（P2P）
        
        参数:
        target_pos (list): 目标坐标 [x, y, z]
        num_points (int): 插补点数
        speed (float): 移动速度 (可选)
        simulator_enabled (bool): 是否启用仿真器
        
        返回:
        bool: 操作是否成功
        """
        return self.move_p2p_with_validation(
            self.current_robot_pos, target_pos, num_points, speed, simulator_enabled, 
            update_ui=True, animate_trajectory=True
        )
    
    def get_trajectory_info(self):
        """
        获取轨迹信息
        
        返回:
        dict: 轨迹信息
        """
        return {
            'point_count': len(self.current_trajectory),
            'start_point': self.current_trajectory[0] if self.current_trajectory else None,
            'end_point': self.current_trajectory[-1] if self.current_trajectory else None,
            'trajectory': self.current_trajectory
        }
    
    def set_speed(self, speed):
        """
        设置运动速度
        
        参数:
        speed (float): 速度 (mm/s)
        """
        self.default_speed = float(speed)
        self.log_signal.emit(f"P2P运动速度设置为: {speed:.1f} mm/s")
    
    def set_animation_speed(self, speed):
        """
        设置动画速度
        
        参数:
        speed (float): 动画速度 (mm/s)
        """
        self.animation_speed = float(speed)
        self.log_signal.emit(f"动画速度设置为: {speed:.1f} mm/s")
    
    def set_workspace_limits(self, x_min, x_max, y_min, y_max, z_min, z_max):
        """
        设置工作空间限位
        """
        self.workspace_limits = {
            'x_min': float(x_min),
            'x_max': float(x_max),
            'y_min': float(y_min),
            'y_max': float(y_max),
            'z_min': float(z_min),
            'z_max': float(z_max)
        }
        self.log_signal.emit(f"工作空间限位设置: X[{x_min:.1f}, {x_max:.1f}], Y[{y_min:.1f}, {y_max:.1f}], Z[{z_min:.1f}, {z_max:.1f}]")
    
    def set_slider_limits(self, min_limit, max_limit):
        """
        设置滑块限位
        """
        self.slider_limits['min'] = float(min_limit)
        self.slider_limits['max'] = float(max_limit)
        self.log_signal.emit(f"滑块限位设置: {min_limit:.1f} ~ {max_limit:.1f} mm")
    
    def emergency_stop(self):
        """
        急停功能
        """
        try:
            self.stop_animation()
            self.log_signal.emit("P2P模块执行急停")
            
            # 构造急停消息
            emergency_data = {
                "header": {
                    "stamp": time.time(),
                    "frame_id": "emergency_stop"
                },
                "command": "emergency_stop",
                "priority": 255,
                "source": "p2p_move_module"
            }
            
            # 发送急停指令
            if self.mqtt_handler.is_connected:
                json_str = json.dumps(emergency_data, indent=2)
                self.mqtt_handler.client.publish(self.TOPIC_ROBOT_COMMAND, json_str, qos=2)
                self._log_ros_message(self.TOPIC_ROBOT_COMMAND, emergency_data)
            
            return True
            
        except Exception as e:
            self.log_signal.emit(f"P2P急停失败: {str(e)}")
            traceback.print_exc()
            return False
    
    def _log_p2p_message(self, topic_type, data):
        """
        按P2P话题格式显示消息内容
        """
        try:
            output_lines = [f"P2P {topic_type}消息:"]
            
            if "x" in data:
                output_lines.append(f"  x: {data['x']:.3f}")
            if "y" in data:
                output_lines.append(f"  y: {data['y']:.3f}")
            if "z" in data:
                output_lines.append(f"  z: {data['z']:.3f}")
            if "velocity" in data:
                output_lines.append(f"  velocity: {data['velocity']:.1f}")
            
            output_lines.append("---")
            
            for line in output_lines:
                self.log_signal.emit(line)
                
        except Exception as e:
            self.log_signal.emit(f"格式化P2P消息失败: {str(e)}")
    
    def _log_ros_message(self, topic, data):
        """
        按ROS话题格式竖向显示消息内容
        """
        try:
            output_lines = [f"Published to {topic}:"]
            
            if "header" in data:
                output_lines.extend([
                    f"header:",
                    f"  stamp: {data['header'].get('stamp', 0):.6f}",
                    f"  frame_id: \"{data['header'].get('frame_id', '')}\""
                ])
            
            if "command" in data:
                output_lines.extend([
                    f"command: \"{data['command']}\"",
                    f"priority: {data.get('priority', 0)}",
                    f"source: \"{data.get('source', '')}\""
                ])
            
            output_lines.append(f"---")
            
            for line in output_lines:
                self.log_signal.emit(line)
                
        except Exception as e:
            self.log_signal.emit(f"格式化ROS消息失败: {str(e)}")