# -*- coding: utf-8 -*-
"""
视觉功能封装模块
"""
from PySide6.QtCore import QObject, QTimer, Signal

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
        self.OBJECT_HEIGHT = 5.0
        self.visual_sorting_origin_z = 10.0
        self.visual_picking_stack_z = 5.0
        self.detected_objects_list = []

    def start_visual_sorting(self):
        # 启动视觉分类流程
        self.robot_mode = 'visual_sorting'
        self.ui.calibrationStatus.setText("状态: 视觉分类模式已启动，等待物体...")
        self.log.emit("视觉分类模式已启动")

    def start_visual_picking(self):
        # 启动视觉拾取流程
        self.robot_mode = 'visual_picking_scan'
        self.detected_objects_list.clear()
        self.ui.calibrationStatus.setText("状态: 视觉拾取模式 - 正在扫描物体(3秒)...")
        self.log.emit("视觉拾取模式: 开始扫描物体")
        QTimer.singleShot(3000, self._after_scanning)

    def _after_scanning(self):
        self.robot_mode = 'visual_picking_executing'
        self.ui.calibrationStatus.setText(f"状态: 扫描完成，发现 {len(self.detected_objects_list)} 个物体。开始拾取。")
        self.log.emit(f"视觉拾取: 扫描完成，发现 {len(self.detected_objects_list)} 个物体")
        self.execute_picking_sequence_signal.emit()

    def handle_object_detection(self, target_info):
        x, y, z = target_info['robot_coords']
        color = target_info['color']
        status_text = f"检测到 {color} 物体 @ ({x:.1f}, {y:.1f}, {z:.1f})"
        self.ui.calibrationStatus.setText(status_text)
        self.object_detected.emit(target_info)
        if self.robot_mode == 'visual_sorting':
            color_map = {'Red': 1, 'Yellow': 2, 'Blue': 3}
            if color not in color_map:
                return
            color_id = color_map[color]
            pick_z = self.visual_sorting_origin_z
            speed = self.serial_com.get_speed_level()
            self.serial_com.send_packet(
                command=self.serial_com.CMD_VISION_CLASSIFY,
                x=x, y=y, z=pick_z, speed=speed, dirc1=color_id
            )
            self.ui.calibrationStatus.setText(f"指令: 分类{color}物体，从Z={pick_z:.1f}处拾取")
            self.log.emit(f"发送分类指令: {color} 物体 @ Z={pick_z:.1f}")
            self.visual_sorting_origin_z -= self.OBJECT_HEIGHT
            self.robot_mode = 'idle'
        elif self.robot_mode == 'visual_picking_scan':
            # 判断是否重复
            is_duplicate = any(
                (abs(obj['robot_coords'][0]-x)<20 and abs(obj['robot_coords'][1]-y)<20)
                for obj in self.detected_objects_list)
            if not is_duplicate:
                self.detected_objects_list.append(target_info)
                self.ui.calibrationStatus.setText(f"扫描中... 已发现 {len(self.detected_objects_list)} 个物体")
                self.log.emit(f"视觉拾取扫描: 发现 {color} 物体，总数: {len(self.detected_objects_list)}")

    def execute_picking_sequence(self):
        # 假设所有目标排好序(可扩展排序规则)
        self.detected_objects_list.sort(key=lambda item: item['robot_coords'][1], reverse=True)
        for item in self.detected_objects_list:
            x, y, z_pick = item['robot_coords']
            color = item['color']
            self.ui.calibrationStatus.setText(f"执行中: 拾取位于({x:.1f}, {y:.1f})的{color}物体")
            self.log.emit(f"视觉拾取: 抓取 {color} 物体 @ ({x:.1f}, {y:.1f}, {z_pick:.1f})")
            self.serial_com.send_packet(command=self.serial_com.CMD_FETCH, x=x, y=y, z=z_pick)
        self.robot_mode = 'idle'
        self.ui.calibrationStatus.setText("状态: 视觉拾取任务完成。")
        self.log.emit("视觉拾取任务完成")
