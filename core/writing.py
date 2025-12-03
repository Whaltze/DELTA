# -*- coding: utf-8 -*-
# core/writing.py
from PySide6.QtCore import QTimer

class WritingFunctionality:
    def __init__(self, ui, motion_controller, writing_canvas, logger=None, simulator=None):
        self.ui = ui
        self.motion_controller = motion_controller # DeltaMotionController
        self.writing_canvas = writing_canvas
        self.logger = logger or print
        self.simulator = simulator

        self.writing_mode = 'idle'
        self.writing_trajectory = []
        self.current_writing_index = 0
        self.writing_timer = QTimer()
        self.writing_timer.timeout.connect(self.send_next_writing_point)
    def text_to_trajectory(self, text, font_size=45, area_size=150, z_height=-280):
        # 优化策略：FZU专用逻辑 + 垂直提笔(消除拖尾) + 倒角美化
        trajectory = []
        z_up = z_height + 20
        
        # 字符几何参数
        char_w = font_size * 0.7       # 字体宽度比例
        bevel = font_size * 0.2        # U字的倒角大小
        char_spacing = font_size * 0.3 # 字符间距
        
        # --- 居中计算 ---
        total_width = len(text) * char_w + (len(text) - 1) * char_spacing
        start_x = -total_width / 2
        start_y = -font_size / 2
        
        for i, char in enumerate(text):
            # 当前字符左下角基准点
            curr_x = start_x + i * (char_w + char_spacing)
            curr_y = start_y
            
            # --- 辅助函数：添加一段笔画 ---
            # 逻辑：先移动到起点上方 -> 下笔 -> 画路径 -> 原地提笔
            def draw_stroke(points):
                if not points: return
                # 1. 提笔移至起点上方
                sx, sy = points[0]
                trajectory.append((sx, sy, z_up, False))
                # 2. 下笔
                trajectory.append((sx, sy, z_height, True))
                # 3. 绘制路径
                for px, py in points[1:]:
                    trajectory.append((px, py, z_height, True))
                # 4. 原地垂直提笔 (关键：修复仿真拖尾)
                ex, ey = points[-1]
                trajectory.append((ex, ey, z_up, False))

            if char == 'F':
                # 第一笔：左竖 + 顶横 (连写)
                # 从左下 -> 左上 -> 右上
                stroke1 = [
                    (curr_x, curr_y),
                    (curr_x, curr_y + font_size),
                    (curr_x + char_w, curr_y + font_size)
                ]
                draw_stroke(stroke1)
                
                # 第二笔：中横 (短一点，位置偏上)
                # 从中左 -> 中右
                mid_y = curr_y + font_size * 0.55
                stroke2 = [
                    (curr_x, mid_y),
                    (curr_x + char_w * 0.6, mid_y)
                ]
                draw_stroke(stroke2)

            elif char == 'Z':
                # 一笔画：左上 -> 右上 -> 左下 -> 右下
                stroke = [
                    (curr_x, curr_y + font_size),          # 起点：左上
                    (curr_x + char_w, curr_y + font_size), # 顶横
                    (curr_x, curr_y),                      # 斜线
                    (curr_x + char_w, curr_y)              # 底横
                ]
                draw_stroke(stroke)

            elif char == 'U':
                # 倒角 U：左上 -> 左下倒角 -> 底横 -> 右下倒角 -> 右上
                stroke = [
                    (curr_x, curr_y + font_size),          # 起点：左上
                    (curr_x, curr_y + bevel),              # 左竖 (停在倒角前)
                    (curr_x + bevel, curr_y),              # 左下倒角 (斜切)
                    (curr_x + char_w - bevel, curr_y),     # 底部横线
                    (curr_x + char_w, curr_y + bevel),     # 右下倒角 (斜切)
                    (curr_x + char_w, curr_y + font_size)  # 右竖
                ]
                draw_stroke(stroke)
                
            else:
                # 默认方框
                stroke = [
                    (curr_x, curr_y),
                    (curr_x, curr_y + font_size),
                    (curr_x + char_w, curr_y + font_size),
                    (curr_x + char_w, curr_y),
                    (curr_x, curr_y)
                ]
                draw_stroke(stroke)
            
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
    def clear_state(self):
        self.writing_trajectory = []
        self.current_writing_index = 0
        if self.simulator:
            self.simulator.set_trajectory([])
        self.ui.writing_status.setText("状态: 画布已清空")

    # ... (text_to_trajectory 和 use_handwriting_trajectory 函数逻辑无需修改，略) ...
    # 请保留您原文件中的 trajectory 生成逻辑

    def start_writing(self):
        if not self.writing_trajectory: return
        self.writing_mode = 'writing'
        self.current_writing_index = 0
        
        # 调整速度: 时间间隔越短，写字越快
        # 注意: 如果板卡指令缓存溢出，需要增大间隔
        speed_level = self.ui.writing_speed.value()
        interval = int(100 - (speed_level - 1) * 8) 
        self.writing_timer.start(max(20, interval))

    def stop_writing(self):
        self.writing_timer.stop()
        self.writing_mode = 'idle'
        self.ui.writing_status.setText("状态: 写字完成")

    def send_next_writing_point(self):
        if self.current_writing_index < len(self.writing_trajectory):
            point = self.writing_trajectory[self.current_writing_index]
            x, y, z, _ = point
            
            # [修改] 使用运动控制卡移动
            success = self.motion_controller.move_to_xyz(x, y, z, wait=False)
            
            if not success:
                self.logger(f"写字警告: 点 ({x:.1f}, {y:.1f}) 超出范围或控制卡错误")
            
            # 更新仿真
            if self.simulator and self.ui.simulator_enable_checkbox.isChecked():
                self.simulator.update_robot_state([x, y, z])
                
            self.writing_canvas.set_current_point(self.current_writing_index)
            self.current_writing_index += 1
        else:
            self.stop_writing()