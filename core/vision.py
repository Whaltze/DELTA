# -*- coding: utf-8 -*-
# core/vision.py
from PySide6.QtCore import QObject, QTimer, Signal
import time
from kinematics.kinematics import DeltaKinematics
from simulator.simulation import DeltaSimulator
from typing import Optional

class VisionFunctionality(QObject):
    visual_sorting_started = Signal()
    visual_picking_started = Signal()
    execute_picking_sequence_signal = Signal()
    object_detected = Signal(dict)
    log = Signal(str)

    def __init__(self, ui, mqtt_handler, kinematics, main_window=None):
        super().__init__()
        self.ui = ui
        self.mqtt_handler = mqtt_handler
        self.kinematics = kinematics
        # 【新增】保存主窗口引用，用于更新UI坐标
        self.main_window = main_window
        
        self.simulator: Optional[DeltaSimulator] = None
        self.robot_mode = 'idle'
        
        self.visual_sorting_origin_z = -220.0 
        self.safe_z = -150.0  # 安全移动高度
        self.MAX_RADIUS = 280.0
        
        self.processed_objects = [] 
        self.DEBOUNCE_DIST = 40.0
        self.DEBOUNCE_TIME = 6.0   

        self.detected_objects_list = []
        self.is_dynamic_mode = False
        self.detection_window_open = False 

        # 定义分类用的垃圾桶坐标 (X, Y)
        self.bins = {
            1: (-150, 200), # Red
            2: (0, 200),    # Yellow
            3: (150, 200),  # Blue
            4: (0, 250)     # Green
        }

    def set_dynamic_mode(self, state):
        self.is_dynamic_mode = (state != 0)
        self.log.emit(f"视觉模式: {'动态' if self.is_dynamic_mode else '静态'}")

    def start_visual_sorting(self):
        self.robot_mode = 'visual_sorting'
        self.processed_objects.clear()
        self.ui.calibrationStatus.setText("状态: 视觉分类中...")
        self.log.emit("视觉分类启动")
        if not self.is_dynamic_mode:
            self.detection_window_open = True
            QTimer.singleShot(5000, self._close_detection_window)

    def start_visual_picking(self):
        self.robot_mode = 'visual_picking_scan'
        self.detected_objects_list.clear()
        self.ui.calibrationStatus.setText("状态: 扫描中...")
        self.log.emit("开始扫描桌面")
        if not self.is_dynamic_mode:
            self.detection_window_open = True
        QTimer.singleShot(3000, self._after_scanning)

    def _close_detection_window(self):
        if self.robot_mode != 'idle':
            self.detection_window_open = False
            self.log.emit("扫描窗口关闭")

    def _after_scanning(self):
        self.robot_mode = 'visual_picking_executing'
        count = len(self.detected_objects_list)
        self.log.emit(f"扫描完成: 发现 {count} 个目标")
        if count > 0:
            self.execute_picking_sequence_signal.emit()
        else:
            self.robot_mode = 'idle'

    def handle_object_detection(self, target_info):
        if not self.is_dynamic_mode and not self.detection_window_open:
            return
        
        x, y, z = target_info['robot_coords']
        color = target_info['color']
        
        if (x**2 + y**2)**0.5 > self.MAX_RADIUS: return

        self.object_detected.emit(target_info)
        current_time = time.time()

        # ================= 分类模式 =================
        if self.robot_mode == 'visual_sorting':
            for obj in self.processed_objects:
                if ((obj['x']-x)**2 + (obj['y']-y)**2)**0.5 < self.DEBOUNCE_DIST and \
                   (current_time - obj['time'] < self.DEBOUNCE_TIME):
                    return 

            color_map = {'Red': 1, 'Yellow': 2, 'Blue': 3, 'Green': 4}
            if color not in color_map: return
            color_id = color_map[color]
            
            self.log.emit(f"执行分类: {color} -> ID {color_id}")
            
            # --- 执行物理动作序列 ---
            self._execute_sorting_action(x, y, color_id)
            
            self.processed_objects.append({'x': x, 'y': y, 'time': current_time})

        # ================= 拾取扫描模式 =================
        elif self.robot_mode == 'visual_picking_scan':
            is_duplicate = False
            for obj in self.detected_objects_list:
                if ((obj['robot_coords'][0]-x)**2 + (obj['robot_coords'][1]-y)**2)**0.5 < self.DEBOUNCE_DIST:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                self.detected_objects_list.append(target_info)
                self.log.emit(f"添加目标: {color} ({x:.1f}, {y:.1f})")

    def _update_robot_state(self, x, y, z):
        """【新增】统一的机器人状态更新方法（像写字功能一样）"""
        try:
            # 1. 计算对应的滑块位置
            target_pos = [x, y, z]
            sliders_z = self.kinematics.inverse_kinematics(target_pos)
            
            # 检查可达性
            if sliders_z is not None:
                # 2. 更新主窗口的内部状态存储
                if self.main_window:
                    self.main_window.current_robot_pos = target_pos
                
                # 3. 【新增】同步更新UI上的坐标显示（像寸动功能一样）
                if self.main_window:
                    self.main_window.update_ui_coords(target_pos)  # 更新动平台坐标
                    self.main_window.update_ui_sliders(sliders_z[0], sliders_z[1], sliders_z[2])  # 更新滑块坐标
                
                # 4. 更新仿真器状态
                if self.simulator and self.main_window.ui.simulator_enable_checkbox.isChecked():
                    self.simulator.update_by_sliders(sliders_z)
                
                # 5. 日志记录
                self.log.emit(f"视觉抓取: 移动到 ({x:.1f}, {y:.1f}, {z:.1f})")
                
                return True
            else:
                self.log.emit(f"视觉抓取警告: 目标位置 ({x:.1f}, {y:.1f}, {z:.1f}) 不可达")
                return False
                
        except Exception as e:
            self.log.emit(f"视觉抓取状态更新失败: {str(e)}")
            return False

    def _execute_sorting_action(self, x, y, color_id):
        """执行具体的 吸取->移动->放置 动作"""
        bin_x, bin_y = self.bins.get(color_id, (150, 0))
        ctrl = self.mqtt_handler

        # 1. 移动到物体上方
        self._update_robot_state(x, y, self.safe_z)
        self.mqtt_handler.move_to_xyz(x, y, self.safe_z, wait=True)

        # 2. 下降
        self._update_robot_state(x, y, self.visual_sorting_origin_z)
        self.mqtt_handler.move_to_xyz(x, y, self.visual_sorting_origin_z, wait=True)

        # 3. 吸气
        ctrl.set_digital_output(0, True)
        time.sleep(0.5)
        
        # 4. 抬起
        self._update_robot_state(x, y, self.safe_z)
        ctrl.move_to_xyz(x, y, self.safe_z, wait=True)

        # 5. 移动到垃圾桶上方
        self._update_robot_state(bin_x, bin_y, self.safe_z)
        ctrl.move_to_xyz(bin_x, bin_y, self.safe_z, wait=True)
        
        # 6. 放气
        ctrl.set_digital_output(0, False)

    def execute_picking_sequence(self):
        if not self.detected_objects_list: return
        self.log.emit("开始批量抓取")
        self._send_next_pick_command(0)

    def _send_next_pick_command(self, index):
        if index >= len(self.detected_objects_list) or self.robot_mode == 'idle':
            self.robot_mode = 'idle'
            self.log.emit("批量抓取完成")
            self.ui.calibrationStatus.setText("状态: 空闲")
            return
        
        item = self.detected_objects_list[index]
        x, y, z = item['robot_coords']
        
        self.ui.calibrationStatus.setText(f"抓取中 ({index+1}/{len(self.detected_objects_list)})...")
        
        # 1. 移动到物体上方
        self._update_robot_state(x, y, self.safe_z)
        self.mqtt_handler.move_to_xyz(x, y, self.safe_z, wait=True)

        # 2. 下降到物体位置
        self._update_robot_state(x, y, self.visual_sorting_origin_z)
        self.mqtt_handler.move_to_xyz(x, y, self.visual_sorting_origin_z, wait=True)

        # 3. 吸气
        self.mqtt_handler.set_digital_output(0, True)
        time.sleep(0.5)
        
        # 4. 抬起
        self._update_robot_state(x, y, self.safe_z)
        self.mqtt_handler.move_to_xyz(x, y, self.safe_z, wait=True)
        
        # 5. 移动到放置位置
        self._update_robot_state(200, 0, self.safe_z)
        self.mqtt_handler.move_to_xyz(200, 0, self.safe_z, wait=True)
        
        # 6. 放气
        self.mqtt_handler.set_digital_output(0, False)
        
        # 延时后执行下一个
        QTimer.singleShot(500, lambda: self._send_next_pick_command(index + 1))
