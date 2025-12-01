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
        """处理检测到的物体"""
        try:
            # 检查target_info结构
            if 'robot_coords' not in target_info or 'color' not in target_info:
                print(f"[Vision] 错误: 无效的target_info结构: {target_info}")
                return
                
            robot_coords = target_info['robot_coords']
            if len(robot_coords) < 3:
                print(f"[Vision] 错误: 坐标数据不完整: {robot_coords}")
                return
                
            x, y, z = robot_coords[:3]  # 只取前三个坐标
            color = target_info['color']
            status_text = f"检测到 {color} 物体 @ ({x:.1f}, {y:.1f}, {z:.1f})"
            self.ui.calibrationStatus.setText(status_text)
            
            # 发射信号
            self.object_detected.emit(target_info)
            
            # 根据模式处理
            if self.robot_mode == 'visual_sorting':
                self._handle_visual_sorting(x, y, z, color)
            elif self.robot_mode == 'visual_picking_scan':
                self._handle_visual_picking_scan(x, y, z, color)
                
        except Exception as e:
            print(f"[Vision] handle_object_detection错误: {e}")
            import traceback
            traceback.print_exc()

    def _handle_visual_sorting(self, x, y, z, color):
        """处理视觉分类模式"""
        try:
            color_map = {'Red': 1, 'Yellow': 2, 'Blue': 3}
            if color not in color_map:
                self.log.emit(f"警告: 未知颜色 {color}，跳过处理")
                return
                
            color_id = color_map[color]
            pick_z = self.visual_sorting_origin_z
            speed = self.serial_com.get_speed_level()
            
            self.serial_com.send_packet(
                command=self.serial_com.CMD_VISION_CLASSIFY,
                x=x, y=y, z=pick_z, speed=speed, dirc1=color_id
            )
            
            status_text = f"指令: 分类{color}物体，从Z={pick_z:.1f}处拾取"
            self.ui.calibrationStatus.setText(status_text)
            self.log.emit(f"发送分类指令: {color} 物体 @ Z={pick_z:.1f}")
            
            self.visual_sorting_origin_z -= self.OBJECT_HEIGHT
            self.robot_mode = 'idle'
            
        except Exception as e:
            self.log.emit(f"视觉分类处理错误: {e}")

    def _handle_visual_picking_scan(self, x, y, z, color):
        """处理视觉拾取扫描模式"""
        try:
            # 检查是否重复检测
            is_duplicate = False
            for obj in self.detected_objects_list:
                if 'robot_coords' in obj and len(obj['robot_coords']) >= 2:
                    obj_x, obj_y = obj['robot_coords'][:2]
                    if abs(obj_x - x) < 20 and abs(obj_y - y) < 20:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                new_target = {
                    'robot_coords': [x, y, z],
                    'color': color,
                    'pixel_coords': target_info.get('pixel_coords', (0, 0))
                }
                self.detected_objects_list.append(new_target)
                
                status_text = f"扫描中... 已发现 {len(self.detected_objects_list)} 个物体"
                self.ui.calibrationStatus.setText(status_text)
                self.log.emit(f"视觉拾取扫描: 发现 {color} 物体，总数: {len(self.detected_objects_list)}")
                
        except Exception as e:
            self.log.emit(f"视觉拾取扫描处理错误: {e}")