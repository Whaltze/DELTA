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

class EnhancedShapeDetector:
    def __init__(self):
        # 形状模板缓存
        self.shape_templates = {}
        self.template_size = (64, 64)
        self.init_shape_templates()
        
        # 形状分类器权重
        self.feature_weights = {
            'circularity': 0.3,
            'rectangularity': 0.25,
            'solidity': 0.2,
            'aspect_ratio': 0.15,
            'contour_approximation': 0.1
        }
    
    def init_shape_templates(self):
        """初始化标准形状模板"""
        # 创建标准形状模板
        templates = {
            'Circle': self.create_circle_template(),
            'Square': self.create_square_template(),
            'Triangle': self.create_triangle_template()
        }
        
        for shape, template in templates.items():
            # 计算模板特征
            self.shape_templates[shape] = {
                'image': template,
                'features': self.extract_template_features(template),
                'contour': self.extract_template_contour(template)
            }
    
    def create_circle_template(self):
        """创建圆形模板"""
        template = np.zeros(self.template_size, dtype=np.uint8)
        center = (self.template_size[0]//2, self.template_size[1]//2)
        radius = min(self.template_size)//3
        cv2.circle(template, center, radius, 255, -1)
        return template
    
    def create_square_template(self):
        """创建正方形模板"""
        template = np.zeros(self.template_size, dtype=np.uint8)
        size = min(self.template_size)//2
        start_x = (self.template_size[0] - size)//2
        start_y = (self.template_size[1] - size)//2
        cv2.rectangle(template, (start_x, start_y), 
                      (start_x+size, start_y+size), 255, -1)
        return template
    
    def create_triangle_template(self):
        """创建三角形模板"""
        template = np.zeros(self.template_size, dtype=np.uint8)
        h, w = self.template_size
        points = np.array([
            [w//2, h//4],      # 顶点
            [w//4, 3*h//4],    # 左下
            [3*w//4, 3*h//4]   # 右下
        ], dtype=np.int32)
        cv2.fillPoly(template, [points], 255)
        return template
    
    def extract_template_features(self, template):
        """提取模板特征"""
        # 查找轮廓
        cnts, _ = cv2.findContours(template, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cnts:
            return {}
        
        contour = cnts[0]
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        features = {}
        
        # 圆度
        if perimeter > 0:
            features['circularity'] = (4 * np.pi * area) / (perimeter * perimeter)
        else:
            features['circularity'] = 0
        
        # 最小外接圆
        (center, radius) = cv2.minEnclosingCircle(contour)
        min_circle_area = np.pi * radius * radius
        if min_circle_area > 0:
            features['enclosing_circle_ratio'] = area / min_circle_area
        else:
            features['enclosing_circle_ratio'] = 0
        
        # 最小外接矩形
        rect = cv2.minAreaRect(contour)
        box = cv2.boxPoints(rect)
        box_area = cv2.contourArea(box.astype(np.int32))
        if box_area > 0:
            features['rectangularity'] = area / box_area
            width, height = rect[1]
            features['aspect_ratio'] = max(width, height) / (min(width, height) + 1e-5)
        else:
            features['rectangularity'] = 0
            features['aspect_ratio'] = 1
        
        # 多边形拟合
        epsilon = 0.04 * perimeter
        approx = cv2.approxPolyDP(contour, epsilon, True)
        features['vertices'] = len(approx)
        
        # 凸包
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        if hull_area > 0:
            features['solidity'] = area / hull_area
        else:
            features['solidity'] = 0
        
        return features
    
    def extract_template_contour(self, template):
        """提取模板轮廓"""
        cnts, _ = cv2.findContours(template, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if cnts:
            return cnts[0]
        return np.array([])
    
    def template_matching_score(self, contour, target_shape):
        """计算轮廓与模板的匹配分数"""
        # 提取轮廓区域
        x, y, w, h = cv2.boundingRect(contour)
        roi = np.zeros((h, w), dtype=np.uint8)
        cv2.drawContours(roi, [contour - [x, y]], -1, 255, -1)
        
        # 调整大小到模板尺寸
        roi_resized = cv2.resize(roi, self.template_size)
        
        # 模板匹配
        template = self.shape_templates[target_shape]['image']
        result = cv2.matchTemplate(roi_resized, template, cv2.TM_CCOEFF_NORMED)
        score = np.max(result)
        
        return score
    
    def calculate_contour_similarity(self, contour, target_shape):
        """计算轮廓相似度"""
        if target_shape not in self.shape_templates:
            return 0.0
        
        template_contour = self.shape_templates[target_shape]['contour']
        if len(template_contour) == 0:
            return 0.0
        
        # 使用Hu矩计算相似度
        moments1 = cv2.moments(contour)
        moments2 = cv2.moments(template_contour)
        
        hu1 = cv2.HuMoments(moments1)
        hu2 = cv2.HuMoments(moments2)
        
        # 计算Hu矩的差异
        diff = 0
        for i in range(7):
            if hu1[i] != 0 and hu2[i] != 0:
                diff += abs(hu1[i] - hu2[i]) / abs(hu1[i] + hu2[i] + 1e-5)
        
        # 转换为相似度分数
        similarity = 1.0 / (1.0 + diff)
        return similarity
    
    def enhanced_shape_classification(self, contour, area):
        """增强的形状分类算法"""
        # 1. 传统特征提取
        features = self.extract_comprehensive_features(contour, area)
        
        # 2. 多维度评分
        shape_scores = {}
        
        for shape_name in ['Circle', 'Square', 'Triangle']:
            # 传统特征评分
            traditional_score = self.calculate_traditional_score(features, shape_name)
            
            # 模板匹配评分
            template_score = self.template_matching_score(contour, shape_name)
            
            # 轮廓相似度评分
            contour_score = self.calculate_contour_similarity(contour, shape_name)
            
            # 加权综合评分
            final_score = (traditional_score * 0.4 + 
                          template_score * 0.4 + 
                          contour_score * 0.2)
            
            shape_scores[shape_name] = final_score
        
        # 选择最高分的形状
        best_shape = max(shape_scores, key=shape_scores.get)
        confidence = shape_scores[best_shape]
        
        # 设置置信度阈值
        if confidence < 0.6:
            return False, "Unknown", contour
        
        return True, best_shape, contour
    
    def extract_comprehensive_features(self, contour, area):
        """提取综合特征"""
        features = {}
        
        # 基础几何特征
        perimeter = cv2.arcLength(contour, True)
        
        # 圆度特征
        if perimeter > 0:
            circularity = (4 * np.pi * area) / (perimeter * perimeter)
            features['circularity'] = circularity
        else:
            features['circularity'] = 0
        
        # 最小外接圆特征
        (center, radius) = cv2.minEnclosingCircle(contour)
        min_circle_area = np.pi * radius * radius
        if min_circle_area > 0:
            features['enclosing_circle_ratio'] = area / min_circle_area
        else:
            features['enclosing_circle_ratio'] = 0
        
        # 最小外接矩形特征
        rect = cv2.minAreaRect(contour)
        box = cv2.boxPoints(rect)
        box_area = cv2.contourArea(box.astype(np.int32))
        if box_area > 0:
            features['rectangularity'] = area / box_area
            width, height = rect[1]
            features['aspect_ratio'] = max(width, height) / (min(width, height) + 1e-5)
        else:
            features['rectangularity'] = 0
            features['aspect_ratio'] = 1
        
        # 多边形拟合特征
        epsilon = 0.04 * perimeter
        approx = cv2.approxPolyDP(contour, epsilon, True)
        features['vertices'] = len(approx)
        
        # 凸包特征
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        if hull_area > 0:
            features['solidity'] = area / hull_area
        else:
            features['solidity'] = 0
        
        return features
    
    def calculate_traditional_score(self, features, shape_name):
        """基于传统特征的形状评分"""
        score = 0.0
        
        if shape_name == "Circle":
            # 圆形评分标准
            circularity = features.get('circularity', 0)
            enclosing_ratio = features.get('enclosing_circle_ratio', 0)
            score = (circularity * 0.6 + enclosing_ratio * 0.4)
            
        elif shape_name == "Square":
            # 正方形评分标准
            rectangularity = features.get('rectangularity', 0)
            aspect_ratio = features.get('aspect_ratio', 1)
            solidity = features.get('solidity', 0)
            
            # 长宽比接近1的程度
            aspect_score = 1.0 - abs(aspect_ratio - 1.0)
            score = (rectangularity * 0.4 + aspect_score * 0.3 + solidity * 0.3)
            
        elif shape_name == "Triangle":
            # 三角形评分标准
            vertices = features.get('vertices', 0)
            solidity = features.get('solidity', 0)
            
            if vertices == 3:
                score = solidity * 0.8 + 0.2
            else:
                score = 0.0
        
        return min(score, 1.0)


class EnhancedColorDetector:
    def __init__(self):
        # 多颜色空间配置
        self.color_spaces = {
            'HSV': self.get_hsv_ranges(),
            'LAB': self.get_lab_ranges(),
            'YCrCb': self.get_ycrcb_ranges()
        }
        
        # 光照补偿参数
        self.illumination_compensation = True
        self.adaptive_threshold = True
        
    def get_hsv_ranges(self):
        """优化后的HSV颜色范围"""
        return {
            'Red': [
                ([0, 120, 70], [10, 255, 255]),
                ([170, 120, 70], [180, 255, 255]),
                ([0, 100, 100], [15, 255, 255]),  # 扩展范围
                ([165, 100, 100], [180, 255, 255])
            ],
            'Yellow': [
                ([20, 100, 100], [35, 255, 255]),
                ([15, 80, 80], [40, 255, 255])  # 扩展黄色范围
            ],
            'Blue': [
                ([100, 150, 60], [140, 255, 255]),
                ([90, 120, 50], [150, 255, 255])  # 扩展蓝色范围
            ]
        }
    
    def get_lab_ranges(self):
        """LAB颜色空间范围"""
        return {
            'Red': [([0, 130, 130], [255, 255, 255])],
            'Yellow': [([0, 0, 150], [255, 255, 255])],
            'Blue': [([0, 0, 0], [255, 130, 130])]
        }
    
    def get_ycrcb_ranges(self):
        """YCrCb颜色空间范围"""
        return {
            'Red': [([0, 150, 0], [255, 255, 150])],
            'Yellow': [([0, 0, 150], [255, 150, 255])],
            'Blue': [([0, 0, 0], [255, 150, 150])]
        }
    
    def detect_color_in_space(self, converted, ranges):
        """在特定颜色空间中检测颜色"""
        if not ranges:
            return np.zeros(converted.shape[:2], dtype=np.uint8)
        
        combined_mask = np.zeros(converted.shape[:2], dtype=np.uint8)
        
        for (lower, upper) in ranges:
            lower_np = np.array(lower, dtype="uint8")
            upper_np = np.array(upper, dtype="uint8")
            mask = cv2.inRange(converted, lower_np, upper_np)
            combined_mask = cv2.bitwise_or(combined_mask, mask)
        
        return combined_mask
    
    def enhanced_color_detection(self, frame):
        """增强的颜色检测算法"""
        # 1. 光照补偿
        if self.illumination_compensation:
            frame = self.apply_illumination_compensation(frame)
        
        # 2. 多颜色空间融合检测
        color_masks = {}
        
        for color_name in ['Red', 'Yellow', 'Blue']:
            combined_mask = np.zeros(frame.shape[:2], dtype=np.uint8)
            
            # 在多个颜色空间中检测
            for space_name, ranges in self.color_spaces.items():
                if space_name == 'HSV':
                    converted = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                elif space_name == 'LAB':
                    converted = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
                elif space_name == 'YCrCb':
                    converted = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
                
                space_mask = self.detect_color_in_space(converted, ranges.get(color_name, []))
                combined_mask = cv2.bitwise_or(combined_mask, space_mask)
            
            # 3. 自适应阈值优化
            if self.adaptive_threshold:
                combined_mask = self.adaptive_mask_optimization(combined_mask, frame)
            
            color_masks[color_name] = combined_mask
        
        return color_masks
    
    def apply_illumination_compensation(self, frame):
        """光照补偿"""
        # 使用CLAHE进行自适应直方图均衡化
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        
        lab = cv2.merge([l, a, b])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    def adaptive_mask_optimization(self, mask, frame):
        """自适应掩码优化"""
        # 1. 形态学操作
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # 2. 基于边缘的优化
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # 将边缘信息融入掩码
        mask = cv2.bitwise_and(mask, cv2.bitwise_not(edges))
        
        return mask


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
            ],
            'Yellow': [
                ([20, 100, 100], [35, 255, 255]),  # 黄色主要范围
            ],
            'Blue': [
                ([100, 150, 60], [140, 255, 255]),  # 蓝色主要范围
            ],
        }

        # 新增增强检测器
        self.shape_detector = EnhancedShapeDetector()
        self.color_detector = EnhancedColorDetector()
        
        # 优化参数
        self.min_detection_confidence = 0.7
        self.enable_template_matching = True
        self.enable_multi_color_space = True

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

    def calculate_robot_coordinates(self, cX, cY):
        """计算机器人坐标"""
        fx, cx = self.camera_matrix[0, 0], self.camera_matrix[0, 2]
        fy, cy = self.camera_matrix[1, 1], self.camera_matrix[1, 2]
        X_cam = (cX - cx) * self.Z_cam_plane / fx
        Y_cam = (cY - cy) * self.Z_cam_plane / fy
        return self.transform_to_robot_coords(np.array([X_cam, Y_cam, self.Z_cam_plane]))

    def calculate_color_confidence(self, contour, color_name):
        """计算颜色置信度"""
        # 简化实现，基于颜色纯度
        return 0.8  # 占位符，可根据需要实现更复杂的逻辑

    def calculate_feature_confidence(self, features, shape_name):
        """计算特征置信度"""
        # 简化实现
        return 0.8  # 占位符，可根据需要实现更复杂的逻辑

    def calculate_overall_confidence(self, contour, shape_name, color_name):
        """计算综合置信度"""
        # 1. 形状置信度
        if self.enable_template_matching:
            template_score = self.shape_detector.template_matching_score(contour, shape_name)
        else:
            template_score = 0.5
        
        # 2. 颜色置信度（基于颜色纯度）
        color_confidence = self.calculate_color_confidence(contour, color_name)
        
        # 3. 形状特征置信度
        features = self.shape_detector.extract_comprehensive_features(contour, cv2.contourArea(contour))
        feature_confidence = self.calculate_feature_confidence(features, shape_name)
        
        # 4. 综合评分
        overall_confidence = (template_score * 0.4 + 
                            color_confidence * 0.3 + 
                            feature_confidence * 0.3)
        
        return overall_confidence

    def apply_tracking_and_filtering(self, frame, current_detections):
        """应用追踪和过滤"""
        # 使用原有的追踪逻辑
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
                confidence_boost = 2 * det['confidence']
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
                    'confidence': 1 * det['confidence'],  # 初始信心值考虑形状置信度
                    'lost_count': 0,
                    'matched': True,
                    'shape_confidence': det['confidence']
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

    def enhanced_preprocessing(self, frame):
        """增强的预处理"""
        # 1. 降噪
        frame = cv2.bilateralFilter(frame, 9, 75, 75)
        
        # 2. 锐化
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        frame = cv2.filter2D(frame, -1, kernel)
        
        # 3. 对比度增强
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        frame = cv2.merge([l, a, b])
        frame = cv2.cvtColor(frame, cv2.COLOR_LAB2BGR)
        
        return frame

    def process_frame(self, frame):
        """增强的帧处理函数"""
        # 1. 预处理
        frame = self.enhanced_preprocessing(frame)
        
        # 2. 增强颜色检测
        if self.enable_multi_color_space:
            color_masks = self.color_detector.enhanced_color_detection(frame)
        else:
            # 使用原有的颜色检测逻辑
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            color_masks = {}
            for color_name, ranges in self.color_thresholds.items():
                combined_mask = np.zeros(frame.shape[:2], dtype=np.uint8)
                for (lower, upper) in ranges:
                    lower_np = np.array(lower, dtype="uint8")
                    upper_np = np.array(upper, dtype="uint8")
                    mask = cv2.inRange(hsv, lower_np, upper_np)
                    combined_mask = cv2.bitwise_or(combined_mask, mask)
                color_masks[color_name] = combined_mask
        
        # 3. 形状检测
        current_detections = []
        
        for color_name, mask in color_masks.items():
            # 查找轮廓
            cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for c in cnts:
                area = cv2.contourArea(c)
                if area < 500 or area > 50000:
                    continue
                
                # 增强形状分类
                if self.enable_template_matching:
                    is_valid, shape_name, approx = self.shape_detector.enhanced_shape_classification(c, area)
                else:
                    # 使用原有的形状检测逻辑
                    is_valid, shape_name, approx = self.strict_shape_check(c, area)
                
                if not is_valid:
                    continue
                
                # 计算中心点和机器人坐标
                M = cv2.moments(c)
                if M["m00"] == 0:
                    continue
                    
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                
                # 坐标变换
                robot_pos = self.calculate_robot_coordinates(cX, cY)
                
                # 计算综合置信度
                confidence = self.calculate_overall_confidence(c, shape_name, color_name)
                
                current_detections.append({
                    'center': (cX, cY),
                    'color': color_name,
                    'shape': shape_name,
                    'contour': approx,
                    'robot_pos': robot_pos,
                    'confidence': confidence,
                    'area': area
                })
        
        # 4. 多帧追踪
        processed_frame = self.apply_tracking_and_filtering(frame, current_detections)
        
        return processed_frame

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

    def run(self):
        # 尝试不同后端，增加稳定性
        cap = cv2.VideoCapture(self.cam_number, cv2.CAP_V4L2)
        if not cap.isOpened():
            cap = cv2.VideoCapture(self.cam_number)
            
        if not cap.isOpened():
            print(f"Error: Camera {self.cam_number} cannot be opened.")
            return

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
