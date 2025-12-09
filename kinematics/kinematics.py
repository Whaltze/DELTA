# -*- coding: utf-8 -*-
# kinematics.py
# 线性Delta (Linear Delta / P副) 机器人运动学解算类

import math
import numpy as np

class DeltaKinematics:
    """
    线性Delta (Linear Delta) 机器人运动学计算类。
    适用于使用丝杆或同步带驱动滑块上下移动的架构 (P副)。
    
    坐标系定义：
    - 原点(0,0,0)位于底座中心（三根立柱的中心）。
    - Z轴垂直向上。
    - 滑块在立柱上移动，计算结果为滑块相对于Z=0平面的高度。
    """

    def __init__(self, sp, ep, rod_length, z_max=0, z_min=-337, joint_angle_limit=None):
        """
        参数:
        sp (float): 静平台（立柱）的外接圆半径 (或中心到立柱的水平距离)。
        ep (float): 动平台（末端执行器）的半径 (或中心到连杆连接点的水平距离)。
        rod_length (float): 连杆（斜杆）长度 (Diagonal Rod)。
        """
        self.R = sp  # 立柱分布半径
        self.r = ep  # 动平台半径
        self.L = rod_length  # 连杆长度
        
        # 线性Delta的关键几何参数：等效水平半径
        # 模型简化为：立柱在 Radius = R-r 的圆上，动平台视为一个点
        self.delta_r = self.R - self.r
        
        self.z_max = z_max
        self.z_min = z_min

        # 滑块工作空间限位
        self.slider_z_min = -337.0  # 滑块下限
        self.slider_z_max = -30.0   # 滑块上限
        
        # 动平台工作空间限位
        self.platform_z_min = -590.0  # 动平台下限
        self.platform_z_max = -390.0     # 动平台上限
        
        # 预计算三根立柱的角度位置 (假设分布为 0, 120, 240 度，或 90, 210, 330)
        # 通常线性Delta立柱位于：Tower A (210 or -30?), Tower B (90), Tower C (330 or -150)
        # 这里为了通用，假设标准分布：
        # Tower 1: alpha = -90 (或者根据你的实际装配调整，这里假设 Y轴正向对应一个柱子或X轴)
        # 常用配置：A柱在Y轴正向(90度)，B柱(330度/-30度)，C柱(210度/-150度)
        # 或者：A(0), B(120), C(240)。
        # **重要**：这里采用标准数学推导常用的 0, 120, 240 分布，如果不符需修改 towers_angle
        self.towers_angle = np.deg2rad([0, 120, 240]) 
        
        # 计算立柱的XY坐标 (立柱半径 R_eff = R)
        # 注意：IK计算中通常使用 effective radius (R-r)，这里为了画图和计算分开处理
        # 逆解核心公式中，我们直接将动平台坐标投射到立柱平面
    
    def inverse_kinematics(self, P):
        """
        逆解：已知末端坐标 P(x,y,z)，求三个滑块的高度 (z1, z2, z3)
        """
        x, y, z = P[0], P[1], P[2]
        
        sliders_z = []
        
        for angle in self.towers_angle:
            # 1. 将末端坐标旋转到当前立柱的局部坐标系 (使立柱位于 X 轴正方向)
            # 或者更简单的：计算末端点到立柱所在垂直平面的距离
            
            # 立柱坐标 (在 Z=0 平面)
            tower_x = self.delta_r * math.cos(angle)
            tower_y = self.delta_r * math.sin(angle)
            
            # 计算水平距离差 (Horizontal Distance)
            # dist_xy = sqrt((x - tower_x)^2 + (y - tower_y)^2)
            # 这种简单距离公式只适用于 连杆也是球铰连接的情况
            
            # 标准线性Delta逆解公式：
            # 连杆投影在XY平面的长度 d_xy
            # d_xy^2 + d_z^2 = L^2
            # d_z = slider_z - z
            
            dx = x - tower_x
            dy = y - tower_y
            d_xy_sq = dx*dx + dy*dy
            
            # 检查是否超出连杆长度
            diff = self.L**2 - d_xy_sq
            if diff < 0:
                return None # 不可达
            
            dz = math.sqrt(diff)
            
            # 滑块高度 = 末端z + 垂直高度差
            # 线性Delta通常滑块在上方，所以 slider_z = z + dz
            sliders_z.append(z + dz)
            
        return np.array(sliders_z)

    def forward_kinematics(self, sliders_z):
        """
        正解：已知三个滑块高度，求末端坐标 (x,y,z)
        这是“三球交汇”问题。
        """
        if sliders_z is None: return None
        z1, z2, z3 = sliders_z
        
        # 三个球心坐标 (立柱位置, 高度zi)
        # 球半径均为 L
        # 简化计算：设有效半径 dr = R - r
        dr = self.delta_r
        
        # 球心坐标
        c1 = np.array([dr * math.cos(self.towers_angle[0]), dr * math.sin(self.towers_angle[0]), z1])
        c2 = np.array([dr * math.cos(self.towers_angle[1]), dr * math.sin(self.towers_angle[1]), z2])
        c3 = np.array([dr * math.cos(self.towers_angle[2]), dr * math.sin(self.towers_angle[2]), z3])
        
        # 使用三球交汇算法求解 (Trilateration)
        # 这里使用一个通用的数值解法或几何解法
        # 为了代码简洁和鲁棒性，这里使用简化的几何推导：
        # 假设球心位于一个圆柱面上
        
        # 算法参考：Linear Delta Forward Kinematics (Kossel)
        # yj = (y2 - y1)*x3 - (y3 - y1)*x2
        # ... 标准几何解法比较繁琐，这里使用 numpy 最小二乘法迭代求解会更稳定，
        # 但为了实时性，我们尝试代数解。
        
        # 下面采用一种广泛使用的线性Delta正解算法
        p1 = c1
        p2 = c2
        p3 = c3
        
        # 变换坐标系使得 p1 在原点? 不，直接解方程组：
        # (x-x1)^2 + (y-y1)^2 + (z-z1)^2 = L^2
        # ...
        
        # 简化逻辑：取平均高度作为初始猜测，利用牛顿迭代法快速收敛（通常2-3次即可）
        # 或者利用 geometric intersection circle of two spheres -> intersection with third
        
        # 为了保证代码在 code interpreter 运行无误，我写一个基于迭代的解法（非常快且鲁棒）
        x, y, z = 0.0, 0.0, np.mean(sliders_z) - math.sqrt(self.L**2 - dr**2) # 初始猜测
        
        for i in range(10): # 迭代
            f = []
            J = [] # 雅可比矩阵
            
            for center in [c1, c2, c3]:
                d = np.array([x, y, z]) - center
                dist_sq = np.dot(d, d)
                f.append(dist_sq - self.L**2)
                J.append(2 * d)
            
            f = np.array(f)
            J = np.array(J)
            
            if np.linalg.cond(J) > 1e10: # 防止奇异
                return None
                
            delta = np.linalg.solve(J, -f)
            x += delta[0]
            y += delta[1]
            z += delta[2]
            
            if np.linalg.norm(delta) < 1e-4:
                return np.array([x, y, z])
                
        return np.array([x, y, z])
    def check_limits(self, position=None, sliders=None):
        """
        检查位置或滑块是否在限位范围内
        参数:
        position (list): 动平台位置 [x, y, z]
        sliders (list): 滑块位置 [s1, s2, s3]
        
        返回:
        bool: 是否在限位范围内
        str: 错误信息（如果超出限位）
        """
        try:
            # 检查滑块限位
            if sliders is not None:
                for i, slider_z in enumerate(sliders):
                    if slider_z < self.z_min:
                        return False, f"滑块{i+1}超出下限: {slider_z:.1f} < {self.z_min}"
                    if slider_z > self.z_max:
                        return False, f"滑块{i+1}超出上限: {slider_z:.1f} > {self.z_max}"
            
            # 检查工作空间限位
            if position is not None:
                x, y, z = position
                # 计算工作空间半径
                max_radius = self.delta_r + math.sqrt(self.L**2 - self.z_min**2)
                radius = math.sqrt(x**2 + y**2)
                
                if radius > max_radius:
                    return False, f"工作空间超出半径: {radius:.1f} > {max_radius:.1f}"
                if z < self.z_min:
                    return False, f"Z轴超出下限: {z:.1f} < {self.z_min}"
                if z > self.z_max:
                    return False, f"Z轴超出上限: {z:.1f} > {self.z_max}"
            
            return True, ""
        except Exception as e:
            return False, f"限位检查失败: {str(e)}"

