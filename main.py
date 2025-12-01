# -*- coding: utf-8 -*-
# main.py (Final Optimized)
import sys
import signal
import numpy as np
from PySide6 import QtWidgets, QtCore, QtGui

# UI与资源
from ui.UI import Ui_Widget
import resources.rc.Background_rc as Background_rc

# 功能模块导入
from camera.camera import Camera
from communication.com import SerialCommunication
from kinematics.kinematics import DeltaKinematics
from kinematics.trajectory import TrajectoryPlanner
from visualization.visualizer import TrajectoryVisualizer
from simulator.simulation import DeltaSimulator 

# 核心逻辑模块
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

        # 1. 硬件与基础组件
        self.camera_thread = None
        self.serial_com = SerialCommunication(self.ui)

        # 2. 算法初始化 (Linear Delta / P副)
        # =================参数配置区域=================
        side_sp = 300.0  # 三角架边长
        side_ep = 100.0  # 动平台边长
        rod_len = 300.0  # 连杆长
        
        sp_radius = side_sp / (3**0.5) # R
        ep_radius = side_ep / (3**0.5) # r
        
        self.kinematics = DeltaKinematics(sp=sp_radius, ep=ep_radius, rod_length=rod_len)
        self.planner = TrajectoryPlanner()
        self.visualizer = TrajectoryVisualizer()
        
        # 3. 初始化 3D 仿真窗口
        self.simulator_window = DeltaSimulator(self.kinematics)
        self.simulator_window.setWindowTitle("Linear Delta 实时数字孪生")
        self.simulator_window.resize(800, 600)
        
        # **核心状态变量**：记录机器人当前的理论位置
        self.current_robot_pos = [0.0, 0.0, -300.0]  # 初始归零位置
        self.simulator_window.update_robot_state(self.current_robot_pos) # 初始同步

        # 4. 功能模块
        self.writing_func = WritingFunctionality(self.ui, self.serial_com, None, self.log_terminal)
        self.vision_func = VisionFunctionality(self.ui, self.serial_com)
        self.calib_handler = CalibrationHandler(self.ui, self.camera_thread, self, self.log_terminal)
        
        self.traj_executor = TrajectoryExecution(
            self.ui, 
            self.serial_com, 
            self.kinematics, 
            self.planner, 
            self.visualizer, 
            logger=self.log_terminal, 
            simulator=self.simulator_window
        )

        # 5. UI初始化与信号连接
        self.init_writing_canvas()
        self.populate_camera_list()
        self.connect_signals()
        
        self.log_terminal("系统就绪：仿真环境已加载 (Linear Delta Mode)")

    def connect_signals(self):
        # ... (摄像头、写字、视觉、标定 保持原有连接不变) ...
        self.ui.cameraButton1.clicked.connect(self.init_camera)
        self.ui.cameraButton2.clicked.connect(self.close_camera)
        self.ui.preview_button.clicked.connect(self.writing_func.preview_writing_trajectory)
        self.ui.start_writing_button.clicked.connect(self.writing_func.start_writing)
        self.ui.stop_writing_button.clicked.connect(self.writing_func.stop_writing)
        self.ui.clear_canvas_button.clicked.connect(self.clear_writing_canvas)
        self.ui.use_handwriting_button.clicked.connect(self.writing_func.use_handwriting_trajectory)
        self.ui.apply_transform_button.clicked.connect(self.calib_handler.apply_hand_eye_transform)
        self.ui.pushButton_4.clicked.connect(self.vision_func.start_visual_sorting)
        self.ui.pushButton_5.clicked.connect(self.vision_func.start_visual_picking)
        self.vision_func.object_detected.connect(self.vision_func.handle_object_detection)
        # self.vision_func.execute_picking_sequence_signal.connect(self.vision_func.execute_picking_sequence)
        # self.camera_thread.object_detected_robot_coords.connect(self.vision_func.handle_object_detection)

        self.ui.camera_selector.currentIndexChanged.connect(self.on_camera_selection_changed)
        # --- 轨迹控制 ---
        self.ui.run_jog_sequence_button.clicked.connect(self.traj_executor.run_jog_sequence)
        self.ui.pushButton_6.clicked.connect(self.traj_executor.run_curve)
        
        # --- 逆解测试联动 ---
        self.ui.solve_ik_button.clicked.connect(self.on_solve_ik)

        # --- 仿真窗口控制 ---
        self.ui.open_simulator_button.clicked.connect(self.show_simulator)
        self.ui.update_simulator_button.clicked.connect(self.manual_update_simulator)

        # =========================================================
        # 高级联动：寸动按钮 (Jog) -> 驱动仿真 + 发送串口
        # =========================================================
        # 步长 (Step)
        step = 10.0 # mm

        # Lambda无法直接处理复杂逻辑，绑定到专用函数
        self.ui.pushButton_8.clicked.connect(lambda: self.handle_inch_move(0, step))   # X+
        self.ui.pushButton_9.clicked.connect(lambda: self.handle_inch_move(0, -step))  # X-
        self.ui.pushButton_10.clicked.connect(lambda: self.handle_inch_move(1, step))  # Y+
        self.ui.pushButton_11.clicked.connect(lambda: self.handle_inch_move(1, -step)) # Y-
        self.ui.pushButton_12.clicked.connect(lambda: self.handle_inch_move(2, step))  # Z+
        self.ui.pushButton_13.clicked.connect(lambda: self.handle_inch_move(2, -step)) # Z-

        # =========================================================
        # 高级联动：电机调试 (Motor Debug) -> 驱动仿真(正解) + 发送串口
        # =========================================================
        # Motor A (Index 0)
        self.ui.pushButton_14.clicked.connect(lambda: self.handle_motor_debug(0, step)) # A+
        self.ui.pushButton_15.clicked.connect(lambda: self.handle_motor_debug(0, -step))# A-
        # Motor B (Index 1)
        self.ui.pushButton_16.clicked.connect(lambda: self.handle_motor_debug(1, step)) # B+
        self.ui.pushButton_17.clicked.connect(lambda: self.handle_motor_debug(1, -step))# B-
        # Motor C (Index 2)
        self.ui.pushButton_18.clicked.connect(lambda: self.handle_motor_debug(2, step)) # C+
        self.ui.pushButton_19.clicked.connect(lambda: self.handle_motor_debug(2, -step))# C-

    # =================== 核心控制逻辑 ===================

    def handle_inch_move(self, axis_idx, delta):
        """处理寸动逻辑：更新内部状态 -> 刷新仿真 -> 发送串口"""
        # 1. 更新预期位置
        new_pos = list(self.current_robot_pos)
        new_pos[axis_idx] += delta
        
        # 2. 检查是否可达 (Safety Check)
        if self.kinematics.inverse_kinematics(new_pos) is None:
            self.log_terminal(f"警告: 目标位置 {new_pos} 不可达，取消移动")
            return

        # 3. 提交更新
        self.current_robot_pos = new_pos
        self.log_terminal(f"寸动: 坐标更新至 ({new_pos[0]:.1f}, {new_pos[1]:.1f}, {new_pos[2]:.1f})")
        
        # 4. 驱动仿真
        if self.ui.simulator_enable_checkbox.isChecked():
            self.simulator_window.update_robot_state(new_pos)

        # 5. 发送串口指令 (映射回 com.py 需要的格式)
        # com.py 定义: axis 1=X, 2=Y, 3=Z; dir 1=+, 0=-
        axis_map = axis_idx + 1
        direction = 1 if delta > 0 else 0
        self.serial_com.send_inch_debug_command(axis_map, direction)

    def handle_motor_debug(self, motor_idx, delta):
        """处理电机调试：获取当前滑块高度 -> 修改 -> 正解更新仿真 -> 发送串口"""
        # 1. 获取当前仿真中的滑块高度 (基准)
        current_sliders = list(self.simulator_window.current_sliders_z)
        
        # 2. 修改指定电机高度
        current_sliders[motor_idx] += delta
        
        # 3. 驱动仿真 (使用 update_by_sliders 方法)
        # 这会自动计算正解，如果正解成功，会更新 self.current_robot_pos
        if self.ui.simulator_enable_checkbox.isChecked():
            success = self.simulator_window.update_by_sliders(current_sliders)
            if success:
                # 如果正解解算成功，反向更新我们的末端坐标记录
                # (因为电机动了，末端位置肯定变了)
                fk_pos = self.kinematics.forward_kinematics(current_sliders)
                if fk_pos is not None:
                    self.current_robot_pos = list(fk_pos)
                    self.log_terminal(f"电机联动: 末端变为 ({fk_pos[0]:.1f}, {fk_pos[1]:.1f}, {fk_pos[2]:.1f})")
            else:
                self.log_terminal("警告: 电机位置导致机构卡死或解算失败")

        # 4. 发送串口指令
        # com.py 定义: 1=A+, 2=A-, 3=B+, 4=B-, 5=C+, 6=C-
        # motor_idx: 0=A, 1=B, 2=C
        # logic: base = motor_idx * 2 + 1 (if +) or + 2 (if -)
        cmd_id = (motor_idx * 2) + (1 if delta > 0 else 2)
        self.serial_com.send_motor_debug_command(cmd_id)

    # =================== 辅助功能 ===================
    def show_simulator(self):
        self.simulator_window.show()
        # 打开时强制同步一次
        self.simulator_window.update_robot_state(self.current_robot_pos)

    def manual_update_simulator(self):
        """UI上手动输入XYZ更新仿真"""
        try:
            x = self.ui.ik_x.value()
            y = self.ui.ik_y.value()
            z = self.ui.ik_z.value()
            self.current_robot_pos = [x, y, z] # 更新记忆
            self.simulator_window.update_robot_state([x, y, z])
        except Exception:
            pass

    def on_solve_ik(self):
        """逆解测试按钮"""
        x = self.ui.ik_x.value()
        y = self.ui.ik_y.value()
        z = self.ui.ik_z.value()
        P = [x, y, z]
        
        sliders = self.kinematics.inverse_kinematics(P)
        if sliders is None:
            self.ui.ik_result_label.setText("不可达")
            return
            
        self.ui.ik_result_label.setText(f"滑块Z: {sliders[0]:.1f}, {sliders[1]:.1f}, {sliders[2]:.1f}")
        
        # 联动仿真
        self.current_robot_pos = P
        if self.ui.simulator_enable_checkbox.isChecked():
            self.simulator_window.update_robot_state(P)

    # ... (其余 log_terminal, init_camera 等方法保持不变) ...
    def log_terminal(self, msg):
        timestamp = QtCore.QDateTime.currentDateTime().toString('HH:mm:ss')
        formatted = f"[{timestamp}] {msg}"
        self.ui.log_terminal(formatted)
        print(formatted)

    def init_writing_canvas(self):
        self.writing_canvas = WritingCanvas(self.ui.writing_group)
        self.writing_canvas.setGeometry(10, 485, 320, 150)
        self.ui.writing_canvas = self.writing_canvas
        self.writing_func.writing_canvas = self.writing_canvas

    def populate_camera_list(self):
        """扫描并填充可用摄像头列表"""
        try:
            self.ui.camera_selector.clear()
            available_cameras = Camera.scan_cameras()
            
            if not available_cameras:
                self.ui.camera_selector.addItem("未检测到摄像头")
                self.ui.camera_selector.setEnabled(False)
                self.ui.cameraButton1.setEnabled(False)
                self.log_terminal("未检测到可用摄像头")
            else:
                for idx, name in available_cameras:
                    display_name = f"{name} (ID: {idx})"
                    self.ui.camera_selector.addItem(display_name, userData=idx)
                
                self.ui.camera_selector.setEnabled(True)
                self.ui.cameraButton1.setEnabled(True)
                
                # 默认选择第一个摄像头
                if available_cameras:
                    self.ui.camera_selector.setCurrentIndex(0)
                    
                camera_list = ", ".join([f"{name}(ID:{idx})" for idx, name in available_cameras])
                self.log_terminal(f"检测到摄像头: {camera_list}")
                
        except Exception as e:
            self.log_terminal(f"扫描摄像头时出错: {e}")

    def init_camera(self):
        """初始化并打开选中的摄像头"""
        try:
            # 获取选中的摄像头编号
            selected_index = self.ui.camera_selector.currentData()
            if selected_index is None:
                self.log_terminal("错误: 未选择有效的摄像头")
                return

            print(f"用户选择的摄像头编号: {selected_index}")

            # 如果摄像头线程已存在，先关闭
            if self.camera_thread and self.camera_thread.isRunning():
                self.close_camera()

            # 创建新的摄像头实例
            self.camera_thread = Camera()

            # 关键步骤：设置摄像头编号
            self.camera_thread.set_cam_number(selected_index)
            print(f"已设置摄像头编号: {selected_index}")

            # 连接信号
            self.camera_thread.sendPicture.connect(self.receive_frame)
            self.camera_thread.object_detected_robot_coords.connect(self.vision_func.handle_object_detection)           
                # 启动摄像头线程
            self.camera_thread.start()
            
            # 更新UI状态
            self.ui.cameraButton1.setEnabled(False)
            self.ui.cameraButton2.setEnabled(True)
            self.ui.cameraButton1.setText("采集中...")
            
            self.log_terminal(f"正在打开摄像头 {selected_index}...")
            
        except Exception as e:
            self.log_terminal(f"打开摄像头时出错: {str(e)}")
            import traceback
            traceback.print_exc()

    def close_camera(self):
        """关闭摄像头"""
        try:
            if self.camera_thread and self.camera_thread.isRunning():
                print("正在关闭摄像头线程...")
                self.camera_thread.stop()
                if not self.camera_thread.wait(2000):  # 等待2秒
                    print("摄像头线程未正常退出，强制终止")
                    self.camera_thread.terminate()
                    self.camera_thread.wait()
                    
            # 更新UI状态
            self.ui.cameraview.clear()
            self.ui.cameraButton1.setEnabled(True)
            self.ui.cameraButton2.setEnabled(False)
            self.ui.cameraButton1.setText("打开摄像头")
            
            self.log_terminal("摄像头已关闭")
            
        except Exception as e:
            self.log_terminal(f"关闭摄像头时出错: {str(e)}")

    def receive_frame(self, img):
        """接收并显示图像帧"""
        if img.isNull():
            return
            
        try:
            # 缩放图像以适应显示区域
            scaled_img = img.scaled(
                self.ui.cameraview.size(), 
                QtCore.Qt.KeepAspectRatio, 
                QtCore.Qt.SmoothTransformation
            )
            self.ui.cameraview.setPixmap(QtGui.QPixmap.fromImage(scaled_img))
        except Exception as e:
            print(f"显示图像时出错: {e}")

    def refresh_camera_list(self):
        """刷新摄像头列表（可以绑定到刷新按钮）"""
        self.populate_camera_list()
        self.log_terminal("摄像头列表已刷新")

    def on_camera_selection_changed(self, index):
        """当摄像头选择改变时的调试信息"""
        selected_index = self.ui.camera_selector.currentData()
        print(f"摄像头选择已改变: 索引={index}, 摄像头ID={selected_index}")

    def clear_writing_canvas(self):
        self.writing_canvas.clear_handwriting()
        self.writing_canvas.set_trajectory([])

    def closeEvent(self, event):
        """程序关闭事件处理"""
        try:
            if self.camera_thread is not None:
                self.close_camera()
                
            if hasattr(self, 'serial_com'):
                self.serial_com.close()
                
            if hasattr(self, 'simulator_window'):
                self.simulator_window.close()
                
        except Exception as e:
            print(f"关闭程序时出错: {e}")
            
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    Background_rc.qInitResources()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())