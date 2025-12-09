# communication/mqtt_interface.py - 修改版

import json
import time
from PySide6.QtCore import QObject, Signal
import paho.mqtt.client as mqtt
from kinematics.kinematics import DeltaKinematics

class DeltaMqttHandler(QObject):
    # 定义信号，用于将日志和状态传回主界面
    log_signal = Signal(str)
    connection_state_changed = Signal(bool)

    def __init__(self, broker_ip="192.168.217.99", port=1883, client_id="Delta_Ubuntu_Master", imcid=0):
        super().__init__()
        self.broker_ip = broker_ip
        self.port = port
        self.client_id = client_id
        self.imcid = imcid  # 设备ID

        self.client = mqtt.Client(client_id=self.client_id, protocol=mqtt.MQTTv311)
        self.is_connected = False
        
        # 更新话题结构
        self.TOPIC_REGISTER = "card/register"
        self.TOPIC_UNREGISTER = "card/unregister"
        self.TOPIC_STATUS = f"card/{self.imcid}/status"
        self.TOPIC_EMERGENCY_STOP = f"card/{self.imcid}/emergency_stop"
        self.TOPIC_PIN_IN_STATUS = f"card/{self.imcid}/pin/in/status"
        self.TOPIC_PIN_OUT_SET = f"card/{self.imcid}/pin/out/set"
        
        # 【新增】位置控制话题 - 与P2P模块保持一致
        self.TOPIC_P2P_INITIAL = f"card/{self.imcid}/position/control/p2p_initial"  # 初始坐标话题
        self.TOPIC_P2P_TARGET = f"card/{self.imcid}/position/control/p2p"          # 末端坐标话题
        

        self.TOPIC_AXIS_HOME = f"card/{self.imcid}/axis/control/home"  # 保留回零控制话题
        self.TOPIC_AXIS_ACC = f"card/{self.imcid}/axis/config/acc"     # 保留加速度配置话题

        self.TOPIC_SLIDER_VEL = f"card/{self.imcid}/slider/control/vel"
        self.TOPIC_SLIDER_POSITION = f"card/{self.imcid}/slider/control/position"

        # 机械参数 (脉冲/毫米)
        self.PULSE_PER_MM = 100  
        
        # 当前轴状态
        self.current_pulses = [0, 0, 0]  # 三个轴的当前脉冲数
        self.axis_moving = [False, False, False]  # 轴运动状态
        
        # 绑定回调
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish

        # 运动学算法 (与main.py保持一致)
        rod_len = 430.0
        sp_radius = 260
        ep_radius = 45
        self.kinematics = DeltaKinematics(sp=sp_radius, ep=ep_radius, rod_length=rod_len)
        
    def register_device(self):
        """注册设备到下位机"""
        payload = {
            "net_card_index": 0,  # 默认网卡索引
            "imcid": self.imcid
        }
        try:
            self.client.publish(self.TOPIC_REGISTER, json.dumps(payload), qos=1)
            self.log_signal.emit(f"设备注册: IMCID={self.imcid}")
        except Exception as e:
            self.log_signal.emit(f"设备注册失败: {str(e)}")
    
    def unregister_device(self):
        """注销设备"""
        payload = {"imcid": self.imcid}
        try:
            self.client.publish(self.TOPIC_UNREGISTER, json.dumps(payload), qos=1)
            self.log_signal.emit(f"设备注销: IMCID={self.imcid}")
        except Exception as e:
            self.log_signal.emit(f"设备注销失败: {str(e)}")
    
    def connect_broker(self, ip=None, port=None):
        if ip: self.broker_ip = ip
        if port: self.port = int(port)

        try:
            self.log_signal.emit(f"正在连接 MQTT Broker: {self.broker_ip}:{self.port} ...")
            self.client.connect(self.broker_ip, self.port, 60)
            self.client.loop_start()
        except Exception as e:
            self.log_signal.emit(f"MQTT 连接失败: {str(e)}")

    def disconnect_broker(self):
        try:
            # 注销设备
            if self.is_connected:
                self.unregister_device()
            
            # 停止循环并断开连接
            self.client.loop_stop()
            self.client.disconnect()
        except Exception as e:
            self.log_signal.emit(f"断开连接失败: {str(e)}")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.is_connected = True
            self.connection_state_changed.emit(True)
            
            # 注册设备
            self.register_device()
            
            # 【修改】订阅新的位置控制话题
            self.client.subscribe(self.TOPIC_STATUS)
            self.client.subscribe(self.TOPIC_PIN_IN_STATUS)
            
            self.log_signal.emit("MQTT连接成功!")
        else:
            self.log_signal.emit(f"MQTT连接失败, 返回码: {rc}")

    def on_disconnect(self, client, userdata, rc):
        self.is_connected = False
        self.connection_state_changed.emit(False)
        self.log_signal.emit(f"MQTT 已断开 (返回码: {rc})")

    def on_publish(self, client, userdata, mid):
        # 消息发送成功的回调，一般不需要太频繁打印
        pass

    def send_target_pos(self, x, y, z, speed=None):
        """发送目标位置 (使用新的P2P位置控制)"""
        if not self.is_connected:
            return False

        # 直接发送到P2P目标话题，下位机自行计算逆运动学
        payload = {
            "x": float(x),
            "y": float(y),
            "z": float(z)
        }
        
        if speed is not None:
            payload["velocity"] = float(speed)
        
        try:
            self.client.publish(self.TOPIC_P2P_TARGET, json.dumps(payload), qos=1)
            self._log_p2p_message("目标位置", payload)
            self.log_signal.emit(f"发送目标位置: ({x:.1f}, {y:.1f}, {z:.1f})")
            return True
        except Exception as e:
            self.log_signal.emit(f"发送目标位置失败: {str(e)}")
            return False
    
    def send_p2p_initial_position(self, position):
        """
        发送初始坐标到P2P初始话题
        
        参数:
        position (list): 初始坐标 [x, y, z]
        
        返回:
        bool: 是否成功
        """
        if not self.is_connected:
            self.log_signal.emit("未连接到MQTT Broker，无法发送初始坐标")
            return False
        
        payload = {
            "x": float(position[0]),
            "y": float(position[1]),
            "z": float(position[2])
        }
        
        try:
            self.client.publish(self.TOPIC_P2P_INITIAL, json.dumps(payload), qos=1)
            self._log_p2p_message("初始坐标", payload)
            self.log_signal.emit(f"初始坐标已发送: X={position[0]:.1f}, Y={position[1]:.1f}, Z={position[2]:.1f}")
            return True
        except Exception as e:
            self.log_signal.emit(f"发送初始坐标失败: {str(e)}")
            return False
    
    def send_p2p_target_position(self, position, speed=None):
        """
        发送末端坐标到P2P目标话题
        
        参数:
        position (list): 末端坐标 [x, y, z]
        speed (float): 移动速度 (可选)
        
        返回:
        bool: 是否成功
        """
        if not self.is_connected:
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
            self.client.publish(self.TOPIC_P2P_TARGET, json.dumps(payload), qos=1)
            self._log_p2p_message("末端坐标", payload)
            
            speed_msg = f", 速度={speed:.1f}mm/s" if speed is not None else ""
            self.log_signal.emit(f"末端坐标已发送: X={position[0]:.1f}, Y={position[1]:.1f}, Z={position[2]:.1f}{speed_msg}")
            return True
        except Exception as e:
            self.log_signal.emit(f"发送末端坐标失败: {str(e)}")
            return False

    def send_home_command(self, axis=0, dir=0, rise_edge=0, switch_pos=0, stop_pos=0, 
                          high_vel=10.0, low_vel=1.0, stop_vel=0.0):
        """
        发送轴回零指令
        
        参数:
        - axis: 轴号 (0, 1, 2)
        - dir: 回零方向，0为正方向搜零
        - rise_edge: 指定检测原点开关的边沿；零：下降沿；非零：上升沿
        - switch_pos: 零点开关位置对应脉冲数
        - stop_pos: 查找到零点后要移动到的脉冲数
        - high_vel: 回零运动的最高速度
        - low_vel: 回零运动的最低速度
        - stop_vel: 到达最终位置后要保持的速度
        """
        if not self.is_connected:
            self.log_signal.emit("未连接到MQTT Broker，无法发送回零指令")
            return False
        
        # 构造回零指令的固定内容
        payload = {
            "dir": dir,
            "rise_edge": rise_edge,
            "switch_pos": switch_pos,
            "stop_pos": stop_pos,
            "high_vel": high_vel,
            "low_vel": low_vel,
            "stop_vel": stop_vel,
            "axis": axis
        }
        
        try:
            self.client.publish(self.TOPIC_AXIS_HOME, json.dumps(payload), qos=1)
            self._log_message(f"轴{axis} 回零指令", payload)
            self.log_signal.emit(f"轴{axis} 回零指令已发送")
            return True
        except Exception as e:
            self.log_signal.emit(f"轴{axis}回零指令发送失败: {str(e)}")
            return False
        
    def _log_message(self, topic, data):
        """统一日志格式"""
        try:
            output_lines = [f"Published to {topic}:"]
            
            # 滑块速度控制
            if "start_vel" in data and "target_vel" in data:
                output_lines.append(f"  start_vel: {data['start_vel']}")
                output_lines.append(f"  target_vel: {data['target_vel']}")
            
            # 滑块位置控制
            if "position" in data:
                output_lines.append(f"  position: {data['position']}")
            
            # 通用字段
            if "axis" in data:
                output_lines.append(f"  axis: {data['axis']}")
            if "start_vel" in data:
                output_lines.append(f"  start_vel: {data['start_vel']}")
            if "target_vel" in data:
                output_lines.append(f"  target_vel: {data['target_vel']}")
            if "stop" in data:
                output_lines.append(f"  stop: {data['stop']}")
            
            # 回零指令特有字段
            if "dir" in data:
                output_lines.append(f"  dir: {data['dir']} ({'正方向' if data['dir'] == 0 else '负方向'})")
            if "rise_edge" in data:
                output_lines.append(f"  rise_edge: {data['rise_edge']} ({'下降沿' if data['rise_edge'] == 0 else '上升沿'})")
            if "switch_pos" in data:
                output_lines.append(f"  switch_pos: {data['switch_pos']}")
            if "stop_pos" in data:
                output_lines.append(f"  stop_pos: {data['stop_pos']}")
            if "high_vel" in data:
                output_lines.append(f"  high_vel: {data['high_vel']}")
            if "low_vel" in data:
                output_lines.append(f"  low_vel: {data['low_vel']}")
            if "stop_vel" in data:
                output_lines.append(f"  stop_vel: {data['stop_vel']}")
            
            output_lines.append("---")
            
            for line in output_lines:
                self.log_signal.emit(line)
        except Exception as e:
            self.log_signal.emit(f"格式化消息失败: {str(e)}")
    
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

    def send_emergency_stop(self):
        """发送急停指令"""
        payload = {"stop": True}
        try:
            self.client.publish(self.TOPIC_EMERGENCY_STOP, json.dumps(payload), qos=2)
            self.log_signal.emit("急停指令已发送")
        except Exception as e:
            self.log_signal.emit(f"急停指令发送失败: {str(e)}")

    def move_to_xyz(self, x, y, z, wait=False):
        """发送XYZ移动指令"""
        return self.send_p2p_target_position([x, y, z])

    def set_digital_output(self, channel, state):
        """控制数字输出"""
        payload = {
            "pin": int(channel),
            "state": bool(state)
        }
        
        try:
            self.client.publish(self.TOPIC_PIN_OUT_SET, json.dumps(payload), qos=1)
            self._log_message("数字输出", payload)
        except Exception as e:
            self.log_signal.emit(f"数字输出失败: {str(e)}")

    def _on_axis_status(self, client, userdata, msg):
        """处理轴状态反馈（已移除，保留空函数）"""
        pass

    def _on_pin_status(self, client, userdata, msg):
        """处理IO状态反馈"""
        try:
            data = json.loads(msg.payload.decode())
            self._log_message("IO状态", data)
        except Exception as e:
            self.log_signal.emit(f"IO状态解析错误: {str(e)}")

    def emergency_stop(self):
        """急停指令"""
        self.send_emergency_stop()

    # 添加状态更新方法
    def update_status(self, sliders_z, end_pos):
        """更新当前状态"""
        self.current_sliders = sliders_z
        self.current_pos = end_pos
        
    def send_slider_velocity(self, axis_idx, start_vel, target_vel):
        """
        发送滑块速度控制指令
        
        参数:
        axis_idx (int): 轴号 (0, 1, 2)
        start_vel (float): 起始速度 (mm/s)
        target_vel (float): 目标速度 (mm/s)
        """
        if not self.is_connected:
            self.log_signal.emit("未连接到MQTT Broker，无法发送滑块速度指令")
            return False
        
        payload = {
            "start_vel": float(start_vel),
            "target_vel": float(target_vel),
            "axis": int(axis_idx)
        }
        
        try:
            self.client.publish(self.TOPIC_SLIDER_VEL, json.dumps(payload), qos=1)
            self._log_message(f"滑块速度控制 轴{axis_idx}", payload)
            self.log_signal.emit(f"滑块速度控制: 轴{axis_idx}, 起始速度={start_vel}, 目标速度={target_vel}")
            return True
        except Exception as e:
            self.log_signal.emit(f"滑块速度控制指令发送失败: {str(e)}")
            return False

    def send_slider_position(self, axis_idx, position):
        """
        发送滑块位置控制指令
        
        参数:
        axis_idx (int): 轴号 (0, 1, 2)
        position (float): 目标位置 (mm)
        """
        if not self.is_connected:
            self.log_signal.emit("未连接到MQTT Broker，无法发送滑块位置指令")
            return False
        
        payload = {
            "position": float(position),
            "axis": int(axis_idx)
        }
        
        try:
            self.client.publish(self.TOPIC_SLIDER_POSITION, json.dumps(payload), qos=1)
            self._log_message(f"滑块位置控制 轴{axis_idx}", payload)
            self.log_signal.emit(f"滑块位置控制: 轴{axis_idx}, 目标位置={position}mm")
            return True
        except Exception as e:
            self.log_signal.emit(f"滑块位置控制指令发送失败: {str(e)}")
            return False

    def move_slider_relative(self, axis_idx, distance_mm, speed=10.0):
        """
        滑块相对移动 (使用位置控制)
        
        参数:
        axis_idx (int): 轴号
        distance_mm (float): 移动距离 (mm)
        speed (float): 移动速度 (mm/s)
        """
        # 计算当前滑块位置
        current_mm = self.current_pulses[axis_idx] / self.PULSE_PER_MM
        target_mm = current_mm + distance_mm
        
        # 首先设置速度
        self.send_slider_velocity(axis_idx, speed, speed)
        
        # 然后移动到位
        return self.send_slider_position(axis_idx, target_mm)

    def move_slider_absolute(self, axis_idx, target_mm, speed=10.0):
        """
        滑块绝对移动 (使用位置控制)
        
        参数:
        axis_idx (int): 轴号
        target_mm (float): 目标位置 (mm)
        speed (float): 移动速度 (mm/s)
        """
        # 首先设置速度
        self.send_slider_velocity(axis_idx, speed, speed)
        
        # 然后移动到位
        return self.send_slider_position(axis_idx, target_mm)
