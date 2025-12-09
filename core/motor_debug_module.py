# -*- coding: utf-8 -*-
# motor_debug_module.py
# Delta机器人电机调试模块

import numpy as np
from PySide6.QtCore import QObject, Signal
import traceback
import time
import json

class MotorDebugModule(QObject):
    """
    Delta机器人电机调试模块
    负责单轴电机的调试移动功能
    """
    
    # 定义信号
    log_signal = Signal(str)                    # 日志信号
    ui_update_signal = Signal(list, list)       # UI更新信号 (动平台坐标, 滑块坐标)
    simulator_update_signal = Signal(list)       # 仿真器更新信号 (滑块坐标)
    
    def __init__(self, mqtt_handler, kinematics, simulator_window=None):
        """
        初始化电机调试模块
        
        参数:
        mqtt_handler: MQTT通信处理器
        kinematics: 运动学计算对象
        simulator_window: 仿真器窗口对象
        """
        super().__init__()
        self.mqtt_handler = mqtt_handler
        self.kinematics = kinematics
        self.simulator_window = simulator_window
        
        # 默认参数
        self.default_pulse_step = 1000  # 默认脉冲步长
        
        # 滑块限位 (单位：mm)
        self.slider_limits = {
            'min': -337,  # 滑块下限
            'max': -30    # 滑块上限
        }
        
        # 工作空间限位 (单位：mm)
        self.workspace_limits = {
            'x_min': -200,
            'x_max': 200,
            'y_min': -200,
            'y_max': 200,
            'z_min': -590,  # 根据运动学参数设置
            'z_max': -390
        }
        
        # 话题定义
        self.TOPIC_SLIDER_VEL = "card/0/slider/control/vel"
        self.TOPIC_SLIDER_POSITION = "card/0/slider/control/position"
        self.TOPIC_ROBOT_COMMAND = "card/0/robot/in/command"
        self.TOPIC_ROBOT_STATUS = "card/0/robot/out/status"
                
        self.log_signal.emit("电机调试模块初始化完成")
    
    def check_slider_limits(self, slider_positions):
        """
        检查滑块位置是否在限位范围内
        
        参数:
        slider_positions (list): 滑块位置 [s1, s2, s3]
        
        返回:
        bool: 是否在限位范围内
        str: 错误信息（如果超出限位）
        """
        try:
            for i, pos in enumerate(slider_positions):
                if pos < self.slider_limits['min']:
                    return False, f"滑块{i+1}超出下限: {pos:.1f} < {self.slider_limits['min']}"
                if pos > self.slider_limits['max']:
                    return False, f"滑块{i+1}超出上限: {pos:.1f} > {self.slider_limits['max']}"
            return True, ""
        except Exception as e:
            # return False, f"检查滑块限位失败: {str(e)}"
            return True, ""
    
    def check_workspace_limits(self, platform_position):
        """
        检查动平台位置是否在工作空间范围内
        
        参数:
        platform_position (list): 动平台位置 [x, y, z]
        
        返回:
        bool: 是否在限位范围内
        str: 错误信息（如果超出限位）
        """
        try:
            x, y, z = platform_position
            
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
            # return False, f"检查工作空间限位失败: {str(e)}"
            return True, ""


    def move_motor(self, motor_idx, delta_mm, simulator_enabled=False, use_velocity_control=False):
        """
        移动单个滑块
        
        参数:
        motor_idx (int): 电机索引 (0, 1, 2)
        delta_mm (float): 移动距离 (mm)
        simulator_enabled (bool): 是否启用仿真器
        use_velocity_control (bool): 是否使用速度控制模式
        
        返回:
        bool: 操作是否成功
        """
        try:
            # 1. 获取当前滑块位置
            current_sliders = [0, 0, 0]
            if self.simulator_window:
                current_sliders = list(self.simulator_window.current_sliders_z)
            
            # 2. 计算新的滑块位置
            new_sliders = current_sliders.copy()
            new_sliders[motor_idx] += delta_mm
            
            # 3. 检查滑块限位
            valid_slider, slider_msg = self.check_slider_limits(new_sliders)
            if not valid_slider:
                self.log_signal.emit(f"限位警告: {slider_msg}")
                return False
            
            # 4. 计算动平台位置并检查工作空间限位
            platform_pos = self.kinematics.forward_kinematics(new_sliders)
            if platform_pos is not None:
                valid_workspace, workspace_msg = self.check_workspace_limits(platform_pos)
                if not valid_workspace:
                    self.log_signal.emit(f"限位警告: {workspace_msg}")
                    return False
            
            # 5. 发送滑块控制指令
            success = False
            if use_velocity_control:
                # 速度控制模式
                if delta_mm > 0:
                    speed_1 = 5.0  # 默认速度 10 mm/s      ////////////////////////////////////////////////////////////////////////////
                    speed_2 = 5.0
                    success = self.mqtt_handler.send_slider_velocity(motor_idx, speed_1, speed_2)
                    time.sleep(0.05)  # 短暂延迟，确保速度设置生效
                    success = success and self.mqtt_handler.send_slider_position(motor_idx, new_sliders[motor_idx])
                    # print(delta_mm)
                    time.sleep(2)
                    speed_1 = 0.0
                    speed_2 = 0.0
                    success = self.mqtt_handler.send_slider_velocity(motor_idx, speed_1, speed_2)
                else:
                    speed_1 = -5.0  # 默认速度 10 mm/s      ////////////////////////////////////////////////////////////////////////////
                    speed_2 = -5.0                    
                    success = self.mqtt_handler.send_slider_velocity(motor_idx, speed_1, speed_2)
                    time.sleep(0.05)  # 短暂延迟，确保速度设置生效
                    success = success and self.mqtt_handler.send_slider_position(motor_idx, new_sliders[motor_idx])
                    time.sleep(2)
                    speed_1 = 0.0
                    speed_2 = 0.0
                    success = self.mqtt_handler.send_slider_velocity(motor_idx, speed_1, speed_2)
            
                # speed = 5.0  # 默认速度 10 mm/s      ////////////////////////////////////////////////////////////////////////////
                # success = self.mqtt_handler.send_slider_velocity(motor_idx, speed, speed)
                # time.sleep(0.05)  # 短暂延迟，确保速度设置生效

                # new_sliders = current_sliders.copy()
                # new_sliders[motor_idx] += delta_mm

                # success = success and self.mqtt_handler.move_slider_absolute(motor_idx, new_sliders[motor_idx], speed=10.0)

                # # success = success and self.mqtt_handler.move_slider_relative(motor_idx, 10, speed=10.0)

                # # success = success and self.mqtt_handler.send_slider_position(motor_idx, new_sliders[motor_idx])

            else:
                # 直接位置控制模式
                success = self.mqtt_handler.send_slider_position(motor_idx, new_sliders[motor_idx])
            
            if success:
                # 6. 发送更新信号
                if platform_pos is not None:
                    self.ui_update_signal.emit(list(platform_pos), new_sliders)
                else:
                    self.ui_update_signal.emit(None, new_sliders)
                
                if simulator_enabled:
                    self.simulator_update_signal.emit(new_sliders)
                
                self.log_signal.emit(f"滑块{motor_idx+1}移动: {delta_mm:+.1f} mm")
            
            return success
            
        except Exception as e:
            self.log_signal.emit(f"滑块移动失败: {str(e)}")
            traceback.print_exc()
            return False
    
    def set_pulse_step(self, step):
        """
        设置脉冲步长
        
        参数:
        step (int): 脉冲步长
        """
        self.default_pulse_step = int(step)
        self.log_signal.emit(f"电机调试步长设置为: {step} 脉冲")
    
    def set_slider_limits(self, min_limit, max_limit):
        """
        设置滑块限位
        
        参数:
        min_limit (float): 滑块下限 (mm)
        max_limit (float): 滑块上限 (mm)
        """
        self.slider_limits['min'] = float(min_limit)
        self.slider_limits['max'] = float(max_limit)
        self.log_signal.emit(f"滑块限位设置: {min_limit:.1f} ~ {max_limit:.1f} mm")
    
    def set_workspace_limits(self, x_min, x_max, y_min, y_max, z_min, z_max):
        """
        设置工作空间限位
        
        参数:
        x_min, x_max (float): X轴限位
        y_min, y_max (float): Y轴限位
        z_min, z_max (float): Z轴限位
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
    
    def emergency_stop(self):
        """
        急停功能
        """
        try:
            self.log_signal.emit("电机调试模块执行急停")
            
            # 构造ROS风格的急停消息
            emergency_data = {
                "header": {
                    "stamp": time.time(),
                    "frame_id": "emergency_stop"
                },
                "command": "emergency_stop",
                "priority": 255,  # 最高优先级
                "source": "motor_debug_module"
            }
            
            # 发送急停指令到 card/0/motor/in/command 话题
            if self.mqtt_handler.is_connected:
                json_str = json.dumps(emergency_data, indent=2)
                self.mqtt_handler.client.publish(self.TOPIC_MOTOR_COMMAND, json_str, qos=2)
                
                # 按ROS话题格式竖向显示消息
                self._log_ros_message(self.TOPIC_MOTOR_COMMAND, emergency_data)
            
            return True
            
        except Exception as e:
            self.log_signal.emit(f"电机调试急停失败: {str(e)}")
            traceback.print_exc()
            return False
    
    def _log_ros_message(self, topic, data):
        """
        按ROS话题格式竖向显示消息内容
        
        参数:
        topic (str): 话题名称
        data (dict): 消息数据
        """
        try:
            # 构建ROS风格的输出
            output_lines = [
                f"Published to {topic}:",
                f"header:",
                f"  stamp: {data.get('header', {}).get('stamp', 0):.6f}",
                f"  frame_id: \"{data.get('header', {}).get('frame_id', '')}\""
            ]
            
            # 根据话题类型添加特定字段
            if "motor_id" in data:
                output_lines.extend([
                    f"motor_id: {data['motor_id']}",
                    f"command: \"{data['command']}\"",
                    f"pulse_delta: {data['pulse_delta']}",
                    f"target_position: [{', '.join([f'{x:.3f}' for x in data['target_position']])}]",
                    f"velocity: {data['velocity']:.1f}",
                    f"acceleration: {data['acceleration']:.1f}"
                ])
            elif "type" in data and data["type"] == "move_xyz":
                output_lines.extend([
                    f"type: \"{data['type']}\"",
                    f"position:",
                    f"  x: {data['x']:.3f}",
                    f"  y: {data['y']:.3f}",
                    f"  z: {data['z']:.3f}"
                ])
                if "speed" in data:
                    output_lines.append(f"speed: {data['speed']:.1f}")
            
            # 添加时间戳
            output_lines.append(f"---")
            
            # 发送日志信号
            for line in output_lines:
                self.log_signal.emit(line)
                
        except Exception as e:
            self.log_signal.emit(f"格式化ROS消息失败: {str(e)}")