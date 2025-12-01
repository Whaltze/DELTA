# -*- coding: utf-8 -*-
# camera/camera.py
import cv2
import os
import numpy as np
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage
import glob
import time

class Camera(QThread):
    sendPicture = Signal(QImage)
    object_detected_robot_coords = Signal(dict)

    def __init__(self):
        super().__init__()
        self.cam_number = 0
        self.is_running = False
        
        # 默认手眼矩阵
        self.T_camera_to_robot = np.identity(4)
        self.transform_matrix_set = False

        self.camera_matrix = None
        self.dist_coeffs = None
        self.load_calibration('./camera/camera_calibration.npz')

    def set_cam_number(self, num):
        self.cam_number = num

    @staticmethod
    def scan_cameras():
        """
        稳健的摄像头扫描：只扫描存在的设备文件
        """
        available_cameras = []
        # Linux下直接查文件
        video_files = sorted(glob.glob('/dev/video*'))
        
        # 过滤掉一些不是摄像头的video设备(如果需要更精细的控制)
        # 这里简单地尝试打开
        for dev_path in video_files:
            try:
                # 提取数字
                idx = int(dev_path.replace('/dev/video', ''))
                # 尝试用 V4L2 打开测试
                cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
                if cap.isOpened():
                    available_cameras.append((idx, dev_path))
                    cap.release()
            except:
                pass
        
        # 如果什么都没扫到，尝试默认的0
        if not available_cameras:
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                available_cameras.append((0, "Default /dev/video0"))
                cap.release()
                
        return available_cameras

    def set_transform_matrix(self, x, y, z, roll, pitch, yaw):
        roll_rad, pitch_rad, yaw_rad = np.deg2rad([roll, pitch, yaw])

        Rx = np.array([[1, 0, 0], [0, np.cos(roll_rad), -np.sin(roll_rad)], [0, np.sin(roll_rad), np.cos(roll_rad)]])
        Ry = np.array([[np.cos(pitch_rad), 0, np.sin(pitch_rad)], [0, 1, 0], [-np.sin(pitch_rad), 0, np.cos(pitch_rad)]])
        Rz = np.array([[np.cos(yaw_rad), -np.sin(yaw_rad), 0], [np.sin(yaw_rad), np.cos(yaw_rad), 0], [0, 0, 1]])
        
        R = Rz @ Ry @ Rx
        
        self.T_camera_to_robot = np.identity(4)
        self.T_camera_to_robot[:3, :3] = R
        self.T_camera_to_robot[:3, 3] = [x, y, z]
        self.transform_matrix_set = True
        print(f"标定矩阵已更新:\n{self.T_camera_to_robot}")

    def transform_to_robot_coords(self, camera_coords):
        if not self.transform_matrix_set:
            return camera_coords 

        camera_coords_homogeneous = np.append(camera_coords, 1)
        robot_coords_homogeneous = self.T_camera_to_robot @ camera_coords_homogeneous
        return robot_coords_homogeneous[:3]

    def load_calibration(self, file_path):
        if os.path.exists(file_path):
            try:
                data = np.load(file_path)
                self.camera_matrix = data['camera_matrix']
                self.dist_coeffs = data['dist_coeffs']
            except:
                pass
        
        if self.camera_matrix is None:
            self.camera_matrix = np.array([[1000, 0, 320], [0, 1000, 240], [0, 0, 1]], dtype=np.float32)
            self.dist_coeffs = np.zeros((5, 1), dtype=np.float32)

    def process_frame(self, frame):
        blurred = cv2.GaussianBlur(frame, (5, 5), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        
        color_ranges = {
            'Red': [([0, 120, 70], [10, 255, 255]), ([170, 120, 70], [180, 255, 255])],
            'Yellow': [([20, 100, 100], [30, 255, 255])],
            'Blue': [([100, 150, 0], [140, 255, 255])],
            'Green': [([35, 43, 46], [77, 255, 255])]
        }

        for color_name, ranges in color_ranges.items():
            mask = np.zeros(hsv.shape[:2], dtype="uint8")
            for (lower, upper) in ranges:
                lower = np.array(lower, dtype="uint8")
                upper = np.array(upper, dtype="uint8")
                mask = cv2.bitwise_or(mask, cv2.inRange(hsv, lower, upper))
            
            mask = cv2.erode(mask, None, iterations=2)
            mask = cv2.dilate(mask, None, iterations=2)
            
            cnts, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for c in cnts:
                if cv2.contourArea(c) < 500: continue
                ((x, y), radius) = cv2.minEnclosingCircle(c)
                if radius > 10:
                    cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                    cv2.putText(frame, color_name, (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    
                    # 假设物体高度 Z_cam = 400 (需根据实际调整)
                    Z_cam = 400 
                    fx, cx = self.camera_matrix[0, 0], self.camera_matrix[0, 2]
                    fy, cy = self.camera_matrix[1, 1], self.camera_matrix[1, 2]
                    
                    X_cam = (x - cx) * Z_cam / fx
                    Y_cam = (y - cy) * Z_cam / fy
                    
                    robot_pos = self.transform_to_robot_coords(np.array([X_cam, Y_cam, Z_cam]))
                    
                    self.object_detected_robot_coords.emit({
                        'color': color_name,
                        'robot_coords': robot_pos.tolist(),
                        'pixel_coords': (x, y)
                    })
        return frame

    def run(self):
        # 尝试使用 V4L2 打开
        cap = cv2.VideoCapture(self.cam_number, cv2.CAP_V4L2)
        if not cap.isOpened():
            # 后备尝试
            cap = cv2.VideoCapture(self.cam_number)
            
        if not cap.isOpened():
            print(f"Error: Camera {self.cam_number} cannot be opened.")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.is_running = True
        while self.is_running:
            ret, frame = cap.read()
            if ret:
                try:
                    frame = self.process_frame(frame)
                    h, w, ch = frame.shape
                    qt_img = QImage(frame.data, w, h, ch * w, QImage.Format_BGR888)
                    self.sendPicture.emit(qt_img)
                except Exception as e:
                    print(f"Frame processing error: {e}")
            else:
                time.sleep(0.1)
                
        cap.release()

    def stop(self):
        self.is_running = False
        self.wait()