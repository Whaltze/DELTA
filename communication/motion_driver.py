# 完整修复 motion_driver.py

from PySide6.QtCore import QObject, Signal, Slot, QThread
import time
import logging
import traceback
from control import IMCControl
from kinematics.kinematics import DeltaKinematics

class DeltaMotionController(QObject):
    # 信号定义保持不变
    update_serial_status = Signal(str)
    update_received_data = Signal(str)
    update_sent_data = Signal(str)
    update_end_effector = Signal(float, float, float)
    update_slider = Signal(float, float, float)
    connection_status_changed = Signal(bool)
    
    def __init__(self, lib_path, kinematics):
        super().__init__()
        
        # 初始化属性
        self.lib_path = lib_path
        self.kinematics = kinematics
        self.is_connected = False
        self.current_position = [0.0, 0.0, -300.0]
        self.current_sliders = [0.0, 0.0, 0.0]
        # 2. 运动学算法
        side_sp, side_ep, rod_len = 300.0, 100.0, 300.0
        sp_radius = side_sp / (3**0.5)
        ep_radius = side_ep / (3**0.5)
        self.kinematics = DeltaKinematics(sp=sp_radius, ep=ep_radius, rod_length=rod_len)
        self.pulses_per_mm = 100.0  # 每毫米脉冲数
        
        # 初始化控制卡实例
        try:
            # 检查库文件是否存在
            import os
            if not os.path.exists(lib_path):
                print(f"警告: 库文件不存在: {lib_path}")
                self.imc = None
            else:
                # 初始化控制卡
                self.imc = IMCControl(lib_path)
                print("控制卡实例化成功")
                
                # 尝试查找网卡（不连接）
                # success, cards = self.imc.find_net_card()
                # if success and cards:
                #     print(f"找到网卡: {cards}")
                # else:
                #     print("未找到网卡")
        except Exception as e:
            print(f"初始化控制卡失败: {e}")
            traceback.print_exc()
            self.imc = None

    def execute_trajectory(self, trajectory_points, speed_factor=1.0, wait_complete=True):
        """
        执行轨迹运动
        trajectory_points: 轨迹点列表，每个点为 [x, y, z]
        speed_factor: 速度因子 (0.1 ~ 2.0)
        wait_complete: 是否等待运动完成
        """
        if not self.is_connected or self.imc is None:
            self.log("错误: 控制卡未连接")
            return False
        
        try:
            self.log(f"开始执行轨迹，点数: {len(trajectory_points)}")
            
            success_count = 0
            total_points = len(trajectory_points)
            
            for i, point in enumerate(trajectory_points):
                if len(point) < 3:
                    continue
                    
                x, y, z = point[:3]
                
                # 显示进度
                if i % 10 == 0:
                    self.log(f"轨迹执行进度: {i+1}/{total_points}")
                
                # 移动到目标点
                point_success = self.move_to_xyz(x, y, z, wait=wait_complete)
                
                if point_success:
                    success_count += 1
                    
                    # 更新仿真器位置（通过信号）
                    self.update_end_effector.emit(x, y, z)
                    
                    # 短暂延迟，确保运动稳定
                    if i < total_points - 1 and wait_complete:
                        time.sleep(0.02 * speed_factor)
                else:
                    self.log(f"警告: 轨迹点 {i} 移动失败: ({x:.1f}, {y:.1f}, {z:.1f})")
            
            success_rate = success_count / total_points if total_points > 0 else 0
            self.log(f"轨迹执行完成，成功率: {success_rate:.1%}")
            
            return success_rate > 0.9  # 90%以上成功率视为成功
            
        except Exception as e:
            self.log(f"执行轨迹异常: {str(e)}")
            traceback.print_exc()
            return False

    def set_velocity_parameters(self, velocity=20.0, acceleration=100.0):
        """
        设置运动速度参数
        velocity: 速度 (脉冲/毫秒)
        acceleration: 加速度 (脉冲/毫秒²)
        """
        if not self.is_connected or self.imc is None:
            return False
        
        try:
            success = True
            for axis_num in range(3):
                # 设置加速度和减速度
                axis_success = self.imc.set_accel(axis_num, acceleration, acceleration)
                if not axis_success:
                    self.log(f"设置轴{axis_num}加速度失败")
                    success = False
                
                # 设置速度限制
                axis_success = self.imc.set_vel_acc_limit(axis_num, velocity * 2, acceleration * 2)
                if not axis_success:
                    self.log(f"设置轴{axis_num}速度限制失败")
                    success = False
            
            if success:
                self.log(f"速度参数设置: V={velocity:.1f}, A={acceleration:.1f}")
            
            return success
            
        except Exception as e:
            self.log(f"设置速度参数异常: {str(e)}")
            return False

    def sync_with_simulator(self, simulator):
        """
        同步控制卡与仿真器位置
        """
        try:
            # 获取控制卡当前位置
            positions = self.get_current_positions()
            if positions and len(positions) >= 3:
                # 将脉冲转换为毫米
                positions_mm = [self.pulse_to_mm(pos) for pos in positions[:3]]
                
                # 更新控制卡内部的滑块位置缓存
                self.current_sliders = positions_mm.copy()
                
                # 计算正运动学得到末端位置
                end_pos = self.kinematics.forward_kinematics(positions_mm)
                if end_pos is not None:
                    self.current_position = list(end_pos)
                    
                    # 更新仿真器
                    if simulator:
                        simulator.update_by_sliders(positions_mm)
                    
                    self.log(f"位置同步: 滑块={positions_mm}, 末端={end_pos}")
                    return True
            
            return False
            
        except Exception as e:
            self.log(f"同步位置异常: {str(e)}")
            return False    
    def find_net_cards(self):
        """查找可用的网卡"""
        try:
            if self.imc is None:
                return []
                
            success, cards = self.imc.find_net_card()
            if success:
                return cards
            else:
                return []
        except Exception as e:
            print(f"查找网卡失败: {e}")
            return []
    
    def log(self, message):
        """记录日志"""
        print(f"[DeltaMotionController] {message}")
        self.update_serial_status.emit(message)
    
    def connect_device(self, net_card_index=0, imc_id=0):
        """连接控制卡设备"""
        if self.is_connected:
            self.log("控制卡已连接")
            return True
            
        if self.imc is None:
            self.log("错误: 控制卡实例未初始化")
            return False
            
        
        try:
            # 先搜索网卡
            success, cards = self.imc.find_net_card()
            if not success or not cards:
                self.log("未找到可用网卡")
                return False
                
            self.log(f"找到网卡: {cards}")
            
            # 确保索引有效
            if net_card_index >= len(cards):
                net_card_index = 0
                self.log(f"网卡索引超出范围，使用默认索引: {net_card_index}")
            
            # 打开控制卡
            self.log(f"尝试连接控制卡 (网卡:{net_card_index}, ID:{imc_id})")
            open_success = self.imc.open_x(net_card_index, imc_id)
            
            if not open_success:
                self.log("打开控制卡失败")
                return False
                
            # # 初始化配置
            # init_success = self.imc.init_cfg()
            # if not init_success:
            #     self.log("初始化控制卡配置失败")
            #     # 关闭已打开的控制卡
            #     self.imc.close()
            #     return False
                
            self.is_connected = True
            self.log(f"成功连接到控制卡 (ID:{imc_id})")
            
            # 配置三个轴
            self._configure_axes()
            
            # 发射连接状态改变信号
            self.connection_status_changed.emit(True)
            
            return True
            
        except Exception as e:
            self.log(f"连接控制卡异常: {str(e)}")
            traceback.print_exc()
            return False
    
    def _configure_axes(self):
        """配置三个轴的基本参数"""
        if not self.is_connected or self.imc is None:
            return
            
        try:
            for axis_num in range(3):
                # 设置脉冲参数
                try:
                    self.imc.set_pul_width(axis_num, 2000)  # 脉冲宽度
                except:
                    pass  # 有些控制卡可能不需要这个
                
                try:
                    self.imc.set_pul_polar(axis_num, True, True)  # 脉冲极性
                except:
                    pass
                
                # 设置速度和加速度限制
                try:
                    vellim = 100.0  # 脉冲/毫秒
                    acclim = 500.0  # 脉冲/毫秒²
                    self.imc.set_vel_acc_limit(axis_num, vellim, acclim)
                except:
                    pass
                
                # 使能驱动器
                try:
                    self.imc.set_enable(axis_num, True)
                except:
                    pass
                
                # 设置平滑度
                try:
                    self.imc.set_smooth(axis_num, 64)
                except:
                    pass
                
            self.log("轴配置完成")
            
        except Exception as e:
            self.log(f"轴配置异常: {str(e)}")
            traceback.print_exc()
    
    def disconnect(self):
        """断开控制卡连接"""
        try:
            if self.is_connected and self.imc is not None:
                # 禁用所有轴
                for axis_num in range(3):
                    try:
                        self.imc.set_enable(axis_num, False)
                    except:
                        pass
                
                # 关闭控制卡
                try:
                    self.imc.close()
                except:
                    pass
                
                self.is_connected = False
                self.log("控制卡已断开")
                
                # 发射连接状态改变信号
                self.connection_status_changed.emit(False)
                
                return True
                
        except Exception as e:
            self.log(f"断开连接异常: {str(e)}")
            
        return False
    
    def mm_to_pulse(self, mm_value):
        """毫米转换为脉冲"""
        return int(mm_value * self.pulses_per_mm)
    
    def pulse_to_mm(self, pulse_value):
        """脉冲转换为毫米"""
        return pulse_value / self.pulses_per_mm
    
    def move_axis_relative(self, axis_num, pulse_distance, wait=False):
        """
        单轴相对运动
        axis_num: 0,1,2 对应 A,B,C 轴
        pulse_distance: 脉冲数 (正负表示方向)
        """
        if not self.is_connected or self.imc is None:
            self.log("错误: 控制卡未连接")
            return False
        
        try:
            # 设置加速度和减速度
            accel = 100.0  # 脉冲/毫秒²
            decel = 100.0  # 脉冲/毫秒²
            
            success = self.imc.set_accel(axis_num, accel, decel)
            if not success:
                self.log(f"设置轴{axis_num}加速度失败")
                return False
            
            # 设置速度
            start_vel = 0.0
            target_vel = 10.0  # 脉冲/毫秒
            
            # 执行相对移动
            success = self.imc.move_distance(
                axis_num, 
                pulse_distance, 
                start_vel, 
                target_vel, 
                wait
            )
            
            if success:
                # 更新滑块位置缓存
                self.current_sliders[axis_num] += self.pulse_to_mm(pulse_distance)
                self.log(f"轴{axis_num}相对移动 {pulse_distance} 脉冲")
            else:
                self.log(f"轴{axis_num}移动失败")
                
            return success
            
        except Exception as e:
            self.log(f"单轴移动异常: {str(e)}")
            traceback.print_exc()
            return False
    
    def move_to_xyz(self, x, y, z, wait=False):
        """移动到XYZ坐标"""
        # 逆运动学计算滑块位置
        target_pos = [x, y, z]
        sliders_z = self.kinematics.inverse_kinematics(target_pos)
        
        if sliders_z is None:
            self.log(f"错误: 目标位置 ({x}, {y}, {z}) 不可达")
            return False
        
        # 这里简化处理：依次移动三个轴
        success = True
        for axis_num in range(3):
            # 计算需要移动的距离
            current_mm = self.current_sliders[axis_num]
            target_mm = sliders_z[axis_num]
            delta_mm = target_mm - current_mm
            
            # 转换为脉冲
            pulse_delta = self.mm_to_pulse(delta_mm)
            
            # 移动轴
            if abs(pulse_delta) > 0:
                axis_success = self.move_axis_relative(axis_num, pulse_delta, wait)
                if not axis_success:
                    success = False
                    self.log(f"轴{axis_num}移动到位置失败")
                else:
                    # 更新当前位置
                    self.current_sliders[axis_num] = target_mm
        
        if success:
            self.current_position = [x, y, z]
            self.update_end_effector.emit(x, y, z)
            self.update_slider.emit(*sliders_z)
            self.log(f"移动到 ({x:.1f}, {y:.1f}, {z:.1f})")
        
        return success
    
    def emergency_stop(self):
        """急停"""
        if self.is_connected and self.imc is not None:
            try:
                success = self.imc.emergency_stop(True)
                if success:
                    self.log("急停命令已发送")
                else:
                    self.log("急停命令发送失败")
                return success
            except Exception as e:
                self.log(f"急停异常: {str(e)}")
                return False
        else:
            self.log("错误: 控制卡未连接")
            return False
    
    def reset_position(self):
        """平滑复位到原点位置"""
        try:
            # 定义复位目标位置
            reset_pos = [0.0, 0.0, -300.0]
            
            # 获取当前位置
            current_pos = self.current_position
            
            # 检查复位位置是否可达
            reset_sliders = self.kinematics.inverse_kinematics(reset_pos)
            if reset_sliders is None:
                self.log("错误：复位位置不可达")
                return False
            
            # 生成复位轨迹（当前位置->复位位置）
            # 使用贝塞尔曲线实现平滑过渡
            trajectory = self._generate_reset_trajectory(current_pos, reset_pos)
            
            if not trajectory:
                self.log("错误：无法生成复位轨迹")
                return False
            
            # 执行复位轨迹
            success = self.execute_trajectory(trajectory, speed_factor=0.5)  # 复位速度较慢
            
            if success:
                self.current_position = reset_pos
                self.current_sliders = reset_sliders
                self.log("平滑复位完成")
            else:
                self.log("复位过程中出现错误")
            
            return success
            
        except Exception as e:
            self.log(f"复位异常: {str(e)}")
            traceback.print_exc()
            return False

    def _generate_reset_trajectory(self, start_pos, end_pos):
        """生成平滑复位轨迹"""
        try:
            # 使用轨迹规划器生成平滑轨迹
            planner = TrajectoryPlanner(
                acc=50,          # 较小的加速度，确保平稳
                max_speed=30,    # 较小的复位速度
                interval=0.05    # 较小的采样间隔，更平滑
            )
            
            # 生成贝塞尔曲线轨迹，实现平滑过渡
            trajectory = planner.bezier_trajectory(
                start_pos[0], start_pos[1], start_pos[2],
                end_pos[0], end_pos[1], end_pos[2],
                show_plot=False
            )
            
            return trajectory
            
        except Exception as e:
            self.log(f"生成复位轨迹失败: {str(e)}")
            return None
    
    def get_current_positions(self):
        """获取当前位置（脉冲）"""
        if self.is_connected and self.imc is not None:
            try:
                success, positions = self.imc.get_command_position()
                if success and positions:
                    return positions
            except Exception as e:
                self.log(f"获取当前位置失败: {e}")
        return None
    
    def get_current_sliders_z(self):
        """获取当前滑块位置（mm）"""
        return self.current_sliders.copy()
    def set_digital_output(self, port, state):
        """设置数字输出（占位实现）"""
        self.log(f"设置数字输出: 端口{port} -> {'开' if state else '关'}")
        return True