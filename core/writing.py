# -*- coding: utf-8 -*-
# core/writing.py
from PySide6.QtCore import QTimer

class WritingFunctionality:
    def __init__(self, ui, serial_com, writing_canvas, logger=None, simulator=None):
        self.ui = ui
        self.serial_com = serial_com
        self.writing_canvas = writing_canvas
        self.logger = logger or print
        self.simulator = simulator

        self.writing_mode = 'idle'
        self.writing_trajectory = []
        self.current_writing_index = 0
        self.writing_timer = QTimer()
        self.writing_timer.timeout.connect(self.send_next_writing_point)

    def clear_state(self):
        self.writing_trajectory = []
        self.current_writing_index = 0
        if self.simulator:
            # 这里传空列表给仿真器，仿真器已修复处理空列表的逻辑
            self.simulator.set_trajectory([])
        self.ui.writing_status.setText("状态: 画布已清空")

    def text_to_trajectory(self, text, font_size=30, area_size=150, z_height=-280):
        # 简化的文本生成逻辑 (字符 F)
        trajectory = []
        z_up = z_height + 20
        start_x = -len(text) * font_size / 2
        
        for i, char in enumerate(text):
            current_x = start_x + i * (font_size + 10)
            current_y = 0
            # 提笔移动
            trajectory.append((current_x, current_y, z_up, False))
            # 下笔
            trajectory.append((current_x, current_y, z_height, True))
            trajectory.append((current_x, current_y + font_size, z_height, True))
            trajectory.append((current_x + font_size*0.6, current_y + font_size, z_height, True))
            # 简单的笔画
            trajectory.append((current_x, current_y + font_size*0.5, z_height, True))
            trajectory.append((current_x + font_size*0.5, current_y + font_size*0.5, z_height, True))
            # 提笔
            trajectory.append((current_x + font_size, current_y, z_up, False))
            
        return trajectory

    def use_handwriting_trajectory(self):
        # [核心修复] 必须在此处动态获取 UI 的高度值
        z_write = self.ui.z_height.value()
        z_safe = z_write + 20.0
        area_size = self.ui.writing_area.value()
        
        raw_points = self.writing_canvas.handwriting_points
        if not raw_points:
            self.logger("警告: 画布为空")
            return False

        trajectory = []
        w = self.writing_canvas.width()
        h = self.writing_canvas.height()
        
        # 转换坐标并应用 Z 高度
        for i, p in enumerate(raw_points):
            if hasattr(p, 'x'): px, py = p.x(), p.y()
            else: px, py = p[0], p[1]
            
            # 映射到物理尺寸，注意 Y 轴反转
            real_x = (px / w - 0.5) * area_size
            real_y = -(py / h - 0.5) * area_size
            
            if i == 0:
                trajectory.append((real_x, real_y, z_safe, False))
            
            trajectory.append((real_x, real_y, z_write, True))
            
        # 最后提笔
        if trajectory:
            last = trajectory[-1]
            trajectory.append((last[0], last[1], z_safe, False))

        self.writing_trajectory = trajectory
        
        if self.simulator:
            # 同步到仿真
            sim_traj = [[p[0], p[1], p[2]] for p in self.writing_trajectory]
            self.simulator.set_trajectory(sim_traj)
            
        self.logger(f"手写轨迹已生成，写字高度: {z_write}")
        return True

    def preview_writing_trajectory(self):
        try:
            self.writing_trajectory = []
            mode = self.ui.input_method.currentText()
            z_val = self.ui.z_height.value()
            area_val = self.ui.writing_area.value()

            if mode == "文本输入":
                text = self.ui.text_input.text()
                if not text: return
                font_val = self.ui.font_size.value()
                self.writing_trajectory = self.text_to_trajectory(text, font_val, area_val, z_val)
            elif mode == "手写输入":
                if not self.use_handwriting_trajectory(): return

            if self.writing_trajectory:
                self.writing_canvas.set_trajectory(self.writing_trajectory)
                # 再次确保仿真同步
                if self.simulator:
                    sim_pts = [[p[0], p[1], p[2]] for p in self.writing_trajectory]
                    self.simulator.set_trajectory(sim_pts)
                self.ui.writing_status.setText(f"状态: {mode}轨迹生成完成")
                
        except Exception as e:
            self.logger(f"轨迹错误: {e}")

    def start_writing(self):
        if not self.writing_trajectory: return
        self.writing_mode = 'writing'
        self.current_writing_index = 0
        speed = self.ui.writing_speed.value()
        interval = int(200 - (speed - 1) * 15)
        self.writing_timer.start(interval)

    def stop_writing(self):
        self.writing_timer.stop()
        self.writing_mode = 'idle'
        self.ui.writing_status.setText("状态: 写字完成")

    def send_next_writing_point(self):
        if self.current_writing_index < len(self.writing_trajectory):
            point = self.writing_trajectory[self.current_writing_index]
            x, y, z, _ = point
            
            # 发送硬件指令
            self.serial_com.send_packet(command=self.serial_com.CMD_JOG, x=x, y=y, z=z)
            
            # 发送仿真指令
            if self.simulator and self.ui.simulator_enable_checkbox.isChecked():
                self.simulator.update_robot_state([x, y, z])
                
            self.writing_canvas.set_current_point(self.current_writing_index)
            self.current_writing_index += 1
        else:
            self.stop_writing()