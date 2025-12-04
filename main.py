# main.py 修复版

import sys
import os
import numpy as np
import time
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
from core.trajectory_curves import TrajectoryCurves
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
            lib_path = './lib/libIMCnet.so.1.0.0'
            self.motion_controller = DeltaMotionController(lib_path, self.kinematics)

            # 3. 运动控制卡初始化

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
            # 【修改】先初始化写字画布
            self.init_writing_canvas() 
            
            # 【修改】现在创建 WritingFunctionality，并传入所有依赖
            self.writing_func = WritingFunctionality(
                ui=self.ui,
                motion_controller=self.motion_controller,
                writing_canvas=self.writing_canvas,  # 传入画布实例
                logger=self.log_terminal,
                simulator=self.simulator_window,
                main_window=self 
            )


            self.vision_func = VisionFunctionality(
                ui=self.ui,
                motion_controller=self.motion_controller,
                kinematics=self.kinematics,
                main_window=self
            )           
            # 在此处添加仿真器引用
            self.vision_func.simulator = self.simulator_window
            self.init_trajectory_curves_ui()

            self.calib_handler = CalibrationHandler(self.ui, self.camera_thread, self, self.log_terminal)
            
    
            # 6. UI初始化

            self.populate_camera_list()
            self.init_connection_ui()
            self.init_ui_signals()
            
            # 7. 连接信号
            self.connect_signals()
            
            # 8. 状态更新定时器
            self.status_timer = QTimer()
            self.status_timer.timeout.connect(self.update_status)
            self.status_timer.start(1000)  # 1秒更新一次
            
            # 9. 初始化仿真器
            self.simulator_window.update_robot_state(self.current_robot_pos)
            self.simulator_window.pose_changed.connect(self.handle_simulator_pose_change)
            # 在创建 VisionFunctionality 实例后添加
            # self.vision_func = VisionFunctionality(self.ui, self.motion_controller, self.kinematics)
            # 【新增】传递仿真器引用给视觉功能
            # self.vision_func.simulator = self.simulator_window

            print("系统初始化完成")
            self.log_terminal("系统全功能就绪")
            
        except Exception as e:
            print(f"初始化失败: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "初始化错误", f"系统初始化失败: {str(e)}")
            sys.exit(1)
    
    def init_connection_ui(self):
        """初始化连接区域UI"""
        try:
            # 修改UI标签
            self.ui.label.setText("网卡选择") 
            self.ui.label_2.setVisible(False)  # 隐藏波特率标签
            self.ui.botrate.setVisible(False)  # 隐藏波特率下拉框
            
            # 填充网卡列表
            if self.motion_controller.imc is not None:
                cards = self.motion_controller.find_net_cards()
                self.ui.com.clear()
                if cards:
                    self.ui.com.addItems(cards)
                    print(f"找到网卡: {cards}")
                else:
                    self.ui.com.addItem("未找到网卡")
                    print("未找到网卡")
            else:
                self.ui.com.addItem("控制卡未初始化")
                print("控制卡未初始化")
                
        except Exception as e:
            print(f"初始化连接UI失败: {e}")
            self.ui.com.addItem("初始化失败")
    
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
            self.motion_controller.update_slider.connect(self.update_ui_sliders)
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
            self.ui.pushButton_4.clicked.connect(self.on_start_visual_sorting_clicked)
            self.ui.pushButton_5.clicked.connect(self.on_start_visual_picking_clicked)
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
            self.ui.run_jog_sequence_button.clicked.connect(self.run_point_to_point_motion)

            if hasattr(self.ui, 'vision_dynamic_checkbox'):
                self.ui.vision_dynamic_checkbox.stateChanged.connect(self.vision_func.set_dynamic_mode)
                
            print("所有信号连接完成")
                
        except Exception as e:
            print(f"连接信号失败: {e}")
            traceback.print_exc()
    def on_start_visual_sorting_clicked(self):
        """处理'视觉分类'按钮点击：先更新目标，再启动分类"""
        self.update_vision_target()
        # 确保在更新目标后再启动，以防万一
        if self.camera_thread: # 可以加个判断，确保线程存在
            self.vision_func.start_visual_sorting()

    def on_start_visual_picking_clicked(self):
        """处理'视觉拾取'按钮点击：先更新目标，再启动拾取"""
        self.update_vision_target()
        # 确保在更新目标后再启动
        if self.camera_thread:
            self.vision_func.start_visual_picking()
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
    
    def update_ui_coords(self, coords):
        """
        更新UI上动平台的坐标显示
        :param coords: 动平台的坐标列表, 例如 [x, y, z]，单位通常是毫米
        """
        try:
            x_mm = coords[0] 
            y_mm = coords[1] 
            z_mm = coords[2] 

            # 假设 textBrowser_6, 7, 8 都是 QTextBrowser
            self.ui.textBrowser_6.setText(f"{x_mm:.3f}") # 保留3位小数更精确
            self.ui.textBrowser_7.setText(f"{y_mm:.3f}")
            self.ui.textBrowser_8.setText(f"{z_mm:.3f}")

        except Exception as e:
            self.log_terminal(f"更新动平台坐标失败: {e}")

    def handle_simulator_pose_change(self, sliders_z, platform_pos):
            """处理来自仿真器的位姿更新"""
            # 更新滑块UI
            self.update_ui_sliders(sliders_z[0], sliders_z[1], sliders_z[2])
            
            # 更新动平台UI (如果位置有效)
            if platform_pos is not None:
                self.update_ui_coords(platform_pos)
                self.current_robot_pos = list(platform_pos)
            else:
                self.log_terminal("仿真器: 当前滑块位置无法构成闭环")
                # 可以选择清空动平台坐标显示
                # self.update_ui_coords([0,0,0])
    
    def update_ui_sliders(self, x, y, z):
        """更新UI上的滑块位置显示"""
        try:
            # 假设 textBrowser_3, 4, 5 都是 QTextBrowser
            self.ui.textBrowser_3.setText(f"{x:.3f}")
            self.ui.textBrowser_4.setText(f"{y:.3f}")
            self.ui.textBrowser_5.setText(f"{z:.3f}")

        except Exception as e:
            self.log_terminal(f"更新滑块位置失败: {e}")
    
    def handle_inch_move(self, axis_idx, delta):
        """处理 XYZ 坐标系下的寸动"""
        try:
            # 1. 计算新的动平台目标位置
            new_pos = list(self.current_robot_pos)
            new_pos[axis_idx] += delta
            
            # [核心新增] 使用逆运动学计算对应的滑块位置
            new_sliders = self.kinematics.inverse_kinematics(new_pos)
            
            # 检查可达性
            if new_sliders is not None:
                # 2. 更新内部存储的状态
                self.current_robot_pos = new_pos
                # 注意：如果需要，也可以在这里更新 self.simulator_window.current_sliders_z
                # 但下面调用 update_by_sliders 时会自动更新，所以这里不是必须的

                # 3. 更新仿真器 (使用与电机调试一致的 update_by_sliders 方法)
                if self.ui.simulator_enable_checkbox.isChecked():
                    # update_by_sliders 会更新图形并返回正解是否成功
                    # 这里我们传入的是逆解的结果，理论上正解会成功
                    self.simulator_window.update_by_sliders(new_sliders)
                
                # [核心新增] 4. 同步更新UI上的坐标显示
                self.update_ui_coords(new_pos)  # 更新动平台坐标
                self.update_ui_sliders(new_sliders[0], new_sliders[1], new_sliders[2]) # 更新滑块坐标
                
                # 5. 使用运动控制卡移动
                success = self.motion_controller.move_to_xyz(
                    new_pos[0], 
                    new_pos[1], 
                    new_pos[2], 
                    wait=False
                )
                
                if success:
                    axis_name = ['X', 'Y', 'Z'][axis_idx]
                    direction = "正向" if delta > 0 else "负向"
                    self.log_terminal(f"寸动: {axis_name}轴 {direction}移动 {abs(delta):.1f}mm -> 目标位置({new_pos[0]:.1f}, {new_pos[1]:.1f}, {new_pos[2]:.1f})")
                else:
                    self.log_terminal("警告: 控制卡移动失败")
            else:
                self.log_terminal("警告: 目标位置不可达，寸动操作取消")
                    
        except Exception as e:
            self.log_terminal(f"寸动操作失败: {str(e)}")
            traceback.print_exc()
    
    def handle_motor_move(self, motor_idx, pulse_delta):
        """处理单轴电机调试移动 (脉冲为单位)"""
        try:
            success = self.motion_controller.move_axis_relative(motor_idx, pulse_delta)
            # success = True
            if success:
                # 1. 获取当前滑块位置并计算新位置
                current_sliders = list(self.simulator_window.current_sliders_z)
                delta_mm = pulse_delta / 100.0
                current_sliders[motor_idx] += delta_mm

                # 2. 更新仿真器
                if self.ui.simulator_enable_checkbox.isChecked():
                    success_fk = self.simulator_window.update_by_sliders(current_sliders)
                    
                    # [核心新增] 无论正解是否成功，滑块位置都已经更新，需要同步到UI
                    self.update_ui_sliders(current_sliders[0], current_sliders[1], current_sliders[2])

                    if success_fk:
                        # 3. 如果正解成功，获取动平台坐标并更新UI
                        # 正解计算可以直接使用 update_by_sliders 更新后的仿真器状态
                        fk = self.kinematics.forward_kinematics(self.simulator_window.current_sliders_z)
                        if fk is not None:
                            self.current_robot_pos = list(fk)
                            self.update_ui_coords(fk)
                        else:
                            # 这种情况理论上不应该发生，因为 success_fk=True 意味着正解成功
                            self.log_terminal("电机调试: 正解计算失败 (逻辑错误)")
                    else:
                        # 4. 如果正解失败，动平台坐标无效，可以清空或标记
                        self.log_terminal(f"电机调试: 轴{motor_idx+1}移动导致无法构成闭环")
                        # 可以在这里清空动平台坐标显示
                        # self.update_ui_coords([0,0,0]) # 或者显示 "N/A"
                
                # 如果仿真器未启用，我们仍应更新滑块UI以反映指令
                else:
                    self.update_ui_sliders(current_sliders[0], current_sliders[1], current_sliders[2])

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
        """处理平滑复位"""
        try:
            self.log_terminal("开始复位...")
            
            # 禁用复位按钮，防止重复操作
            self.ui.pushButton_3.setEnabled(False)
            self.ui.pushButton_3.setText("复位中...")
            
            # 定义复位目标位置
            reset_pos = [0.0, 0.0, -300.0]

            #  # 在关键点更新状态

            # self._update_reset_status("生成轨迹")
            # trajectory = self._generate_reset_trajectory(self.current_robot_pos, reset_pos)
            
            # self._update_reset_status("执行复位")
            # success = self._execute_smooth_reset(trajectory)

            # 检查复位位置是否可达
            reset_sliders = self.kinematics.inverse_kinematics(reset_pos)
            if reset_sliders is None:
                self.log_terminal("错误：复位位置不可达")
                self._reset_button_state()
                return
            
            # 生成平滑复位轨迹
            trajectory = self._generate_reset_trajectory(self.current_robot_pos, reset_pos)
            
            if not trajectory:
                self.log_terminal("错误：无法生成复位轨迹")
                self._reset_button_state()
                return
            

            # 可视化复位轨迹
            if self.ui.visualization_checkbox.isChecked():
                from threading import Thread
                viz_thread = Thread(
                    target=self.visualizer.plot_realtime_trajectory,
                    args=(np.array(trajectory), "复位轨迹实时可视化"),
                    daemon=True
                )
                viz_thread.start()
            
            # 执行平滑复位
            success = self._execute_smooth_reset(trajectory)
            
            if success:
                self.current_robot_pos = reset_pos
                self.simulator_window.current_sliders_z = reset_sliders
                self.log_terminal("平滑复位完成")
                
                # 清除轨迹显示
                if self.ui.simulator_enable_checkbox.isChecked():
                    self.simulator_window.set_trajectory([])
            else:
                self.log_terminal("复位过程中出现错误")
            
            # 恢复按钮状态
            self._reset_button_state()
            
        except Exception as e:
            self.log_terminal(f"复位失败: {str(e)}")
            traceback.print_exc()
            self._reset_button_state()

    def _generate_reset_trajectory(self, start_pos, end_pos):
        """生成平滑复位轨迹"""
        try:
            # 使用轨迹规划器生成平滑轨迹
            planner = TrajectoryPlanner(
                acc=50,          # 较小的加速度，确保平稳
                max_speed=30,    # 较小的复位速度
                interval=0.05    # 较小的采样间隔，更平滑
            )
            
            # 生成贝塞尔曲线轨迹，实现平滑过渡
            trajectory = planner.bezier_trajectory(
                start_pos[0], start_pos[1], start_pos[2],
                end_pos[0], end_pos[1], end_pos[2],
                show_plot=False
            )
            
            return trajectory
            
        except Exception as e:
            self.log_terminal(f"生成复位轨迹失败: {str(e)}")
            return None

    def _execute_smooth_reset(self, trajectory):
        """执行平滑复位过程"""
        try:
            if not self.motion_controller.is_connected:
                self.log_terminal("警告: 控制卡未连接，仅仿真")
            
            # 设置复位速度参数（较慢）
            self.motion_controller.set_velocity_parameters(
                velocity=20.0,    # 较慢的速度
                acceleration=100.0
            )
            
            # 逐步执行轨迹，实现平滑运动
            for i, point in enumerate(trajectory):
                # 计算滑块位置
                sliders_z = self.kinematics.inverse_kinematics(point)
                if sliders_z is None:
                    self.log_terminal(f"警告: 轨迹点 {i} 不可达")
                    continue
                
                # 更新UI显示
                self.update_ui_coords(point)
                self.update_ui_sliders(sliders_z[0], sliders_z[1], sliders_z[2])
                
                # 更新仿真器
                if self.ui.simulator_enable_checkbox.isChecked():
                    self.simulator_window.update_by_sliders(sliders_z)
                
                # 驱动实际电机
                if self.motion_controller.is_connected:
                    success = self.motion_controller.move_to_xyz(
                        point[0], point[1], point[2], wait=True
                    )
                    if not success:
                        self.log_terminal(f"警告: 轨迹点 {i} 移动失败")
                
                # 实时更新界面
                QApplication.processEvents()
                
                # 根据轨迹点位置调整延迟（开始和结束较慢）
                if i < len(trajectory) * 0.1 or i > len(trajectory) * 0.9:
                    time.sleep(0.05)  # 开始和结束阶段较慢
                else:
                    time.sleep(0.02)  # 中间阶段稍快
            
            return True
            
        except Exception as e:
            self.log_terminal(f"执行复位轨迹失败: {str(e)}")
            return False

    def _reset_button_state(self):
        """恢复复位按钮状态"""
        self.ui.pushButton_3.setEnabled(True)
        self.ui.pushButton_3.setText("复位")

    def execute_trajectory(self, trajectory_points):
        """执行轨迹（增强版）"""

        # if not self.motion_controller.is_connected:
        #     self.log_terminal("错误: 控制卡未连接")
        #     return False
        
        try:
            # 设置速度参数
            self.motion_controller.set_velocity_parameters(
                velocity=30.0,
                acceleration=150.0
            )
            
            # 在仿真器中显示轨迹
            if self.ui.simulator_enable_checkbox.isChecked():
                self.simulator_window.set_trajectory(trajectory_points)
            
            # 执行轨迹
            success = self.motion_controller.execute_trajectory(
                trajectory_points, 
                speed_factor=1.0,
                wait_complete=True
            )
            
            # 实时更新位置
            for point in trajectory_points:
                self.current_robot_pos = list(point)
                self.update_ui_coords(point)
                
                # 更新滑块位置
                sliders_z = self.kinematics.inverse_kinematics(point)
                if sliders_z is not None:
                    self.update_ui_sliders(sliders_z[0], sliders_z[1], sliders_z[2])
                
                # 更新仿真器
                if self.ui.simulator_enable_checkbox.isChecked():
                    self.simulator_window.update_robot_state(point)
                
                # 短暂延迟以显示动画效果
                QApplication.processEvents()
                time.sleep(0.02)
            
            return success
            
        except Exception as e:
            self.log_terminal(f"执行轨迹失败: {str(e)}")
            traceback.print_exc()
            return False
# 在MainWindow类中添加以下方法

    def init_trajectory_curves_ui(self):
        """初始化轨迹曲线UI"""
        try:
            # 创建轨迹曲线下拉框
            if hasattr(self.ui, 'comboBox'):
                self.ui.comboBox.addItems(["门型曲线", "花朵", "Lame曲线", "螺旋线"])
                self.ui.comboBox.setCurrentText("门型曲线")
            
            # 初始化轨迹曲线生成器
            self.trajectory_curves = TrajectoryCurves(self.kinematics)
            
            # 连接信号
            self.trajectory_curves.trajectory_generated.connect(self.on_trajectory_generated)
            self.trajectory_curves.execution_progress.connect(self.on_execution_progress)
            self.trajectory_curves.execution_completed.connect(self.on_execution_completed)
            self.trajectory_curves.log_message.connect(self.log_terminal)
            
            # 连接UI信号
            if hasattr(self.ui, 'pushButton_6'):
                self.ui.pushButton_6.clicked.connect(self.generate_selected_curve)
            
            if hasattr(self.ui, 'pushButton_6'):
                self.ui.pushButton_6.clicked.connect(self.execute_selected_curve)
            
            if hasattr(self.ui, 'pushButton_2'):
                self.ui.pushButton_2.clicked.connect(self.stop_curve_execution)
            
            if hasattr(self.ui, 'visualization_checkbox'):
                self.ui.visualization_checkbox.clicked.connect(self.visualize_selected_curve)
            
            print("轨迹曲线UI初始化完成")
            
        except Exception as e:
            print(f"初始化轨迹曲线UI失败: {e}")

    def generate_selected_curve(self):
        """生成选中的轨迹曲线"""
        try:
            if not hasattr(self.ui, 'comboBox'):
                self.log_terminal("错误: 未找到曲线选择控件")
                return
            
            curve_type = self.ui.comboBox.currentText()
            
            # 获取参数（可以从UI控件获取，这里使用默认值）
            params = self._get_curve_parameters(curve_type)
            
            # 生成轨迹
            trajectory = self.trajectory_curves.generate_curve(curve_type, **params)
            
            if trajectory is not None:
                # 在仿真器中显示轨迹
                if self.ui.simulator_enable_checkbox.isChecked():
                    self.simulator_window.set_trajectory(trajectory)
                
                self.log_terminal(f"成功生成{curve_type}轨迹，共{len(trajectory)}个点")
            
        except Exception as e:
            self.log_terminal(f"生成轨迹失败: {str(e)}")

    def _get_curve_parameters(self, curve_type):
        """获取曲线参数"""
        # 这里可以从UI控件获取参数，为简化使用默认值
        if curve_type == "门型曲线":
            return {
                'width': 200,
                'height': 150,
                'base_z': -300,
                'num_points': 100
            }
        elif curve_type == "花朵":
            return {
                'petals': 6,
                'radius': 100,
                'base_z': -300,
                'height_variation': 50,
                'num_points': 200
            }
        elif curve_type == "Lame曲线":
            return {
                'a': 150,
                'b': 100,
                'n': 4,
                'base_z': -300,
                'num_points': 150
            }
        elif curve_type == "螺旋线":
            return {
                'radius': 100,
                'pitch': 50,
                'turns': 3,
                'base_z': -300,
                'num_points': 200
            }
        else:
            return {}

    def execute_selected_curve(self):
        """执行选中的轨迹曲线"""
        try:
            if not self.trajectory_curves.current_trajectory:
                self.log_terminal("错误: 请先生成轨迹")
                return
            
            # 获取速度因子
            speed_factor = getattr(self.ui, 'v', 1.0)
            if hasattr(speed_factor, 'value'):
                speed_factor = speed_factor.value() / 100.0
            
            # 开始执行轨迹
            success = self.trajectory_curves.start_execution(
                self.motion_controller,
                self.simulator_window,
                self._update_curve_execution_ui,
                speed_factor
            )
            
            if success:
                # 更新UI状态
                if hasattr(self.ui, 'pushButton_6'):
                    self.ui.pushButton_6.setEnabled(False)
                if hasattr(self.ui, 'pushButton_2'):
                    self.ui.pushButton_2.setEnabled(True)
            
        except Exception as e:
            self.log_terminal(f"执行轨迹失败: {str(e)}")

    def stop_curve_execution(self):
        """停止轨迹执行"""
        try:
            self.trajectory_curves.stop_execution()
            
            # 恢复UI状态
            if hasattr(self.ui, 'pushButton_6'):
                self.ui.pushButton_6.setEnabled(True)
            if hasattr(self.ui, 'pushButton_2'):
                self.ui.pushButton_2.setEnabled(False)
            
            self.log_terminal("轨迹执行已停止")
            
        except Exception as e:
            self.log_terminal(f"停止轨迹失败: {str(e)}")

    def visualize_selected_curve(self):
        """可视化选中的轨迹曲线"""
        try:
            if not self.trajectory_curves.current_trajectory:
                self.log_terminal("错误: 请先生成轨迹")
                return
            
            curve_type = getattr(self.ui, 'comboBox', {}).currentText() or "未知曲线"
            self.trajectory_curves.visualize_trajectory(
                self.trajectory_curves.current_trajectory,
                title=f"{curve_type}轨迹可视化"
            )
            
        except Exception as e:
            self.log_terminal(f"可视化失败: {str(e)}")

    def _update_curve_execution_ui(self, end_pos, sliders_z):
        """
        更新轨迹执行时的UI（与寸动功能保持一致）
        """
        try:
            # 更新动平台坐标
            self.update_ui_coords(end_pos)
            
            # 更新滑块位置
            self.update_ui_sliders(sliders_z[0], sliders_z[1], sliders_z[2])
            
            # 更新内部状态
            self.current_robot_pos = list(end_pos)
            
        except Exception as e:
            self.log_terminal(f"更新UI失败: {str(e)}")

    def on_trajectory_generated(self, trajectory):
        """轨迹生成完成回调"""
        self.log_terminal(f"轨迹生成完成，共{len(trajectory)}个点")

    def on_execution_progress(self, current, total):
        """轨迹执行进度回调"""
        progress = (current / total) * 100
        self.log_terminal(f"轨迹执行进度: {current}/{total} ({progress:.1f}%)")
        
        # # 更新进度条（如果有）
        # if hasattr(self.ui, 'curve_progress_bar'):
        #     self.ui.curve_progress_bar.setValue(int(progress))

    def on_execution_completed(self, success):
        """轨迹执行完成回调"""
        if success:
            self.log_terminal("轨迹执行完成")
        else:
            self.log_terminal("轨迹执行失败")
        
        # 恢复UI状态
        if hasattr(self.ui, 'pushButton_6'):
            self.ui.pushButton_6.setEnabled(True)
        if hasattr(self.ui, 'pushButton_2'):
            self.ui.pushButton_2.setEnabled(False)
        
        # # 重置进度条
        # if hasattr(self.ui, 'curve_progress_bar'):
        #     self.ui.curve_progress_bar.setValue(0)





    def circle_trajectory(self):
        """圆形轨迹"""
        try:
            import numpy as np
            
            center = self.current_robot_pos.copy()
            radius = 50.0  # 半径50mm
            points = []
            
            for angle in np.linspace(0, 2*np.pi, 50):
                x = center[0] + radius * np.cos(angle)
                y = center[1] + radius * np.sin(angle)
                z = center[2]
                points.append([x, y, z])
            
            # 闭合圆形
            points.append(points[0])
            
            self.execute_trajectory(points)
            
        except Exception as e:
            self.log_terminal(f"圆形轨迹失败: {str(e)}")
    

    def run_point_to_point_motion(self):
        """执行点到点运动"""
        try:
            # 获取起点和终点坐标
            start_pos = np.array([
                self.ui.start_x_spinbox.value(),
                self.ui.start_y_spinbox.value(),
                self.ui.start_z_spinbox.value()
            ])
            end_pos = np.array([
                self.ui.end_x_spinbox.value(),
                self.ui.end_y_spinbox.value(),
                self.ui.end_z_spinbox.value()
            ])

            # 检查起点和终点是否可达
            start_sliders = self.kinematics.inverse_kinematics(start_pos)
            if start_sliders is None:
                self.log_terminal("错误：起点位置不可达")
                return

            end_sliders = self.kinematics.inverse_kinematics(end_pos)
            if end_sliders is None:
                self.log_terminal("错误：终点位置不可达")
                return

            # 生成轨迹（从当前位置到起点，再到终点）
            if np.allclose(self.current_robot_pos, start_pos):
                # 如果当前位置就是起点，只生成到终点的轨迹
                trajectory = self.planner.linear_trajectory(start_pos, end_pos, num_points=50)
            else:
                # 生成两段轨迹：当前位置->起点，起点->终点
                trajectory1 = self.planner.linear_trajectory(self.current_robot_pos, start_pos, num_points=20)
                trajectory2 = self.planner.linear_trajectory(start_pos, end_pos, num_points=50)
                # 合并轨迹（去除重复点）
                trajectory = np.vstack((trajectory1, trajectory2[1:]))

            # 执行轨迹
            self.execute_trajectory(trajectory)
            
            # # 更新可视化
            # if self.ui.visualization_checkbox.isChecked():
            #     self.visualizer.plot_3d_trajectory(trajectory, title="点动轨迹可视化")
            # 更新可视化
            if self.ui.visualization_checkbox.isChecked():
                # 使用线程避免阻塞主界面
                from threading import Thread
                viz_thread = Thread(
                    target=self.visualizer.plot_realtime_trajectory,
                    args=(trajectory, "点动轨迹实时可视化"),
                    daemon=True
                )
                viz_thread.start()

        except Exception as e:
            self.log_terminal(f"点动运动失败: {str(e)}")
            traceback.print_exc()


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
            # self.ui.writing_canvas = self.writing_canvas
            # self.writing_func.writing_canvas = self.writing_canvas
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