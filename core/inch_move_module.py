# inch_move_module.py - 优化为微小点动版

import numpy as np
from PySide6.QtCore import QObject, Signal
import traceback
import time
import json

class InchMoveModule(QObject):
    """
    Delta机器人寸动模块 - 优化为微小点动版
    使用P2P位置控制话题进行微小步长的点动
    """
    
    # 定义信号
    log_signal = Signal(str)                    # 日志信号
    ui_update_signal = Signal(list, list)       # UI更新信号 (动平台坐标, 滑块坐标)
    simulator_update_signal = Signal(list)      # 仿真器更新信号 (动平台坐标)
    
    def __init__(self, mqtt_handler, kinematics, simulator_window=None):
        """
        初始化寸动模块
        
        参数:
        mqtt_handler: MQTT通信处理器
        kinematics: 运动学计算对象
        simulator_window: 仿真器窗口对象
        """
        super().__init__()
        self.mqtt_handler = mqtt_handler
        self.kinematics = kinematics
        self.simulator_window = simulator_window
        
        # 当前机器人位置（需要从外部更新）
        self.current_robot_pos = [0.0, 0.0, -410.0]
        
        # 寸动参数
        self.micro_step_size = 1.0  # 微小步长 (mm) - 默认1mm
        self.default_step = 10.0    # 默认寸动步长 (mm) - 兼容旧接口
        
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
            'min': -337,  # 滑块下限
            'max': -30    # 滑块上限
        }
        
        self.log_signal.emit("寸动模块初始化完成（微小点动模式）")
    
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
    
    def move_micro_inch(self, axis_idx, delta, simulator_enabled=False, speed=None, validate_only=False):
        """
        执行微小点动（使用P2P位置控制话题）
        
        参数:
        axis_idx (int): 轴索引 (0:X, 1:Y, 2:Z)
        delta (float): 移动距离 (mm)
        simulator_enabled (bool): 是否启用仿真器
        speed (float): 移动速度 (可选)
        validate_only (bool): 仅验证不发送
        
        返回:
        bool: 操作是否成功
        """
        try:
            # 1. 计算新的动平台目标位置
            new_pos = list(self.current_robot_pos)
            new_pos[axis_idx] += float(delta)
            
            # 2. 检查工作空间限位
            valid_workspace, workspace_msg = self.check_workspace_limits(new_pos)
            if not valid_workspace:
                self.log_signal.emit(f"限位警告: {workspace_msg}")
                return False
            
            # 3. 检查目标位置是否可达
            new_sliders = self.kinematics.inverse_kinematics(new_pos)
            if new_sliders is None:
                self.log_signal.emit(f"警告: 目标位置不可达 ({new_pos[0]:.1f}, {new_pos[1]:.1f}, {new_pos[2]:.1f})")
                return False
            
            # 4. 检查滑块限位
            valid_slider, slider_msg = self.check_slider_limits(new_sliders)
            if not valid_slider:
                self.log_signal.emit(f"限位警告: {slider_msg}")
                return False
            
            # 5. 如果仅验证，返回成功
            if validate_only:
                return True
            
            # 6. 发送到P2P位置控制话题（使用绝对坐标）
            success = self.mqtt_handler.send_p2p_target_position(new_pos, speed)
            
            if success:
                # 7. 发送更新信号
                self.ui_update_signal.emit(new_pos, new_sliders)
                if simulator_enabled and self.simulator_window:
                    self.simulator_update_signal.emit(new_pos)
                    
                # 8. 更新内部状态
                self.current_robot_pos = new_pos
                
                axis_names = ['X', 'Y', 'Z']
                self.log_signal.emit(f"微小点动完成: {axis_names[axis_idx]}轴 {delta:+.3f}mm -> ({new_pos[0]:.1f}, {new_pos[1]:.1f}, {new_pos[2]:.1f})")
            
            return success
            
        except Exception as e:
            self.log_signal.emit(f"微小点动操作失败: {str(e)}")
            traceback.print_exc()
            return False
    
    # def move_inch(self, axis_idx, delta, simulator_enabled=False, speed=None):
    #     """
    #     执行寸动（兼容旧接口，使用微小点动）
        
    #     参数:
    #     axis_idx (int): 轴索引 (0:X, 1:Y, 2:Z)
    #     delta (float): 移动距离 (mm)
    #     simulator_enabled (bool): 是否启用仿真器
    #     speed (float): 移动速度 (可选)
        
    #     返回:
    #     bool: 操作是否成功
    #     """
    #     # 调用微小点动函数
    #     return self.move_micro_inch(axis_idx, delta, simulator_enabled, speed, validate_only=False)
    
    def move_to_position(self, x, y, z, simulator_enabled=False, speed=None):
        """
        移动到指定位置（使用P2P位置控制话题）
        
        参数:
        x, y, z (float): 目标坐标
        simulator_enabled (bool): 是否启用仿真器
        speed (float): 移动速度 (可选)
        
        返回:
        bool: 操作是否成功
        """
        try:
            target_pos = [float(x), float(y), float(z)]
            
            # 1. 检查工作空间限位
            valid_workspace, workspace_msg = self.check_workspace_limits(target_pos)
            if not valid_workspace:
                self.log_signal.emit(f"限位警告: {workspace_msg}")
                return False
            
            # 2. 检查目标位置是否可达
            new_sliders = self.kinematics.inverse_kinematics(target_pos)
            if new_sliders is None:
                self.log_signal.emit(f"警告: 目标位置({x:.1f}, {y:.1f}, {z:.1f})不可达")
                return False
            
            # 3. 检查滑块限位
            valid_slider, slider_msg = self.check_slider_limits(new_sliders)
            if not valid_slider:
                self.log_signal.emit(f"限位警告: {slider_msg}")
                return False
            
            # 4. 发送到P2P位置控制话题
            success = self.mqtt_handler.send_p2p_target_position(target_pos, speed)
            
            if success:
                # 5. 发送更新信号
                self.ui_update_signal.emit(target_pos, new_sliders)
                if simulator_enabled and self.simulator_window:
                    self.simulator_update_signal.emit(target_pos)
                    
                # 6. 更新内部状态
                self.current_robot_pos = target_pos
                
                self.log_signal.emit(f"移动到位置: ({x:.1f}, {y:.1f}, {z:.1f})")
            
            return success
            
        except Exception as e:
            self.log_signal.emit(f"移动到指定位置失败: {str(e)}")
            traceback.print_exc()
            return False
    
    def validate_micro_move(self, axis_idx, delta):
        """
        验证微小移动是否可行（不实际发送）
        
        参数:
        axis_idx (int): 轴索引 (0:X, 1:Y, 2:Z)
        delta (float): 移动距离 (mm)
        
        返回:
        tuple: (是否成功, 新位置, 错误信息)
        """
        try:
            # 计算新的动平台目标位置
            new_pos = list(self.current_robot_pos)
            new_pos[axis_idx] += float(delta)
            
            # 检查工作空间限位
            valid_workspace, workspace_msg = self.check_workspace_limits(new_pos)
            if not valid_workspace:
                return False, new_pos, workspace_msg
            
            # 检查目标位置是否可达
            new_sliders = self.kinematics.inverse_kinematics(new_pos)
            if new_sliders is None:
                return False, new_pos, f"目标位置不可达 ({new_pos[0]:.1f}, {new_pos[1]:.1f}, {new_pos[2]:.1f})"
            
            # 检查滑块限位
            valid_slider, slider_msg = self.check_slider_limits(new_sliders)
            if not valid_slider:
                return False, new_pos, slider_msg
            
            return True, new_pos, "验证通过"
            
        except Exception as e:
            return False, None, f"验证失败: {str(e)}"
    
    def set_micro_step_size(self, step):
        """
        设置微小点动步长
        
        参数:
        step (float): 微小步长 (mm)
        """
        self.micro_step_size = float(step)
        self.log_signal.emit(f"微小点动步长设置为: {step:.3f} mm")
    
    def set_step_size(self, step):
        """
        设置寸动步长（兼容旧接口）
        
        参数:
        step (float): 步长 (mm)
        """
        self.default_step = float(step)
        self.log_signal.emit(f"寸动步长设置为: {step:.1f} mm")
    
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

    def emergency_stop(self, stop_state=True):
        """
        急停功能
        """
        try:
            # self.log_signal.emit("寸动模块执行急停")
            
            # 使用MQTT处理器的急停功能
            if self.mqtt_handler and self.mqtt_handler.is_connected:
                self.mqtt_handler.send_emergency_stop(stop_state)

            if stop_state:
                # 停止所有本地定时器/动画
                if hasattr(self, 'animation_timer'):
                    self.animation_timer.stop()
                self.log_signal.emit("寸动模块急停激活")
            else:
                self.log_signal.emit("寸动模块急停解除")
                
            return True
            
        except Exception as e:
            self.log_signal.emit(f"寸动急停失败: {str(e)}")
            traceback.print_exc()
            return False
    
    def get_current_position(self):
        """
        获取当前位置
        
        返回:
        list: 当前位置 [x, y, z]
        """
        return self.current_robot_pos.copy()
    
    def get_micro_step_size(self):
        """
        获取微小点动步长
        
        返回:
        float: 微小步长 (mm)
        """
        return self.micro_step_size