# -*- coding: utf-8 -*-
# core/vision.py
"""
视觉功能封装模块 - 增强版
包含：防抖动、坐标过滤、分类逻辑修复
"""
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
        
        # 分类参数
        self.visual_sorting_origin_z = -200.0 # 修改为合理的抓取高度 (Linear Delta通常Z是负的)
        
        # 防抖动列表：存储 {'x': x, 'y': y, 'time': t}
        self.processed_objects = [] 
        self.DEBOUNCE_DIST = 30.0  # 判定为同一物体的距离阈值 (mm)
        self.DEBOUNCE_TIME = 5.0   # 相同位置物体忽略时间 (秒)

        self.detected_objects_list = []

    def start_visual_sorting(self):
        """启动实时分类模式"""
        self.robot_mode = 'visual_sorting'
        self.processed_objects.clear()
        self.ui.calibrationStatus.setText("状态: 视觉分类模式 - 监控中...")
        self.log.emit("视觉分类启动: 等待物体进入视野")

    def start_visual_picking(self):
        """启动批量拾取模式 (先扫描后执行)"""
        self.robot_mode = 'visual_picking_scan'
        self.detected_objects_list.clear()
        self.ui.calibrationStatus.setText("状态: 正在扫描桌面 (3秒)...")
        self.log.emit("开始视觉扫描...")
        # 3秒后结束扫描
        QTimer.singleShot(3000, self._after_scanning)

    def _after_scanning(self):
        self.robot_mode = 'visual_picking_executing'
        count = len(self.detected_objects_list)
        self.ui.calibrationStatus.setText(f"扫描结束: 发现 {count} 个目标")
        self.log.emit(f"扫描完成，准备抓取 {count} 个物体")
        self.execute_picking_sequence_signal.emit()

    def handle_object_detection(self, target_info):
        """处理摄像头线程发来的物体坐标"""
        x, y, z = target_info['robot_coords']
        color = target_info['color']
        
        # 坐标有效性检查 (过滤掉明显的噪声，比如坐标极大的点)
        if abs(x) > 200 or abs(y) > 200: 
            return

        # 更新UI显示
        self.object_detected.emit(target_info) # 触发仿真器画球

        current_time = time.time()

        # ================= 分类模式逻辑 =================
        if self.robot_mode == 'visual_sorting':
            # 1. 检查防抖动 (是否最近已处理过该位置的物体)
            for obj in self.processed_objects:
                dist = ((obj['x'] - x)**2 + (obj['y'] - y)**2)**0.5
                if dist < self.DEBOUNCE_DIST and (current_time - obj['time'] < self.DEBOUNCE_TIME):
                    return # 忽略此物体

            # 2. 确认为新物体，执行分类
            color_map = {'Red': 1, 'Yellow': 2, 'Blue': 3, 'Green': 4}
            if color not in color_map:
                return

            color_id = color_map[color]
            pick_z = self.visual_sorting_origin_z
            speed = 5 # 固定速度

            self.log.emit(f"检测到新物体: {color} @ ({x:.1f}, {y:.1f})")
            self.ui.calibrationStatus.setText(f"执行分类: {color} -> ID {color_id}")
            
            # 发送指令
            # 注意：MCU 应该负责具体的 吸起->移动->放置 动作
            self.serial_com.send_packet(
                command=self.serial_com.CMD_VISION_CLASSIFY,
                x=x, y=y, z=pick_z, speed=speed, dirc1=color_id
            )
            
            # 记录到防抖动列表
            self.processed_objects.append({'x': x, 'y': y, 'time': current_time})
            
            # 清理过期的防抖记录
            self.processed_objects = [o for o in self.processed_objects if current_time - o['time'] < self.DEBOUNCE_TIME]

        # ================= 拾取模式逻辑 =================
        elif self.robot_mode == 'visual_picking_scan':
            # 简单的去重逻辑
            is_duplicate = False
            for obj in self.detected_objects_list:
                dist = ((obj['robot_coords'][0] - x)**2 + (obj['robot_coords'][1] - y)**2)**0.5
                if dist < 20: # 20mm 内认为是同一个
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                self.detected_objects_list.append(target_info)
                self.log.emit(f"记录物体: {color} @ ({x:.1f}, {y:.1f})")

    def execute_picking_sequence(self):
        """执行批量抓取"""
        if not self.detected_objects_list:
            self.log.emit("列表为空，无动作")
            self.robot_mode = 'idle'
            return

        # 简单的执行逻辑：遍历列表发送 FETCH 指令
        # 实际工程中可能需要等待上一个动作完成（通过串口应答），这里简化为定时发送
        
        self.log.emit("开始批量执行抓取序列...")
        
        # 使用递归或定时器来逐个执行，防止瞬间发送所有指令堵塞串口
        self._send_next_pick_command(0)

    def _send_next_pick_command(self, index):
        if index >= len(self.detected_objects_list):
            self.robot_mode = 'idle'
            self.log.emit("批量抓取完成")
            self.ui.calibrationStatus.setText("状态: 批量抓取完成")
            return

        item = self.detected_objects_list[index]
        x, y, z = item['robot_coords']
        z_pick = self.visual_sorting_origin_z # 使用统一的抓取高度
        
        self.ui.calibrationStatus.setText(f"抓取第 {index+1}/{len(self.detected_objects_list)} 个: {item['color']}")
        self.serial_com.send_packet(command=self.serial_com.CMD_FETCH, x=x, y=y, z=z_pick)
        
        # 假设每次抓取动作耗时 4 秒，4秒后发送下一个
        QTimer.singleShot(4000, lambda: self._send_next_pick_command(index + 1))