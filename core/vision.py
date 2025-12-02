# -*- coding: utf-8 -*-
# core/vision.py
from PySide6.QtCore import QObject, QTimer, Signal
import time

class VisionFunctionality(QObject):
    visual_sorting_started = Signal()
    visual_picking_started = Signal()
    execute_picking_sequence_signal = Signal()
    object_detected = Signal(dict)
    log = Signal(str)

    def __init__(self, ui, serial_com):
        super().__init__()
        self.ui = ui
        self.serial_com = serial_com
        self.robot_mode = 'idle'
        
        # [优化] 根据Delta机器人实际行程调整抓取高度和工作范围
        self.visual_sorting_origin_z = -220.0 
        self.MAX_RADIUS = 280.0 # Delta机器人的最大活动半径
        
        self.processed_objects = [] 
        self.DEBOUNCE_DIST = 40.0  # 稍微增大防抖距离
        self.DEBOUNCE_TIME = 6.0   

        self.detected_objects_list = []

    def start_visual_sorting(self):
        self.robot_mode = 'visual_sorting'
        self.processed_objects.clear()
        self.ui.calibrationStatus.setText("状态: 视觉分类模式 (形状+颜色)")
        self.log.emit("视觉分类启动: 等待物体进入视野...")

    def start_visual_picking(self):
        self.robot_mode = 'visual_picking_scan'
        self.detected_objects_list.clear()
        self.ui.calibrationStatus.setText("状态: 正在扫描桌面 (3秒)...")
        self.log.emit("开始视觉扫描...")
        QTimer.singleShot(3000, self._after_scanning)

    def _after_scanning(self):
        self.robot_mode = 'visual_picking_executing'
        count = len(self.detected_objects_list)
        if count == 0:
            self.ui.calibrationStatus.setText("扫描结束: 未发现物体")
            self.robot_mode = 'idle'
            return
            
        self.ui.calibrationStatus.setText(f"扫描结束: 发现 {count} 个目标")
        self.log.emit(f"扫描完成，准备抓取 {count} 个物体")
        self.execute_picking_sequence_signal.emit()

    def handle_object_detection(self, target_info):
        x, y, z = target_info['robot_coords']
        color = target_info['color']
        shape = target_info.get('shape', 'Unknown')
        
        # 过滤坐标：防止发送超出 Delta 工作半径的坐标 (假设最大半径280mm)
        if (x**2 + y**2)**0.5 > 280: return

        self.object_detected.emit(target_info) # 更新仿真

        # [打印到终端]
        # 这样您就可以在控制台看到识别到的坐标
        print(f"[VISION DETECTED] Color: {color}, Shape: {shape}, RobotPos: ({x:.1f}, {y:.1f}, {z:.1f})")

        current_time = time.time()

        # [打印识别结果到终端]
        # 只有当开启了视觉功能时才打印，避免闲时刷屏
        if self.robot_mode in ['visual_sorting', 'visual_picking_scan']:
            print(f"[VISION] Detected: {color} {shape} at Robot(X={x:.1f}, Y={y:.1f})")

        # ================= 分类模式逻辑 =================
        if self.robot_mode == 'visual_sorting':
            # 防抖动
            for obj in self.processed_objects:
                dist = ((obj['x'] - x)**2 + (obj['y'] - y)**2)**0.5
                if dist < self.DEBOUNCE_DIST and (current_time - obj['time'] < self.DEBOUNCE_TIME):
                    return 

            # 映射表: 颜色 -> 对应分拣槽位ID
            color_map = {'Red': 1, 'Yellow': 2, 'Blue': 3, 'Green': 4}
            if color not in color_map: return

            color_id = color_map[color]
            
            # [终端打印] 确认执行动作
            msg = f"执行分类: {color} {shape} -> ID {color_id}, Coords: ({x:.1f}, {y:.1f})"
            print(f">>> {msg}") 
            self.log.emit(msg)
            
            # 发送指令
            self.serial_com.send_packet(
                command=self.serial_com.CMD_VISION_CLASSIFY,
                x=float(x), y=float(y), z=float(self.visual_sorting_origin_z), 
                speed=5, dirc1=int(color_id)
            )
            
            self.processed_objects.append({'x': x, 'y': y, 'time': current_time})
            # 清理过期防抖记录
            self.processed_objects = [o for o in self.processed_objects if current_time - o['time'] < self.DEBOUNCE_TIME]

        # ================= 拾取模式逻辑 =================
        elif self.robot_mode == 'visual_picking_scan':
            # 简单的去重
            is_duplicate = False
            for obj in self.detected_objects_list:
                dist = ((obj['robot_coords'][0] - x)**2 + (obj['robot_coords'][1] - y)**2)**0.5
                if dist < self.DEBOUNCE_DIST:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                print(f"[SCAN] Added to queue: {color} {shape} ({x:.1f}, {y:.1f})")
                self.detected_objects_list.append(target_info)
    def execute_picking_sequence(self):
        if not self.detected_objects_list:
            return

        self.log.emit(">>> 开始批量码垛执行 <<<")
        self._send_next_pick_command(0)

    def _send_next_pick_command(self, index):
        if index >= len(self.detected_objects_list) or self.robot_mode == 'idle':
            self.robot_mode = 'idle'
            self.log.emit("批量任务完成")
            self.ui.calibrationStatus.setText("状态: 空闲")
            return

        item = self.detected_objects_list[index]
        x, y, z = item['robot_coords']
        shape = item.get('shape', '')
        z_pick = self.visual_sorting_origin_z
        
        self.ui.calibrationStatus.setText(f"处理中 ({index+1}/{len(self.detected_objects_list)}): {item['color']} {shape}")
        
        # 发送抓取指令
        self.serial_com.send_packet(command=self.serial_com.CMD_FETCH, x=float(x), y=float(y), z=float(z_pick))
        
        # [优化] 根据实际机械运动时间调整间隔，避免指令堆积
        # 建议：如果串口有“动作完成”的回传信号，最好改成监听信号触发下一步
        delay_ms = 4500 
        QTimer.singleShot(delay_ms, lambda: self._send_next_pick_command(index + 1))