# main.py 修复版

import sys
import os
import traceback
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox

from ui.UI import Ui_Widget
import resources.rc.Background_rc as Background_rc

from camera.camera import Camera
from communication.motion_driver import DeltaMotionController
from kinematics.kinematics import DeltaKinematics
from kinematics.trajectory import TrajectoryPlanner
from visualization.visualizer import TrajectoryVisualizer
from simulator.simulation import DeltaSimulator 

from core.writing import WritingFunctionality
from core.vision import VisionFunctionality
from core.calibration import CalibrationHandler
from ui.writing_canvas import WritingCanvas

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            self.ui = Ui_Widget()
            self.ui.setupUi(self)
            
            # 设置应用程序名称
            self.setWindowTitle("Delta 机器人控制系统")
            
            print("开始初始化系统...")
            
            # 1. 基础组件
            self.camera_thread = Camera()
            
            # 2. 运动学算法
            side_sp, side_ep, rod_len = 300.0, 100.0, 300.0
            sp_radius = side_sp / (3**0.5)
            ep_radius = side_ep / (3**0.5)
            self.kinematics = DeltaKinematics(sp=sp_radius, ep=ep_radius, rod_length=rod_len)
            self.planner = TrajectoryPlanner()
            self.visualizer = TrajectoryVisualizer()
            
            # 3. 运动控制卡初始化
            lib_path = './lib/libIMCnet.so.1.0.0'
            print(f"初始化运动控制卡，库路径: {lib_path}")
            
            # 检查库文件是否存在
            if not os.path.exists(lib_path):
                print(f"警告: 控制卡库文件不存在: {lib_path}")
                print("将使用虚拟控制模式")
            
            self.motion_controller = DeltaMotionController(lib_path, self.kinematics)
            
            # 4. 仿真窗口
            self.simulator_window = DeltaSimulator(self.kinematics)
            self.simulator_window.setWindowTitle("Delta 机器人仿真器")
            self.simulator_window.resize(1000, 800)
            self.current_robot_pos = [0.0, 0.0, -300.0]
            self.simulator_window.update_robot_state(self.current_robot_pos)

            # 5. 核心功能
            self.writing_func = WritingFunctionality(
                self.ui, self.motion_controller, None, self.log_terminal, 
                simulator=self.simulator_window
            )
            
            self.vision_func = VisionFunctionality(self.ui, self.motion_controller)
            self.calib_handler = CalibrationHandler(self.ui, self.camera_thread, self, self.log_terminal)
            
    
            # 6. UI初始化
            self.init_writing_canvas()
            self.populate_camera_list()
            # self.init_connection_ui()
            self.init_ui_signals()
            
            # 7. 连接信号
            self.connect_signals()
            
            # 8. 状态更新定时器
            self.status_timer = QTimer()
            self.status_timer.timeout.connect(self.update_status)
            self.status_timer.start(1000)  # 1秒更新一次
            
            # 9. 初始化仿真器
            self.simulator_window.update_robot_state(self.current_robot_pos)
            
            print("系统初始化完成")
            self.log_terminal("系统全功能就绪")
            
        except Exception as e:
            print(f"初始化失败: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "初始化错误", f"系统初始化失败: {str(e)}")
            sys.exit(1)
    
    # def init_connection_ui(self):
    #     """初始化连接区域UI"""
    #     try:
    #         # 修改UI标签
    #         self.ui.label.setText("网卡选择") 
    #         self.ui.label_2.setVisible(False)  # 隐藏波特率标签
    #         self.ui.botrate.setVisible(False)  # 隐藏波特率下拉框
            
    #         # 填充网卡列表
    #         if self.motion_controller.imc is not None:
    #             cards = self.motion_controller.find_net_cards()
    #             self.ui.com.clear()
    #             if cards:
    #                 self.ui.com.addItems(cards)
    #                 print(f"找到网卡: {cards}")
    #             else:
    #                 self.ui.com.addItem("未找到网卡")
    #                 print("未找到网卡")
    #         else:
    #             self.ui.com.addItem("控制卡未初始化")
    #             print("控制卡未初始化")
                
    #     except Exception as e:
    #         print(f"初始化连接UI失败: {e}")
    #         self.ui.com.addItem("初始化失败")
    
    def init_ui_signals(self):
        """初始化UI信号"""
        if hasattr(self.ui, 'shape_comboBox'):
            self.ui.shape_comboBox.addItems(["正方形", "圆形", "三角形"])
            self.ui.shape_comboBox.setCurrentText("正方形")
        
        if hasattr(self.ui, 'color_comboBox'):
            self.ui.color_comboBox.addItems(["红色", "黄色", "蓝色"])
            self.ui.color_comboBox.setCurrentText("红色")
    
    def update_vision_target(self):
        """将UI的中文选择转换为英文参数并传递给摄像头"""
        if not hasattr(self.ui, 'shape_comboBox') or not hasattr(self.ui, 'color_comboBox'):
            return

        shape_cn = self.ui.shape_comboBox.currentText()
        color_cn = self.ui.color_comboBox.currentText()

        # 映射表
        shape_map = {"正方形": "Square", "圆形": "Circle", "三角形": "Triangle"}
        color_map = {"红色": "Red", "黄色": "Yellow", "蓝色": "Blue"}

        target_shape = shape_map.get(shape_cn, None)
        target_color = color_map.get(color_cn, None)

        if self.camera_thread:
            self.camera_thread.set_target_filter(target_color, target_shape)
            self.log_terminal(f"视觉目标已更新: {color_cn} {shape_cn}")
    
    def connect_signals(self):
        """连接所有信号"""
        try:
            # 连接按钮
            self.ui.pushButton.clicked.connect(self.handle_connection_click)
            self.ui.open_simulator_button.clicked.connect(self.show_simulator)
            # 连接运动控制卡信号
            self.motion_controller.update_serial_status.connect(self.ui.respond)
            self.motion_controller.update_end_effector.connect(self.update_ui_coords)
            self.motion_controller.connection_status_changed.connect(self.update_connection_status)
            
            # 摄像头
            self.ui.cameraButton1.clicked.connect(self.init_camera)
            self.ui.cameraButton2.clicked.connect(self.close_camera)
            
            # 手眼标定
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
            if self.camera_thread:
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
            step_pulse = 1000  # 脉冲数
            self.ui.pushButton_14.clicked.connect(lambda: self.handle_motor_move(0, step_pulse))
            self.ui.pushButton_15.clicked.connect(lambda: self.handle_motor_move(0, -step_pulse))
            self.ui.pushButton_16.clicked.connect(lambda: self.handle_motor_move(1, step_pulse))
            self.ui.pushButton_17.clicked.connect(lambda: self.handle_motor_move(1, -step_pulse))
            self.ui.pushButton_18.clicked.connect(lambda: self.handle_motor_move(2, step_pulse))
            self.ui.pushButton_19.clicked.connect(lambda: self.handle_motor_move(2, -step_pulse))
            
            # 轨迹运行
            
            if hasattr(self.ui, 'vision_dynamic_checkbox'):
                self.ui.vision_dynamic_checkbox.stateChanged.connect(self.vision_func.set_dynamic_mode)
                
            print("所有信号连接完成")
                
        except Exception as e:
            print(f"连接信号失败: {e}")
            traceback.print_exc()
    
    def handle_connection_click(self):
        """处理连接/断开按钮点击"""
        try:
            if self.motion_controller.is_connected:
                # 断开连接
                success = self.motion_controller.disconnect()
                if success:
                    self.ui.pushButton.setText("连接")
                    self.ui.pushButton.setStyleSheet("")
                    self.log_terminal("控制卡已断开")
                else:
                    self.log_terminal("警告: 断开连接失败")
            else:
                # 连接控制卡
                if self.ui.com.currentText() in ["未找到网卡", "控制卡未初始化", "初始化失败"]:
                    self.log_terminal("错误: 没有可用的网卡")
                    return
                
                # 获取选择的网卡索引
                card_index = self.ui.com.currentIndex()
                
                # 尝试连接
                if self.motion_controller.connect_device(card_index):
                    self.ui.pushButton.setText("断开")
                    self.ui.pushButton.setStyleSheet("background-color: green;")
                    self.log_terminal("控制卡连接成功")
                else:
                    self.log_terminal("错误: 连接控制卡失败")
                    
        except Exception as e:
            self.log_terminal(f"连接操作失败: {str(e)}")
            traceback.print_exc()
    
    def update_connection_status(self, connected):
        """更新连接状态"""
        if connected:
            self.ui.pushButton.setText("断开")
            self.ui.pushButton.setStyleSheet("background-color: green;")
        else:
            self.ui.pushButton.setText("连接")
            self.ui.pushButton.setStyleSheet("")
    
    def update_ui_coords(self, x, y, z):
        """更新UI上的坐标显示"""
        try:
            self.ui.textBrowser_6.setText(f"{x:.1f}")
            self.ui.textBrowser_7.setText(f"{y:.1f}")
            self.ui.textBrowser_8.setText(f"{z:.1f}")
        except Exception as e:
            print(f"更新UI坐标失败: {e}")
    
    def handle_inch_move(self, axis_idx, delta):
        """处理 XYZ 坐标系下的点动"""
        try:
            # 计算新位置
            new_pos = list(self.current_robot_pos)
            new_pos[axis_idx] += delta
            
            # 检查可达性
            if self.kinematics.inverse_kinematics(new_pos) is not None:
                self.current_robot_pos = new_pos
                
                # 更新仿真
                if self.ui.simulator_enable_checkbox.isChecked():
                    self.simulator_window.update_robot_state(new_pos)
                
                # 使用运动控制卡移动
                success = self.motion_controller.move_to_xyz(
                    new_pos[0], 
                    new_pos[1], 
                    new_pos[2], 
                    wait=False
                )
                
                if success:
                    self.log_terminal(f"移动: ({new_pos[0]:.1f}, {new_pos[1]:.1f}, {new_pos[2]:.1f})")
                else:
                    self.log_terminal("警告: 控制卡移动失败")
            else:
                self.log_terminal("警告: 目标位置不可达")
                
        except Exception as e:
            self.log_terminal(f"寸动操作失败: {str(e)}")
            traceback.print_exc()
    
    def handle_motor_move(self, motor_idx, pulse_delta):
        """处理单轴电机调试移动 (脉冲为单位)"""
        try:
            # 使用运动控制卡的单轴相对移动
            success = self.motion_controller.move_axis_relative(motor_idx, pulse_delta)
            
            if success:
                # 获取仿真器当前滑块位置
                current_sliders = list(self.simulator_window.current_sliders_z)
                
                # 将脉冲转换为毫米（假设100脉冲=1mm，根据实际情况调整）
                delta_mm = pulse_delta / 100.0
                current_sliders[motor_idx] += delta_mm
                
                # [核心修复] 调用 update_by_sliders 进行仿真更新(包含正解)
                if self.ui.simulator_enable_checkbox.isChecked():
                    success_fk = self.simulator_window.update_by_sliders(current_sliders)
                    if success_fk:
                        # 如果正解成功，更新当前全局坐标
                        fk = self.kinematics.forward_kinematics(current_sliders)
                        if fk is not None:
                            self.current_robot_pos = list(fk)
                            # 更新UI
                            self.update_ui_coords(fk[0], fk[1], fk[2])
                    else:
                        self.log_terminal(f"电机调试: 轴{motor_idx+1}移动导致无法构成闭环")
                
                # 同时从运动控制卡获取实际的滑块位置（如果有）
                current_sliders_from_ctrl = self.motion_controller.get_current_sliders_z()
                if current_sliders_from_ctrl:
                    # 确保仿真器与真实控制卡同步
                    self.simulator_window.current_sliders_z = current_sliders_from_ctrl.copy()
                
                axis_name = ['A', 'B', 'C'][motor_idx]
                direction = "正向" if pulse_delta > 0 else "负向"
                self.log_terminal(f"电机调试: 轴{axis_name} {direction}移动 {abs(pulse_delta)} 脉冲")
            else:
                self.log_terminal("警告: 电机移动失败")
                
        except Exception as e:
            self.log_terminal(f"电机移动操作失败: {str(e)}")
            traceback.print_exc()
    
    def execute_vision_pick_simulation(self):
        """执行视觉抓取仿真"""
        try:
            self.vision_func.execute_picking_sequence()
            # 简单的仿真动画
            if self.ui.simulator_enable_checkbox.isChecked():
                objects = self.vision_func.detected_objects_list
                if not objects: 
                    return
                
                self.sim_animation_step = 0
                self.sim_animation_objects = objects
                self.sim_timer = QTimer()
                self.sim_timer.timeout.connect(self._animate_next_pick_step)
                self.sim_timer.start(1000)
        except Exception as e:
            self.log_terminal(f"视觉抓取仿真失败: {str(e)}")
    
    def _animate_next_pick_step(self):
        """动画下一抓取步骤"""
        try:
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
        except Exception as e:
            self.sim_timer.stop()
            self.log_terminal(f"抓取动画失败: {str(e)}")
    
    def update_sim_vision_object(self, target_info):
        """更新仿真中的视觉物体"""
        try:
            if self.ui.simulator_enable_checkbox.isChecked():
                c = target_info['robot_coords']
                self.simulator_window.add_detected_object(c[0], c[1], c[2], target_info['color'])
        except Exception as e:
            self.log_terminal(f"更新仿真视觉物体失败: {str(e)}")
    
    def handle_reset(self):
        """复位系统"""
        try:
            self.log_terminal("复位系统...")
            self.motion_controller.reset_position()
            self.current_robot_pos = [0.0, 0.0, -300.0]
            self.simulator_window.update_robot_state(self.current_robot_pos)
            self.simulator_window.set_emergency_state(False)
            self.simulator_window.set_trajectory([])
            self.simulator_window.clear_detected_objects()
            self.log_terminal("复位完成")
        except Exception as e:
            self.log_terminal(f"复位失败: {str(e)}")
    
    def handle_emergency(self):
        """急停"""
        try:
            self.log_terminal("!!! 急停 !!!")
            self.motion_controller.emergency_stop()
            self.simulator_window.set_emergency_state(True)
            if hasattr(self, 'sim_timer'): 
                self.sim_timer.stop()
            self.writing_func.writing_timer.stop()
            self.log_terminal("急停已执行")
        except Exception as e:
            self.log_terminal(f"急停失败: {str(e)}")
    
    def on_solve_ik(self):
        """求解逆运动学"""
        try:
            P = [self.ui.ik_x.value(), self.ui.ik_y.value(), self.ui.ik_z.value()]
            sliders = self.kinematics.inverse_kinematics(P)
            if sliders is not None: 
                self.ui.ik_result_label.setText(f"Z: {sliders[0]:.1f}, {sliders[1]:.1f}, {sliders[2]:.1f}")
                if self.ui.simulator_enable_checkbox.isChecked():
                    self.simulator_window.update_robot_state(P)
            else:
                self.ui.ik_result_label.setText("不可达")
        except Exception as e:
            self.ui.ik_result_label.setText("计算错误")
            self.log_terminal(f"逆运动学求解失败: {str(e)}")
    
    def log_terminal(self, msg):
        """记录终端日志"""
        try:
            timestamp = QtCore.QDateTime.currentDateTime().toString('HH:mm:ss')
            log_msg = f"[{timestamp}] {msg}"
            print(log_msg)
            
            # 如果UI中有日志显示控件
            if hasattr(self.ui, 'log_display'):
                self.ui.log_display.append(log_msg)
        except Exception as e:
            print(f"记录日志失败: {e}")
    
    def init_writing_canvas(self):
        """初始化写字画布"""
        try:
            self.writing_canvas = WritingCanvas(self.ui.writing_group)
            self.writing_canvas.setGeometry(10, 485, 320, 150)
            self.ui.writing_canvas = self.writing_canvas
            self.writing_func.writing_canvas = self.writing_canvas
            # 设置默认值
            self.ui.z_height.setValue(-280.0)
            self.ui.writing_area.setValue(200)
            print("写字画布初始化完成")
        except Exception as e:
            print(f"初始化写字画布失败: {e}")
    
    def populate_camera_list(self):
        """填充摄像头列表"""
        try:
            self.ui.camera_selector.clear()
            cams = Camera.scan_cameras()
            if not cams:
                self.ui.camera_selector.addItem("无摄像头")
                self.ui.cameraButton1.setEnabled(False)
                print("未检测到摄像头")
            else:
                for idx, name in cams:
                    self.ui.camera_selector.addItem(f"{name}", userData=idx)
                self.ui.cameraButton1.setEnabled(True)
                print(f"找到 {len(cams)} 个摄像头")
        except Exception as e:
            print(f"填充摄像头列表失败: {e}")
            self.ui.camera_selector.addItem("摄像头错误")
    
    def init_camera(self):
        """初始化摄像头"""
        try:
            idx = self.ui.camera_selector.currentData()
            if idx is None: 
                QMessageBox.warning(self, "摄像头错误", "请选择有效的摄像头")
                return
            
            print(f"尝试打开摄像头 {idx}")
            
            self.camera_thread = Camera()
            self.camera_thread.set_cam_number(idx)
            self.update_vision_target()
            
            # 连接摄像头线程的信号
            self.camera_thread.sendPicture.connect(self.receive_frame)
            self.camera_thread.object_detected_robot_coords.connect(self.vision_func.handle_object_detection)
            
            self.camera_thread.start()
            self.ui.cameraButton1.setText("采集中...")
            self.ui.cameraButton1.setEnabled(False)
            self.ui.cameraButton2.setEnabled(True)
            
            print("摄像头已启动")
            
        except Exception as e:
            print(f"初始化摄像头失败: {e}")
            traceback.print_exc()
            QMessageBox.warning(self, "摄像头错误", f"无法打开摄像头: {str(e)}")
    
    def close_camera(self):
        """关闭摄像头"""
        try:
            if self.camera_thread:
                self.camera_thread.stop()
            
            self.ui.cameraview.clear()
            self.ui.cameraview.setStyleSheet("background-color: rgb(0, 0, 0);\n"
                                    "border-image: url(:/Whalze/images/福州大学logo(红).jpg);\n")
            
            self.ui.cameraview.update()
            self.ui.cameraButton1.setText("打开摄像头")
            self.ui.cameraButton1.setEnabled(True)
            
            print("摄像头已关闭")
            
        except Exception as e:
            print(f"关闭摄像头失败: {e}")
    
    def receive_frame(self, img):
        """接收摄像头帧"""
        try:
            if not img.isNull():
                scaled_img = img.scaled(self.ui.cameraview.size(), QtCore.Qt.KeepAspectRatio)
                self.ui.cameraview.setPixmap(QtGui.QPixmap.fromImage(scaled_img))
        except Exception as e:
            print(f"显示图像失败: {e}")
    
    def clear_writing_canvas(self):
        """清除写字画布"""
        try:
            self.writing_canvas.clear_handwriting()
            self.writing_canvas.set_trajectory([])
            self.writing_func.clear_state()
            self.log_terminal("画布清除")
        except Exception as e:
            self.log_terminal(f"清除画布失败: {str(e)}")
    
    def show_simulator(self):
        """显示仿真器窗口"""
        try:
            self.simulator_window.show()
            self.simulator_window.update_robot_state(self.current_robot_pos)
            self.log_terminal("仿真器已打开")
        except Exception as e:
            self.log_terminal(f"打开仿真器失败: {str(e)}")
    
    def update_status(self):
        """更新系统状态"""
        try:
            # 这里可以添加状态更新逻辑
            pass
        except Exception as e:
            print(f"更新状态失败: {e}")
    
    def closeEvent(self, event):
        """关闭事件处理"""
        try:
            print("正在关闭应用程序...")
            
            # 停止摄像头
            if hasattr(self, 'camera_thread'):
                self.camera_thread.stop()
            
            # 停止状态更新定时器
            if hasattr(self, 'status_timer'):
                self.status_timer.stop()
            
            # 断开控制卡
            if hasattr(self, 'motion_controller') and self.motion_controller.is_connected:
                self.motion_controller.disconnect()
            
            # 关闭仿真窗口
            if hasattr(self, 'simulator_window'):
                self.simulator_window.close()
            
            print("应用程序关闭完成")
            event.accept()
            
        except Exception as e:
            print(f"关闭应用程序时出错: {e}")
            traceback.print_exc()
            event.accept()

if __name__ == "__main__":
    try:
        app = QtWidgets.QApplication(sys.argv)
        Background_rc.qInitResources()
        main_window = MainWindow()
        main_window.show()
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        traceback.print_exc()
        sys.exit(1)