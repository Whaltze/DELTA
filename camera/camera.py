# -*- coding: utf-8 -*-
# camera/camera.py
import cv2
import os
import numpy as np
import math
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
        
        # 坐标变换相关
        self.T_camera_to_robot = np.identity(4)
        self.transform_matrix_set = False
        self.camera_matrix = None
        self.dist_coeffs = None
        self.Z_cam_plane = 400.0 
        self.load_calibration('./camera/camera_calibration.npz')

        # --- 新增：多帧追踪缓冲区 ---
        # 结构: list of dict {'center': (x,y), 'color': str, 'shape': str, 'confidence': int, 'robot_pos': np.array}
        self.trackers = [] 
        self.MAX_TRACK_DIST = 30  # 像素距离，认定为同一个物体的最大位移
        self.CONFIDENCE_THRESHOLD = 5 # 连续识别多少帧才输出
        self.MAX_CONFIDENCE = 15      # 信心上限
        self.LOST_THRESHOLD = 3       # 连续丢失多少帧删除

    def set_cam_number(self, num):
        self.cam_number = num

    @staticmethod
    def scan_cameras():
        available_cameras = []
        video_files = sorted(glob.glob('/dev/video*'))
        for dev_path in video_files:
            try:
                idx = int(dev_path.replace('/dev/video', ''))
                cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
                if cap.isOpened():
                    available_cameras.append((idx, dev_path))
                    cap.release()
            except:
                pass
        if not available_cameras:
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                available_cameras.append((0, "Default /dev/video0"))
                cap.release()
        return available_cameras
    
    def set_transform_matrix(self, x, y, z, roll, pitch, yaw):
        print(f"[Camera] Receiving Transform: X={x} Y={y} Z={z} R={roll} P={pitch} Y={yaw}")
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

    # --- 新增：计算三个点之间的夹角余弦 ---
    def angle_cos(self, p0, p1, p2):
        d1, d2 = np.array(p0) - p1, np.array(p2) - p1
        lens1 = np.linalg.norm(d1)
        lens2 = np.linalg.norm(d2)
        if lens1 == 0 or lens2 == 0: return 0.0
        return np.dot(d1, d2) / (lens1 * lens2)

    def strict_shape_check(self, contour, area):
        """
        高精度形状检测算法 (增加角度检测和多帧滤波准备)
        """
        shape = "Unknown"
        peri = cv2.arcLength(contour, True)
        if peri == 0: return False, shape, contour
        
        # 1. 凸包与实心度 (Solidity) 检查 - 过滤不规则碎片
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        if hull_area == 0: return False, shape, contour
        
        solidity = float(area) / hull_area
        # 规则图形 Solidity 通常非常接近 1.0 (三角形可能稍低，但也在0.9以上)
        if solidity < 0.88: 
            return False, "Irregular", contour

        # 2. 多边形拟合精度
        # 使用 peri * 0.04 是经验值，若想更严格，可降低系数例如 0.03
        epsilon = 0.04 * peri
        approx = cv2.approxPolyDP(contour, epsilon, True)
        vertices = len(approx)

        # 3. 几何角度与长宽比判定
        if vertices == 3:
            # 进一步验证是否为三角形：角度不能太小（排除极度扁平的三角形）
            p = [pt[0] for pt in approx]
            cosines = []
            for i in range(3):
                cosines.append(self.angle_cos(p[i-1], p[i], p[(i+1)%3]))
            # 所有的角的余弦值应该在 -0.9 到 0.9 之间 (排除接近180度或0度的角)
            if all(c < 0.95 and c > -0.95 for c in cosines):
                shape = "Triangle"
            else:
                return False, "Deformed_Tri", approx

        elif vertices == 4:
            (x, y, w, h) = cv2.boundingRect(approx)
            ar = w / float(h)
            
            # 计算最大余弦值，检查是否接近直角 (cos90 = 0)
            p = [pt[0] for pt in approx]
            cosines = []
            for i in range(4):
                cosines.append(abs(self.angle_cos(p[i-1], p[i], p[(i+1)%4])))
            max_cos = max(cosines)
            
            # 最大余弦值越小，说明越接近矩形（最大允许偏差约 18度 -> cos=0.3）
            if max_cos < 0.3: 
                if 0.85 <= ar <= 1.15:
                    shape = "Square"
                else:
                    # 也可以根据需求返回 Rectangle，这里只要求正方形
                    shape = "Rectangle" 
            else:
                # 可能是菱形或梯形
                return False, "Polygon4", approx

        else:
            # 圆度 (Circularity) 检测
            circularity = (4 * np.pi * area) / (peri * peri)
            # 增加对 vertices 数量的限制，圆经过多边形拟合顶点通常 > 5
            if vertices > 5 and circularity > 0.82:
                shape = "Circle"
            else:
                return False, "Polygon_N", approx
        
        return True, shape, approx

    def process_frame(self, frame):
        # 1. 预处理：保留边缘去噪
        blurred = cv2.bilateralFilter(frame, 9, 75, 75)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        
        # 调整后的颜色范围 (更精准)
        color_ranges = {
            'Red': [([0, 120, 70], [10, 255, 255]), ([170, 120, 70], [180, 255, 255])],
            'Yellow': [([20, 100, 100], [35, 255, 255])],
            'Blue': [([100, 150, 60], [140, 255, 255])], 
            # 'Green': [([40, 70, 70], [80, 255, 255])] # 如果不需要绿色可以注释掉减少干扰
        }

        # 本帧检测到的所有候选物体
        current_detections = []

        for color_name, ranges in color_ranges.items():
            mask = np.zeros(hsv.shape[:2], dtype="uint8")
            for (lower, upper) in ranges:
                lower = np.array(lower, dtype="uint8")
                upper = np.array(upper, dtype="uint8")
                mask = cv2.bitwise_or(mask, cv2.inRange(hsv, lower, upper))
            
            # 形态学操作：先腐蚀后膨胀(开运算)去除噪点，再膨胀后腐蚀(闭运算)填充孔洞
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            
            cnts, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for c in cnts:
                area = cv2.contourArea(c)
                # 严格的面积过滤，排除太小和太大的物体
                if area < 2000 or area > 40000: continue
                
                # 严格形状检查
                is_valid, shape_name, approx_contour = self.strict_shape_check(c, area)
                
                if not is_valid: 
                    continue

                # 计算重心
                M = cv2.moments(c)
                if M["m00"] == 0: continue
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])

                # 计算机器人坐标 (暂存，还未发送)
                fx, cx = self.camera_matrix[0, 0], self.camera_matrix[0, 2]
                fy, cy = self.camera_matrix[1, 1], self.camera_matrix[1, 2]
                X_cam = (cX - cx) * self.Z_cam_plane / fx
                Y_cam = (cY - cy) * self.Z_cam_plane / fy
                robot_pos = self.transform_to_robot_coords(np.array([X_cam, Y_cam, self.Z_cam_plane]))

                current_detections.append({
                    'center': (cX, cY),
                    'color': color_name,
                    'shape': shape_name,
                    'contour': approx_contour,
                    'robot_pos': robot_pos
                })

        # --- 核心算法升级：多帧匹配与追踪 ---
        
        # 1. 标记所有现有追踪器为"未匹配"
        for trk in self.trackers:
            trk['matched'] = False

        # 2. 将本帧检测结果与现有追踪器匹配 (基于欧氏距离)
        for det in current_detections:
            matched = False
            for trk in self.trackers:
                dist = math.hypot(det['center'][0] - trk['center'][0], det['center'][1] - trk['center'][1])
                
                # 匹配条件：距离近 + 颜色相同 + 形状相同
                if dist < self.MAX_TRACK_DIST and det['color'] == trk['color'] and det['shape'] == trk['shape']:
                    # 更新追踪器
                    trk['center'] = det['center'] # 更新中心点
                    trk['contour'] = det['contour']
                    trk['robot_pos'] = det['robot_pos'] * 0.3 + trk['robot_pos'] * 0.7 # 简单的坐标低通滤波，平滑数值
                    trk['confidence'] = min(trk['confidence'] + 2, self.MAX_CONFIDENCE) # 增加信心值
                    trk['lost_count'] = 0 # 重置丢失计数
                    trk['matched'] = True
                    matched = True
                    break
            
            # 如果是新出现的物体，创建新追踪器
            if not matched:
                self.trackers.append({
                    'center': det['center'],
                    'color': det['color'],
                    'shape': det['shape'],
                    'contour': det['contour'],
                    'robot_pos': det['robot_pos'],
                    'confidence': 1,
                    'lost_count': 0,
                    'matched': True
                })

        # 3. 处理未匹配的追踪器 (信心值衰减)
        for trk in self.trackers:
            if not trk['matched']:
                trk['lost_count'] += 1
                trk['confidence'] -= 1

        # 4. 清理无效追踪器 (丢失太久或信心归零)
        self.trackers = [t for t in self.trackers if t['lost_count'] < self.LOST_THRESHOLD and t['confidence'] > 0]

        # 5. 绘制并输出高置信度的结果
        for trk in self.trackers:
            if trk['confidence'] >= self.CONFIDENCE_THRESHOLD:
                # 绘制
                cX, cY = trk['center']
                cv2.drawContours(frame, [trk['contour']], -1, (0, 255, 0), 2)
                label = f"{trk['color']} {trk['shape']}"
                cv2.putText(frame, label, (cX - 20, cY - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.circle(frame, (cX, cY), 5, (255, 255, 255), -1)

                # 发送信号 (使用滤波后的坐标)
                self.object_detected_robot_coords.emit({
                    'color': trk['color'],
                    'shape': trk['shape'],
                    'robot_coords': trk['robot_pos'].tolist(),
                    'pixel_coords': (cX, cY)
                })
        
        return frame

    def run(self):
        # 尝试不同后端，增加稳定性
        cap = cv2.VideoCapture(self.cam_number, cv2.CAP_V4L2)
        if not cap.isOpened():
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
                    # 确保图像格式正确
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