# -*- coding: utf-8 -*-
# com.py (已更新)

import serial
import serial.tools.list_ports
import glob
import os
import time
from PySide6.QtCore import QObject, Signal, Slot, QThread
from PySide6.QtWidgets import QMessageBox

class SerialCommunication(QObject):
    # 定义用于更新UI的信号
    update_serial_status = Signal(str)
    update_received_data = Signal(str)
    update_sent_data = Signal(str)
    update_end_effector = Signal(float, float, float)
    update_slider = Signal(float, float, float)
    connection_status_changed = Signal(bool)
    
    # 数据包协议定义
    PACKET_HEADER = 0x40
    PACKET_FOOTER = [0x23, 0x21]
    PACKET_SIZE = 17
    

    CMD_IGNORE = 0
    CMD_POLL = 1
    CMD_EMERGENCY = 2
    CMD_RESET = 3
    CMD_JOG = 4
    CMD_GATE = 5
    CMD_VISION_CLASSIFY = 6   # 视觉分类命令
    CMD_VISION_PICKUP = 7     # 视觉拾取命令
    CMD_MOTOR_DEBUG = 8       # 电机调试命令
    CMD_INCH_MOVE = 9         # 寸动移动命令
    CMD_FETCH = 10

    CMD_NAMES = {
    CMD_IGNORE: "IGNORE",
    CMD_POLL: "POLL",
    CMD_EMERGENCY: "EMERGENCY",
    CMD_RESET: "RESET",
    CMD_JOG: "JOG",
    CMD_GATE: "GATE",
    CMD_VISION_CLASSIFY: "VISION_CLASSIFY",
    CMD_VISION_PICKUP: "VISION_PICKUP",
    CMD_MOTOR_DEBUG: "MOTOR_DEBUG",
    CMD_INCH_MOVE: "INCH_MOVE",
    CMD_FETCH: "FETCH",
    }

    def __init__(self, ui_instance):
        super().__init__()
        self.ui = ui_instance
        self.serial_port = None
        self.is_connected = False
        self.receive_buffer = bytearray()
        
        # 创建并启动串口读取线程
        self.read_thread = SerialReadThread(self)
        self.read_thread.data_received.connect(self.handle_received_data)
        self.read_thread.error_occurred.connect(self.handle_serial_error)
        
        self.connect_signals()
        self.scan_serial_ports()

    def connect_signals(self):
        """连接UI信号到本类的槽函数"""
        # 串口连接
        self.ui.pushButton.clicked.connect(self.toggle_serial_connection)
        
        # 机器人控制
        self.ui.pushButton_2.clicked.connect(self.emergency_stop)
        self.ui.pushButton_3.clicked.connect(self.reset_position)
        
        # 寸动
        self.ui.pushButton_8.clicked.connect(lambda: self.send_inch_debug_command(1, 1)) # x+
        self.ui.pushButton_9.clicked.connect(lambda: self.send_inch_debug_command(1, 0))  # x-
        self.ui.pushButton_10.clicked.connect(lambda: self.send_inch_debug_command(2, 1))  # y+
        self.ui.pushButton_11.clicked.connect(lambda: self.send_inch_debug_command(2, 0))  # y-
        self.ui.pushButton_12.clicked.connect(lambda: self.send_inch_debug_command(3, 1))  # z+
        self.ui.pushButton_13.clicked.connect(lambda: self.send_inch_debug_command(3, 0))  # z-

        # 连接电机调试按钮
        self.ui.pushButton_14.clicked.connect(lambda: self.send_motor_debug_command(1))  # A+
        self.ui.pushButton_15.clicked.connect(lambda: self.send_motor_debug_command(2))  # A-
        self.ui.pushButton_16.clicked.connect(lambda: self.send_motor_debug_command(3))  # B+
        self.ui.pushButton_17.clicked.connect(lambda: self.send_motor_debug_command(4))  # B-
        self.ui.pushButton_18.clicked.connect(lambda: self.send_motor_debug_command(5))  # C+
        self.ui.pushButton_19.clicked.connect(lambda: self.send_motor_debug_command(6))  # C-

        # 视觉与曲线按钮 (主逻辑在main.py中连接)
        self.ui.pushButton_6.clicked.connect(self.run_curve) # 运行曲线

        # UI更新信号
        self.update_received_data.connect(self.ui.respond)
        self.update_sent_data.connect(self.ui.message)
        self.update_end_effector.connect(self.update_end_effector_ui)
        self.update_slider.connect(self.update_slider_ui)
        self.connection_status_changed.connect(self.update_ui_connection_status)

    def scan_serial_ports(self):
        """扫描可用串口并更新UI"""
        self.ui.com.clear()
        ports = serial.tools.list_ports.comports()
        
        port_list = []
        if ports:
            for port in ports:
                port_list.append(port.device)
        
        # 添加常见的Linux虚拟和物理串口
        for pattern in ['/dev/pts/*', '/dev/ttyACM*', '/dev/ttyUSB*', '/dev/ttyS*', '/dev/ttyAMA*']:
            for port_path in glob.glob(pattern):
                if port_path not in port_list:
                    port_list.append(port_path)
        
        if not port_list:
            self.ui.com.addItem("未检测到串口")
        else:
            self.ui.com.addItems(sorted(port_list))

    @Slot()
    def toggle_serial_connection(self):
        """切换串口连接状态"""
        if self.is_connected:
            self.close_serial()
        else:
            self.open_serial()

    def open_serial(self):
        port = self.ui.com.currentText()
        if "未检测到串口" in port:
            QMessageBox.warning(self.ui, "错误", "请选择一个有效的串口。")
            return
        
        baudrate = int(self.ui.botrate.currentText())
        
        try:
            self.serial_port = serial.Serial(port, baudrate, timeout=0.1)
            self.is_connected = True
            self.connection_status_changed.emit(True)
            self.update_serial_status.emit(f"已连接到 {port}")
            if not self.read_thread.isRunning():
                self.read_thread.start()
        except Exception as e:
            QMessageBox.critical(self.ui, "连接错误", f"无法打开串口: {e}")
            self.is_connected = False
            self.connection_status_changed.emit(False)

    def close_serial(self):
        if self.read_thread.isRunning():
            self.read_thread.stop()
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.is_connected = False
        self.connection_status_changed.emit(False)
        self.update_serial_status.emit("串口已断开")

    def handle_received_data(self, data):
        """处理从串口接收到的原始字节数据"""
        self.receive_buffer.extend(data)
        
        while len(self.receive_buffer) >= self.PACKET_SIZE:
            # 寻找包头
            if self.receive_buffer[0] != self.PACKET_HEADER:
                self.receive_buffer.pop(0)
                continue
            
            # 检查包尾是否完整
            if list(self.receive_buffer[15:17]) != self.PACKET_FOOTER:
                self.receive_buffer.pop(0)
                continue

            # 处理有效的数据包
            packet = self.receive_buffer[:self.PACKET_SIZE]
            self.parse_received_packet(packet)
            self.receive_buffer = self.receive_buffer[self.PACKET_SIZE:]

    def parse_received_packet(self, packet):
        """解析一个完整的数据包"""
        hex_data = ' '.join(f'{b:02x}' for b in packet)
        self.update_received_data.emit(hex_data)
        
        try:
            # 从数据包中解包数据 (假设是这种结构)
            slider_x = self.unmap_position(packet[9])
            slider_y = self.unmap_position(packet[10])
            slider_z = self.unmap_position(packet[11])
            self.update_slider.emit(slider_x, slider_y, slider_z)
            
            platform_x = self.unmap_position(packet[12])
            platform_y = self.unmap_position(packet[13])
            platform_z = self.unmap_position(packet[14])
            self.update_end_effector.emit(platform_x, platform_y, platform_z)

             # ===== 新增：向终端输出可读 RX 日志 =====
            if hasattr(self.ui, "log_terminal"):
                log_msg = (
                    f"[RX] slider=({slider_x:.1f}, {slider_y:.1f}, {slider_z:.1f}) | "
                    f"platform=({platform_x:.1f}, {platform_y:.1f}, {platform_z:.1f})"
                )
                self.ui.log_terminal(log_msg)

        except Exception as e:
            self.update_serial_status.emit(f"解析数据包错误: {e}")


    def handle_serial_error(self, error_msg):
        self.update_serial_status.emit(f"串口错误: {error_msg}")
        self.close_serial()

    def send_packet(self, command, x=0, y=0, z=0, speed=5, dir1=0, dir2=0, dirm1=0, dirc1=0):
        """
        发送数据包
        - 对于电机调试命令 (CMD_MOTOR_DEBUG):
        dirm1: 电机方向 (1-6 对应 A+ A- B+ B- C+ C-)
        - 对于寸动命令 (CMD_INCH_MOVE):
        dir1: 轴 (1=X, 2=Y, 3=Z)
        dir2: 方向 (0=后退, 1=前进)
        - 对于视觉分类命令 (CMD_VISION_CLASSIFY):
        dirc1: 颜色ID (1=Red, 2=Yellow, 3=Blue)
        """
        if not self.is_connected:
            print("发送失败：串口未连接。")
            return False
            
        packet = bytearray(self.PACKET_SIZE)
        packet[0] = self.PACKET_HEADER
        packet[1] = command
        
        # 坐标映射
        packet[2] = self.map_position(x)
        packet[3] = self.map_position(y)
        packet[4] = self.map_position(z)
        
        # 速度等级
        packet[5] = int(speed)
        
        # 方向控制 - 根据命令类型使用不同格式
        packet[6] = int(dir1)   # 寸动 轴向
        packet[7] = int(dir2)   # 寸动 前后
        packet[8] = int(dirm1)  # 电机方向
        packet[9] = int(dirc1)  # 颜色ID (视觉分类用)
        
        # 保留位 (10-14) 设为0
        for i in range(10, 15):
            packet[i] = 0
        
        # 包尾
        packet[15] = self.PACKET_FOOTER[0]
        packet[16] = self.PACKET_FOOTER[1]
        
        try:
            self.serial_port.write(packet)
            hex_packet = ' '.join(f'{b:02x}' for b in packet)
            self.update_sent_data.emit(hex_packet)

            # ===== 新增：向终端输出可读 TX 日志 =====
            cmd_name = self.CMD_NAMES.get(command, f"CMD_{command}")
            log_msg = (
                f"[TX] {cmd_name} | "
                f"XYZ=({x:.1f}, {y:.1f}, {z:.1f}) "
                f"speed={speed} axis={dir1} dir={dir2} "
                f"motor={dirm1} colorID={dirc1}"
            )
            if hasattr(self.ui, "log_terminal"):
                self.ui.log_terminal(log_msg)

            return True
        except Exception as e:
            self.update_serial_status.emit(f"发送错误: {e}")
            return False
        
    def map_position(self, value):
        """将物理位置 (-1000 到 1000) 映射到字节 (0-255)"""
        return max(0, min(255, int((value + 1000) * 255 / 2000)))
    
    def unmap_position(self, value):
        """将字节 (0-255) 映射回物理位置 (-1000 到 1000)"""
        return (float(value) * 2000 / 255) - 1000

    @Slot()
    def emergency_stop(self):
        if self.send_packet(command=self.CMD_EMERGENCY):
            self.update_serial_status.emit("急停命令已发送")

    @Slot()
    def reset_position(self):
        if self.send_packet(command=self.CMD_RESET):
            self.update_serial_status.emit("复位命令已发送")

    @Slot()
    def run_coordinates(self):
        """移动到UI中指定的目标坐标"""
        x = self.ui.spinBox.value()
        y = self.ui.spinBox_2.value()
        z = self.ui.spinBox_3.value()
        speed = self.get_speed_level()
        
        if self.send_packet(command=self.CMD_JOG, x=x, y=y, z=z, speed=speed):
            self.update_serial_status.emit(f"发送坐标: X={x}, Y={y}, Z={z}")

    def move_direction(self, direction):
        """手动点动控制"""
        step = 20  # 点动步长 (mm)
        try:
            current_x = float(self.ui.textBrowser_6.toPlainText() or 0)
            current_y = float(self.ui.textBrowser_7.toPlainText() or 0)
            current_z = float(self.ui.textBrowser_8.toPlainText() or 0)
        except ValueError:
            current_x, current_y, current_z = 0, 0, 0
        
        target_x, target_y, target_z = current_x, current_y, current_z

        if direction == 'x+': target_x += step
        elif direction == 'x-': target_x -= step
        elif direction == 'y+': target_y += step
        elif direction == 'y-': target_y -= step
        elif direction == 'z+': target_z += step
        elif direction == 'z-': target_z -= step
        
        speed = self.get_speed_level()
        if self.send_packet(command=self.CMD_JOG, x=target_x, y=target_y, z=target_z, speed=speed):
            self.update_serial_status.emit(f"向 {direction} 方向移动到 ({target_x:.1f}, {target_y:.1f}, {target_z:.1f})")

    @Slot()
    def run_curve(self):
        """运行预定义的曲线运动"""
        curve_type = self.ui.comboBox.currentIndex() 
        speed = self.get_speed_level()
        if self.send_packet(command=self.CMD_GATE, x=curve_type, speed=speed):
            self.update_serial_status.emit(f"运行曲线: {self.ui.comboBox.currentText()}")

    def send_motor_debug_command(self, motor_action):
        """
        发送电机调试指令
        :param motor_action: 电机动作 (1=A+, 2=A-, 3=B+, 4=B-, 5=C+, 6=C-)
        """
        motor_actions = {
            1: "A+", 2: "A-", 3: "B+", 4: "B-", 5: "C+", 6: "C-"
        }
        
        if motor_action not in range(1, 7):
            self.update_serial_status.emit("错误: 无效的电机动作")
            return False
        
        if self.send_packet(
            command=self.CMD_MOTOR_DEBUG,
            dirm1=motor_action
        ):
            self.update_serial_status.emit(
                f"发送电机调试指令: 电机 {motor_actions[motor_action]}"
            )
            return True
        return False

    def send_inch_debug_command(self, axis, direction):
        """
        发送寸动移动命令
        :param axis: 轴 (1=X, 2=Y, 3=Z)
        :param direction: 方向 (0=后退, 1=前进)
        """
        axis_names = {1: "X", 2: "Y", 3: "Z"}
        dir_names = {0: "后退", 1: "前进"}
        
        if axis not in [1, 2, 3]:
            self.update_serial_status.emit("错误: 无效的轴选择")
            return False
        
        if direction not in [0, 1]:
            self.update_serial_status.emit("错误: 无效的方向选择")
            return False
        
        if self.send_packet(
            command=self.CMD_INCH_MOVE,
            dir1=axis,
            dir2=direction
        ):
            self.update_serial_status.emit(
                f"发送寸动命令: {axis_names[axis]}轴 {dir_names[direction]}"
            )
            return True
        return False

    def get_speed_level(self):
        """从UI滑块获取速度等级 (0-9)"""
        return min(9, max(0, int(self.ui.v.value() * 9 / 100)))

    # ================== UI 更新槽函数 ==================
    def update_ui_connection_status(self, connected):
        if connected:
            self.ui.pushButton.setText("断开")
            self.ui.pushButton.setStyleSheet("background-color: #FF6347;")
        else:
            self.ui.pushButton.setText("连接")
            self.ui.pushButton.setStyleSheet("")

    def update_end_effector_ui(self, x, y, z):
        self.ui.textBrowser_6.setText(f"{x:.1f}")
        self.ui.textBrowser_7.setText(f"{y:.1f}")
        self.ui.textBrowser_8.setText(f"{z:.1f}")

    def update_slider_ui(self, x, y, z):
        self.ui.textBrowser_3.setText(f"{x:.1f}")
        self.ui.textBrowser_4.setText(f"{y:.1f}")
        self.ui.textBrowser_5.setText(f"{z:.1f}")

    def close(self):
        self.close_serial()

class SerialReadThread(QThread):
    """用于读取串口数据的专用线程，以防止UI阻塞"""
    data_received = Signal(bytes)
    error_occurred = Signal(str)
    
    def __init__(self, serial_com):
        super().__init__()
        self.serial_com = serial_com
        self._running = False
        
    def run(self):
        self._running = True
        while self._running:
            if self.serial_com.is_connected and self.serial_com.serial_port:
                try:
                    if self.serial_com.serial_port.in_waiting > 0:
                        data = self.serial_com.serial_port.read_all()
                        if data:
                            self.data_received.emit(data)
                except Exception as e:
                    self.error_occurred.emit(str(e))
                    break
            time.sleep(0.02) # 降低CPU使用率
    
    def stop(self):
        self._running = False
        self.wait(500)