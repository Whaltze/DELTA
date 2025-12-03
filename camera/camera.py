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
        self.MAX_CONFIDENCE = 20      # 信心上限
        self.LOST_THRESHOLD = 3       # 连续丢失多少帧删除

        # --- 新增：目标过滤器 ---
        self.target_color = "Red"     # 默认值
        self.target_shape = "Square"  # 默认值
        
        # --- 新增：颜色检测多阈值配置 ---
        self.color_thresholds = {
            'Red': [
                ([0, 120, 70], [10, 255, 255]),  # 红色低范围
                ([170, 120, 70], [180, 255, 255]),  # 红色高范围
                ([0, 100, 50], [8, 255, 255]),  # 新增：红色宽松低范围
                ([172, 100, 50], [180, 255, 255])  # 新增：红色宽松高范围
            ],
            'Yellow': [
                ([20, 100, 100], [35, 255, 255]),  # 黄色主要范围
                ([15, 80, 80], [25, 255, 255]),    # 新增：黄色偏橙范围
                ([25, 80, 80], [40, 255, 255])     # 新增：黄色偏绿范围
            ],
            'Blue': [
                ([100, 150, 60], [140, 255, 255]),  # 蓝色主要范围
                ([90, 120, 50], [110, 255, 255]),   # 新增：蓝色偏青范围
                ([110, 120, 50], [130, 255, 255])   # 新增：蓝色偏紫范围
            ],
            # 如果需要绿色，可以取消注释并添加多阈值
            # 'Green': [([40, 70, 70], [80, 255, 255]), ([35, 50, 50], [45, 255, 255])]
        }

    # --- 新增：设置识别目标 ---
    def set_target_filter(self, color, shape):
        """设定只识别特定的颜色和形状"""
        self.target_color = color
        self.target_shape = shape
        print(f"[Camera] 目标锁定: {self.target_color} - {self.target_shape}")

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
    
    # --- 新增：改进的形状特征提取 ---
    def extract_shape_features(self, contour):
        """提取轮廓的形状特征用于更精确的分类"""
        features = {}
        
        # 1. 基础几何特征
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        # 2. 圆度特征 (多个圆度指标)
        if perimeter > 0:
            circularity = (4 * np.pi * area) / (perimeter * perimeter)
            features['circularity'] = circularity
        else:
            features['circularity'] = 0
        
        # 3. 最小外接圆特征
        (center, radius) = cv2.minEnclosingCircle(contour)
        min_circle_area = np.pi * radius * radius
        if min_circle_area > 0:
            features['enclosing_circle_ratio'] = area / min_circle_area
        else:
            features['enclosing_circle_ratio'] = 0
        
        # 4. 最小外接矩形特征
        rect = cv2.minAreaRect(contour)
        box = cv2.boxPoints(rect)
        box_area = cv2.contourArea(box.astype(np.int32))
        if box_area > 0:
            features['rectangularity'] = area / box_area
            # 长宽比
            width, height = rect[1]
            features['aspect_ratio'] = max(width, height) / (min(width, height) + 1e-5)
        else:
            features['rectangularity'] = 0
            features['aspect_ratio'] = 1
        
        # 5. 多边形拟合特征
        epsilon = 0.04 * perimeter
        approx = cv2.approxPolyDP(contour, epsilon, True)
        features['vertices'] = len(approx)
        
        # 6. 凸包特征
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        if hull_area > 0:
            features['solidity'] = area / hull_area
            features['hull_defects'] = len(hull) - len(contour) if len(contour) > len(hull) else 0
        else:
            features['solidity'] = 0
            features['hull_defects'] = 0
        
        # 7. 三角形特定特征
        if features['vertices'] == 3:
            # 计算三个内角
            p = [pt[0] for pt in approx]
            angles = []
            for i in range(3):
                a = np.linalg.norm(np.array(p[i-1]) - p[i])
                b = np.linalg.norm(np.array(p[(i+1)%3]) - p[i])
                c = np.linalg.norm(np.array(p[(i+1)%3]) - p[i-1])
                if a > 0 and b > 0:
                    angle = np.arccos((a*a + b*b - c*c) / (2*a*b + 1e-5))
                    angles.append(np.degrees(angle))
            features['triangle_angles'] = angles
            if angles:
                features['triangle_angle_std'] = np.std(angles)
                features['triangle_min_angle'] = min(angles)
                features['triangle_max_angle'] = max(angles)
        
        return features

    def strict_shape_check(self, contour, area):
        """
        高精度形状检测算法 (改进版)
        """
        shape = "Unknown"
        peri = cv2.arcLength(contour, True)
        if peri == 0: return False, shape, contour
        
        # 1. 凸包与实心度检查
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        if hull_area == 0: return False, shape, contour
        
        solidity = float(area) / hull_area
        
        # 提取形状特征
        features = self.extract_shape_features(contour)
        
        # 2. 多边形拟合精度 (针对不同形状使用不同精度)
        epsilon_multiplier = 0.04  # 默认值
        approx = None
        
        # 尝试不同拟合精度以提高识别率
        for eps in [0.03, 0.04, 0.05]:
            epsilon = eps * peri
            approx = cv2.approxPolyDP(contour, epsilon, True)
            vertices = len(approx)
            
            # 三角形检测 (优化)
            if vertices == 3:
                # 使用三角形特征进行验证
                if 'triangle_angles' in features:
                    angles = features['triangle_angles']
                    # 验证三角形角度合理性 (所有角在15-150度之间)
                    if all(15 <= angle <= 150 for angle in angles):
                        # 检查实心度和面积
                        if solidity > 0.85:  # 三角形实心度可稍低
                            shape = "Triangle"
                            break
                else:
                    # 备用三角形检测
                    p = [pt[0] for pt in approx]
                    cosines = []
                    for i in range(3):
                        cosines.append(self.angle_cos(p[i-1], p[i], p[(i+1)%3]))
                    if all(c < 0.9 and c > -0.9 for c in cosines) and solidity > 0.8:
                        shape = "Triangle"
                        break
            
            # 四边形检测
            elif vertices == 4:
                (x, y, w, h) = cv2.boundingRect(approx)
                ar = w / float(h)
                
                # 计算四个内角的余弦值
                p = [pt[0] for pt in approx]
                cosines = []
                for i in range(4):
                    cosines.append(abs(self.angle_cos(p[i-1], p[i], p[(i+1)%4])))
                max_cos = max(cosines)
                
                # 矩形/正方形检测
                if max_cos < 0.3: 
                    if 0.9 <= ar <= 1.1:  # 放宽正方形长宽比要求
                        shape = "Square"
                    else:
                        shape = "Rectangle" 
                    break
                # 如果是菱形等，可能形状不规则，继续尝试其他拟合精度
            
            # 圆形检测 (优化)
            elif vertices >= 5:  # 圆形通常有较多顶点
                # 使用多个圆形度指标
                circularity = features.get('circularity', 0)
                enclosing_ratio = features.get('enclosing_circle_ratio', 0)
                
                # 综合圆形度判断 (放宽条件以提高识别率)
                circular_score = (circularity * 0.5 + enclosing_ratio * 0.5)
                
                if circular_score > 0.75:  # 降低阈值
                    shape = "Circle"
                    break
                elif vertices >= 8 and circularity > 0.7:  # 对于顶点多的多边形
                    shape = "Circle"
                    break
        
        # 如果未识别，尝试使用最小外接圆方法检测圆形
        if shape == "Unknown" and features.get('circularity', 0) > 0.7:
            # 使用最小外接圆与轮廓面积比
            if features.get('enclosing_circle_ratio', 0) > 0.75:
                shape = "Circle"
                # 重新进行多边形拟合，精度更低以适应圆形
                epsilon = 0.05 * peri
                approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # 如果仍未识别，使用凸包顶点数进行简单分类
        if shape == "Unknown":
            hull_vertices = len(cv2.convexHull(contour, returnPoints=True))
            if hull_vertices == 3 and solidity > 0.8:
                shape = "Triangle"
            elif hull_vertices == 4 and solidity > 0.85:
                shape = "Square" if features.get('aspect_ratio', 1) < 1.2 else "Rectangle"
            elif hull_vertices > 6 and features.get('circularity', 0) > 0.65:
                shape = "Circle"
        
        # 最终检查：确保有有效的approx
        if approx is None:
            epsilon = 0.04 * peri
            approx = cv2.approxPolyDP(contour, epsilon, True)
        
        return shape != "Unknown", shape, approx

    def process_frame(self, frame):
        # 1. 增强预处理：自适应直方图均衡化提高对比度
        # 转换为HSV并均衡V通道
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        
        # 对亮度通道进行CLAHE均衡化
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        v_eq = clahe.apply(v)
        
        # 合并通道并转换回BGR进行后续处理
        hsv_eq = cv2.merge([h, s, v_eq])
        frame_eq = cv2.cvtColor(hsv_eq, cv2.COLOR_HSV2BGR)
        
        # 双边滤波保留边缘
        blurred = cv2.bilateralFilter(frame_eq, 9, 75, 75)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        
        # 本帧检测到的所有候选物体
        current_detections = []

        # 使用多阈值颜色检测
        for color_name, ranges in self.color_thresholds.items():
            # 创建多个掩码并合并
            masks = []
            for (lower, upper) in ranges:
                lower_np = np.array(lower, dtype="uint8")
                upper_np = np.array(upper, dtype="uint8")
                mask = cv2.inRange(hsv, lower_np, upper_np)
                masks.append(mask)
            
            # 合并所有阈值范围的掩码
            if masks:
                combined_mask = masks[0]
                for mask in masks[1:]:
                    combined_mask = cv2.bitwise_or(combined_mask, mask)
            else:
                continue
            
            # 改进的形态学操作
            kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            kernel_medium = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            
            # 先腐蚀去除小噪点
            mask_clean = cv2.erode(combined_mask, kernel_small, iterations=1)
            # 再膨胀连接相近区域
            mask_clean = cv2.dilate(mask_clean, kernel_medium, iterations=2)
            # 闭运算填充孔洞
            mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_CLOSE, kernel_medium, iterations=2)
            
            # 查找轮廓
            cnts, _ = cv2.findContours(mask_clean.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for c in cnts:
                area = cv2.contourArea(c)
                # 调整面积过滤范围，适应不同大小的形状
                if area < 500 or area > 50000: 
                    continue
                
                # 计算轮廓的外接矩形
                x, y, w, h = cv2.boundingRect(c)
                aspect_ratio = w / float(h)
                
                # 过滤过于细长的轮廓（可能是噪声）
                if aspect_ratio > 5 or aspect_ratio < 0.2:
                    continue
                
                # 严格形状检查
                is_valid, shape_name, approx_contour = self.strict_shape_check(c, area)
                
                if not is_valid: 
                    continue

                # 计算重心
                M = cv2.moments(c)
                if M["m00"] == 0: 
                    continue
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])

                # 计算机器人坐标
                fx, cx = self.camera_matrix[0, 0], self.camera_matrix[0, 2]
                fy, cy = self.camera_matrix[1, 1], self.camera_matrix[1, 2]
                X_cam = (cX - cx) * self.Z_cam_plane / fx
                Y_cam = (cY - cy) * self.Z_cam_plane / fy
                robot_pos = self.transform_to_robot_coords(np.array([X_cam, Y_cam, self.Z_cam_plane]))

                # 计算形状置信度（基于实心度和圆度）
                features = self.extract_shape_features(c)
                shape_confidence = 1.0
                
                if shape_name == "Triangle":
                    shape_confidence = min(features.get('solidity', 0.8) * 1.2, 1.0)
                elif shape_name == "Circle":
                    shape_confidence = min(features.get('circularity', 0.7) * 1.3, 1.0)
                elif shape_name == "Square":
                    shape_confidence = min(features.get('rectangularity', 0.85) * 1.1, 1.0)

                current_detections.append({
                    'center': (cX, cY),
                    'color': color_name,
                    'shape': shape_name,
                    'contour': approx_contour,
                    'robot_pos': robot_pos,
                    'shape_confidence': shape_confidence,
                    'area': area
                })

        # --- 多帧匹配与追踪（改进版）---
        
        # 1. 标记所有现有追踪器为"未匹配"
        for trk in self.trackers:
            trk['matched'] = False

        # 2. 将本帧检测结果与现有追踪器匹配
        for det in current_detections:
            matched = False
            best_match = None
            best_distance = float('inf')
            
            for idx, trk in enumerate(self.trackers):
                dist = math.hypot(det['center'][0] - trk['center'][0], 
                                 det['center'][1] - trk['center'][1])
                
                # 匹配条件：距离近 + 颜色相同 + 形状相同
                if (dist < self.MAX_TRACK_DIST and 
                    det['color'] == trk['color'] and 
                    det['shape'] == trk['shape'] and
                    dist < best_distance):
                    
                    best_distance = dist
                    best_match = idx
            
            if best_match is not None:
                # 更新追踪器
                trk = self.trackers[best_match]
                trk['center'] = det['center']
                trk['contour'] = det['contour']
                # 加权更新机器人坐标（新的检测结果权重更高）
                trk['robot_pos'] = det['robot_pos'] * 0.4 + trk['robot_pos'] * 0.6
                # 根据形状置信度调整信心值增加量
                confidence_boost = 2 * det['shape_confidence']
                trk['confidence'] = min(trk['confidence'] + confidence_boost, self.MAX_CONFIDENCE)
                trk['lost_count'] = 0
                trk['matched'] = True
                matched = True
            
            # 如果是新出现的物体，创建新追踪器
            if not matched:
                self.trackers.append({
                    'center': det['center'],
                    'color': det['color'],
                    'shape': det['shape'],
                    'contour': det['contour'],
                    'robot_pos': det['robot_pos'],
                    'confidence': 1 * det['shape_confidence'],  # 初始信心值考虑形状置信度
                    'lost_count': 0,
                    'matched': True,
                    'shape_confidence': det['shape_confidence']
                })

        # 3. 处理未匹配的追踪器
        for trk in self.trackers:
            if not trk['matched']:
                trk['lost_count'] += 1
                trk['confidence'] = max(trk['confidence'] - 1, 0)

        # 4. 清理无效追踪器
        self.trackers = [t for t in self.trackers if t['lost_count'] < self.LOST_THRESHOLD and t['confidence'] > 0]

        # --- 筛选最优结果 ---
        # 1. 收集所有符合置信度要求的对象
        valid_candidates = []
        for trk in self.trackers:
            if trk['confidence'] >= self.CONFIDENCE_THRESHOLD:
                # 绘制轮廓
                cv2.drawContours(frame, [trk['contour']], -1, (0, 255, 0), 2)
                
                # 绘制形状标签
                cX, cY = trk['center']
                label = f"{trk['color']} {trk['shape']}"
                cv2.putText(frame, label, (cX - 30, cY - 30), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                
                # 过滤条件：如果设定了目标，只选择匹配的目标
                if self.target_color and trk['color'] != self.target_color:
                    continue
                if self.target_shape and trk['shape'] != self.target_shape:
                    continue
                
                valid_candidates.append(trk)

        # 2. 如果有候选者，选出最佳目标
        if valid_candidates:
            # 按综合评分排序：置信度 * 形状置信度
            valid_candidates.sort(key=lambda x: x['confidence'] * x.get('shape_confidence', 1.0), reverse=True)
            
            # 选择最佳目标
            best_target = valid_candidates[0]
            
            # 绘制特殊标记
            cX, cY = best_target['center']
            label = f"TARGET: {best_target['color']} {best_target['shape']}"
            cv2.putText(frame, label, (cX - 20, cY - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.circle(frame, (cX, cY), 8, (0, 0, 255), -1)
            
            # 绘制目标边界框
            rect = cv2.minAreaRect(best_target['contour'])
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            cv2.drawContours(frame, [box], 0, (0, 0, 255), 2)

            # 发送信号
            self.object_detected_robot_coords.emit({
                'color': best_target['color'],
                'shape': best_target['shape'],
                'robot_coords': best_target['robot_pos'].tolist(),
                'pixel_coords': (cX, cY),
                'confidence': best_target['confidence'],
                'shape_confidence': best_target.get('shape_confidence', 1.0)
            })
        
        # 在画面上显示统计信息
        cv2.putText(frame, f"Trackers: {len(self.trackers)}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(frame, f"Target: {self.target_color} {self.target_shape}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        return frame

    def run(self):
        # 尝试不同后端，增加稳定性
        cap = cv2.VideoCapture(self.cam_number, cv2.CAP_V4L2)
        if not cap.isOpened():
            cap = cv2.VideoCapture(self.cam_number)
            
        if not cap.isOpened():
            print(f"Error: Camera {self.cam_number} cannot be opened.")
            return

        # 设置相机参数以获得更好图像质量
        # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        # cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)  # 关闭自动曝光
        # cap.set(cv2.CAP_PROP_EXPOSURE, -1)      # 手动设置曝光 -1 ~ -13 数值越小,亮度越低
        # cap.set(cv2.CAP_PROP_BRIGHTNESS, 0)    # 亮度
        # cap.set(cv2.CAP_PROP_CONTRAST, 50)      # 对比度
        # cap.set(cv2.CAP_PROP_SATURATION, 30)    # 饱和度
        
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
        