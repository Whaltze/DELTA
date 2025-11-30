# -*- coding: utf-8 -*-
# camera.py (已更新)

import cv2
import os
import numpy as np
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QImage
import sys
import signal
import numpy as np
from functools import partial
import time

class Camera(QThread):
    """
    用于摄像头控制、图像处理和坐标变换的线程。
    """
    # 信号定义
    sendPicture = Signal(QImage)  # 发送处理后的图像以在UI中显示
    object_detected_robot_coords = Signal(dict) # 发送在机器人坐标系下检测到的物体信息

    def __init__(self):
        super().__init__()
        self.cam_number = 0
        self.is_running = False
        self.video_capture = None
        
        # 手眼标定：从相机到机器人基座的齐次变换矩阵
        self.T_camera_to_robot = np.identity(4)
        self.transform_matrix_set = False


        self.camera_matrix = None
        self.dist_coeffs = None
        self.load_calibration('./camera/camera_calibration.npz')

    def set_cam_number(self, num):
        """设置要使用的摄像头编号"""
        self.cam_number = num

    @staticmethod
    def scan_cameras():
        """扫描可用的摄像头 (适用于Linux)"""
        available_cameras = []
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                device_name = f"/dev/video{i}" if os.path.exists(f"/dev/video{i}") else f"摄像头 {i}"
                available_cameras.append((i, device_name))
                cap.release()
        return available_cameras
    def set_transform_matrix(self, x, y, z, roll, pitch, yaw):
        """
        根据用户输入的XYZ平移和RPY旋转，构建齐次变换矩阵。
        :param x, y, z: 平移 (mm)
        :param roll, pitch, yaw: 旋转 (度)
        """
        roll_rad, pitch_rad, yaw_rad = np.deg2rad([roll, pitch, yaw])

        Rx = np.array([[1, 0, 0], [0, np.cos(roll_rad), -np.sin(roll_rad)], [0, np.sin(roll_rad), np.cos(roll_rad)]])
        Ry = np.array([[np.cos(pitch_rad), 0, np.sin(pitch_rad)], [0, 1, 0], [-np.sin(pitch_rad), 0, np.cos(pitch_rad)]])
        Rz = np.array([[np.cos(yaw_rad), -np.sin(yaw_rad), 0], [np.sin(yaw_rad), np.cos(yaw_rad), 0], [0, 0, 1]])
        
        R = Rz @ Ry @ Rx
        
        self.T_camera_to_robot = np.identity(4)
        self.T_camera_to_robot[:3, :3] = R
        self.T_camera_to_robot[:3, 3] = [x, y, z]
        self.transform_matrix_set = True
        print("变换矩阵已更新:\n", self.T_camera_to_robot)

    def transform_to_robot_coords(self, camera_coords):
        """将相机坐标系下的坐标转换为机器人坐标系下的坐标"""
        if not self.transform_matrix_set:
            return None 

        camera_coords_homogeneous = np.append(camera_coords, 1)
        robot_coords_homogeneous = self.T_camera_to_robot @ camera_coords_homogeneous
        return robot_coords_homogeneous[:3]

    def process_frame(self, frame):
        """处理单帧图像：进行物体检测、定位和坐标变换。"""
        # 应用高斯模糊减少噪声
        blurred = cv2.GaussianBlur(frame, (5, 5), 0)
        hsv_frame = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        
        # 定义颜色的HSV范围（根据实际环境调整）
        color_ranges = {
            'Red': [([0, 150, 100], [10, 255, 255]), ([170, 150, 100], [180, 255, 255])],
            'Yellow': [([20, 100, 100], [30, 255, 255])],
            'Blue': [([90, 150, 50], [130, 255, 255])],
            'Green': [([40, 70, 70], [80, 255, 255])]
        }

        detected_items = []

        for color, ranges in color_ranges.items():
            # 为当前颜色创建掩码
            mask = cv2.inRange(hsv_frame, np.array(ranges[0][0]), np.array(ranges[0][1]))
            if len(ranges) > 1:
                mask2 = cv2.inRange(hsv_frame, np.array(ranges[1][0]), np.array(ranges[1][1]))
                mask = cv2.bitwise_or(mask, mask2)
            
            # 形态学操作：开运算（先腐蚀后膨胀）去除小噪点
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            # 在掩码中寻找轮廓
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 800:  # 过滤掉面积过小的噪点
                    continue
                    
                # 计算轮廓的周长
                perimeter = cv2.arcLength(cnt, True)
                
                # 计算圆形度 (4*pi*面积/周长²)
                circularity = 4 * np.pi * area / (perimeter ** 2) if perimeter > 0 else 0
                
                # 只接受高圆形度的物体 (接近1的圆)
                if circularity < 0.8:
                    continue
                    
                # 计算最小外接圆
                (x, y), radius = cv2.minEnclosingCircle(cnt)
                
                # 计算中心点
                M = cv2.moments(cnt)
                if M["m00"] == 0: 
                    continue
                    
                u = int(M["m10"] / M["m00"])
                v = int(M["m01"] / M["m00"])
                
                # 检查中心和半径是否一致 (确保是真正的圆)
                if abs(u - x) > 10 or abs(v - y) > 10 or radius < 10:
                    continue
                    
                # 添加到检测到的物体列表
                detected_items.append({
                    'contour': cnt, 
                    'center': (u, v), 
                    'radius': radius,
                    'color': color,
                    'circularity': circularity
                })

        # 处理并绘制所有检测到的物体
        for item in detected_items:
            u, v = item['center']
            contour = item['contour']
            color_name = item['color']
            radius = item['radius']
            
            # 在画面上绘制轮廓和中心点
            cv2.drawContours(frame, [contour], -1, (0, 255, 0), 2)
            cv2.circle(frame, (u, v), int(radius), (0, 255, 255), 2)
            cv2.circle(frame, (u, v), 5, (0, 0, 255), -1)
            cv2.putText(frame, color_name, (u-20, v-20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # === 修改的关键部分：使用直接几何变换 ===
            # 假设物体在固定高度平面上（根据实际工作距离调整）
            Z_cam = 400  # 单位：mm
            
            if self.camera_matrix is not None:
                # 获取相机内参
                fx = self.camera_matrix[0, 0]
                fy = self.camera_matrix[1, 1]
                cx = self.camera_matrix[0, 2]
                cy = self.camera_matrix[1, 2]
                
                # 计算归一化坐标
                x_normalized = (u - cx) / fx
                y_normalized = (v - cy) / fy
                
                # 计算相机坐标系中的3D坐标
                X_cam = x_normalized * Z_cam
                Y_cam = y_normalized * Z_cam
                camera_coords = np.array([X_cam, Y_cam, Z_cam])
                
                # 进行坐标系变换
                robot_coords = self.transform_to_robot_coords(camera_coords)
                
                if robot_coords is not None:
                    # 在画面上显示机器人坐标
                    coord_text = f"R:({robot_coords[0]:.0f},{robot_coords[1]:.0f},{robot_coords[2]:.0f})"
                    cv2.putText(frame, coord_text, (u, v + 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    
                    # 发送检测到的物体信息
                    target_info = {
                        'color': color_name,
                        'robot_coords': robot_coords.tolist(),
                        'pixel_coords': (u, v)
                    }
                    self.object_detected_robot_coords.emit(target_info)
        
        return frame
    def load_calibration(self, calibration_file):
        """加载相机标定参数"""
        try:
            calibration_data = np.load(calibration_file)
            self.camera_matrix = calibration_data['camera_matrix']
            self.dist_coeffs = calibration_data['dist_coeffs']
            print("成功加载相机标定参数")
        except Exception as e:
            print(f"无法加载标定参数: {e}")
            # 创建默认内参矩阵（近似值）
            self.camera_matrix = np.array([
                [1000, 0, 640/2],
                [0, 1000, 480/2],
                [0, 0, 1]
            ], dtype=np.float32)
            self.dist_coeffs = np.zeros((5, 1), dtype=np.float32)
    
    def undistort_frame(self, frame):
        """应用畸变校正"""
        if self.camera_matrix is not None and self.dist_coeffs is not None:
            h, w = frame.shape[:2]
            new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
                self.camera_matrix, self.dist_coeffs, (w, h), 1, (w, h)
            )
            return cv2.undistort(
                frame, self.camera_matrix, self.dist_coeffs, None, new_camera_matrix
            )
        return frame
    def run(self):
        """线程的主循环：捕获、处理并发送图像帧"""
        print(f"尝试打开摄像头: {self.cam_number}")
        
        # 尝试不同的API
        cap = None
        for api in [cv2.CAP_V4L2, cv2.CAP_ANY]:
            try:
                if isinstance(self.cam_number, int):
                    cap = cv2.VideoCapture(self.cam_number, api)
                else:  # 字符串路径
                    cap = cv2.VideoCapture(self.cam_number, api)
                    
                if cap.isOpened():
                    print(f"使用API {api} 成功打开摄像头")
                    break
            except:
                continue
        
        if cap is None or not cap.isOpened():
            print(f"错误：无法打开摄像头 {self.cam_number}")
            return
        
        # 设置分辨率
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # 打印实际分辨率
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"实际分辨率: {width}x{height}")
        
        self.is_running = True
        while self.is_running:
            ret, frame = cap.read()
            if not ret:
                print("读取帧失败")
                break
            
            try:
                # 应用畸变校正
                undistorted_frame = self.undistort_frame(frame)
                
                # 处理帧
                processed_frame = self.process_frame(undistorted_frame)
                
                # 转换并发送图像
                rgb_image = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                qt_image = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
                self.sendPicture.emit(qt_image)
            except Exception as e:
                print(f"处理帧时出错: {e}")
                import traceback
                traceback.print_exc()

        cap.release()
        print("摄像头线程退出")

    def stop(self):
        """停止线程"""
        self.is_running = False
        self.wait(500)


