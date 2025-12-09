# main.py 修复版

import sys
import os
import numpy as np
import time
import traceback
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from core.p2p_move_module import P2PMoveModule
from ui.UI import Ui_Widget
import resources.rc.Background_rc as Background_rc
from communication.mqtt_interface import DeltaMqttHandler # 【新增】
from camera.camera import Camera
from kinematics.kinematics import DeltaKinematics
from kinematics.trajectory import TrajectoryPlanner
from visualization.visualizer import TrajectoryVisualizer
from simulator.simulation import DeltaSimulator 
from core.trajectory_curves import TrajectoryCurves
from core.writing import WritingFunctionality
from core.vision import VisionFunctionality
from core.calibration import CalibrationHandler
from ui.writing_canvas import WritingCanvas
from core.motor_debug_module import MotorDebugModule
from core.inch_move_module import InchMoveModule

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            self.ui = Ui_Widget()
            self.ui.setupUi(self)
            

            # 设置应用程序名称
            self.setWindowTitle("Delta 机器人控制系统")
            
            print("开始初始化系统...")
            
            # 【新增】MQTT 模块初始化
            # 请将下面的 IP 修改为你 Windows 下位机的 IP 地址，或者 MQTT Broker 的地址
            # self.mqtt_handler = DeltaMqttHandler(broker_ip="192.168.174.99", port=1883)
            self.mqtt_handler = DeltaMqttHandler(broker_ip="192.168.174.99", port=1883)
            # self.mqtt_handler.set_kinematics(self.kinematics)

            self.mqtt_handler.log_signal.connect(self.log_terminal)
            self.mqtt_handler.connection_state_changed.connect(self.update_connection_status)
            self.mqtt_handler.connect_broker()

            # 尝试自动连接 MQTT (可选)
            # 这里的 IP 应该改为你实际的 Broker IP
            self.mqtt_handler.connect_broker("127.0.0.1", 1883)




            # 1. 基础组件
            self.camera_thread = Camera()
            
            # 2. 运动学算法
            # side_sp, side_ep, rod_len = 300.0, 100.0, 430.0
            # sp_radius = side_sp / (3**0.5)
            # ep_radius = side_ep / (3**0.5)
            rod_len = 430.0
            sp_radius = 260 #静平台半径
            ep_radius = 45 #动平台半径
            self.kinematics = DeltaKinematics(sp=sp_radius, ep=ep_radius, rod_length=rod_len)
            self.planner = TrajectoryPlanner()
            self.visualizer = TrajectoryVisualizer()
            # lib_path = './lib/libIMCnet.so.1.0.0'

            
            
            # 4. 仿真窗口
            self.simulator_window = DeltaSimulator(self.kinematics)
            self.simulator_window.setWindowTitle("Delta 机器人仿真器")
            self.simulator_window.resize(1000, 800)
            self.current_robot_pos = [0.0, 0.0, -410.0]
            self.simulator_window.update_robot_state(self.current_robot_pos)

            # 5. 核心功能
            # 【修改】先初始化写字画布
            self.init_writing_canvas() 
            
            # 【修改】现在创建 WritingFunctionality，并传入所有依赖
            self.writing_func = WritingFunctionality(
                ui=self.ui,
                mqtt_handler=self.mqtt_handler,
                writing_canvas=self.writing_canvas,  # 传入画布实例
                logger=self.log_terminal,
                simulator=self.simulator_window,
                main_window=self 
            )


            self.vision_func = VisionFunctionality(
                ui=self.ui,
                mqtt_handler=self.mqtt_handler,
                kinematics=self.kinematics,
                main_window=self
            )           
            # 在此处添加仿真器引用
            self.vision_func.simulator = self.simulator_window
            self.init_trajectory_curves_ui()

            self.calib_handler = CalibrationHandler(self.ui, self.camera_thread, self, self.log_terminal)
            
            self.init_debug_modules()
            # 在 init_debug_modules() 调用后添加
            self.init_p2p_module()
            self.init_trajectory_module()

            # 然后调用限位设置
            self.setup_limits()  # 初始化限位函数
    
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

            if hasattr(self, 'inch_move_module'):
                    self.inch_move_module.set_micro_step_size(1.0)  # 设置微小点动步长为1mm

            print("系统初始化完成")
            self.log_terminal("系统全功能就绪")
            
        except Exception as e:
            print(f"初始化失败: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "初始化错误", f"系统初始化失败: {str(e)}")
            sys.exit(1)

    # ================== 【新增】统一更新函数 ==================
    def update_ui_and_simulator(self, platform_pos, sliders_pos, update_simulator=True):
        """
        统一更新UI和仿真器
        
        参数:
        platform_pos (list): 动平台坐标 [x, y, z]
        sliders_pos (list): 滑块坐标 [s1, s2, s3]
        update_simulator (bool): 是否更新仿真器
        """
        try:
            # 更新动平台坐标UI
            self.update_ui_coords(platform_pos)
            
            # 更新滑块位置UI
            if sliders_pos is not None:
                self.update_ui_sliders(sliders_pos[0], sliders_pos[1], sliders_pos[2])
            
            # 更新内部状态
            self.current_robot_pos = list(platform_pos)
            
            # 更新寸动模块的当前位置
            if hasattr(self, 'inch_move_module'):
                self.inch_move_module.update_current_position(platform_pos)
            
            # 更新仿真器
            if update_simulator and self.ui.simulator_enable_checkbox.isChecked():
                if self.simulator_window:
                    self.simulator_window.update_robot_state(platform_pos)
            
        except Exception as e:
            self.log_terminal(f"统一更新失败: {str(e)}")

    def update_simulator_by_sliders(self, sliders_pos):
        """
        通过滑块位置更新仿真器
        
        参数:
        sliders_pos (list): 滑块坐标 [s1, s2, s3]
        """
        try:
            if self.ui.simulator_enable_checkbox.isChecked() and self.simulator_window:
                success = self.simulator_window.update_by_sliders(sliders_pos)
                if success:
                    # 获取动平台位置并更新UI
                    platform_pos = self.kinematics.forward_kinematics(sliders_pos)
                    if platform_pos is not None:
                        self.update_ui_coords(platform_pos)
                        self.current_robot_pos = list(platform_pos)
                return success
        except Exception as e:
            self.log_terminal(f"更新仿真器失败: {str(e)}")
        return False
    # ================== 调试模块初始化 ==================
    def init_debug_modules(self):
        """初始化调试模块"""
        try:
            # 初始化电机调试模块
            self.motor_debug_module = MotorDebugModule(
                mqtt_handler=self.mqtt_handler,
                kinematics=self.kinematics,
                simulator_window=self.simulator_window
            )
            
            # 初始化寸动模块
            self.inch_move_module = InchMoveModule(
                mqtt_handler=self.mqtt_handler,
                kinematics=self.kinematics,
                simulator_window=self.simulator_window
            )
            
            # 连接信号
            self.motor_debug_module.log_signal.connect(self.log_terminal)
            self.motor_debug_module.ui_update_signal.connect(self.handle_debug_ui_update)
            self.motor_debug_module.simulator_update_signal.connect(self.handle_motor_simulator_update)
            
            self.inch_move_module.log_signal.connect(self.log_terminal)
            self.inch_move_module.ui_update_signal.connect(self.handle_debug_ui_update)
            self.inch_move_module.simulator_update_signal.connect(self.handle_inch_simulator_update)
            
            print("调试模块初始化完成")
            
        except Exception as e:
            print(f"初始化调试模块失败: {e}")
            traceback.print_exc()

    def setup_limits(self):
        """设置机器人的限位参数"""
        try:
            # 获取仿真器的限位设置
            slider_limits = self.simulator_window.get_slider_limits()
            workspace_limits = self.simulator_window.get_workspace_limits()
            
            # 设置寸动模块限位
            self.inch_move_module.set_workspace_limits(
                x_min=workspace_limits['x_min'], x_max=workspace_limits['x_max'],
                y_min=workspace_limits['y_min'], y_max=workspace_limits['y_max'],
                z_min=workspace_limits['z_min'], z_max=workspace_limits['z_max']
            )
            self.inch_move_module.set_slider_limits(
                min_limit=slider_limits['min'], 
                max_limit=slider_limits['max']
            )
            
            # 设置电机调试模块限位
            self.motor_debug_module.set_workspace_limits(
                x_min=workspace_limits['x_min'], x_max=workspace_limits['x_max'],
                y_min=workspace_limits['y_min'], y_max=workspace_limits['y_max'],
                z_min=workspace_limits['z_min'], z_max=workspace_limits['z_max']
            )
            self.motor_debug_module.set_slider_limits(
                min_limit=slider_limits['min'], 
                max_limit=slider_limits['max']
            )
            
            self.log_terminal(f"机器人限位参数已设置:")
            self.log_terminal(f"  滑块限位: {slider_limits['min']:.1f} ~ {slider_limits['max']:.1f} mm")
            self.log_terminal(f"  工作空间限位: X[{workspace_limits['x_min']:.1f}, {workspace_limits['x_max']:.1f}], "
                            f"Y[{workspace_limits['y_min']:.1f}, {workspace_limits['y_max']:.1f}], "
                            f"Z[{workspace_limits['z_min']:.1f}, {workspace_limits['z_max']:.1f}]")
            
        except Exception as e:
            self.log_terminal(f"设置限位失败: {str(e)}")

    def handle_debug_ui_update(self, platform_pos, sliders_pos):
        """处理调试模块的UI更新"""
        try:
            # 使用统一更新函数
            self.update_ui_and_simulator(platform_pos, sliders_pos, update_simulator=False)
                
        except Exception as e:
            self.log_terminal(f"处理UI更新失败: {str(e)}")

    def handle_motor_simulator_update(self, sliders_pos):
        """处理电机调试的仿真器更新"""
        try:
            self.update_simulator_by_sliders(sliders_pos)
        except Exception as e:
            self.log_terminal(f"处理电机仿真更新失败: {str(e)}")

    def handle_inch_simulator_update(self, platform_pos):
        """处理寸动的仿真器更新"""
        try:
            if self.ui.simulator_enable_checkbox.isChecked() and self.simulator_window:
                self.simulator_window.update_robot_state(platform_pos)
        except Exception as e:
            self.log_terminal(f"处理寸动仿真更新失败: {str(e)}")

    # ================== 机器人控制方法 ==================
    def handle_micro_inch_move(self, axis_idx, delta):
        """处理 XYZ 坐标系下的微小点动"""
        try:
            # 更新寸动模块的当前位置
            self.inch_move_module.update_current_position(self.current_robot_pos)
            
            # 执行微小点动
            success = self.inch_move_module.move_micro_inch(
                axis_idx=axis_idx,
                delta=delta,
                simulator_enabled=self.ui.simulator_enable_checkbox.isChecked(),
                speed=self.ui.v.value() if hasattr(self.ui, 'v') else None
            )
            
            return success
            
        except Exception as e:
            self.log_terminal(f"微小点动操作失败: {str(e)}")
            return False


    
    def handle_motor_move(self, motor_idx, delta_mm):
        """处理单轴电机调试移动 (毫米为单位)"""
        try:
            # 执行电机移动
            success = self.motor_debug_module.move_motor(
                motor_idx=motor_idx,
                delta_mm=delta_mm,  # 改为毫米单位
                simulator_enabled=self.ui.simulator_enable_checkbox.isChecked(),
                use_velocity_control=False  # 使用速度控制模式 #######################################################
            )
            
            return success
            
        except Exception as e:
            self.log_terminal(f"滑块移动操作失败: {str(e)}")
            return False

    def handle_emergency(self):
        """急停"""
        try:
            self.log_terminal("!!! 急停 !!!")
            
            # 通过模块执行急停
            self.motor_debug_module.emergency_stop()
            self.inch_move_module.emergency_stop()
            
            # 原有功能
            self.simulator_window.set_emergency_state(True)
            if hasattr(self, 'sim_timer'): 
                self.sim_timer.stop()
            self.writing_func.writing_timer.stop()
            self.log_terminal("急停已执行")
        except Exception as e:
            self.log_terminal(f"急停失败: {str(e)}")

    # ================== 其他方法 ==================
    def handle_connection_click(self):
        if self.mqtt_handler.is_connected:
            self.mqtt_handler.disconnect_broker()
            self.ui.pushButton.setText("连接")
        else:
            # 获取选择的设备ID
            imcid = int(self.ui.device_selector.currentText())
            self.mqtt_handler.imcid = imcid
            
            # 更新话题
            self.mqtt_handler.TOPIC_STATUS = f"card/{imcid}/status"
            self.mqtt_handler.TOPIC_EMERGENCY_STOP = f"card/{imcid}/emergency_stop"
            # ... 更新其他话题
            
            self.mqtt_handler.connect_broker("192.168.174.99", 1883)
            self.ui.pushButton.setText("断开")
            
    def init_connection_ui(self):
        """初始化连接区域UI"""
        try:
            # 修改UI标签
            self.ui.label.setText("IP选择") 
            self.ui.label_2.setVisible(False)  # 隐藏波特率标签
            self.ui.botrate.setVisible(False)  # 隐藏波特率下拉框

            # 添加多个IP地址选项
            ip_list = [
                "192.168.174.99",  # 下位机IP
                "192.168.174.50",   # 备用IP
                "127.0.0.1",       # 本地测试
                "192.168.0.100"    # 其他网络
            ]
            self.ui.com.addItems(ip_list)

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
            
            
            # 电机调试 (单轴移动)
            # 修改电机调试按钮的连接，将脉冲改为毫米
            step_mm = 30.0  # 10毫米步长
            self.ui.pushButton_14.clicked.connect(lambda: self.handle_motor_move(0, step_mm))
            self.ui.pushButton_15.clicked.connect(lambda: self.handle_motor_move(0, -step_mm))
            self.ui.pushButton_16.clicked.connect(lambda: self.handle_motor_move(1, step_mm))
            self.ui.pushButton_17.clicked.connect(lambda: self.handle_motor_move(1, -step_mm))
            self.ui.pushButton_18.clicked.connect(lambda: self.handle_motor_move(2, step_mm))
            self.ui.pushButton_19.clicked.connect(lambda: self.handle_motor_move(2, -step_mm))

            micro_step = 1.0  # 微小步长1mm
            self.ui.pushButton_8.clicked.connect(lambda: self.handle_micro_inch_move(0, micro_step))
            self.ui.pushButton_9.clicked.connect(lambda: self.handle_micro_inch_move(0, -micro_step))
            self.ui.pushButton_10.clicked.connect(lambda: self.handle_micro_inch_move(1, micro_step))
            self.ui.pushButton_11.clicked.connect(lambda: self.handle_micro_inch_move(1, -micro_step))
            self.ui.pushButton_12.clicked.connect(lambda: self.handle_micro_inch_move(2, micro_step))
            self.ui.pushButton_13.clicked.connect(lambda: self.handle_micro_inch_move(2, -micro_step))

            # 点动运行
            self.ui.run_jog_sequence_button.clicked.connect(self.run_point_to_point_motion)
            
            if hasattr(self, 'p2p_move_module'):
                self.p2p_move_module.trajectory_verified.connect(self.handle_p2p_trajectory_verified)
                self.p2p_move_module.animation_update.connect(self.handle_p2p_animation_update)


            if hasattr(self.ui, 'vision_dynamic_checkbox'):
                self.ui.vision_dynamic_checkbox.stateChanged.connect(self.vision_func.set_dynamic_mode)
                



            # 连接各个模块的日志信号到主窗口的log_terminal方法
            if hasattr(self, 'mqtt_handler'):
                self.mqtt_handler.log_signal.connect(self.log_terminal)
            
            if hasattr(self, 'inch_move_module'):
                self.inch_move_module.log_signal.connect(self.log_terminal)
            
            if hasattr(self, 'motor_debug_module'):
                self.motor_debug_module.log_signal.connect(self.log_terminal)
            
            if hasattr(self, 'p2p_move_module'):
                self.p2p_move_module.log_signal.connect(self.log_terminal)
            
            if hasattr(self, 'trajectory_curves_module'):
                self.trajectory_curves_module.log_signal.connect(self.log_terminal)
            
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

    def update_connection_status(self, connected):
        """更新连接状态"""
        if connected:
            self.ui.pushButton.setText("断开")
            self.ui.pushButton.setStyleSheet("background-color: hsla(123, 75.50%, 68.00%, 0.25); border-radius: 3px; border: 3px solid hsla(123, 75.50%, 68.00%, 0.25);")
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

            # 【新增】MQTT 数据同步
            # 只有当坐标发生实际变化时才发送，或者根据需要发送
            # if hasattr(self, 'mqtt_handler') and self.mqtt_handler.is_connected:
            #     # 获取当前速度设置 (从 UI 滑块)
            #     current_speed = self.ui.v.value() if hasattr(self.ui, 'v') else 50
            #     self.mqtt_handler.send_target_pos(x_mm, y_mm, z_mm, speed=current_speed)

        except Exception as e:
            print(f"更新坐标/MQTT同步失败: {e}")
            # self.log_terminal(f"更新动平台坐标失败: {e}")

    def handle_simulator_pose_change(self, sliders_z, platform_pos):
            """处理来自仿真器的位姿更新"""
            try:
                # 更新滑块UI
                self.update_ui_sliders(sliders_z[0], sliders_z[1], sliders_z[2])
                
                # 更新动平台UI (如果位置有效)
                if platform_pos is not None:
                    self.update_ui_coords(platform_pos)
                    self.current_robot_pos = list(platform_pos)
                    # 同步到寸动模块
                    if hasattr(self, 'inch_move_module'):
                        self.inch_move_module.update_current_position(platform_pos)
                else:
                    self.log_terminal("仿真器: 当前滑块位置无法构成闭环")
                    # 可以选择清空动平台坐标显示
                    # self.update_ui_coords([0,0,0])
            except Exception as e:
                self.log_terminal(f"处理仿真器位姿更新失败: {str(e)}")
    
    def update_ui_sliders(self, x, y, z):
        """更新UI上的滑块位置显示"""
        try:
            # 假设 textBrowser_3, 4, 5 都是 QTextBrowser
            self.ui.textBrowser_3.setText(f"{x:.3f}")
            self.ui.textBrowser_4.setText(f"{y:.3f}")
            self.ui.textBrowser_5.setText(f"{z:.3f}")

        except Exception as e:
            self.log_terminal(f"更新滑块位置失败: {e}")
    
    # ================== 视觉相关方法 ==================
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

    # ================== 复位和轨迹执行方法 ==================
    def handle_reset(self):
        """处理复位和回零功能（合并）"""
        try:
            self.log_terminal("开始复位/回零...")
            
            # 禁用复位按钮，防止重复操作
            self.ui.pushButton_3.setEnabled(False)
            self.ui.pushButton_3.setText("复位中...")
            
            # 定义复位目标位置（工作空间内安全位置）
            reset_pos = [0.0, 0.0, -450.0]  # Z轴提升到-450，确保安全
            
            # 检查复位位置是否可达
            reset_sliders = self.kinematics.inverse_kinematics(reset_pos)
            if reset_sliders is None:
                self.log_terminal("错误：复位位置不可达，尝试调整Z轴高度")
                # 尝试更高位置
                reset_pos = [0.0, 0.0, -400.0]
                reset_sliders = self.kinematics.inverse_kinematics(reset_pos)
                if reset_sliders is None:
                    self.log_terminal("错误：调整后位置仍不可达")
                    self._reset_button_state()
                    return
            
            # 根据连接状态选择复位方式
            if self.mqtt_handler.is_connected:
                # 连接到实体机器人，使用回零话题
                self._execute_homing_sequence()
            else:
                # 未连接，使用仿真平滑复位
                self._execute_simulation_reset(reset_pos, reset_sliders)
            
        except Exception as e:
            self.log_terminal(f"复位/回零失败: {str(e)}")
            traceback.print_exc()
            self._reset_button_state()

    def _execute_homing_sequence(self):
        """执行实体机器人回零序列"""
        try:
            self.log_terminal("开始实体机器人回零...")
            
            # 设置回零参数（根据控制卡要求固定值）
            # 参数说明：
            # dir: 回零方向，0为正方向搜零（向上）
            # rise_edge: 指定检测原点开关的边沿；零：下降沿；非零：上升沿
            # switch_pos: 零点开关位置对应脉冲数（滑块位置）
            # stop_pos: 查找到零点后要移动到的脉冲数（最终位置）
            # high_vel: 回零运动的最高速度
            # low_vel: 回零运动的最低速度
            # stop_vel: 到达最终位置后要保持的速度
            
            # 假设每个滑块的回零参数（需要根据实际硬件调整）
            homing_params = [
                {
                    "dir": 0,           # 正方向搜零（向上）
                    "rise_edge": 0,     # 下降沿
                    "switch_pos": -337, # 零点开关位置（滑块下限）
                    "stop_pos": -300,   # 回零后停止位置（安全位置）
                    "high_vel": 5.0,    # 高速搜索速度
                    "low_vel": 1.0,     # 低速搜索速度
                    "stop_vel": 0.0     # 停止速度
                },
                {
                    "dir": 0,
                    "rise_edge": 0,
                    "switch_pos": -337,
                    "stop_pos": -300,
                    "high_vel": 5.0,
                    "low_vel": 1.0,
                    "stop_vel": 0.0
                },
                {
                    "dir": 0,
                    "rise_edge": 0,
                    "switch_pos": -337,
                    "stop_pos": -300,
                    "high_vel": 5.0,
                    "low_vel": 1.0,
                    "stop_vel": 0.0
                }
            ]
            
            # 逐个轴执行回零
            all_success = True
            for axis_idx in range(3):
                params = homing_params[axis_idx]
                self.log_terminal(f"轴{axis_idx+1}开始回零...")
                
                success = self.mqtt_handler.send_home_command(
                    axis=axis_idx,
                    dir=params["dir"],
                    rise_edge=params["rise_edge"],
                    switch_pos=params["switch_pos"],
                    stop_pos=params["stop_pos"],
                    high_vel=params["high_vel"],
                    low_vel=params["low_vel"],
                    stop_vel=params["stop_vel"]
                )
                
                if success:
                    # 等待回零完成（简单延迟，实际应该监听状态话题）
                    import time
                    time.sleep(2)
                    
                    # 更新仿真器状态（显示回零过程）
                    if self.ui.simulator_enable_checkbox.isChecked():
                        # 模拟回零动画：从当前位置向上移动
                        for i in range(10):
                            pos = [-337 + (i * 3), -337 + (i * 3), -337 + (i * 3)]
                            self.simulator_window.update_by_sliders(pos)
                            QApplication.processEvents()
                            time.sleep(0.1)
                        
                        # 最终位置
                        final_sliders = [-300, -300, -300]
                        self.simulator_window.update_by_sliders(final_sliders)
                        
                        # 计算并显示动平台位置
                        platform_pos = self.kinematics.forward_kinematics(final_sliders)
                        if platform_pos:
                            self.update_ui_and_simulator(platform_pos, final_sliders)
                else:
                    all_success = False
                    self.log_terminal(f"轴{axis_idx+1}回零失败")
            
            if all_success:
                self.log_terminal("所有轴回零完成！机器人已复位到安全位置")
            else:
                self.log_terminal("部分轴回零失败，请检查硬件连接")
            
            self._reset_button_state()
            
        except Exception as e:
            self.log_terminal(f"回零序列执行失败: {str(e)}")
            self._reset_button_state()

    def _execute_simulation_reset(self, reset_pos, reset_sliders):
        """执行仿真器平滑复位"""
        try:
            self.log_terminal("执行仿真平滑复位...")
            
            # 生成直线轨迹（不使用贝塞尔曲线，简化）
            trajectory = []
            steps = 50
            
            # 线性插值
            for i in range(steps + 1):
                ratio = i / steps
                x = self.current_robot_pos[0] + (reset_pos[0] - self.current_robot_pos[0]) * ratio
                y = self.current_robot_pos[1] + (reset_pos[1] - self.current_robot_pos[1]) * ratio
                z = self.current_robot_pos[2] + (reset_pos[2] - self.current_robot_pos[2]) * ratio
                trajectory.append([x, y, z])
            
            # 可视化复位轨迹
            if self.ui.visualization_checkbox.isChecked():
                self.simulator_window.set_trajectory(trajectory)
            
            # 执行轨迹
            for i, point in enumerate(trajectory):
                sliders_z = self.kinematics.inverse_kinematics(point)
                if sliders_z is not None:
                    # 使用统一更新函数
                    self.update_ui_and_simulator(point, sliders_z, update_simulator=True)
                
                # 短暂延迟，模拟运动
                QApplication.processEvents()
                time.sleep(0.02)
            
            # 复位完成，更新到最终位置
            self.update_ui_and_simulator(reset_pos, reset_sliders)
            
            # 清除轨迹显示
            if self.ui.simulator_enable_checkbox.isChecked():
                self.simulator_window.set_trajectory([])
            
            self.log_terminal("仿真复位完成")
            self._reset_button_state()
            
        except Exception as e:
            self.log_terminal(f"仿真复位失败: {str(e)}")
            self._reset_button_state()   

    # def _generate_reset_trajectory(self, start_pos, end_pos):
    #     """生成平滑复位轨迹"""
    #     try:
    #         # 使用轨迹规划器生成平滑轨迹
    #         planner = TrajectoryPlanner(
    #             acc=50,          # 较小的加速度，确保平稳
    #             max_speed=30,    # 较小的复位速度
    #             interval=0.05    # 较小的采样间隔，更平滑
    #         )
            
    #         # 生成贝塞尔曲线轨迹，实现平滑过渡
    #         trajectory = planner.bezier_trajectory(
    #             start_pos[0], start_pos[1], start_pos[2],
    #             end_pos[0], end_pos[1], end_pos[2],
    #             show_plot=False
    #         )
            
    #         return trajectory
            
    #     except Exception as e:
    #         self.log_terminal(f"生成复位轨迹失败: {str(e)}")
    #         return None

    # def _execute_smooth_reset(self, trajectory):
    #     """执行平滑复位过程"""
    #     try:
    #         if not self.mqtt_handler.is_connected:
    #             self.log_terminal("警告: 未连接，")
            
    #         # 逐步执行轨迹，实现平滑运动
    #         for i, point in enumerate(trajectory):
    #             # 计算滑块位置
    #             sliders_z = self.kinematics.inverse_kinematics(point)
    #             if sliders_z is None:
    #                 self.log_terminal(f"警告: 轨迹点 {i} 不可达")
    #                 continue
                
    #             # 使用统一更新函数
    #             self.update_ui_and_simulator(point, sliders_z, update_simulator=True)
                
    #             # 驱动实际电机
    #             if self.mqtt_handler.is_connected:
    #                 success = self.mqtt_handler.move_to_xyz(
    #                     point[0], point[1], point[2], wait=True
    #                 )
    #                 if not success:
    #                     self.log_terminal(f"警告: 轨迹点 {i} 移动失败")
                
    #             # 实时更新界面
    #             QApplication.processEvents()
                
    #             # 根据轨迹点位置调整延迟（开始和结束较慢）
    #             if i < len(trajectory) * 0.1 or i > len(trajectory) * 0.9:
    #                 time.sleep(0.05)  # 开始和结束阶段较慢
    #             else:
    #                 time.sleep(0.02)  # 中间阶段稍快
            
    #         return True
            
    #     except Exception as e:
    #         self.log_terminal(f"执行复位轨迹失败: {str(e)}")
    #         return False

    def _reset_button_state(self):
        """恢复复位按钮状态"""
        self.ui.pushButton_3.setEnabled(True)
        self.ui.pushButton_3.setText("复位")

    def execute_trajectory(self, trajectory_points):
        """执行轨迹（增强版）"""

        if not self.mqtt_handler.is_connected:
            self.log_terminal("错误: 未连接")
            return False
        
        try:
            # 设置速度参数
            self.mqtt_handler.set_velocity_parameters(
                velocity=30.0,
                acceleration=150.0
            )
            
            # 在仿真器中显示轨迹
            if self.ui.simulator_enable_checkbox.isChecked():
                self.simulator_window.set_trajectory(trajectory_points)
            
            # 执行轨迹
            success = self.mqtt_handler.execute_trajectory(
                trajectory_points, 
                speed_factor=1.0,
                wait_complete=True
            )
            
            # 实时更新位置
            for point in trajectory_points:
                sliders_z = self.kinematics.inverse_kinematics(point)
                if sliders_z is not None:
                    # 使用统一更新函数
                    self.update_ui_and_simulator(point, sliders_z, update_simulator=True)
                
                # 短暂延迟以显示动画效果
                QApplication.processEvents()
                time.sleep(0.02)
            
            return success
            
        except Exception as e:
            self.log_terminal(f"执行轨迹失败: {str(e)}")
            traceback.print_exc()
            return False

    # ================== 轨迹曲线相关方法 ==================
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
                'base_z': -500,
                'num_points': 100
            }
        elif curve_type == "花朵":
            return {
                'petals': 6,
                'radius': 100,
                'base_z': -500,
                'height_variation': 50,
                'num_points': 200
            }
        elif curve_type == "Lame曲线":
            return {
                'a': 150,
                'b': 100,
                'n': 4,
                'base_z': -500,
                'num_points': 150
            }
        elif curve_type == "螺旋线":
            return {
                'radius': 100,
                'pitch': 50,
                'turns': 3,
                'base_z': -500,
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
                self.mqtt_handler,
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
            # 使用统一更新函数
            self.update_ui_and_simulator(end_pos, sliders_z, update_simulator=True)
        except Exception as e:
            self.log_terminal(f"更新UI失败: {str(e)}")

    def on_trajectory_generated(self, trajectory):
        """轨迹生成完成回调"""
        self.log_terminal(f"轨迹生成完成，共{len(trajectory)}个点")

    def on_execution_progress(self, current, total):
        """轨迹执行进度回调"""
        progress = (current / total) * 100
        self.log_terminal(f"轨迹执行进度: {current}/{total} ({progress:.1f}%)")

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
    

    def init_p2p_module(self):
        """初始化P2P点动模块"""
        try:
            self.p2p_move_module = P2PMoveModule(
                mqtt_handler=self.mqtt_handler,
                kinematics=self.kinematics,
                simulator_window=self.simulator_window
            )
            
            # 连接信号
            self.p2p_move_module.log_signal.connect(self.log_terminal)
            self.p2p_move_module.ui_update_signal.connect(self.handle_p2p_ui_update)
            self.p2p_move_module.simulator_update_signal.connect(self.handle_p2p_simulator_update)
            self.p2p_move_module.execution_progress.connect(self.handle_p2p_progress)
            self.p2p_move_module.execution_completed.connect(self.handle_p2p_completed)
            
            print("P2P点动模块初始化完成")
            
        except Exception as e:
            print(f"初始化P2P点动模块失败: {e}")
            traceback.print_exc()

    def init_trajectory_module(self):
        """初始化轨迹曲线模块"""
        try:
            # 替换原有的轨迹曲线初始化
            self.trajectory_curves_module = TrajectoryCurves(
                kinematics=self.kinematics,
                mqtt_handler=self.mqtt_handler,
                simulator_window=self.simulator_window
            )
            
            # 连接信号
            self.trajectory_curves_module.log_signal.connect(self.log_terminal)
            self.trajectory_curves_module.ui_update_signal.connect(self.handle_trajectory_ui_update)
            self.trajectory_curves_module.simulator_update_signal.connect(self.handle_trajectory_simulator_update)
            self.trajectory_curves_module.execution_progress.connect(self.handle_trajectory_progress)
            self.trajectory_curves_module.execution_completed.connect(self.handle_trajectory_completed)
            self.trajectory_curves_module.trajectory_generated.connect(self.handle_trajectory_generated)
            
            print("轨迹曲线模块初始化完成")
            
        except Exception as e:
            print(f"初始化轨迹曲线模块失败: {e}")
            traceback.print_exc()

    # 处理P2P模块的UI更新
    def handle_p2p_ui_update(self, platform_pos, sliders_pos):
        """处理P2P模块的UI更新"""
        self.update_ui_and_simulator(platform_pos, sliders_pos, update_simulator=False)

    def handle_p2p_simulator_update(self, platform_pos):
        """处理P2P模块的仿真器更新"""
        if self.ui.simulator_enable_checkbox.isChecked() and self.simulator_window:
            self.simulator_window.update_robot_state(platform_pos)

    def handle_p2p_progress(self, current, total):
        """处理P2P模块的执行进度"""
        progress = (current / total) * 100
        self.log_terminal(f"P2P执行进度: {current}/{total} ({progress:.1f}%)")

    def handle_p2p_completed(self, success):
        """处理P2P模块的执行完成"""
        if success:
            self.log_terminal("P2P运动执行完成")
        else:
            self.log_terminal("P2P运动执行失败")

    # 处理轨迹模块的UI更新
    def handle_trajectory_ui_update(self, platform_pos, sliders_pos):
        """处理轨迹模块的UI更新"""
        self.update_ui_and_simulator(platform_pos, sliders_pos, update_simulator=False)

    def handle_trajectory_simulator_update(self, platform_pos):
        """处理轨迹模块的仿真器更新"""
        if self.ui.simulator_enable_checkbox.isChecked() and self.simulator_window:
            self.simulator_window.update_robot_state(platform_pos)

    def handle_trajectory_progress(self, current, total):
        """处理轨迹模块的执行进度"""
        progress = (current / total) * 100
        self.log_terminal(f"轨迹执行进度: {current}/{total} ({progress:.1f}%)")

    def handle_trajectory_completed(self, success):
        """处理轨迹模块的执行完成"""
        if success:
            self.log_terminal("轨迹执行完成")
        else:
            self.log_terminal("轨迹执行失败")

    def handle_trajectory_generated(self, trajectory):
        """处理轨迹生成完成"""
        self.log_terminal(f"轨迹生成完成，共{len(trajectory)}个点")
        # 在仿真器中显示轨迹
        if self.ui.simulator_enable_checkbox.isChecked():
            self.simulator_window.set_trajectory(trajectory)
    def handle_p2p_trajectory_verified(self, trajectory):
        """
        处理P2P轨迹验证完成信号
        """
        try:
            self.log_terminal(f"P2P轨迹验证完成，共{len(trajectory)}个点")
            
            # 更新仿真器显示轨迹
            if self.ui.simulator_enable_checkbox.isChecked() and self.simulator_window:
                self.simulator_window.set_trajectory(trajectory)
                
                # 显示轨迹信息
                if len(trajectory) >= 2:
                    start = trajectory[0]
                    end = trajectory[-1]
                    self.log_terminal(f"轨迹范围: 起点({start[0]:.1f}, {start[1]:.1f}, {start[2]:.1f}) -> "
                                    f"终点({end[0]:.1f}, {end[1]:.1f}, {end[2]:.1f})")
                    
        except Exception as e:
            self.log_terminal(f"处理轨迹验证信号失败: {str(e)}")

    def handle_p2p_animation_update(self, platform_pos, sliders_pos):
        """
        处理P2P动画更新信号
        """
        try:
            # 使用统一更新函数
            self.update_ui_and_simulator(platform_pos, sliders_pos, update_simulator=True)
        except Exception as e:
            self.log_terminal(f"处理动画更新失败: {str(e)}")

    # 修改 run_point_to_point_motion 方法
    def run_point_to_point_motion(self):
        """执行点到点运动（使用P2P模块）"""
        try:
            # 获取起点和终点坐标
            start_pos = [
                self.ui.start_x_spinbox.value(),
                self.ui.start_y_spinbox.value(),
                self.ui.start_z_spinbox.value()
            ]
            end_pos = [
                self.ui.end_x_spinbox.value(),
                self.ui.end_y_spinbox.value(),
                self.ui.end_z_spinbox.value()
            ]

            # 获取速度参数
            speed = self.ui.v.value() if hasattr(self.ui, 'v') else self.p2p_move_module.default_speed
            
            # 获取插补点数（可以从UI获取，这里使用默认值）
            num_points = 50
            
            # 检查仿真器是否启用
            simulator_enabled = self.ui.simulator_enable_checkbox.isChecked()
            
            # 执行P2P运动（使用带验证和新动画的方法）
            success = self.p2p_move_module.move_p2p_with_validation(
                start_pos=start_pos,
                end_pos=end_pos,
                num_points=num_points,
                speed=speed,
                simulator_enabled=simulator_enabled,
                update_ui=True,
                animate_trajectory=simulator_enabled  # 如果仿真器启用，则进行动画
            )
            
            if success:
                self.log_terminal(f"P2P直线运动指令已发送: 起点{start_pos} -> 终点{end_pos}, 速度={speed:.1f}mm/s")
                if simulator_enabled:
                    self.log_terminal("轨迹动画已开始，将在仿真器中显示平滑运动过程")
            else:
                self.log_terminal("P2P运动失败，请检查轨迹点是否可达")
            
        except Exception as e:
            self.log_terminal(f"P2P运动失败: {str(e)}")
            traceback.print_exc()
    def on_solve_ik(self):
        """求解逆运动学"""
        try:
            P = [self.ui.ik_x.value(), self.ui.ik_y.value(), self.ui.ik_z.value()]
            sliders = self.kinematics.inverse_kinematics(P)
            if sliders is not None: 
                self.ui.ik_result_label.setText(f"Z: {sliders[0]:.1f}, {sliders[1]:.1f}, {sliders[2]:.1f}")
                # 使用统一更新函数
                self.update_ui_and_simulator(P, sliders, update_simulator=True)
            else:
                self.ui.ik_result_label.setText("不可达")
        except Exception as e:
            self.ui.ik_result_label.setText("计算错误")
            self.log_terminal(f"逆运动学求解失败: {str(e)}")
    
    # ================== 基础功能方法 ==================
    def log_terminal(self, msg):
        """记录终端日志"""
        try:
            timestamp = QtCore.QDateTime.currentDateTime().toString('HH:mm:ss')
            log_msg = f"[{timestamp}] {msg}"
            print(log_msg)
            
            # 如果UI中有日志显示控件
            if hasattr(self.ui, 'terminal_output'):
                # 将日志添加到组件中
                self.ui.terminal_output.append(log_msg)
                
                # 可选：自动滚动到底部
                self.ui.terminal_output.verticalScrollBar().setValue(
                    self.ui.terminal_output.verticalScrollBar().maximum()
                )
            elif hasattr(self.ui, 'log_display'):
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
            
            # 断开链接
            if hasattr(self, 'mqtt_handler') and self.mqtt_handler.is_connected:
                self.mqtt_handler.on_disconnect()
            
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