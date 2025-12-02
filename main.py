# -*- coding: utf-8 -*-
# main.py
import sys
import signal
import numpy as np
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import QTimer
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox

from ui.UI import Ui_Widget
import resources.rc.Background_rc as Background_rc

from camera.camera import Camera
from communication.com import SerialCommunication
from kinematics.kinematics import DeltaKinematics
from kinematics.trajectory import TrajectoryPlanner
from visualization.visualizer import TrajectoryVisualizer
from simulator.simulation import DeltaSimulator 

from core.writing import WritingFunctionality
from core.vision import VisionFunctionality
from core.calibration import CalibrationHandler
from core.trajectory_exec import TrajectoryExecution
from ui.writing_canvas import WritingCanvas

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Widget()
        self.ui.setupUi(self)

        # 1. 基础组件
        self.camera_thread = Camera()
        self.serial_com = SerialCommunication(self.ui)

        # 2. 算法
        side_sp, side_ep, rod_len = 300.0, 100.0, 300.0
        sp_radius = side_sp / (3**0.5)
        ep_radius = side_ep / (3**0.5)
        self.kinematics = DeltaKinematics(sp=sp_radius, ep=ep_radius, rod_length=rod_len)
        self.planner = TrajectoryPlanner()
        self.visualizer = TrajectoryVisualizer()
        
        # 3. 仿真窗口
        self.simulator_window = DeltaSimulator(self.kinematics)
        self.simulator_window.setWindowTitle("Linear Delta 数字孪生系统")
        self.simulator_window.resize(800, 600)
        self.current_robot_pos = [0.0, 0.0, -300.0]
        self.simulator_window.update_robot_state(self.current_robot_pos)

        # 4. 核心功能
        self.writing_func = WritingFunctionality(
            self.ui, self.serial_com, None, self.log_terminal, 
            simulator=self.simulator_window
        )
        self.vision_func = VisionFunctionality(self.ui, self.serial_com)
        self.calib_handler = CalibrationHandler(self.ui, self.camera_thread, self, self.log_terminal)
        
        self.traj_executor = TrajectoryExecution(
            self.ui, self.serial_com, self.kinematics, self.planner, self.visualizer, 
            logger=self.log_terminal, simulator=self.simulator_window
        )

        # 5. UI初始化
        self.init_writing_canvas()
        self.populate_camera_list()
        self.connect_signals()
        
        self.log_terminal("系统全功能就绪")

    def connect_signals(self):
        # 摄像头
        self.ui.cameraButton1.clicked.connect(self.init_camera)
        self.ui.cameraButton2.clicked.connect(self.close_camera)
        # self.ui.apply_transform_button.clicked.connect(self.apply_calibration_matrix)
        self.ui.apply_transform_button.clicked.connect(self.calib_handler.apply_hand_eye_transform)


        # 写字
        self.ui.preview_button.clicked.connect(self.writing_func.preview_writing_trajectory)
        self.ui.start_writing_button.clicked.connect(self.writing_func.start_writing)
        self.ui.stop_writing_button.clicked.connect(self.writing_func.stop_writing)
        self.ui.clear_canvas_button.clicked.connect(self.clear_writing_canvas)
        self.ui.use_handwriting_button.clicked.connect(self.writing_func.use_handwriting_trajectory)

        # 视觉
        self.ui.pushButton_4.clicked.connect(self.vision_func.start_visual_sorting)
        self.ui.pushButton_5.clicked.connect(self.vision_func.start_visual_picking)
        self.vision_func.object_detected.connect(self.update_sim_vision_object)
        self.vision_func.log.connect(self.log_terminal)
        self.camera_thread.object_detected_robot_coords.connect(self.vision_func.handle_object_detection)
        self.vision_func.execute_picking_sequence_signal.connect(self.execute_vision_pick_simulation)

        # 机器人控制
        self.ui.pushButton_2.clicked.connect(self.handle_emergency)
        self.ui.pushButton_3.clicked.connect(self.handle_reset)
        self.ui.solve_ik_button.clicked.connect(self.on_solve_ik)
        
        # 寸动 (XYZ移动)
        step = 10.0
        self.ui.pushButton_8.clicked.connect(lambda: self.handle_inch_move(0, step))
        self.ui.pushButton_9.clicked.connect(lambda: self.handle_inch_move(0, -step))
        self.ui.pushButton_10.clicked.connect(lambda: self.handle_inch_move(1, step))
        self.ui.pushButton_11.clicked.connect(lambda: self.handle_inch_move(1, -step))
        self.ui.pushButton_12.clicked.connect(lambda: self.handle_inch_move(2, step))
        self.ui.pushButton_13.clicked.connect(lambda: self.handle_inch_move(2, -step))

        # 电机调试 (单轴移动)
        self.ui.pushButton_14.clicked.connect(lambda: self.handle_motor_debug(0, step))
        self.ui.pushButton_15.clicked.connect(lambda: self.handle_motor_debug(0, -step))
        self.ui.pushButton_16.clicked.connect(lambda: self.handle_motor_debug(1, step))
        self.ui.pushButton_17.clicked.connect(lambda: self.handle_motor_debug(1, -step))
        self.ui.pushButton_18.clicked.connect(lambda: self.handle_motor_debug(2, step))
        self.ui.pushButton_19.clicked.connect(lambda: self.handle_motor_debug(2, -step))

        self.ui.pushButton_6.clicked.connect(self.traj_executor.run_curve)
        self.ui.run_jog_sequence_button.clicked.connect(self.traj_executor.run_jog_sequence)
        self.ui.open_simulator_button.clicked.connect(self.show_simulator)

    # def apply_calibration_matrix(self):
    #     """应用手眼标定矩阵"""
    #     try:
    #         x, y, z = self.ui.trans_x.value(), self.ui.trans_y.value(), self.ui.trans_z.value()
    #         r, p, yw = self.ui.trans_r.value(), self.ui.trans_p.value(), self.ui.trans_y_2.value()
    #         self.camera_thread.set_transform_matrix(x, y, z, r, p, yw)
    #         self.log_terminal("已应用标定矩阵")
    #     except Exception as e:
    #         self.log_terminal(f"标定参数错误: {e}")

    # ================= 核心修复：寸动与电机调试 =================
    def handle_inch_move(self, axis_idx, delta):
        """处理 XYZ 坐标系下的点动"""
        new_pos = list(self.current_robot_pos)
        new_pos[axis_idx] += delta
        
        # [修复] 必须使用 is not None 判断 numpy 数组返回
        if self.kinematics.inverse_kinematics(new_pos) is not None:
            self.current_robot_pos = new_pos
            if self.ui.simulator_enable_checkbox.isChecked():
                self.simulator_window.update_robot_state(new_pos)
            self.serial_com.send_inch_debug_command(axis_idx + 1, 1 if delta > 0 else 0)
        else:
            self.log_terminal("警告: 目标位置不可达")

    def handle_motor_debug(self, motor_idx, delta):
        """处理 单轴电机 调试"""
        # 获取仿真器当前滑块位置
        current_sliders = list(self.simulator_window.current_sliders_z)
        current_sliders[motor_idx] += delta
        
        # [修复] 调用 update_by_sliders 进行仿真更新(包含正解)
        if self.ui.simulator_enable_checkbox.isChecked():
            success = self.simulator_window.update_by_sliders(current_sliders)
            if success:
                # 如果正解成功，更新当前全局坐标
                fk = self.kinematics.forward_kinematics(current_sliders)
                if fk is not None:
                    self.current_robot_pos = list(fk)
            else:
                self.log_terminal(f"电机调试: 轴{motor_idx+1}移动导致无法构成闭环")

        # 发送串口指令 (1-6 对应 A+ A- B+ ...)
        cmd_idx = (motor_idx * 2) + (1 if delta > 0 else 2)
        self.serial_com.send_motor_debug_command(cmd_idx)

    # ========================================================

    def execute_vision_pick_simulation(self):
        self.vision_func.execute_picking_sequence()
        # 简单的仿真动画
        if self.ui.simulator_enable_checkbox.isChecked():
            objects = self.vision_func.detected_objects_list
            if not objects: return
            self.sim_animation_step = 0
            self.sim_animation_objects = objects
            self.sim_timer = QTimer()
            self.sim_timer.timeout.connect(self._animate_next_pick_step)
            self.sim_timer.start(1000)

    def _animate_next_pick_step(self):
        if self.sim_animation_step >= len(self.sim_animation_objects):
            self.sim_timer.stop()
            return
        obj = self.sim_animation_objects[self.sim_animation_step]
        tx, ty, tz = obj['robot_coords']
        # 模拟 移动->下->抓->上->放
        QTimer.singleShot(100, lambda: self.simulator_window.update_robot_state([tx, ty, tz + 50]))
        QTimer.singleShot(500, lambda: self.simulator_window.update_robot_state([tx, ty, tz]))
        QTimer.singleShot(1000, lambda: self.simulator_window.update_robot_state([tx, ty, tz + 50]))
        QTimer.singleShot(1500, lambda: self.simulator_window.update_robot_state([200, 0, -200])) # 假设卸料点
        QTimer.singleShot(1600, lambda: self.simulator_window.clear_detected_objects()) # 简化：一次清空
        self.sim_animation_step += 1

    def update_sim_vision_object(self, target_info):
        if self.ui.simulator_enable_checkbox.isChecked():
            c = target_info['robot_coords']
            self.simulator_window.add_detected_object(c[0], c[1], c[2], target_info['color'])

    def handle_reset(self):
        self.log_terminal("复位系统...")
        self.serial_com.reset_position()
        self.current_robot_pos = [0.0, 0.0, -300.0]
        self.simulator_window.update_robot_state(self.current_robot_pos)
        self.simulator_window.set_emergency_state(False)
        self.simulator_window.set_trajectory([])
        self.simulator_window.clear_detected_objects()

    def handle_emergency(self):
        self.log_terminal("!!! 急停 !!!")
        self.serial_com.emergency_stop()
        self.simulator_window.set_emergency_state(True)
        if hasattr(self, 'sim_timer'): self.sim_timer.stop()
        self.writing_func.writing_timer.stop()

    def on_solve_ik(self):
        P = [self.ui.ik_x.value(), self.ui.ik_y.value(), self.ui.ik_z.value()]
        sliders = self.kinematics.inverse_kinematics(P)
        if sliders is not None: 
            self.ui.ik_result_label.setText(f"Z: {sliders[0]:.1f}, {sliders[1]:.1f}, {sliders[2]:.1f}")
            if self.ui.simulator_enable_checkbox.isChecked():
                self.simulator_window.update_robot_state(P)
        else:
            self.ui.ik_result_label.setText("不可达")

    def log_terminal(self, msg):
        self.ui.log_terminal(f"[{QtCore.QDateTime.currentDateTime().toString('HH:mm:ss')}] {msg}")

    def init_writing_canvas(self):
        self.writing_canvas = WritingCanvas(self.ui.writing_group)
        self.writing_canvas.setGeometry(10, 485, 320, 150)
        self.ui.writing_canvas = self.writing_canvas
        self.writing_func.writing_canvas = self.writing_canvas
        # 设置默认值
        self.ui.z_height.setValue(-280.0)
        self.ui.writing_area.setValue(200)

    def populate_camera_list(self):
        self.ui.camera_selector.clear()
        cams = Camera.scan_cameras()
        if not cams:
            self.ui.camera_selector.addItem("无摄像头")
            self.ui.cameraButton1.setEnabled(False)
        else:
            for idx, name in cams:
                self.ui.camera_selector.addItem(f"{name}", userData=idx)
            self.ui.cameraButton1.setEnabled(True)

    # def init_camera(self):
    #     idx = self.ui.camera_selector.currentData()
    #     if idx is None: return
    #     self.camera_thread = Camera()
    #     self.camera_thread.set_cam_number(idx)
    #     self.camera_thread.sendPicture.connect(self.receive_frame)
    #     self.camera_thread.start()
    #     self.ui.cameraButton1.setText("运行中")
    #     self.ui.cameraButton1.setEnabled(False)
    #     self.ui.cameraButton2.setEnabled(True)

    def init_camera(self):
        """根据选择初始化并打开摄像头"""
        if self.camera_thread and self.camera_thread.isRunning():
            self.close_camera()

        selected_index = self.ui.camera_selector.currentData()
        if selected_index is None:
            QMessageBox.warning(self, "摄像头错误", "未选择有效的摄像头。")
            return

        self.camera_thread = Camera()
        self.camera_thread.set_cam_number(selected_index)

        # 连接摄像头线程的信号
        self.camera_thread.sendPicture.connect(self.receive_frame)
        self.camera_thread.object_detected_robot_coords.connect(self.vision_func.handle_object_detection)

        self.camera_thread.start()
        self.ui.cameraButton1.setText("采集中...")
        self.ui.cameraButton1.setEnabled(False)
        self.ui.cameraButton2.setEnabled(True)

    def close_camera(self):
        self.camera_thread.stop()
        
        self.ui.cameraview.clear()
        self.ui.cameraview.setStyleSheet("background-color: rgb(0, 0, 0);\n"
                                "border-image: url(:/Whalze/images/福州大学logo(红).jpg);\n")
        
        self.ui.cameraview.update()
        self.ui.cameraButton1.setText("打开摄像头")
        self.ui.cameraButton1.setEnabled(True)
        # self.ui.cameraButton2.setEnabled(False)

    def receive_frame(self, img):
        if not img.isNull():
            self.ui.cameraview.setPixmap(QtGui.QPixmap.fromImage(img.scaled(self.ui.cameraview.size(), QtCore.Qt.KeepAspectRatio)))

    def clear_writing_canvas(self):
        self.writing_canvas.clear_handwriting()
        self.writing_canvas.set_trajectory([])
        self.writing_func.clear_state()
        self.log_terminal("画布清除")

    def show_simulator(self):
        self.simulator_window.show()
        self.simulator_window.update_robot_state(self.current_robot_pos)

    def closeEvent(self, event):
        self.camera_thread.stop()
        self.serial_com.close()
        self.simulator_window.close()
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    Background_rc.qInitResources()
    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec()) #  执行应用程序并退出