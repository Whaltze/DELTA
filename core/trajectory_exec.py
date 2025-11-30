# -*- coding: utf-8 -*-
"""
轨迹调度和执行模块
"""
from PySide6.QtCore import QTimer
import numpy as np

class TrajectoryExecution:
    def __init__(self, ui, serial_com, kinematics, planner, visualizer, logger=None, simulator=None):
        self.ui = ui
        self.serial_com = serial_com
        self.kinematics = kinematics
        self.planner = planner
        self.visualizer = visualizer
        self.logger = logger or (lambda msg: print(msg))
        self.simulator = simulator  # Delta机器人仿真器
        self.trajectory_timer = QTimer()
        self.trajectory_timer.timeout.connect(self.send_next_trajectory_point)
        self.trajectory_points = []
        self.current_trajectory_index = 0

    def run_jog_sequence(self):
        """生成线性末端轨迹，做正逆解可视化，并可选择发送给机器人执行。"""
        if self.trajectory_timer.isActive():
            self.logger("轨迹执行中，请稍候。")
            return
        start_x = self.ui.start_x_spinbox.value()
        start_y = self.ui.start_y_spinbox.value()
        start_z = self.ui.start_z_spinbox.value()
        end_x = self.ui.end_x_spinbox.value()
        end_y = self.ui.end_y_spinbox.value()
        end_z = self.ui.end_z_spinbox.value()
        num_points = 200
        send_interval_ms = 20
        trajectory = self.planner.linear_trajectory(
            [start_x, start_y, start_z], [end_x, end_y, end_z], num_points=num_points
        )
        self.logger(
            f"点动序列: 生成轨迹从({start_x}, {start_y}, {start_z})到({end_x}, {end_y}, {end_z})"
        )
        # 可视化末端与关节/误差
        self.visualizer.plot_3d_trajectory(
            trajectory,
            title=f"线性轨迹: 从({start_x}, {start_y}, {start_z})到({end_x}, {end_y}, {end_z})",
        )
        self.visualizer.plot_kinematics_analysis(
            trajectory,
            self.kinematics,
            send_interval_ms / 1000.0,
            title="线性轨迹 正逆解分析",
        )
        # 发送给机器人执行
        self.trajectory_points = trajectory
        self.current_trajectory_index = 0
        
        # 如果启用了仿真，更新仿真显示
        if self.simulator and self.ui.simulator_enable_checkbox.isChecked():
            self.simulator.set_trajectory(trajectory)
            self.simulator.trajectory_index = 0
        
        self.ui.calibrationStatus.setText(f"状态: 开始发送线性轨迹，共 {num_points} 个点。")
        self.trajectory_timer.start(send_interval_ms)

    def run_curve(self):
        """生成预定义曲线末端轨迹，做正逆解可视化，并发送执行。"""
        if self.trajectory_timer.isActive():
            self.logger("曲线运动执行中，请稍候。")
            return
        curve_type = self.ui.comboBox.currentText()
        num_points = 300
        send_interval_ms = 15
        trajectory = None
        import numpy as np
        if curve_type == "门型曲线":
            p1 = np.array([50, -100, -250])
            p2 = np.array([50, 100, -250])
            p3 = np.array([-50, 100, -250])
            p4 = np.array([-50, -100, -250])
            path1 = self.planner.linear_trajectory(p1, p2, 100)
            path2 = self.planner.linear_trajectory(p2, p3, 100)
            path3 = self.planner.linear_trajectory(p3, p4, 100)
            trajectory = np.vstack((path1, path2, path3))
        elif curve_type == "花朵":
            center = np.array([0, 0, -280])
            a = 80
            n = 5
            thetas = np.linspace(0, 2 * np.pi, num_points)
            radii = a * np.sin(n * thetas)
            x_coords = center[0] + radii * np.cos(thetas)
            y_coords = center[1] + radii * np.sin(thetas)
            z_coords = np.full(num_points, center[2])
            trajectory = np.vstack((x_coords, y_coords, z_coords)).T
        elif curve_type == "Lame曲线":
            center = np.array([0, 0, -280])
            a = 120
            b = 80
            n = 2.5
            t = np.linspace(0, 2 * np.pi, num_points)
            x_coords = center[0] + a * np.sign(np.cos(t)) * np.abs(np.cos(t)) ** (2 / n)
            y_coords = center[1] + b * np.sign(np.sin(t)) * np.abs(np.sin(t)) ** (2 / n)
            z_coords = np.full(num_points, center[2])
            trajectory = np.vstack((x_coords, y_coords, z_coords)).T
        if trajectory is None:
            return
        self.visualizer.plot_3d_trajectory(trajectory, title=f"曲线轨迹: {curve_type}")
        self.visualizer.plot_kinematics_analysis(
            trajectory,
            self.kinematics,
            send_interval_ms / 1000.0,
            title=f"曲线 '{curve_type}' 正逆解分析",
        )
        self.trajectory_points = trajectory
        self.current_trajectory_index = 0
        
        # 如果启用了仿真，更新仿真显示
        if self.simulator and self.ui.simulator_enable_checkbox.isChecked():
            self.simulator.set_trajectory(trajectory)
            self.simulator.trajectory_index = 0
        
        self.ui.calibrationStatus.setText(f"状态: 开始发送曲线 '{curve_type}'...")
        self.trajectory_timer.start(send_interval_ms)

    def send_next_trajectory_point(self):
        if self.current_trajectory_index < len(self.trajectory_points):
            point = self.trajectory_points[self.current_trajectory_index]
            if self.kinematics.inverse_kinematics(point) is None:
                self.logger(f"轨迹点警告: 点 {point} 不可达，已跳过")
                self.current_trajectory_index += 1
                return
            
            # 如果启用了仿真，实时更新仿真显示
            if self.simulator and self.ui.simulator_enable_checkbox.isChecked():
                try:
                    self.simulator.trajectory_index = self.current_trajectory_index
                    self.simulator.update_robot_state(point, redraw=True)
                except Exception as e:
                    self.logger(f"仿真更新错误: {e}")
            
            speed = self.serial_com.get_speed_level()
            self.serial_com.send_packet(
                command=self.serial_com.CMD_JOG, x=point[0], y=point[1], z=point[2], speed=speed)
            progress = (self.current_trajectory_index + 1) / len(self.trajectory_points) * 100
            self.ui.calibrationStatus.setText(f"状态: 轨迹执行中... ({progress:.1f}%)")
            self.current_trajectory_index += 1
        else:
            self.trajectory_timer.stop()
            self.ui.calibrationStatus.setText("状态: 轨迹执行完成。")
            self.logger("轨迹执行完成")
