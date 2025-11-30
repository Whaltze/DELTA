# convert_to_ui_complete.py
import xml.etree.ElementTree as ET
from xml.dom import minidom

def python_to_ui():
    """将 Python UI 代码转换为完整的 .ui 文件"""
    
    # 创建 XML 结构
    ui = ET.Element("ui", version="4.0")
    class_element = ET.SubElement(ui, "class")
    class_element.text = "Widget"
    
    widget = ET.SubElement(ui, "widget", {"class": "QWidget", "name": "Widget"})
    
    # 窗口属性
    property_geometry = ET.SubElement(widget, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "0"
    ET.SubElement(rect, "y").text = "0"
    ET.SubElement(rect, "width").text = "1300"
    ET.SubElement(rect, "height").text = "700"
    
    property_windowTitle = ET.SubElement(widget, "property", {"name": "windowTitle"})
    ET.SubElement(property_windowTitle, "string").text = "Delta机器人控制器"
    
    # =================================================================
    # 串口通信区域（之前已包含，这里省略重复代码）
    # =================================================================
    
    # 串口通信区域
    serial_group = ET.SubElement(widget, "widget", {"class": "QGroupBox", "name": "serial_group"})
    property_geometry = ET.SubElement(serial_group, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "10"
    ET.SubElement(rect, "width").text = "321"
    ET.SubElement(rect, "height").text = "281"
    property_title = ET.SubElement(serial_group, "property", {"name": "title"})
    ET.SubElement(property_title, "string").text = "串口控制"
    
    # 串口选择标签
    label = ET.SubElement(serial_group, "widget", {"class": "QLabel", "name": "label"})
    property_geometry = ET.SubElement(label, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "15"
    ET.SubElement(rect, "y").text = "30"
    ET.SubElement(rect, "width").text = "81"
    ET.SubElement(rect, "height").text = "21"
    property_text = ET.SubElement(label, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "串口选择"
    
    # 串口选择下拉框
    com = ET.SubElement(serial_group, "widget", {"class": "QComboBox", "name": "com"})
    property_geometry = ET.SubElement(com, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "90"
    ET.SubElement(rect, "y").text = "30"
    ET.SubElement(rect, "width").text = "140"
    ET.SubElement(rect, "height").text = "22"
    
    # 波特率标签
    label_2 = ET.SubElement(serial_group, "widget", {"class": "QLabel", "name": "label_2"})
    property_geometry = ET.SubElement(label_2, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "15"
    ET.SubElement(rect, "y").text = "60"
    ET.SubElement(rect, "width").text = "81"
    ET.SubElement(rect, "height").text = "21"
    property_text = ET.SubElement(label_2, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "波特率"
    
    # 波特率下拉框
    botrate = ET.SubElement(serial_group, "widget", {"class": "QComboBox", "name": "botrate"})
    property_geometry = ET.SubElement(botrate, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "90"
    ET.SubElement(rect, "y").text = "60"
    ET.SubElement(rect, "width").text = "140"
    ET.SubElement(rect, "height").text = "22"
    
    # 连接按钮
    pushButton = ET.SubElement(serial_group, "widget", {"class": "QPushButton", "name": "pushButton"})
    property_geometry = ET.SubElement(pushButton, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "240"
    ET.SubElement(rect, "y").text = "30"
    ET.SubElement(rect, "width").text = "71"
    ET.SubElement(rect, "height").text = "52"
    property_text = ET.SubElement(pushButton, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "连接"
    property_styleSheet = ET.SubElement(pushButton, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 串口发送标签
    label_8 = ET.SubElement(serial_group, "widget", {"class": "QLabel", "name": "label_8"})
    property_geometry = ET.SubElement(label_8, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "15"
    ET.SubElement(rect, "y").text = "95"
    ET.SubElement(rect, "width").text = "71"
    ET.SubElement(rect, "height").text = "21"
    property_text = ET.SubElement(label_8, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "串口发送"
    
    # 串口发送文本框
    textBrowser_2 = ET.SubElement(serial_group, "widget", {"class": "QTextBrowser", "name": "textBrowser_2"})
    property_geometry = ET.SubElement(textBrowser_2, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "15"
    ET.SubElement(rect, "y").text = "125"
    ET.SubElement(rect, "width").text = "291"
    ET.SubElement(rect, "height").text = "41"
    property_styleSheet = ET.SubElement(textBrowser_2, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 串口接收标签
    label_3 = ET.SubElement(serial_group, "widget", {"class": "QLabel", "name": "label_3"})
    property_geometry = ET.SubElement(label_3, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "15"
    ET.SubElement(rect, "y").text = "175"
    ET.SubElement(rect, "width").text = "100"
    ET.SubElement(rect, "height").text = "21"
    property_text = ET.SubElement(label_3, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "串口接收"
    
    # 串口接收文本框
    textBrowser = ET.SubElement(serial_group, "widget", {"class": "QTextBrowser", "name": "textBrowser"})
    property_geometry = ET.SubElement(textBrowser, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "15"
    ET.SubElement(rect, "y").text = "205"
    ET.SubElement(rect, "width").text = "291"
    ET.SubElement(rect, "height").text = "61"
    property_styleSheet = ET.SubElement(textBrowser, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # =================================================================
    # 摄像头与视觉控制区域（之前已包含，这里省略重复代码）
    # =================================================================
    
    # 视觉控制区域
    vision_group = ET.SubElement(widget, "widget", {"class": "QGroupBox", "name": "vision_group"})
    property_geometry = ET.SubElement(vision_group, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "300"
    ET.SubElement(rect, "width").text = "321"
    ET.SubElement(rect, "height").text = "340"
    property_title = ET.SubElement(vision_group, "property", {"name": "title"})
    ET.SubElement(property_title, "string").text = "视觉控制"
    
    # 摄像头选择标签
    label_4 = ET.SubElement(vision_group, "widget", {"class": "QLabel", "name": "label_4"})
    property_geometry = ET.SubElement(label_4, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "15"
    ET.SubElement(rect, "y").text = "30"
    ET.SubElement(rect, "width").text = "100"
    ET.SubElement(rect, "height").text = "22"
    property_text = ET.SubElement(label_4, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "摄像头选择"
    
    # 摄像头选择下拉框
    camera_selector = ET.SubElement(vision_group, "widget", {"class": "QComboBox", "name": "camera_selector"})
    property_geometry = ET.SubElement(camera_selector, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "110"
    ET.SubElement(rect, "y").text = "30"
    ET.SubElement(rect, "width").text = "191"
    ET.SubElement(rect, "height").text = "22"
    property_styleSheet = ET.SubElement(camera_selector, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 打开摄像头按钮
    cameraButton1 = ET.SubElement(vision_group, "widget", {"class": "QPushButton", "name": "cameraButton1"})
    property_geometry = ET.SubElement(cameraButton1, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "40"
    ET.SubElement(rect, "y").text = "60"
    ET.SubElement(rect, "width").text = "100"
    ET.SubElement(rect, "height").text = "25"
    property_text = ET.SubElement(cameraButton1, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "打开摄像头"
    property_styleSheet = ET.SubElement(cameraButton1, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 关闭摄像头按钮
    cameraButton2 = ET.SubElement(vision_group, "widget", {"class": "QPushButton", "name": "cameraButton2"})
    property_geometry = ET.SubElement(cameraButton2, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "180"
    ET.SubElement(rect, "y").text = "60"
    ET.SubElement(rect, "width").text = "100"
    ET.SubElement(rect, "height").text = "25"
    property_text = ET.SubElement(cameraButton2, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "关闭摄像头"
    property_enabled = ET.SubElement(cameraButton2, "property", {"name": "enabled"})
    ET.SubElement(property_enabled, "bool").text = "false"
    property_styleSheet = ET.SubElement(cameraButton2, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 摄像头视图
    cameraview = ET.SubElement(vision_group, "widget", {"class": "QLabel", "name": "cameraview"})
    property_geometry = ET.SubElement(cameraview, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "15"
    ET.SubElement(rect, "y").text = "100"
    ET.SubElement(rect, "width").text = "290"
    ET.SubElement(rect, "height").text = "218"
    property_styleSheet = ET.SubElement(cameraview, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: rgb(0, 0, 0); border-image: url(:/Whalze/images/福州大学logo(红).jpg);"
    property_alignment = ET.SubElement(cameraview, "property", {"name": "alignment"})
    ET.SubElement(property_alignment, "set").text = "AlignCenter"
    
    # =================================================================
    # 手眼标定区域（之前已包含，这里省略重复代码）
    # =================================================================
    
    # 手眼标定区域
    calibration_group = ET.SubElement(widget, "widget", {"class": "QGroupBox", "name": "calibration_group"})
    property_geometry = ET.SubElement(calibration_group, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "340"
    ET.SubElement(rect, "y").text = "10"
    ET.SubElement(rect, "width").text = "281"
    ET.SubElement(rect, "height").text = "281"
    property_title = ET.SubElement(calibration_group, "property", {"name": "title"})
    ET.SubElement(property_title, "string").text = "手眼标定 (相机 -&gt; 动平台)"
    
    # 平移 X
    label_trans_x = ET.SubElement(calibration_group, "widget", {"class": "QLabel", "name": "label_trans_x"})
    property_geometry = ET.SubElement(label_trans_x, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "20"
    ET.SubElement(rect, "y").text = "30"
    ET.SubElement(rect, "width").text = "100"
    ET.SubElement(rect, "height").text = "20"
    property_text = ET.SubElement(label_trans_x, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "平移 X (mm)"
    
    trans_x = ET.SubElement(calibration_group, "widget", {"class": "QDoubleSpinBox", "name": "trans_x"})
    property_geometry = ET.SubElement(trans_x, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "130"
    ET.SubElement(rect, "y").text = "30"
    ET.SubElement(rect, "width").text = "120"
    ET.SubElement(rect, "height").text = "22"
    property_minimum = ET.SubElement(trans_x, "property", {"name": "minimum"})
    ET.SubElement(property_minimum, "double").text = "-2000.000000000000000"
    property_maximum = ET.SubElement(trans_x, "property", {"name": "maximum"})
    ET.SubElement(property_maximum, "double").text = "2000.000000000000000"
    
    # 平移 Y
    label_trans_y = ET.SubElement(calibration_group, "widget", {"class": "QLabel", "name": "label_trans_y"})
    property_geometry = ET.SubElement(label_trans_y, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "20"
    ET.SubElement(rect, "y").text = "60"
    ET.SubElement(rect, "width").text = "100"
    ET.SubElement(rect, "height").text = "20"
    property_text = ET.SubElement(label_trans_y, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "平移 Y (mm)"
    
    trans_y = ET.SubElement(calibration_group, "widget", {"class": "QDoubleSpinBox", "name": "trans_y"})
    property_geometry = ET.SubElement(trans_y, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "130"
    ET.SubElement(rect, "y").text = "60"
    ET.SubElement(rect, "width").text = "120"
    ET.SubElement(rect, "height").text = "22"
    property_minimum = ET.SubElement(trans_y, "property", {"name": "minimum"})
    ET.SubElement(property_minimum, "double").text = "-2000.000000000000000"
    property_maximum = ET.SubElement(trans_y, "property", {"name": "maximum"})
    ET.SubElement(property_maximum, "double").text = "2000.000000000000000"
    
    # 平移 Z
    label_trans_z = ET.SubElement(calibration_group, "widget", {"class": "QLabel", "name": "label_trans_z"})
    property_geometry = ET.SubElement(label_trans_z, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "20"
    ET.SubElement(rect, "y").text = "90"
    ET.SubElement(rect, "width").text = "100"
    ET.SubElement(rect, "height").text = "20"
    property_text = ET.SubElement(label_trans_z, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "平移 Z (mm)"
    
    trans_z = ET.SubElement(calibration_group, "widget", {"class": "QDoubleSpinBox", "name": "trans_z"})
    property_geometry = ET.SubElement(trans_z, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "130"
    ET.SubElement(rect, "y").text = "90"
    ET.SubElement(rect, "width").text = "120"
    ET.SubElement(rect, "height").text = "22"
    property_minimum = ET.SubElement(trans_z, "property", {"name": "minimum"})
    ET.SubElement(property_minimum, "double").text = "-2000.000000000000000"
    property_maximum = ET.SubElement(trans_z, "property", {"name": "maximum"})
    ET.SubElement(property_maximum, "double").text = "2000.000000000000000"
    
    # 旋转 Roll
    label_trans_r = ET.SubElement(calibration_group, "widget", {"class": "QLabel", "name": "label_trans_r"})
    property_geometry = ET.SubElement(label_trans_r, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "20"
    ET.SubElement(rect, "y").text = "130"
    ET.SubElement(rect, "width").text = "110"
    ET.SubElement(rect, "height").text = "20"
    property_text = ET.SubElement(label_trans_r, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "旋转 Roll (deg)"
    
    trans_r = ET.SubElement(calibration_group, "widget", {"class": "QDoubleSpinBox", "name": "trans_r"})
    property_geometry = ET.SubElement(trans_r, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "130"
    ET.SubElement(rect, "y").text = "130"
    ET.SubElement(rect, "width").text = "120"
    ET.SubElement(rect, "height").text = "22"
    property_minimum = ET.SubElement(trans_r, "property", {"name": "minimum"})
    ET.SubElement(property_minimum, "double").text = "-180.000000000000000"
    property_maximum = ET.SubElement(trans_r, "property", {"name": "maximum"})
    ET.SubElement(property_maximum, "double").text = "180.000000000000000"
    
    # 旋转 Pitch
    label_trans_p = ET.SubElement(calibration_group, "widget", {"class": "QLabel", "name": "label_trans_p"})
    property_geometry = ET.SubElement(label_trans_p, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "20"
    ET.SubElement(rect, "y").text = "160"
    ET.SubElement(rect, "width").text = "110"
    ET.SubElement(rect, "height").text = "20"
    property_text = ET.SubElement(label_trans_p, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "旋转 Pitch (deg)"
    
    trans_p = ET.SubElement(calibration_group, "widget", {"class": "QDoubleSpinBox", "name": "trans_p"})
    property_geometry = ET.SubElement(trans_p, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "130"
    ET.SubElement(rect, "y").text = "160"
    ET.SubElement(rect, "width").text = "120"
    ET.SubElement(rect, "height").text = "22"
    property_minimum = ET.SubElement(trans_p, "property", {"name": "minimum"})
    ET.SubElement(property_minimum, "double").text = "-180.000000000000000"
    property_maximum = ET.SubElement(trans_p, "property", {"name": "maximum"})
    ET.SubElement(property_maximum, "double").text = "180.000000000000000"
    
    # 旋转 Yaw
    label_trans_y_2 = ET.SubElement(calibration_group, "widget", {"class": "QLabel", "name": "label_trans_y_2"})
    property_geometry = ET.SubElement(label_trans_y_2, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "20"
    ET.SubElement(rect, "y").text = "190"
    ET.SubElement(rect, "width").text = "110"
    ET.SubElement(rect, "height").text = "20"
    property_text = ET.SubElement(label_trans_y_2, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "旋转 Yaw (deg)"
    
    trans_y_2 = ET.SubElement(calibration_group, "widget", {"class": "QDoubleSpinBox", "name": "trans_y_2"})
    property_geometry = ET.SubElement(trans_y_2, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "130"
    ET.SubElement(rect, "y").text = "190"
    ET.SubElement(rect, "width").text = "120"
    ET.SubElement(rect, "height").text = "22"
    property_minimum = ET.SubElement(trans_y_2, "property", {"name": "minimum"})
    ET.SubElement(property_minimum, "double").text = "-180.000000000000000"
    property_maximum = ET.SubElement(trans_y_2, "property", {"name": "maximum"})
    ET.SubElement(property_maximum, "double").text = "180.000000000000000"
    
    # 应用变换矩阵按钮
    apply_transform_button = ET.SubElement(calibration_group, "widget", {"class": "QPushButton", "name": "apply_transform_button"})
    property_geometry = ET.SubElement(apply_transform_button, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "40"
    ET.SubElement(rect, "y").text = "230"
    ET.SubElement(rect, "width").text = "200"
    ET.SubElement(rect, "height").text = "30"
    property_text = ET.SubElement(apply_transform_button, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "应用变换矩阵"
    property_styleSheet = ET.SubElement(apply_transform_button, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # =================================================================
    # 机器人控制区域 - 完整版本
    # =================================================================
    robot_control_group = ET.SubElement(widget, "widget", {"class": "QGroupBox", "name": "robot_control_group"})
    property_geometry = ET.SubElement(robot_control_group, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "340"
    ET.SubElement(rect, "y").text = "300"
    ET.SubElement(rect, "width").text = "601"
    ET.SubElement(rect, "height").text = "340"
    property_title = ET.SubElement(robot_control_group, "property", {"name": "title"})
    ET.SubElement(property_title, "string").text = "机器人控制"
    
    # --- 紧急控制 ---
    # 复位按钮
    pushButton_3 = ET.SubElement(robot_control_group, "widget", {"class": "QPushButton", "name": "pushButton_3"})
    property_geometry = ET.SubElement(pushButton_3, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "450"
    ET.SubElement(rect, "y").text = "20"
    ET.SubElement(rect, "width").text = "61"
    ET.SubElement(rect, "height").text = "41"
    property_text = ET.SubElement(pushButton_3, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "复位"
    property_styleSheet = ET.SubElement(pushButton_3, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(123, 75.50%, 68.00%, 0.25); border-radius: 3px; border: 3px solid hsla(123, 75.50%, 68.00%, 0.25)"
    
    # 急停按钮
    pushButton_2 = ET.SubElement(robot_control_group, "widget", {"class": "QPushButton", "name": "pushButton_2"})
    property_geometry = ET.SubElement(pushButton_2, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "520"
    ET.SubElement(rect, "y").text = "20"
    ET.SubElement(rect, "width").text = "61"
    ET.SubElement(rect, "height").text = "41"
    property_text = ET.SubElement(pushButton_2, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "急停"
    property_styleSheet = ET.SubElement(pushButton_2, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(14, 83.40%, 59.80%, 0.25); border-radius: 3px; border: 3px solid hsla(14, 83.40%, 59.80%, 0.25)"
    
    # --- 速度控制 ---
    # 速度标签
    label_21 = ET.SubElement(robot_control_group, "widget", {"class": "QLabel", "name": "label_21"})
    property_geometry = ET.SubElement(label_21, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "292"
    ET.SubElement(rect, "y").text = "75"
    ET.SubElement(rect, "width").text = "41"
    ET.SubElement(rect, "height").text = "21"
    property_text = ET.SubElement(label_21, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "速度"
    
    # 速度滑块
    v = ET.SubElement(robot_control_group, "widget", {"class": "QSlider", "name": "v"})
    property_geometry = ET.SubElement(v, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "298"
    ET.SubElement(rect, "y").text = "110"
    ET.SubElement(rect, "width").text = "22"
    ET.SubElement(rect, "height").text = "121"
    property_orientation = ET.SubElement(v, "property", {"name": "orientation"})
    ET.SubElement(property_orientation, "enum").text = "Qt::Vertical"
    property_value = ET.SubElement(v, "property", {"name": "value"})
    ET.SubElement(property_value, "number").text = "50"
    property_styleSheet = ET.SubElement(v, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "selection-background-color: hsla(213, 88.40%, 62.90%, 0.94)"
    
    # --- 视觉与曲线功能 ---
    # 视觉分类按钮
    pushButton_4 = ET.SubElement(robot_control_group, "widget", {"class": "QPushButton", "name": "pushButton_4"})
    property_geometry = ET.SubElement(pushButton_4, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "350"
    ET.SubElement(rect, "y").text = "80"
    ET.SubElement(rect, "width").text = "100"
    ET.SubElement(rect, "height").text = "31"
    property_text = ET.SubElement(pushButton_4, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "视觉分类"
    property_styleSheet = ET.SubElement(pushButton_4, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 视觉拾取按钮
    pushButton_5 = ET.SubElement(robot_control_group, "widget", {"class": "QPushButton", "name": "pushButton_5"})
    property_geometry = ET.SubElement(pushButton_5, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "480"
    ET.SubElement(rect, "y").text = "80"
    ET.SubElement(rect, "width").text = "100"
    ET.SubElement(rect, "height").text = "31"
    property_text = ET.SubElement(pushButton_5, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "视觉拾取"
    property_styleSheet = ET.SubElement(pushButton_5, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 曲线选择下拉框
    comboBox = ET.SubElement(robot_control_group, "widget", {"class": "QComboBox", "name": "comboBox"})
    property_geometry = ET.SubElement(comboBox, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "350"
    ET.SubElement(rect, "y").text = "130"
    ET.SubElement(rect, "width").text = "100"
    ET.SubElement(rect, "height").text = "31"
    
    # 运行曲线按钮
    pushButton_6 = ET.SubElement(robot_control_group, "widget", {"class": "QPushButton", "name": "pushButton_6"})
    property_geometry = ET.SubElement(pushButton_6, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "480"
    ET.SubElement(rect, "y").text = "130"
    ET.SubElement(rect, "width").text = "100"
    ET.SubElement(rect, "height").text = "31"
    property_text = ET.SubElement(pushButton_6, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "运行曲线"
    property_styleSheet = ET.SubElement(pushButton_6, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # --- 寸动控制 ---
    inch_group = ET.SubElement(robot_control_group, "widget", {"class": "QGroupBox", "name": "inch_group"})
    property_geometry = ET.SubElement(inch_group, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "35"
    ET.SubElement(rect, "width").text = "271"
    ET.SubElement(rect, "height").text = "171"
    property_title = ET.SubElement(inch_group, "property", {"name": "title"})
    ET.SubElement(property_title, "string").text = "寸动"
    
    # 寸动按钮 X+
    pushButton_8 = ET.SubElement(inch_group, "widget", {"class": "QPushButton", "name": "pushButton_8"})
    property_geometry = ET.SubElement(pushButton_8, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "42"
    ET.SubElement(rect, "width").text = "31"
    ET.SubElement(rect, "height").text = "31"
    property_text = ET.SubElement(pushButton_8, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "X+"
    property_styleSheet = ET.SubElement(pushButton_8, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 寸动按钮 X-
    pushButton_9 = ET.SubElement(inch_group, "widget", {"class": "QPushButton", "name": "pushButton_9"})
    property_geometry = ET.SubElement(pushButton_9, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "50"
    ET.SubElement(rect, "y").text = "41"
    ET.SubElement(rect, "width").text = "31"
    ET.SubElement(rect, "height").text = "31"
    property_text = ET.SubElement(pushButton_9, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "X-"
    property_styleSheet = ET.SubElement(pushButton_9, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 寸动按钮 Y+
    pushButton_10 = ET.SubElement(inch_group, "widget", {"class": "QPushButton", "name": "pushButton_10"})
    property_geometry = ET.SubElement(pushButton_10, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "90"
    ET.SubElement(rect, "y").text = "41"
    ET.SubElement(rect, "width").text = "31"
    ET.SubElement(rect, "height").text = "31"
    property_text = ET.SubElement(pushButton_10, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "Y+"
    property_styleSheet = ET.SubElement(pushButton_10, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 寸动按钮 Y-
    pushButton_11 = ET.SubElement(inch_group, "widget", {"class": "QPushButton", "name": "pushButton_11"})
    property_geometry = ET.SubElement(pushButton_11, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "130"
    ET.SubElement(rect, "y").text = "41"
    ET.SubElement(rect, "width").text = "31"
    ET.SubElement(rect, "height").text = "31"
    property_text = ET.SubElement(pushButton_11, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "Y-"
    property_styleSheet = ET.SubElement(pushButton_11, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 寸动按钮 Z+
    pushButton_12 = ET.SubElement(inch_group, "widget", {"class": "QPushButton", "name": "pushButton_12"})
    property_geometry = ET.SubElement(pushButton_12, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "170"
    ET.SubElement(rect, "y").text = "41"
    ET.SubElement(rect, "width").text = "31"
    ET.SubElement(rect, "height").text = "31"
    property_text = ET.SubElement(pushButton_12, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "Z+"
    property_styleSheet = ET.SubElement(pushButton_12, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 寸动按钮 Z-
    pushButton_13 = ET.SubElement(inch_group, "widget", {"class": "QPushButton", "name": "pushButton_13"})
    property_geometry = ET.SubElement(pushButton_13, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "210"
    ET.SubElement(rect, "y").text = "41"
    ET.SubElement(rect, "width").text = "31"
    ET.SubElement(rect, "height").text = "31"
    property_text = ET.SubElement(pushButton_13, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "Z-"
    property_styleSheet = ET.SubElement(pushButton_13, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # --- 点动序列控制 ---
    jog_sequence_group = ET.SubElement(robot_control_group, "widget", {"class": "QGroupBox", "name": "jog_sequence_group"})
    property_geometry = ET.SubElement(jog_sequence_group, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "120"
    ET.SubElement(rect, "width").text = "271"
    ET.SubElement(rect, "height").text = "210"
    property_title = ET.SubElement(jog_sequence_group, "property", {"name": "title"})
    ET.SubElement(property_title, "string").text = "点动"
    
    # 初始坐标标签
    start_point_label = ET.SubElement(jog_sequence_group, "widget", {"class": "QLabel", "name": "start_point_label"})
    property_geometry = ET.SubElement(start_point_label, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "30"
    ET.SubElement(rect, "width").text = "100"
    ET.SubElement(rect, "height").text = "20"
    property_text = ET.SubElement(start_point_label, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "初始坐标"
    
    # 初始坐标 X
    start_x_spinbox = ET.SubElement(jog_sequence_group, "widget", {"class": "QDoubleSpinBox", "name": "start_x_spinbox"})
    property_geometry = ET.SubElement(start_x_spinbox, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "57"
    ET.SubElement(rect, "width").text = "71"
    ET.SubElement(rect, "height").text = "31"
    property_minimum = ET.SubElement(start_x_spinbox, "property", {"name": "minimum"})
    ET.SubElement(property_minimum, "double").text = "-150.000000000000000"
    property_maximum = ET.SubElement(start_x_spinbox, "property", {"name": "maximum"})
    ET.SubElement(property_maximum, "double").text = "150.000000000000000"
    property_suffix = ET.SubElement(start_x_spinbox, "property", {"name": "suffix"})
    ET.SubElement(property_suffix, "string").text = " mm"
    
    # 初始坐标 Y
    start_y_spinbox = ET.SubElement(jog_sequence_group, "widget", {"class": "QDoubleSpinBox", "name": "start_y_spinbox"})
    property_geometry = ET.SubElement(start_y_spinbox, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "95"
    ET.SubElement(rect, "y").text = "57"
    ET.SubElement(rect, "width").text = "71"
    ET.SubElement(rect, "height").text = "31"
    property_minimum = ET.SubElement(start_y_spinbox, "property", {"name": "minimum"})
    ET.SubElement(property_minimum, "double").text = "-150.000000000000000"
    property_maximum = ET.SubElement(start_y_spinbox, "property", {"name": "maximum"})
    ET.SubElement(property_maximum, "double").text = "150.000000000000000"
    property_suffix = ET.SubElement(start_y_spinbox, "property", {"name": "suffix"})
    ET.SubElement(property_suffix, "string").text = " mm"
    
    # 初始坐标 Z
    start_z_spinbox = ET.SubElement(jog_sequence_group, "widget", {"class": "QDoubleSpinBox", "name": "start_z_spinbox"})
    property_geometry = ET.SubElement(start_z_spinbox, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "180"
    ET.SubElement(rect, "y").text = "57"
    ET.SubElement(rect, "width").text = "71"
    ET.SubElement(rect, "height").text = "31"
    property_minimum = ET.SubElement(start_z_spinbox, "property", {"name": "minimum"})
    ET.SubElement(property_minimum, "double").text = "-400.000000000000000"
    property_maximum = ET.SubElement(start_z_spinbox, "property", {"name": "maximum"})
    ET.SubElement(property_maximum, "double").text = "-100.000000000000000"
    property_suffix = ET.SubElement(start_z_spinbox, "property", {"name": "suffix"})
    ET.SubElement(property_suffix, "string").text = " mm"
    
    # 终点坐标标签
    end_point_label = ET.SubElement(jog_sequence_group, "widget", {"class": "QLabel", "name": "end_point_label"})
    property_geometry = ET.SubElement(end_point_label, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "97"
    ET.SubElement(rect, "width").text = "100"
    ET.SubElement(rect, "height").text = "20"
    property_text = ET.SubElement(end_point_label, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "终点坐标"
    
    # 终点坐标 X
    end_x_spinbox = ET.SubElement(jog_sequence_group, "widget", {"class": "QDoubleSpinBox", "name": "end_x_spinbox"})
    property_geometry = ET.SubElement(end_x_spinbox, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "127"
    ET.SubElement(rect, "width").text = "71"
    ET.SubElement(rect, "height").text = "31"
    property_minimum = ET.SubElement(end_x_spinbox, "property", {"name": "minimum"})
    ET.SubElement(property_minimum, "double").text = "-150.000000000000000"
    property_maximum = ET.SubElement(end_x_spinbox, "property", {"name": "maximum"})
    ET.SubElement(property_maximum, "double").text = "150.000000000000000"
    property_suffix = ET.SubElement(end_x_spinbox, "property", {"name": "suffix"})
    ET.SubElement(property_suffix, "string").text = " mm"
    
    # 终点坐标 Y
    end_y_spinbox = ET.SubElement(jog_sequence_group, "widget", {"class": "QDoubleSpinBox", "name": "end_y_spinbox"})
    property_geometry = ET.SubElement(end_y_spinbox, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "95"
    ET.SubElement(rect, "y").text = "127"
    ET.SubElement(rect, "width").text = "71"
    ET.SubElement(rect, "height").text = "31"
    property_minimum = ET.SubElement(end_y_spinbox, "property", {"name": "minimum"})
    ET.SubElement(property_minimum, "double").text = "-150.000000000000000"
    property_maximum = ET.SubElement(end_y_spinbox, "property", {"name": "maximum"})
    ET.SubElement(property_maximum, "double").text = "150.000000000000000"
    property_suffix = ET.SubElement(end_y_spinbox, "property", {"name": "suffix"})
    ET.SubElement(property_suffix, "string").text = " mm"
    
    # 终点坐标 Z
    end_z_spinbox = ET.SubElement(jog_sequence_group, "widget", {"class": "QDoubleSpinBox", "name": "end_z_spinbox"})
    property_geometry = ET.SubElement(end_z_spinbox, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "180"
    ET.SubElement(rect, "y").text = "127"
    ET.SubElement(rect, "width").text = "71"
    ET.SubElement(rect, "height").text = "31"
    property_minimum = ET.SubElement(end_z_spinbox, "property", {"name": "minimum"})
    ET.SubElement(property_minimum, "double").text = "-400.000000000000000"
    property_maximum = ET.SubElement(end_z_spinbox, "property", {"name": "maximum"})
    ET.SubElement(property_maximum, "double").text = "-100.000000000000000"
    property_suffix = ET.SubElement(end_z_spinbox, "property", {"name": "suffix"})
    ET.SubElement(property_suffix, "string").text = " mm"
    
    # 运行点动序列按钮
    run_jog_sequence_button = ET.SubElement(jog_sequence_group, "widget", {"class": "QPushButton", "name": "run_jog_sequence_button"})
    property_geometry = ET.SubElement(run_jog_sequence_button, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "170"
    ET.SubElement(rect, "width").text = "241"
    ET.SubElement(rect, "height").text = "31"
    property_text = ET.SubElement(run_jog_sequence_button, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "运行点动序列"
    
    # --- 电机调试 ---
    motor_debug_group = ET.SubElement(robot_control_group, "widget", {"class": "QGroupBox", "name": "motor_debug_group"})
    property_geometry = ET.SubElement(motor_debug_group, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "340"
    ET.SubElement(rect, "y").text = "180"
    ET.SubElement(rect, "width").text = "261"
    ET.SubElement(rect, "height").text = "71"
    property_title = ET.SubElement(motor_debug_group, "property", {"name": "title"})
    ET.SubElement(property_title, "string").text = "电机调试"
    
    # 电机调试按钮 A+
    pushButton_14 = ET.SubElement(motor_debug_group, "widget", {"class": "QPushButton", "name": "pushButton_14"})
    property_geometry = ET.SubElement(pushButton_14, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "30"
    ET.SubElement(rect, "width").text = "31"
    ET.SubElement(rect, "height").text = "31"
    property_text = ET.SubElement(pushButton_14, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "A+"
    property_styleSheet = ET.SubElement(pushButton_14, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 电机调试按钮 A-
    pushButton_15 = ET.SubElement(motor_debug_group, "widget", {"class": "QPushButton", "name": "pushButton_15"})
    property_geometry = ET.SubElement(pushButton_15, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "50"
    ET.SubElement(rect, "y").text = "30"
    ET.SubElement(rect, "width").text = "31"
    ET.SubElement(rect, "height").text = "31"
    property_text = ET.SubElement(pushButton_15, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "A-"
    property_styleSheet = ET.SubElement(pushButton_15, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 电机调试按钮 B+
    pushButton_16 = ET.SubElement(motor_debug_group, "widget", {"class": "QPushButton", "name": "pushButton_16"})
    property_geometry = ET.SubElement(pushButton_16, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "90"
    ET.SubElement(rect, "y").text = "30"
    ET.SubElement(rect, "width").text = "31"
    ET.SubElement(rect, "height").text = "31"
    property_text = ET.SubElement(pushButton_16, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "B+"
    property_styleSheet = ET.SubElement(pushButton_16, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 电机调试按钮 B-
    pushButton_17 = ET.SubElement(motor_debug_group, "widget", {"class": "QPushButton", "name": "pushButton_17"})
    property_geometry = ET.SubElement(pushButton_17, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "130"
    ET.SubElement(rect, "y").text = "30"
    ET.SubElement(rect, "width").text = "31"
    ET.SubElement(rect, "height").text = "31"
    property_text = ET.SubElement(pushButton_17, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "B-"
    property_styleSheet = ET.SubElement(pushButton_17, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 电机调试按钮 C+
    pushButton_18 = ET.SubElement(motor_debug_group, "widget", {"class": "QPushButton", "name": "pushButton_18"})
    property_geometry = ET.SubElement(pushButton_18, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "170"
    ET.SubElement(rect, "y").text = "30"
    ET.SubElement(rect, "width").text = "31"
    ET.SubElement(rect, "height").text = "31"
    property_text = ET.SubElement(pushButton_18, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "C+"
    property_styleSheet = ET.SubElement(pushButton_18, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 电机调试按钮 C-
    pushButton_19 = ET.SubElement(motor_debug_group, "widget", {"class": "QPushButton", "name": "pushButton_19"})
    property_geometry = ET.SubElement(pushButton_19, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "210"
    ET.SubElement(rect, "y").text = "30"
    ET.SubElement(rect, "width").text = "31"
    ET.SubElement(rect, "height").text = "31"
    property_text = ET.SubElement(pushButton_19, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "C-"
    property_styleSheet = ET.SubElement(pushButton_19, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # --- 运动学解算测试 ---
    kinematics_group = ET.SubElement(robot_control_group, "widget", {"class": "QGroupBox", "name": "kinematics_group"})
    property_geometry = ET.SubElement(kinematics_group, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "340"
    ET.SubElement(rect, "y").text = "260"
    ET.SubElement(rect, "width").text = "261"
    ET.SubElement(rect, "height").text = "130"
    property_title = ET.SubElement(kinematics_group, "property", {"name": "title"})
    ET.SubElement(property_title, "string").text = "运动学解算测试"
    
    # 目标末端 XYZ 标签
    label_fk = ET.SubElement(kinematics_group, "widget", {"class": "QLabel", "name": "label_fk"})
    property_geometry = ET.SubElement(label_fk, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "25"
    ET.SubElement(rect, "width").text = "150"
    ET.SubElement(rect, "height").text = "20"
    property_text = ET.SubElement(label_fk, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "目标末端 XYZ (mm)"
    
    # 逆解 X 坐标
    ik_x = ET.SubElement(kinematics_group, "widget", {"class": "QDoubleSpinBox", "name": "ik_x"})
    property_geometry = ET.SubElement(ik_x, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "50"
    ET.SubElement(rect, "width").text = "71"
    ET.SubElement(rect, "height").text = "25"
    property_minimum = ET.SubElement(ik_x, "property", {"name": "minimum"})
    ET.SubElement(property_minimum, "double").text = "-150.000000000000000"
    property_maximum = ET.SubElement(ik_x, "property", {"name": "maximum"})
    ET.SubElement(property_maximum, "double").text = "150.000000000000000"
    property_suffix = ET.SubElement(ik_x, "property", {"name": "suffix"})
    ET.SubElement(property_suffix, "string").text = " mm"
    
    # 逆解 Y 坐标
    ik_y = ET.SubElement(kinematics_group, "widget", {"class": "QDoubleSpinBox", "name": "ik_y"})
    property_geometry = ET.SubElement(ik_y, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "90"
    ET.SubElement(rect, "y").text = "50"
    ET.SubElement(rect, "width").text = "71"
    ET.SubElement(rect, "height").text = "25"
    property_minimum = ET.SubElement(ik_y, "property", {"name": "minimum"})
    ET.SubElement(property_minimum, "double").text = "-150.000000000000000"
    property_maximum = ET.SubElement(ik_y, "property", {"name": "maximum"})
    ET.SubElement(property_maximum, "double").text = "150.000000000000000"
    property_suffix = ET.SubElement(ik_y, "property", {"name": "suffix"})
    ET.SubElement(property_suffix, "string").text = " mm"
    
    # 逆解 Z 坐标
    ik_z = ET.SubElement(kinematics_group, "widget", {"class": "QDoubleSpinBox", "name": "ik_z"})
    property_geometry = ET.SubElement(ik_z, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "170"
    ET.SubElement(rect, "y").text = "50"
    ET.SubElement(rect, "width").text = "71"
    ET.SubElement(rect, "height").text = "25"
    property_minimum = ET.SubElement(ik_z, "property", {"name": "minimum"})
    ET.SubElement(property_minimum, "double").text = "-400.000000000000000"
    property_maximum = ET.SubElement(ik_z, "property", {"name": "maximum"})
    ET.SubElement(property_maximum, "double").text = "-100.000000000000000"
    property_suffix = ET.SubElement(ik_z, "property", {"name": "suffix"})
    ET.SubElement(property_suffix, "string").text = " mm"
    
    # 逆解 + 正解验证按钮
    solve_ik_button = ET.SubElement(kinematics_group, "widget", {"class": "QPushButton", "name": "solve_ik_button"})
    property_geometry = ET.SubElement(solve_ik_button, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "80"
    ET.SubElement(rect, "width").text = "120"
    ET.SubElement(rect, "height").text = "30"
    property_text = ET.SubElement(solve_ik_button, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "逆解 + 正解验证"
    
    # 逆解结果标签
    ik_result_label = ET.SubElement(kinematics_group, "widget", {"class": "QLabel", "name": "ik_result_label"})
    property_geometry = ET.SubElement(ik_result_label, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "110"
    ET.SubElement(rect, "width").text = "230"
    ET.SubElement(rect, "height").text = "20"
    property_text = ET.SubElement(ik_result_label, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "角度 / 误差：--"
    property_styleSheet = ET.SubElement(ik_result_label, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "font-size: 11px;"
    
    # --- 3D仿真控制 ---
    simulator_group = ET.SubElement(robot_control_group, "widget", {"class": "QGroupBox", "name": "simulator_group"})
    property_geometry = ET.SubElement(simulator_group, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "340"
    ET.SubElement(rect, "width").text = "271"
    ET.SubElement(rect, "height").text = "80"
    property_title = ET.SubElement(simulator_group, "property", {"name": "title"})
    ET.SubElement(property_title, "string").text = "3D仿真"
    
    # 启用仿真显示复选框
    simulator_enable_checkbox = ET.SubElement(simulator_group, "widget", {"class": "QCheckBox", "name": "simulator_enable_checkbox"})
    property_geometry = ET.SubElement(simulator_enable_checkbox, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "25"
    ET.SubElement(rect, "width").text = "120"
    ET.SubElement(rect, "height").text = "20"
    property_text = ET.SubElement(simulator_enable_checkbox, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "启用仿真显示"
    property_checked = ET.SubElement(simulator_enable_checkbox, "property", {"name": "checked"})
    ET.SubElement(property_checked, "bool").text = "false"
    
    # 打开仿真窗口按钮
    open_simulator_button = ET.SubElement(simulator_group, "widget", {"class": "QPushButton", "name": "open_simulator_button"})
    property_geometry = ET.SubElement(open_simulator_button, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "50"
    ET.SubElement(rect, "width").text = "120"
    ET.SubElement(rect, "height").text = "25"
    property_text = ET.SubElement(open_simulator_button, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "打开仿真窗口"
    property_styleSheet = ET.SubElement(open_simulator_button, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(213, 88.40%, 62.90%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 更新仿真按钮
    update_simulator_button = ET.SubElement(simulator_group, "widget", {"class": "QPushButton", "name": "update_simulator_button"})
    property_geometry = ET.SubElement(update_simulator_button, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "140"
    ET.SubElement(rect, "y").text = "50"
    ET.SubElement(rect, "width").text = "120"
    ET.SubElement(rect, "height").text = "25"
    property_text = ET.SubElement(update_simulator_button, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "更新仿真"
    property_styleSheet = ET.SubElement(update_simulator_button, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(213, 88.40%, 62.90%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # =================================================================
    # 机器人状态区域（之前已包含，这里省略重复代码）
    # =================================================================
    
    # 机器人状态区域
    status_group = ET.SubElement(widget, "widget", {"class": "QGroupBox", "name": "status_group"})
    property_geometry = ET.SubElement(status_group, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "630"
    ET.SubElement(rect, "y").text = "10"
    ET.SubElement(rect, "width").text = "311"
    ET.SubElement(rect, "height").text = "241"
    property_title = ET.SubElement(status_group, "property", {"name": "title"})
    ET.SubElement(property_title, "string").text = "机器人状态"
    
    # 滑台位置标签
    label_9 = ET.SubElement(status_group, "widget", {"class": "QLabel", "name": "label_9"})
    property_geometry = ET.SubElement(label_9, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "20"
    ET.SubElement(rect, "y").text = "30"
    ET.SubElement(rect, "width").text = "121"
    ET.SubElement(rect, "height").text = "21"
    property_text = ET.SubElement(label_9, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "滑台位置"
    
    # X坐标标签
    label_10 = ET.SubElement(status_group, "widget", {"class": "QLabel", "name": "label_10"})
    property_geometry = ET.SubElement(label_10, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "30"
    ET.SubElement(rect, "y").text = "60"
    ET.SubElement(rect, "width").text = "21"
    ET.SubElement(rect, "height").text = "21"
    property_text = ET.SubElement(label_10, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "X"
    
    # X坐标显示
    textBrowser_3 = ET.SubElement(status_group, "widget", {"class": "QTextBrowser", "name": "textBrowser_3"})
    property_geometry = ET.SubElement(textBrowser_3, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "50"
    ET.SubElement(rect, "y").text = "55"
    ET.SubElement(rect, "width").text = "61"
    ET.SubElement(rect, "height").text = "31"
    property_styleSheet = ET.SubElement(textBrowser_3, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # Y坐标标签
    label_12 = ET.SubElement(status_group, "widget", {"class": "QLabel", "name": "label_12"})
    property_geometry = ET.SubElement(label_12, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "120"
    ET.SubElement(rect, "y").text = "60"
    ET.SubElement(rect, "width").text = "21"
    ET.SubElement(rect, "height").text = "21"
    property_text = ET.SubElement(label_12, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "Y"
    
    # Y坐标显示
    textBrowser_4 = ET.SubElement(status_group, "widget", {"class": "QTextBrowser", "name": "textBrowser_4"})
    property_geometry = ET.SubElement(textBrowser_4, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "140"
    ET.SubElement(rect, "y").text = "55"
    ET.SubElement(rect, "width").text = "61"
    ET.SubElement(rect, "height").text = "31"
    property_styleSheet = ET.SubElement(textBrowser_4, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # Z坐标标签
    label_11 = ET.SubElement(status_group, "widget", {"class": "QLabel", "name": "label_11"})
    property_geometry = ET.SubElement(label_11, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "210"
    ET.SubElement(rect, "y").text = "60"
    ET.SubElement(rect, "width").text = "21"
    ET.SubElement(rect, "height").text = "21"
    property_text = ET.SubElement(label_11, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "Z"
    
    # Z坐标显示
    textBrowser_5 = ET.SubElement(status_group, "widget", {"class": "QTextBrowser", "name": "textBrowser_5"})
    property_geometry = ET.SubElement(textBrowser_5, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "230"
    ET.SubElement(rect, "y").text = "55"
    ET.SubElement(rect, "width").text = "61"
    ET.SubElement(rect, "height").text = "31"
    property_styleSheet = ET.SubElement(textBrowser_5, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 动平台位置标签
    label_13 = ET.SubElement(status_group, "widget", {"class": "QLabel", "name": "label_13"})
    property_geometry = ET.SubElement(label_13, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "20"
    ET.SubElement(rect, "y").text = "110"
    ET.SubElement(rect, "width").text = "121"
    ET.SubElement(rect, "height").text = "21"
    property_text = ET.SubElement(label_13, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "动平台位置"
    
    # 动平台X坐标标签
    label_14 = ET.SubElement(status_group, "widget", {"class": "QLabel", "name": "label_14"})
    property_geometry = ET.SubElement(label_14, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "30"
    ET.SubElement(rect, "y").text = "140"
    ET.SubElement(rect, "width").text = "21"
    ET.SubElement(rect, "height").text = "21"
    property_text = ET.SubElement(label_14, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "X"
    
    # 动平台X坐标显示
    textBrowser_6 = ET.SubElement(status_group, "widget", {"class": "QTextBrowser", "name": "textBrowser_6"})
    property_geometry = ET.SubElement(textBrowser_6, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "50"
    ET.SubElement(rect, "y").text = "135"
    ET.SubElement(rect, "width").text = "61"
    ET.SubElement(rect, "height").text = "31"
    property_styleSheet = ET.SubElement(textBrowser_6, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 动平台Y坐标标签
    label_16 = ET.SubElement(status_group, "widget", {"class": "QLabel", "name": "label_16"})
    property_geometry = ET.SubElement(label_16, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "120"
    ET.SubElement(rect, "y").text = "140"
    ET.SubElement(rect, "width").text = "21"
    ET.SubElement(rect, "height").text = "21"
    property_text = ET.SubElement(label_16, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "Y"
    
    # 动平台Y坐标显示
    textBrowser_7 = ET.SubElement(status_group, "widget", {"class": "QTextBrowser", "name": "textBrowser_7"})
    property_geometry = ET.SubElement(textBrowser_7, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "140"
    ET.SubElement(rect, "y").text = "135"
    ET.SubElement(rect, "width").text = "61"
    ET.SubElement(rect, "height").text = "31"
    property_styleSheet = ET.SubElement(textBrowser_7, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 动平台Z坐标标签
    label_15 = ET.SubElement(status_group, "widget", {"class": "QLabel", "name": "label_15"})
    property_geometry = ET.SubElement(label_15, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "210"
    ET.SubElement(rect, "y").text = "140"
    ET.SubElement(rect, "width").text = "21"
    ET.SubElement(rect, "height").text = "21"
    property_text = ET.SubElement(label_15, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "Z"
    
    # 动平台Z坐标显示
    textBrowser_8 = ET.SubElement(status_group, "widget", {"class": "QTextBrowser", "name": "textBrowser_8"})
    property_geometry = ET.SubElement(textBrowser_8, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "230"
    ET.SubElement(rect, "y").text = "135"
    ET.SubElement(rect, "width").text = "61"
    ET.SubElement(rect, "height").text = "31"
    property_styleSheet = ET.SubElement(textBrowser_8, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 标定状态显示
    calibrationStatus = ET.SubElement(widget, "widget", {"class": "QLabel", "name": "calibrationStatus"})
    property_geometry = ET.SubElement(calibrationStatus, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "630"
    ET.SubElement(rect, "y").text = "260"
    ET.SubElement(rect, "width").text = "311"
    ET.SubElement(rect, "height").text = "30"
    property_text = ET.SubElement(calibrationStatus, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "状态: 等待检测..."
    property_styleSheet = ET.SubElement(calibrationStatus, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "font-size: 12px; border: 1px solid gray; padding: 2px; background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # =================================================================
    # 写字功能区域（之前已包含，这里省略重复代码）
    # =================================================================
    
    # 写字功能区域
    writing_group = ET.SubElement(widget, "widget", {"class": "QGroupBox", "name": "writing_group"})
    property_geometry = ET.SubElement(writing_group, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "950"
    ET.SubElement(rect, "y").text = "10"
    ET.SubElement(rect, "width").text = "340"
    ET.SubElement(rect, "height").text = "680"
    property_title = ET.SubElement(writing_group, "property", {"name": "title"})
    ET.SubElement(property_title, "string").text = "写字功能"
    
    # 终端输出标签
    terminal_label = ET.SubElement(writing_group, "widget", {"class": "QLabel", "name": "terminal_label"})
    property_geometry = ET.SubElement(terminal_label, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "25"
    ET.SubElement(rect, "width").text = "80"
    ET.SubElement(rect, "height").text = "20"
    property_text = ET.SubElement(terminal_label, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "终端输出:"
    
    # 终端输出文本框
    terminal_output = ET.SubElement(writing_group, "widget", {"class": "QTextBrowser", "name": "terminal_output"})
    property_geometry = ET.SubElement(terminal_output, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "50"
    ET.SubElement(rect, "width").text = "320"
    ET.SubElement(rect, "height").text = "180"
    property_styleSheet = ET.SubElement(terminal_output, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 写字控制标签
    writing_control_label = ET.SubElement(writing_group, "widget", {"class": "QLabel", "name": "writing_control_label"})
    property_geometry = ET.SubElement(writing_control_label, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "240"
    ET.SubElement(rect, "width").text = "80"
    ET.SubElement(rect, "height").text = "20"
    property_text = ET.SubElement(writing_control_label, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "写字控制:"
    
    # 输入方式标签
    input_method_label = ET.SubElement(writing_group, "widget", {"class": "QLabel", "name": "input_method_label"})
    property_geometry = ET.SubElement(input_method_label, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "270"
    ET.SubElement(rect, "width").text = "60"
    ET.SubElement(rect, "height").text = "20"
    property_text = ET.SubElement(input_method_label, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "输入方式:"
    
    # 输入方式下拉框
    input_method = ET.SubElement(writing_group, "widget", {"class": "QComboBox", "name": "input_method"})
    property_geometry = ET.SubElement(input_method, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "80"
    ET.SubElement(rect, "y").text = "270"
    ET.SubElement(rect, "width").text = "100"
    ET.SubElement(rect, "height").text = "25"
    property_styleSheet = ET.SubElement(input_method, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 输入文字标签
    text_input_label = ET.SubElement(writing_group, "widget", {"class": "QLabel", "name": "text_input_label"})
    property_geometry = ET.SubElement(text_input_label, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "190"
    ET.SubElement(rect, "y").text = "270"
    ET.SubElement(rect, "width").text = "60"
    ET.SubElement(rect, "height").text = "20"
    property_text = ET.SubElement(text_input_label, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "输入文字:"
    
    # 文本输入框
    text_input = ET.SubElement(writing_group, "widget", {"class": "QLineEdit", "name": "text_input"})
    property_geometry = ET.SubElement(text_input, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "260"
    ET.SubElement(rect, "y").text = "270"
    ET.SubElement(rect, "width").text = "70"
    ET.SubElement(rect, "height").text = "25"
    property_text = ET.SubElement(text_input, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "FZU"
    property_styleSheet = ET.SubElement(text_input, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 字体大小标签
    font_size_label = ET.SubElement(writing_group, "widget", {"class": "QLabel", "name": "font_size_label"})
    property_geometry = ET.SubElement(font_size_label, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "305"
    ET.SubElement(rect, "width").text = "60"
    ET.SubElement(rect, "height").text = "20"
    property_text = ET.SubElement(font_size_label, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "字体大小:"
    
    # 字体大小选择框
    font_size = ET.SubElement(writing_group, "widget", {"class": "QSpinBox", "name": "font_size"})
    property_geometry = ET.SubElement(font_size, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "80"
    ET.SubElement(rect, "y").text = "305"
    ET.SubElement(rect, "width").text = "70"
    ET.SubElement(rect, "height").text = "25"
    property_minimum = ET.SubElement(font_size, "property", {"name": "minimum"})
    ET.SubElement(property_minimum, "number").text = "10"
    property_maximum = ET.SubElement(font_size, "property", {"name": "maximum"})
    ET.SubElement(property_maximum, "number").text = "100"
    property_value = ET.SubElement(font_size, "property", {"name": "value"})
    ET.SubElement(property_value, "number").text = "30"
    
    # 写字区域标签
    writing_area_label = ET.SubElement(writing_group, "widget", {"class": "QLabel", "name": "writing_area_label"})
    property_geometry = ET.SubElement(writing_area_label, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "160"
    ET.SubElement(rect, "y").text = "305"
    ET.SubElement(rect, "width").text = "60"
    ET.SubElement(rect, "height").text = "20"
    property_text = ET.SubElement(writing_area_label, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "区域(mm):"
    
    # 写字区域选择框
    writing_area = ET.SubElement(writing_group, "widget", {"class": "QSpinBox", "name": "writing_area"})
    property_geometry = ET.SubElement(writing_area, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "230"
    ET.SubElement(rect, "y").text = "305"
    ET.SubElement(rect, "width").text = "70"
    ET.SubElement(rect, "height").text = "25"
    property_minimum = ET.SubElement(writing_area, "property", {"name": "minimum"})
    ET.SubElement(property_minimum, "number").text = "50"
    property_maximum = ET.SubElement(writing_area, "property", {"name": "maximum"})
    ET.SubElement(property_maximum, "number").text = "300"
    property_value = ET.SubElement(writing_area, "property", {"name": "value"})
    ET.SubElement(property_value, "number").text = "150"
    
    # 写字高度Z标签
    z_height_label = ET.SubElement(writing_group, "widget", {"class": "QLabel", "name": "z_height_label"})
    property_geometry = ET.SubElement(z_height_label, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "340"
    ET.SubElement(rect, "width").text = "70"
    ET.SubElement(rect, "height").text = "20"
    property_text = ET.SubElement(z_height_label, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "写字高度Z:"
    
    # 写字高度Z选择框
    z_height = ET.SubElement(writing_group, "widget", {"class": "QDoubleSpinBox", "name": "z_height"})
    property_geometry = ET.SubElement(z_height, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "80"
    ET.SubElement(rect, "y").text = "340"
    ET.SubElement(rect, "width").text = "70"
    ET.SubElement(rect, "height").text = "25"
    property_minimum = ET.SubElement(z_height, "property", {"name": "minimum"})
    ET.SubElement(property_minimum, "double").text = "-400.000000000000000"
    property_maximum = ET.SubElement(z_height, "property", {"name": "maximum"})
    ET.SubElement(property_maximum, "double").text = "-100.000000000000000"
    property_value = ET.SubElement(z_height, "property", {"name": "value"})
    ET.SubElement(property_value, "double").text = "-280.000000000000000"
    property_singleStep = ET.SubElement(z_height, "property", {"name": "singleStep"})
    ET.SubElement(property_singleStep, "double").text = "5.000000000000000"
    
    # 写字速度标签
    writing_speed_label = ET.SubElement(writing_group, "widget", {"class": "QLabel", "name": "writing_speed_label"})
    property_geometry = ET.SubElement(writing_speed_label, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "160"
    ET.SubElement(rect, "y").text = "340"
    ET.SubElement(rect, "width").text = "60"
    ET.SubElement(rect, "height").text = "20"
    property_text = ET.SubElement(writing_speed_label, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "写字速度:"
    
    # 写字速度选择框
    writing_speed = ET.SubElement(writing_group, "widget", {"class": "QSpinBox", "name": "writing_speed"})
    property_geometry = ET.SubElement(writing_speed, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "230"
    ET.SubElement(rect, "y").text = "340"
    ET.SubElement(rect, "width").text = "70"
    ET.SubElement(rect, "height").text = "25"
    property_minimum = ET.SubElement(writing_speed, "property", {"name": "minimum"})
    ET.SubElement(property_minimum, "number").text = "1"
    property_maximum = ET.SubElement(writing_speed, "property", {"name": "maximum"})
    ET.SubElement(property_maximum, "number").text = "10"
    property_value = ET.SubElement(writing_speed, "property", {"name": "value"})
    ET.SubElement(property_value, "number").text = "5"
    
    # 使用手写按钮
    use_handwriting_button = ET.SubElement(writing_group, "widget", {"class": "QPushButton", "name": "use_handwriting_button"})
    property_geometry = ET.SubElement(use_handwriting_button, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "380"
    ET.SubElement(rect, "width").text = "75"
    ET.SubElement(rect, "height").text = "30"
    property_text = ET.SubElement(use_handwriting_button, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "使用手写"
    property_styleSheet = ET.SubElement(use_handwriting_button, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 预览轨迹按钮
    preview_button = ET.SubElement(writing_group, "widget", {"class": "QPushButton", "name": "preview_button"})
    property_geometry = ET.SubElement(preview_button, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "95"
    ET.SubElement(rect, "y").text = "380"
    ET.SubElement(rect, "width").text = "75"
    ET.SubElement(rect, "height").text = "30"
    property_text = ET.SubElement(preview_button, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "预览轨迹"
    property_styleSheet = ET.SubElement(preview_button, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 开始写字按钮
    start_writing_button = ET.SubElement(writing_group, "widget", {"class": "QPushButton", "name": "start_writing_button"})
    property_geometry = ET.SubElement(start_writing_button, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "180"
    ET.SubElement(rect, "y").text = "380"
    ET.SubElement(rect, "width").text = "75"
    ET.SubElement(rect, "height").text = "30"
    property_text = ET.SubElement(start_writing_button, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "开始写字"
    property_styleSheet = ET.SubElement(start_writing_button, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(123, 75.50%, 68.00%, 0.25); border-radius: 5px; border: 1px solid hsla(123, 75.50%, 68.00%, 0.94)"
    
    # 停止写字按钮
    stop_writing_button = ET.SubElement(writing_group, "widget", {"class": "QPushButton", "name": "stop_writing_button"})
    property_geometry = ET.SubElement(stop_writing_button, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "265"
    ET.SubElement(rect, "y").text = "380"
    ET.SubElement(rect, "width").text = "75"
    ET.SubElement(rect, "height").text = "30"
    property_text = ET.SubElement(stop_writing_button, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "停止写字"
    property_styleSheet = ET.SubElement(stop_writing_button, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(14, 83.40%, 59.80%, 0.25); border-radius: 5px; border: 1px solid hsla(14, 83.40%, 59.80%, 0.94)"
    
    # 清空画布按钮
    clear_canvas_button = ET.SubElement(writing_group, "widget", {"class": "QPushButton", "name": "clear_canvas_button"})
    property_geometry = ET.SubElement(clear_canvas_button, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "420"
    ET.SubElement(rect, "width").text = "320"
    ET.SubElement(rect, "height").text = "30"
    property_text = ET.SubElement(clear_canvas_button, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "清空画布"
    property_styleSheet = ET.SubElement(clear_canvas_button, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "background-color: hsla(0, 0.00%, 49.00%, 0.25); border-radius: 5px; border: 1px solid hsla(213, 88.40%, 62.90%, 0.94)"
    
    # 写字画布标签
    writing_canvas_label = ET.SubElement(writing_group, "widget", {"class": "QLabel", "name": "writing_canvas_label"})
    property_geometry = ET.SubElement(writing_canvas_label, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "460"
    ET.SubElement(rect, "width").text = "200"
    ET.SubElement(rect, "height").text = "20"
    property_text = ET.SubElement(writing_canvas_label, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "写字轨迹预览 (可手写):"
    
    # 状态显示
    writing_status = ET.SubElement(writing_group, "widget", {"class": "QLabel", "name": "writing_status"})
    property_geometry = ET.SubElement(writing_status, "property", {"name": "geometry"})
    rect = ET.SubElement(property_geometry, "rect")
    ET.SubElement(rect, "x").text = "10"
    ET.SubElement(rect, "y").text = "650"
    ET.SubElement(rect, "width").text = "320"
    ET.SubElement(rect, "height").text = "20"
    property_text = ET.SubElement(writing_status, "property", {"name": "text"})
    ET.SubElement(property_text, "string").text = "状态: 就绪"
    property_styleSheet = ET.SubElement(writing_status, "property", {"name": "styleSheet"})
    ET.SubElement(property_styleSheet, "string").text = "font-size: 12px; border: 1px solid gray; padding: 2px;"
    
    # 美化 XML 输出
    rough_string = ET.tostring(ui, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # 保存为 .ui 文件
    with open("delta_robot_controller_complete.ui", "w", encoding="utf-8") as f:
        f.write(pretty_xml)
    
    print("已生成 delta_robot_controller_complete.ui 文件，可在 Qt Designer 中打开编辑")

if __name__ == "__main__":
    python_to_ui()