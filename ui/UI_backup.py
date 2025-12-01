# -*- coding: utf-8 -*-
# UI.py (已更新)

from PySide6 import QtCore, QtWidgets, QtGui

class Ui_Widget(object):
    def setupUi(self, Widget):
        Widget.setObjectName("Widget")
        Widget.resize(1300, 700)  # 增加窗口宽度和高度
        Widget.setWindowTitle("Delta机器人控制器")

        # =================================================================
        # 串口通信区域
        # =================================================================
        self.serial_group = QtWidgets.QGroupBox("串口控制", Widget)
        self.serial_group.setGeometry(QtCore.QRect(10, 10, 321, 281))

        self.label = QtWidgets.QLabel("串口选择", self.serial_group)
        self.label.setGeometry(QtCore.QRect(15, 30, 81, 21))
        self.com = QtWidgets.QComboBox(self.serial_group)
        self.com.setGeometry(QtCore.QRect(90, 30, 140, 22))


        # self.cameraButton1.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")

        self.label_2 = QtWidgets.QLabel("波特率", self.serial_group)
        self.label_2.setGeometry(QtCore.QRect(15, 60, 81, 21))
        self.botrate = QtWidgets.QComboBox(self.serial_group)
        self.botrate.setGeometry(QtCore.QRect(90, 60, 140, 22))
        self.botrate.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.botrate.setCurrentText("115200")

        self.pushButton = QtWidgets.QPushButton("连接", self.serial_group)
        self.pushButton.setGeometry(QtCore.QRect(240, 30, 71, 52))
        self.pushButton.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")


        self.label_8 = QtWidgets.QLabel("串口发送", self.serial_group)
        self.label_8.setGeometry(QtCore.QRect(15, 95, 71, 21))
        self.textBrowser_2 = QtWidgets.QTextBrowser(self.serial_group)
        self.textBrowser_2.setGeometry(QtCore.QRect(15, 125, 291, 41))
        self.textBrowser_2.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")

        self.label_3 = QtWidgets.QLabel("串口接收", self.serial_group)
        self.label_3.setGeometry(QtCore.QRect(15,175, 100, 21))
        self.textBrowser = QtWidgets.QTextBrowser(self.serial_group)
        self.textBrowser.setGeometry(QtCore.QRect(15, 205, 291, 61))
        self.textBrowser.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")


        # =================================================================
        # 摄像头与视觉控制区域
        # =================================================================
        self.vision_group = QtWidgets.QGroupBox("视觉控制", Widget)
        self.vision_group.setGeometry(QtCore.QRect(10, 300, 321, 340))

        self.label_4 = QtWidgets.QLabel("摄像头选择", self.vision_group)
        self.label_4.setGeometry(QtCore.QRect(15, 30, 100, 22))
        self.camera_selector = QtWidgets.QComboBox(self.vision_group)
        self.camera_selector.setGeometry(QtCore.QRect(110, 30, 191, 22))
        self.camera_selector.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")
        

        self.cameraButton1 = QtWidgets.QPushButton("打开摄像头", self.vision_group)
        self.cameraButton1.setGeometry(QtCore.QRect(40, 60, 100, 25))
        self.cameraButton2 = QtWidgets.QPushButton("关闭摄像头", self.vision_group)
        self.cameraButton2.setGeometry(QtCore.QRect(180, 60, 100, 25))
        self.cameraButton2.setEnabled(False)
        self.cameraButton1.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")
        self.cameraButton2.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")


        self.cameraview = QtWidgets.QLabel(self.vision_group)
        self.cameraview.setGeometry(QtCore.QRect(15, 100, 290, 218))
        self.cameraview.setStyleSheet("background-color: rgb(0, 0, 0);\n"
                                      "border-image: url(:/Whalze/images/福州大学logo(红).jpg);\n")
        
        self.cameraview.setAlignment(QtCore.Qt.AlignCenter)
        
        # =================================================================
        # 手眼标定区域
        # =================================================================
        self.calibration_group = QtWidgets.QGroupBox("手眼标定 (相机 -> 动平台)", Widget)
        self.calibration_group.setGeometry(QtCore.QRect(340, 10, 281, 281))

        
        self.label_trans_x = QtWidgets.QLabel("平移 X (mm)", self.calibration_group)
        self.label_trans_x.setGeometry(QtCore.QRect(20, 30, 100, 20))
        self.trans_x = QtWidgets.QDoubleSpinBox(self.calibration_group)
        self.trans_x.setGeometry(QtCore.QRect(130, 30, 120, 22))
        self.trans_x.setRange(-2000, 2000)

        self.label_trans_y = QtWidgets.QLabel("平移 Y (mm)", self.calibration_group)
        self.label_trans_y.setGeometry(QtCore.QRect(20, 60, 100, 20))
        self.trans_y = QtWidgets.QDoubleSpinBox(self.calibration_group)
        self.trans_y.setGeometry(QtCore.QRect(130, 60, 120, 22))
        self.trans_y.setRange(-2000, 2000)

        self.label_trans_z = QtWidgets.QLabel("平移 Z (mm)", self.calibration_group)
        self.label_trans_z.setGeometry(QtCore.QRect(20, 90, 100, 20))
        self.trans_z = QtWidgets.QDoubleSpinBox(self.calibration_group)
        self.trans_z.setGeometry(QtCore.QRect(130, 90, 120, 22))
        self.trans_z.setRange(-2000, 2000)

        self.label_trans_r = QtWidgets.QLabel("旋转 Roll (deg)", self.calibration_group)
        self.label_trans_r.setGeometry(QtCore.QRect(20, 130, 110, 20))
        self.trans_r = QtWidgets.QDoubleSpinBox(self.calibration_group)
        self.trans_r.setGeometry(QtCore.QRect(130, 130, 120, 22))
        self.trans_r.setRange(-180, 180)

        self.label_trans_p = QtWidgets.QLabel("旋转 Pitch (deg)", self.calibration_group)
        self.label_trans_p.setGeometry(QtCore.QRect(20, 160, 110, 20))
        self.trans_p = QtWidgets.QDoubleSpinBox(self.calibration_group)
        self.trans_p.setGeometry(QtCore.QRect(130, 160, 120, 22))
        self.trans_p.setRange(-180, 180)

        self.label_trans_y_2 = QtWidgets.QLabel("旋转 Yaw (deg)", self.calibration_group)
        self.label_trans_y_2.setGeometry(QtCore.QRect(20, 190, 110, 20))
        self.trans_y_2 = QtWidgets.QDoubleSpinBox(self.calibration_group)
        self.trans_y_2.setGeometry(QtCore.QRect(130, 190, 120, 22))
        self.trans_y_2.setRange(-180, 180)

        self.apply_transform_button = QtWidgets.QPushButton("应用变换矩阵", self.calibration_group)
        self.apply_transform_button.setGeometry(QtCore.QRect(40, 230, 200, 30))
        self.apply_transform_button.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")

        
        self.calibrationStatus = QtWidgets.QLabel("状态: 等待检测...", Widget)
        self.calibrationStatus.setGeometry(QtCore.QRect(630, 260, 311, 30))
        self.calibrationStatus.setStyleSheet("font-size: 12px; border: 1px solid gray; padding: 2px;")
        self.calibrationStatus.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")

        
        # =================================================================
        # 机器人控制区域
        # =================================================================
        self.robot_control_group = QtWidgets.QGroupBox("机器人控制", Widget)
        self.robot_control_group.setGeometry(QtCore.QRect(340, 300, 601, 340))

        # --- 紧急控制 ---
        self.pushButton_3 = QtWidgets.QPushButton("复位", self.robot_control_group)
        self.pushButton_3.setGeometry(QtCore.QRect(450, 20, 61, 41))
        self.pushButton_3.setStyleSheet("background-color: hsla(123, 75.50%, 68.00%, 0.25); border-radius: 3px; border: 3px solid hsla(123, 75.50%, 68.00%, 0.25) ;")

        self.pushButton_2 = QtWidgets.QPushButton("急停", self.robot_control_group)
        self.pushButton_2.setGeometry(QtCore.QRect(520, 20, 61, 41))
        self.pushButton_2.setStyleSheet("background-color: hsla(14, 83.40%, 59.80%, 0.25); border-radius: 3px; border: 3px solid hsla(14, 83.40%, 59.80%, 0.25) ;")


        # =================================================================
        # 修改：写字功能区域 - 扩大并重新布局
        # =================================================================
        self.writing_group = QtWidgets.QGroupBox("写字功能", Widget)
        self.writing_group.setGeometry(QtCore.QRect(950, 10, 340, 680))  # 增加宽度和高度

        # 终端输出区域 - 扩大
        self.terminal_label = QtWidgets.QLabel("终端输出:", self.writing_group)
        self.terminal_label.setGeometry(QtCore.QRect(10, 25, 80, 20))
        
        self.terminal_output = QtWidgets.QTextBrowser(self.writing_group)
        self.terminal_output.setGeometry(QtCore.QRect(10, 50, 320, 180))  # 增加宽度和高度
        self.terminal_output.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)")

        # 写字控制区域 - 重新布局，增加间距
        self.writing_control_label = QtWidgets.QLabel("写字控制:", self.writing_group)
        self.writing_control_label.setGeometry(QtCore.QRect(10, 240, 80, 20))

        # 第一行：输入方式和文本输入
        self.input_method_label = QtWidgets.QLabel("输入方式:", self.writing_group)
        self.input_method_label.setGeometry(QtCore.QRect(10, 270, 60, 20))
        self.input_method = QtWidgets.QComboBox(self.writing_group)
        self.input_method.setGeometry(QtCore.QRect(80, 270, 100, 25))
        self.input_method.addItems(["文本输入", "手写输入"])
        self.input_method.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)")

        self.text_input_label = QtWidgets.QLabel("输入文字:", self.writing_group)
        self.text_input_label.setGeometry(QtCore.QRect(190, 270, 60, 20))
        self.text_input = QtWidgets.QLineEdit(self.writing_group)
        self.text_input.setGeometry(QtCore.QRect(260, 270, 70, 25))  # 增加宽度
        self.text_input.setText("FZU")
        self.text_input.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)")

        # 第二行：字体大小和写字区域
        self.font_size_label = QtWidgets.QLabel("字体大小:", self.writing_group)
        self.font_size_label.setGeometry(QtCore.QRect(10, 305, 60, 20))
        self.font_size = QtWidgets.QSpinBox(self.writing_group)
        self.font_size.setGeometry(QtCore.QRect(80, 305, 70, 25))  # 增加宽度
        self.font_size.setRange(10, 100)
        self.font_size.setValue(30)

        self.writing_area_label = QtWidgets.QLabel("区域(mm):", self.writing_group)
        self.writing_area_label.setGeometry(QtCore.QRect(160, 305, 60, 20))
        self.writing_area = QtWidgets.QSpinBox(self.writing_group)
        self.writing_area.setGeometry(QtCore.QRect(230, 305, 70, 25))  # 增加宽度
        self.writing_area.setRange(50, 300)
        self.writing_area.setValue(150)

        # 第三行：Z轴高度和写字速度
        self.z_height_label = QtWidgets.QLabel("写字高度Z:", self.writing_group)
        self.z_height_label.setGeometry(QtCore.QRect(10, 340, 70, 20))
        self.z_height = QtWidgets.QDoubleSpinBox(self.writing_group)
        self.z_height.setGeometry(QtCore.QRect(80, 340, 70, 25))  # 增加宽度
        self.z_height.setRange(-400, -100)
        self.z_height.setValue(-280)
        self.z_height.setSingleStep(5)

        self.writing_speed_label = QtWidgets.QLabel("写字速度:", self.writing_group)
        self.writing_speed_label.setGeometry(QtCore.QRect(160, 340, 60, 20))
        self.writing_speed = QtWidgets.QSpinBox(self.writing_group)
        self.writing_speed.setGeometry(QtCore.QRect(230, 340, 70, 25))  # 增加宽度
        self.writing_speed.setRange(1, 10)
        self.writing_speed.setValue(5)

        # 第四行：按钮控制 - 增加横向间距
        self.use_handwriting_button = QtWidgets.QPushButton("使用手写", self.writing_group)
        self.use_handwriting_button.setGeometry(QtCore.QRect(10, 380, 75, 30))
        self.use_handwriting_button.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)")

        self.preview_button = QtWidgets.QPushButton("预览轨迹", self.writing_group)
        self.preview_button.setGeometry(QtCore.QRect(95, 380, 75, 30))  # 增加间距
        self.preview_button.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)")

        self.start_writing_button = QtWidgets.QPushButton("开始写字", self.writing_group)
        self.start_writing_button.setGeometry(QtCore.QRect(180, 380, 75, 30))  # 增加间距
        self.start_writing_button.setStyleSheet("background-color: hsla(123, 75.50%, 68.00%, 0.25); border-radius: 5px; border: 1px solid hsla(123, 75.50%, 68.00%, 0.94)")

        self.stop_writing_button = QtWidgets.QPushButton("停止写字", self.writing_group)
        self.stop_writing_button.setGeometry(QtCore.QRect(265, 380, 75, 30))  # 增加间距
        self.stop_writing_button.setStyleSheet("background-color: hsla(14, 83.40%, 59.80%, 0.25); border-radius: 5px; border: 1px solid hsla(14, 83.40%, 59.80%, 0.94)")

        # 清空画布按钮
        self.clear_canvas_button = QtWidgets.QPushButton("清空画布", self.writing_group)
        self.clear_canvas_button.setGeometry(QtCore.QRect(10, 420, 320, 30))  # 增加宽度
        self.clear_canvas_button.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)")

        # 写字画布区域 - 扩大
        self.writing_canvas_label = QtWidgets.QLabel("写字轨迹预览 (可手写):", self.writing_group)
        self.writing_canvas_label.setGeometry(QtCore.QRect(10, 460, 200, 20))

        # 状态显示
        self.writing_status = QtWidgets.QLabel("状态: 就绪", self.writing_group)
        self.writing_status.setGeometry(QtCore.QRect(10, 650, 320, 20))
        self.writing_status.setStyleSheet("font-size: 12px; border: 1px solid gray; padding: 2px;")


        # --- 速度控制 ---
        self.label_21 = QtWidgets.QLabel("速度", self.robot_control_group)
        self.label_21.setGeometry(QtCore.QRect(292, 75, 41, 21))
        self.v = QtWidgets.QSlider(self.robot_control_group)
        self.v.setGeometry(QtCore.QRect(298, 110, 22, 121))
        self.v.setStyleSheet("selection-background-color: hsla(213, 88.40%, 62.90%, 0.94);") 
        self.v.setValue(50)

        # --- 状态显示 ---
        self.status_group = QtWidgets.QGroupBox("机器人状态", Widget)
        self.status_group.setGeometry(QtCore.QRect(630, 10, 311, 241))
        self.label_9 = QtWidgets.QLabel("滑台位置", self.status_group); self.label_9.setGeometry(QtCore.QRect(20, 30, 121, 21))
        self.label_10 = QtWidgets.QLabel("X", self.status_group); self.label_10.setGeometry(QtCore.QRect(30, 60, 21, 21))
        self.textBrowser_3 = QtWidgets.QTextBrowser(self.status_group); self.textBrowser_3.setGeometry(QtCore.QRect(50, 55, 61, 31))
        self.textBrowser_3.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")

        self.label_12 = QtWidgets.QLabel("Y", self.status_group); self.label_12.setGeometry(QtCore.QRect(120, 60, 21, 21))
        self.textBrowser_4 = QtWidgets.QTextBrowser(self.status_group); self.textBrowser_4.setGeometry(QtCore.QRect(140, 55, 61, 31))
        self.textBrowser_4.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")

        self.label_11 = QtWidgets.QLabel("Z", self.status_group); self.label_11.setGeometry(QtCore.QRect(210, 60, 21, 21))
        self.textBrowser_5 = QtWidgets.QTextBrowser(self.status_group); self.textBrowser_5.setGeometry(QtCore.QRect(230, 55, 61, 31))
        self.textBrowser_5.setStyleSheet("background-color: hsla(0, 00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")

        self.label_13 = QtWidgets.QLabel("动平台位置", self.status_group); self.label_13.setGeometry(QtCore.QRect(20, 110, 121, 21))
        self.label_14 = QtWidgets.QLabel("X", self.status_group); self.label_14.setGeometry(QtCore.QRect(30, 140, 21, 21))
        self.textBrowser_6 = QtWidgets.QTextBrowser(self.status_group); self.textBrowser_6.setGeometry(QtCore.QRect(50, 135, 61, 31))
        self.textBrowser_6.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")

        self.label_16 = QtWidgets.QLabel("Y", self.status_group); self.label_16.setGeometry(QtCore.QRect(120, 140, 21, 21))
        self.textBrowser_7 = QtWidgets.QTextBrowser(self.status_group); self.textBrowser_7.setGeometry(QtCore.QRect(140, 135, 61, 31))
        self.textBrowser_7.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")

        self.label_15 = QtWidgets.QLabel("Z", self.status_group); self.label_15.setGeometry(QtCore.QRect(210, 140, 21, 21))
        self.textBrowser_8 = QtWidgets.QTextBrowser(self.status_group); self.textBrowser_8.setGeometry(QtCore.QRect(230, 135, 61, 31))
        self.textBrowser_8.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")

        # --- 视觉与曲线功能 ---
        self.pushButton_4 = QtWidgets.QPushButton("视觉分类", self.robot_control_group)
        self.pushButton_4.setGeometry(QtCore.QRect(350, 80, 100, 31))
        self.pushButton_4.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")


        self.pushButton_5 = QtWidgets.QPushButton("视觉拾取", self.robot_control_group)
        self.pushButton_5.setGeometry(QtCore.QRect(480, 80, 100, 31))
        self.pushButton_5.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")



        self.comboBox = QtWidgets.QComboBox(self.robot_control_group)
        self.comboBox.setGeometry(QtCore.QRect(350, 130, 100, 31))
        self.comboBox.addItems(["门型曲线", "花朵", "Lame曲线"])

        self.pushButton_6 = QtWidgets.QPushButton("运行曲线", self.robot_control_group)
        self.pushButton_6.setGeometry(QtCore.QRect(480, 130, 100, 31))
        self.pushButton_6.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")



        # --- 寸动 ----
        self.inch_group = QtWidgets.QGroupBox("寸动", self.robot_control_group)
        self.inch_group.setGeometry(QtCore.QRect(10, 35, 271, 171))

        self.pushButton_8 = QtWidgets.QPushButton("X+", self.inch_group); self.pushButton_8.setGeometry(QtCore.QRect(10, 42, 31, 31))
        self.pushButton_9 = QtWidgets.QPushButton("X-", self.inch_group); self.pushButton_9.setGeometry(QtCore.QRect(50, 41, 31, 31))
        self.pushButton_10 = QtWidgets.QPushButton("Y+", self.inch_group); self.pushButton_10.setGeometry(QtCore.QRect(90, 41, 31, 31))
        self.pushButton_11 = QtWidgets.QPushButton("Y-", self.inch_group); self.pushButton_11.setGeometry(QtCore.QRect(130, 41, 31, 31))
        self.pushButton_12 = QtWidgets.QPushButton("Z+", self.inch_group); self.pushButton_12.setGeometry(QtCore.QRect(170, 41, 31, 31))
        self.pushButton_13 = QtWidgets.QPushButton("Z-", self.inch_group); self.pushButton_13.setGeometry(QtCore.QRect(210, 41, 31, 31))

        self.pushButton_8.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")
        self.pushButton_9.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")
        self.pushButton_10.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")
        self.pushButton_11.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")
        self.pushButton_12.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")
        self.pushButton_13.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")


        # --- 新增：点动序列控制 ---
        self.jog_sequence_group = QtWidgets.QGroupBox("点动", self.robot_control_group)
        self.jog_sequence_group.setGeometry(QtCore.QRect(10, 120, 271, 210))
        
        self.start_point_label = QtWidgets.QLabel("初始坐标", self.jog_sequence_group)
        self.start_point_label.setGeometry(QtCore.QRect(10, 30, 100, 20))
        self.start_x_spinbox = QtWidgets.QDoubleSpinBox(self.jog_sequence_group); self.start_x_spinbox.setGeometry(QtCore.QRect(10, 57, 71, 31)); self.start_x_spinbox.setRange(-150, 150); self.start_x_spinbox.setSuffix(" mm"); self.start_x_spinbox.setToolTip("X坐标范围: -150 ~ 150 mm")
        self.start_y_spinbox = QtWidgets.QDoubleSpinBox(self.jog_sequence_group); self.start_y_spinbox.setGeometry(QtCore.QRect(95, 57, 71, 31)); self.start_y_spinbox.setRange(-150, 150); self.start_y_spinbox.setSuffix(" mm"); self.start_y_spinbox.setToolTip("Y坐标范围: -150 ~ 150 mm")
        self.start_z_spinbox = QtWidgets.QDoubleSpinBox(self.jog_sequence_group); self.start_z_spinbox.setGeometry(QtCore.QRect(180, 57, 71, 31)); self.start_z_spinbox.setRange(-400, -100); self.start_z_spinbox.setSuffix(" mm"); self.start_z_spinbox.setToolTip("Z坐标范围: -400 ~ -100 mm")

        self.end_point_label = QtWidgets.QLabel("终点坐标", self.jog_sequence_group)
        self.end_point_label.setGeometry(QtCore.QRect(10, 97, 100, 20))
        self.end_x_spinbox = QtWidgets.QDoubleSpinBox(self.jog_sequence_group); self.end_x_spinbox.setGeometry(QtCore.QRect(10, 127, 71, 31)); self.end_x_spinbox.setRange(-150, 150); self.end_x_spinbox.setSuffix(" mm"); self.end_x_spinbox.setToolTip("X坐标范围: -150 ~ 150 mm")
        self.end_y_spinbox = QtWidgets.QDoubleSpinBox(self.jog_sequence_group); self.end_y_spinbox.setGeometry(QtCore.QRect(95, 127, 71, 31)); self.end_y_spinbox.setRange(-150, 150); self.end_y_spinbox.setSuffix(" mm"); self.end_y_spinbox.setToolTip("Y坐标范围: -150 ~ 150 mm")
        self.end_z_spinbox = QtWidgets.QDoubleSpinBox(self.jog_sequence_group); self.end_z_spinbox.setGeometry(QtCore.QRect(180, 127, 71, 31)); self.end_z_spinbox.setRange(-400, -100); self.end_z_spinbox.setSuffix(" mm"); self.end_z_spinbox.setToolTip("Z坐标范围: -400 ~ -100 mm")
        
        self.run_jog_sequence_button = QtWidgets.QPushButton("运行点动序列", self.jog_sequence_group)
        self.run_jog_sequence_button.setGeometry(QtCore.QRect(10, 170, 241, 31))

        # --- 电机调试 ---
        self.motor_debug_group = QtWidgets.QGroupBox("电机调试", self.robot_control_group)
        self.motor_debug_group.setGeometry(QtCore.QRect(340, 180, 261, 71))
        
        self.pushButton_14 = QtWidgets.QPushButton("A+", self.motor_debug_group); self.pushButton_14.setGeometry(QtCore.QRect(10, 30, 31, 31))
        self.pushButton_15 = QtWidgets.QPushButton("A-", self.motor_debug_group); self.pushButton_15.setGeometry(QtCore.QRect(50, 30, 31, 31))
        self.pushButton_16 = QtWidgets.QPushButton("B+", self.motor_debug_group); self.pushButton_16.setGeometry(QtCore.QRect(90, 30, 31, 31))
        self.pushButton_17 = QtWidgets.QPushButton("B-", self.motor_debug_group); self.pushButton_17.setGeometry(QtCore.QRect(130, 30, 31, 31))
        self.pushButton_18 = QtWidgets.QPushButton("C+", self.motor_debug_group); self.pushButton_18.setGeometry(QtCore.QRect(170, 30, 31, 31))
        self.pushButton_19 = QtWidgets.QPushButton("C-", self.motor_debug_group); self.pushButton_19.setGeometry(QtCore.QRect(210, 30, 31, 31))

        self.pushButton_14.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")
        self.pushButton_15.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")
        self.pushButton_16.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")
        self.pushButton_17.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")
        self.pushButton_18.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")
        self.pushButton_19.setStyleSheet("background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94) ")
  # 新增：运动学 / 轨迹解算测试
        self.kinematics_group = QtWidgets.QGroupBox("运动学解算测试", self.robot_control_group)
        self.kinematics_group.setGeometry(QtCore.QRect(340, 260, 261, 130))

        self.label_fk = QtWidgets.QLabel("目标末端 XYZ (mm)", self.kinematics_group)
        self.label_fk.setGeometry(QtCore.QRect(10, 25, 150, 20))

        self.ik_x = QtWidgets.QDoubleSpinBox(self.kinematics_group)
        self.ik_x.setGeometry(QtCore.QRect(10, 50, 71, 25))
        self.ik_x.setRange(-150, 150)
        self.ik_x.setSuffix(" mm")
        self.ik_x.setToolTip("X坐标范围: -150 ~ 150 mm")

        self.ik_y = QtWidgets.QDoubleSpinBox(self.kinematics_group)
        self.ik_y.setGeometry(QtCore.QRect(90, 50, 71, 25))
        self.ik_y.setRange(-150, 150)
        self.ik_y.setSuffix(" mm")
        self.ik_y.setToolTip("Y坐标范围: -150 ~ 150 mm")

        self.ik_z = QtWidgets.QDoubleSpinBox(self.kinematics_group)
        self.ik_z.setGeometry(QtCore.QRect(170, 50, 71, 25))
        self.ik_z.setRange(-400, -100)
        self.ik_z.setSuffix(" mm")
        self.ik_z.setToolTip("Z坐标范围: -400 ~ -100 mm")

        self.solve_ik_button = QtWidgets.QPushButton("逆解 + 正解验证", self.kinematics_group)
        self.solve_ik_button.setGeometry(QtCore.QRect(10, 80, 120, 30))

        self.ik_result_label = QtWidgets.QLabel("角度 / 误差：--", self.kinematics_group)
        self.ik_result_label.setGeometry(QtCore.QRect(10, 110, 230, 20))
        self.ik_result_label.setStyleSheet("font-size: 11px;")

        # --- 新增：3D仿真控制 ---
        self.simulator_group = QtWidgets.QGroupBox("3D仿真", self.robot_control_group)
        self.simulator_group.setGeometry(QtCore.QRect(10, 340, 271, 80))
        
        self.simulator_enable_checkbox = QtWidgets.QCheckBox("启用仿真显示", self.simulator_group)
        self.simulator_enable_checkbox.setGeometry(QtCore.QRect(10, 25, 120, 20))
        self.simulator_enable_checkbox.setChecked(False)
        
        self.open_simulator_button = QtWidgets.QPushButton("打开仿真窗口", self.simulator_group)
        self.open_simulator_button.setGeometry(QtCore.QRect(10, 50, 120, 25))
        self.open_simulator_button.setStyleSheet("background-color: hsla(213, 88.40%, 62.90%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)")
        
        self.update_simulator_button = QtWidgets.QPushButton("更新仿真", self.simulator_group)
        self.update_simulator_button.setGeometry(QtCore.QRect(140, 50, 120, 25))
        self.update_simulator_button.setStyleSheet("background-color: hsla(213, 88.40%, 62.90%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)")

        QtCore.QMetaObject.connectSlotsByName(Widget)

    # ====================== UI交互方法 ======================
    def respond(self, message):
        """向‘串口接收’文本浏览器追加消息。"""
        self.textBrowser.append(message)
        self.textBrowser.moveCursor(QtGui.QTextCursor.End)

    def message(self, message):
        """向‘串口发送’文本浏览器追加消息。"""
        self.textBrowser_2.append(message)
        self.textBrowser_2.moveCursor(QtGui.QTextCursor.End)

    def log_terminal(self, message):
        """向终端输出区域追加消息。"""
        self.terminal_output.append(message)
        self.terminal_output.moveCursor(QtGui.QTextCursor.End)



# #######################################################
# from PySide6 import QtCore, QtWidgets, QtGui

        # self.comboBox.addItems(["门型曲线", "花朵", "Lame曲线"])
        
        # self.input_method.addItems(["文本输入", "手写输入"])
        # self.input_method.setCurrentText("文本输入")

        # self.botrate.addItems(["9600", "19200", "38400", "57600", "115200"])
        # self.botrate.setCurrentText("115200")
# #########################################################