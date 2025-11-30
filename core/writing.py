# -*- coding: utf-8 -*-
"""
写字功能模块：封装和 UI 交互、轨迹生成、写字执行等相关。
"""
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox
from PySide6.QtGui import QPixmap
import time

class WritingFunctionality:
    def __init__(self, ui, serial_com, writing_canvas, logger=None):
        self.ui = ui
        self.serial_com = serial_com
        self.writing_canvas = writing_canvas
        self.logger = logger or self.log_terminal

        self.writing_mode = 'idle'
        self.writing_trajectory = []
        self.current_writing_index = 0
        self.writing_timer = QTimer()
        self.writing_timer.timeout.connect(self.send_next_writing_point)

    def log_terminal(self, msg):
        print(msg)

    def use_handwriting_trajectory(self):
        handwriting_trajectory = self.writing_canvas.get_handwriting_trajectory(
            z_height=self.ui.z_height.value(),
            area_size=self.ui.writing_area.value()
        )
        if not handwriting_trajectory:
            self.logger("警告: 未检测到手写轨迹，请先在画布上书写")
            return False
        self.writing_trajectory = handwriting_trajectory
        self.writing_canvas.set_trajectory(self.writing_trajectory)
        self.logger(f"手写轨迹已转换，共{len(self.writing_trajectory)}个点")
        return True

    def text_to_trajectory(self, text, font_size=30, area_size=150, z_height=-280):
        trajectory = []
        char_spacing = font_size * 0.8
        start_x = -area_size / 2
        start_y = 0
        current_x = start_x
        current_y = start_y
        trajectory.append((current_x, current_y, z_height + 10, False))
        for char in text:
            if char.upper() == 'F':
                points = [
                    (current_x, current_y + font_size, z_height, True),
                    (current_x, current_y, z_height, True),
                    (current_x, current_y + font_size, z_height, True),
                    (current_x + font_size * 0.6, current_y + font_size, z_height, True),
                    (current_x, current_y + font_size * 0.5, z_height, True),
                    (current_x + font_size * 0.4, current_y + font_size * 0.5, z_height, True),
                ]
                trajectory.extend(points)
                trajectory.append((current_x + char_spacing * 0.8, current_y, z_height + 10, False))
                current_x += char_spacing
            elif char.upper() == 'Z':
                points = [
                    (current_x, current_y + font_size, z_height, True),
                    (current_x + font_size * 0.8, current_y + font_size, z_height, True),
                    (current_x, current_y, z_height, True),
                    (current_x + font_size * 0.8, current_y, z_height, True),
                ]
                trajectory.extend(points)
                trajectory.append((current_x + char_spacing, current_y, z_height + 10, False))
                current_x += char_spacing
            elif char.upper() == 'U':
                points = [
                    (current_x, current_y + font_size, z_height, True),
                    (current_x, current_y + font_size * 0.2, z_height, True),
                    (current_x + font_size * 0.2, current_y, z_height, True),
                    (current_x + font_size * 0.6, current_y, z_height, True),
                    (current_x + font_size * 0.8, current_y + font_size * 0.2, z_height, True),
                    (current_x + font_size * 0.8, current_y + font_size, z_height, True),
                ]
                trajectory.extend(points)
                trajectory.append((current_x + char_spacing, current_y + font_size, z_height + 10, False))
                current_x += char_spacing
            else:
                points = [
                    (current_x, current_y, z_height, True),
                    (current_x + font_size * 0.8, current_y, z_height, True),
                    (current_x + font_size * 0.8, current_y + font_size, z_height, True),
                    (current_x, current_y + font_size, z_height, True),
                    (current_x, current_y, z_height, True),
                ]
                trajectory.extend(points)
                trajectory.append((current_x + char_spacing, current_y, z_height + 10, False))
                current_x += char_spacing
        return trajectory

    def preview_writing_trajectory(self):
        try:
            if self.ui.input_method.currentText() == "文本输入":
                text = self.ui.text_input.text()
                if not text:
                    self.logger("错误: 请输入要写的文字")
                    return
                font_size = self.ui.font_size.value()
                area_size = self.ui.writing_area.value()
                z_height = self.ui.z_height.value()
                self.writing_trajectory = self.text_to_trajectory(text, font_size, area_size, z_height)
                self.logger(f"文本轨迹生成完成: '{text}', 共{len(self.writing_trajectory)}个点")
            else:
                if not self.writing_canvas.handwriting_points:
                    self.logger("错误: 请先在画布上手写文字")
                    return
                self.use_handwriting_trajectory()
            self.writing_canvas.set_trajectory(self.writing_trajectory)
            self.ui.writing_status.setText("状态: 轨迹预览完成")
        except Exception as e:
            self.logger(f"轨迹生成错误: {str(e)}")
            self.ui.writing_status.setText("状态: 轨迹生成错误")

    def start_writing(self):
        if not self.serial_com.is_connected:
            self.logger("错误: 请先连接串口")
            return
        if not self.writing_trajectory:
            self.logger("错误: 请先生成轨迹预览")
            return
        if self.writing_timer.isActive():
            self.logger("警告: 写字任务正在进行中")
            return
        self.writing_mode = 'writing'
        self.current_writing_index = 0
        self.ui.writing_status.setText("状态: 写字进行中...")
        self.logger("开始执行写字任务")
        speed = self.ui.writing_speed.value()
        interval = max(50, 200 - speed * 15)
        self.writing_timer.start(interval)

    def stop_writing(self):
        self.writing_timer.stop()
        self.writing_mode = 'idle'
        self.ui.writing_status.setText("状态: 已停止")
        self.logger("写字任务已停止")
        self.writing_canvas.set_current_point(-1)
        if self.writing_trajectory and self.current_writing_index < len(self.writing_trajectory):
            last_point = self.writing_trajectory[self.current_writing_index - 1] if self.current_writing_index > 0 else self.writing_trajectory[0]
            x, y, z, pen_down = last_point
            self.serial_com.send_packet(
                command=self.serial_com.CMD_JOG,
                x=x, y=y, z=z + 10,
                speed=self.ui.writing_speed.value()
            )

    def send_next_writing_point(self):
        if self.current_writing_index < len(self.writing_trajectory):
            point = self.writing_trajectory[self.current_writing_index]
            x, y, z, pen_down = point
            speed = self.ui.writing_speed.value()
            self.serial_com.send_packet(
                command=self.serial_com.CMD_JOG,
                x=x, y=y, z=z,
                speed=speed
            )
            self.writing_canvas.set_current_point(self.current_writing_index)
            progress = (self.current_writing_index + 1) / len(self.writing_trajectory) * 100
            self.ui.writing_status.setText(f"状态: 写字中... {progress:.1f}%")
            self.current_writing_index += 1
        else:
            self.writing_timer.stop()
            self.writing_mode = 'idle'
            self.ui.writing_status.setText("状态: 写字完成")
            self.logger("写字任务完成")
            self.writing_canvas.set_current_point(-1)
