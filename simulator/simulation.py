# -*- coding: utf-8 -*-
# simulator/simulation.py
"""
Delta机器人(P副/线性) 3D 高级仿真模块 - 工程美学版
包含：
1. 双平行连杆结构
2. 球头关节渲染
3. 精确对齐的六边形机架
4. 工业级配色方案
"""

import numpy as np
import pyqtgraph.opengl as gl
from PySide6.QtWidgets import QWidget, QVBoxLayout
import math

class DeltaSimulator(QWidget):
    def __init__(self, kinematics, parent=None):
        super().__init__(parent)
        self.kinematics = kinematics
        
        # --- 工业配色方案 (RGBA) ---
        self.COLOR_BG = '#1e1e1e'          # 深灰背景
        self.COLOR_GRID = (0.3, 0.3, 0.3, 1)
        # self.COLOR_FRAME = (0.6, 0.6, 0.65, 1)  # 铝型材银灰色
        # self.COLOR_TOWER = (0.8, 0.8, 0.85, 1)  # 光轴/导轨亮银色
        # self.COLOR_SLIDER = (1.0, 0.55, 0.0, 1) # 安全橙色滑块
        # self.COLOR_ROD = (0.1, 0.1, 0.1, 1)     # 碳纤维黑色
        # self.COLOR_JOINT = (0.0, 0.7, 1.0, 1)   # 阳极氧化蓝关节
        # self.COLOR_PLATFORM = (0.2, 0.2, 0.2, 1)# 动平台深色
        # self.COLOR_TRAJ = (0.0, 1.0, 0.5, 0.5)  # 轨迹荧光绿
        self.COLOR_FRAME = (0.95, 0.95, 0.2, 1)   # 明亮黄色框架
        self.COLOR_TOWER = (0.2, 0.8, 0.9, 1)    # 天蓝色立柱
        self.COLOR_SLIDER = (1.0, 0.2, 0.6, 1)   # 亮粉色滑块
        self.COLOR_ROD = (0.5, 0.0, 0.8, 1)      # 紫色连杆
        self.COLOR_JOINT = (0.0, 1.0, 0.0, 1)    # 亮绿色关节
        self.COLOR_PLATFORM = (1.0, 0.4, 0.0, 1) # 橙红色动平台
        self.COLOR_TRAJ = (1.0, 0.0, 1.0, 0.5)   # 紫红色轨迹

        # 窗口布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建 3D 视图
        self.view = gl.GLViewWidget()
        self.view.setBackgroundColor(self.COLOR_BG)
        self.view.setCameraPosition(distance=900, elevation=25, azimuth=45)
        self.view.pan(0, 0, -300)
        self.layout.addWidget(self.view)

        # 几何参数缓存
        self.R = kinematics.R  # 立柱半径
        self.r = kinematics.r  # 动平台半径
        self.L = kinematics.L  # 连杆长度
        
        # 视觉参数
        self.rod_spacing = 50.0  # 双连杆之间的间距 (mm)
        self.frame_radius = self.R * 1.15 # 框架稍微比立柱大一点，包住立柱
        
        # 绘图对象引用
        self.slider_items = []    # 滑块列表
        self.rod_lines = []       # 连杆列表 (每组2根)
        self.joint_points = []    # 关节列表 (每组4个点: 上2下2)
        self.platform_item = None # 动平台
        
        self.current_sliders_z = [0, 0, 0] 
        
        self._init_scene()

    def _init_scene(self):
        """初始化静态场景"""
        # 1. 地面网格
        g = gl.GLGridItem()
        g.setSize(x=800, y=800, z=0)
        g.setSpacing(x=100, y=100, z=0)
        g.translate(0, 0, -800)
        g.setColor(self.COLOR_GRID)
        self.view.addItem(g)
        
        # 2. 坐标轴 (缩小一点，显得精致)
        axis = gl.GLAxisItem()
        axis.setSize(50, 50, 50)
        self.view.addItem(axis)

        # 3. 绘制机架
        self._draw_structure()

        # 4. 初始化动件
        self._init_movable_parts()

    def _draw_structure(self):
        """绘制符合工程美学的机架"""
        h_top = 100
        h_bottom = -500
        
        # --- 生成六边形 ---
        # 技巧：我们要让六边形的顶点正好落在立柱的角度上
        # 立柱角度通常是 0, 120, 240 (或90, 210, 330)
        # 六边形有6个角，每隔60度一个。如果立柱间隔120度，正好占据 1, 3, 5 号顶点。
        
        angles = self.kinematics.towers_angle # [rad, rad, rad]
        # 假设第一个立柱在 angles[0]，我们需要生成一个包含这些角度的六边形
        # 这里为了通用性，直接画两层六边形框架
        
        def draw_hex_ring(z_height, color, width):
            pts = []
            # 起始角度偏移，确保平边或者顶点对齐
            # 这里让顶点对齐立柱：立柱在 angle[0]，六边形顶点也就从 angle[0] 开始
            start_angle = angles[0] 
            for i in range(7):
                ang = start_angle + math.radians(i * 60)
                x = self.frame_radius * math.cos(ang)
                y = self.frame_radius * math.sin(ang)
                pts.append([x, y, z_height])
            
            item = gl.GLLinePlotItem(pos=np.array(pts), width=width, color=color, antialias=True)
            self.view.addItem(item)

        # 顶部框架 (双层圈，更有厚重感)
        draw_hex_ring(h_top, self.COLOR_FRAME, 8)
        draw_hex_ring(h_top - 10, self.COLOR_FRAME, 3)

        # 底部框架
        draw_hex_ring(h_bottom, self.COLOR_FRAME, 8)
        
        # --- 绘制三根立柱 (光轴) ---
        for angle in angles:
            # 立柱位置
            x = self.R * math.cos(angle)
            y = self.R * math.sin(angle)
            
            # 1. 导轨主杆
            line_data = np.array([[x, y, h_bottom], [x, y, h_top]])
            tower = gl.GLLinePlotItem(pos=line_data, width=10, color=self.COLOR_TOWER, antialias=True)
            self.view.addItem(tower)
            
            # 2. 增加立柱底座和顶盖的装饰点
            caps = gl.GLScatterPlotItem(
                pos=np.array([[x, y, h_bottom], [x, y, h_top]]), 
                size=10, color=self.COLOR_FRAME, pxMode=True
            )
            self.view.addItem(caps)

    def _init_movable_parts(self):
        """初始化运动部件：双连杆、关节、滑块"""
        angles = self.kinematics.towers_angle
        
        for i in range(3):
            # --- 1. 滑块 (Slider) ---
            # 使用 ScatterPlot 模拟方块 (size大一点)
            # 初始位置设为 0
            tx = self.R * math.cos(angles[i])
            ty = self.R * math.sin(angles[i])
            
            slider = gl.GLScatterPlotItem(
                pos=np.array([[tx, ty, 0]]), 
                size=25, color=self.COLOR_SLIDER, pxMode=True
            )
            self.view.addItem(slider)
            self.slider_items.append(slider)
            
            # --- 2. 双平行连杆 (Parallel Rods) ---
            # 这是一个包含两条线的对象
            rods = gl.GLLinePlotItem(width=8, color=self.COLOR_ROD, mode='lines', antialias=True)
            self.view.addItem(rods)
            self.rod_lines.append(rods)
            
            # --- 3. 关节球头 (Joints) ---
            # 每根连杆两头各有一个，一共4个点
            joints = gl.GLScatterPlotItem(size=8, color=self.COLOR_JOINT, pxMode=True)
            self.view.addItem(joints)
            self.joint_points.append(joints)
            
        # --- 4. 动平台 (End Effector) ---
        # 绘制一个小三角形表示末端
        self.platform_item = gl.GLLinePlotItem(width=8, color=self.COLOR_PLATFORM, mode='line_strip', antialias=True)
        self.view.addItem(self.platform_item)

    def update_robot_state(self, pos, redraw=True):
        """模式1：通过末端坐标驱动"""
        sliders_z = self.kinematics.inverse_kinematics(pos)
        if sliders_z is None:
            self._set_alarm_state(True)
            return False
        
        self.current_sliders_z = sliders_z
        self._update_graphics(pos, sliders_z)
        return True

    def update_by_sliders(self, sliders_z):
        """模式2：通过滑块高度驱动"""
        pos = self.kinematics.forward_kinematics(sliders_z)
        self.current_sliders_z = sliders_z
        
        if pos is None:
            # 物理上不可达 (拉扯)，只更新滑块，不画连杆
            self._update_graphics_sliders_only(sliders_z)
            return False
            
        self._update_graphics(pos, sliders_z)
        return True

    def _update_graphics(self, pos, sliders_z):
        """核心渲染逻辑：计算双连杆的端点坐标"""
        self._set_alarm_state(False)
        x, y, z = pos
        angles = self.kinematics.towers_angle
        
        plat_pts = [] # 动平台几何中心点
        
        # 双连杆的一半间距
        half_spacing = self.rod_spacing / 2.0
        
        for i, angle in enumerate(angles):
            # --- 计算偏移向量 ---
            # 连杆间距是垂直于立柱径向的
            # 向量方向：angle + 90度
            off_x = half_spacing * math.cos(angle + math.pi/2)
            off_y = half_spacing * math.sin(angle + math.pi/2)
            
            # --- A. 滑块位置 (Slider Center) ---
            tx = self.R * math.cos(angle)
            ty = self.R * math.sin(angle)
            sz = sliders_z[i]
            
            # 更新滑块显示
            self.slider_items[i].setData(pos=np.array([[tx, ty, sz]]))
            
            # --- B. 动平台连接点 (Platform Center for this arm) ---
            px = x + self.r * math.cos(angle)
            py = y + self.r * math.sin(angle)
            pz = z
            plat_pts.append([px, py, pz])
            
            # --- C. 计算4个关节坐标 ---
            # 上方两点 (滑块两侧)
            p_up_1 = [tx + off_x, ty + off_y, sz]
            p_up_2 = [tx - off_x, ty - off_y, sz]
            
            # 下方两点 (动平台两侧)
            p_low_1 = [px + off_x, py + off_y, pz]
            p_low_2 = [px - off_x, py - off_y, pz]
            
            # --- D. 绘制连杆 ---
            # GLLinePlotItem mode='lines' 需要点对: [p1, p2, p3, p4] -> line(p1,p2), line(p3,p4)
            rods_data = np.array([p_up_1, p_low_1, p_up_2, p_low_2])
            self.rod_lines[i].setData(pos=rods_data)
            
            # --- E. 绘制关节 ---
            self.joint_points[i].setData(pos=rods_data)

        # 闭合动平台三角形
        plat_pts.append(plat_pts[0])
        self.platform_item.setData(pos=np.array(plat_pts), color=self.COLOR_PLATFORM)

    def _update_graphics_sliders_only(self, sliders_z):
        """异常状态渲染"""
        angles = self.kinematics.towers_angle
        for i, angle in enumerate(angles):
            tx = self.R * math.cos(angle)
            ty = self.R * math.sin(angle)
            sz = sliders_z[i]
            self.slider_items[i].setData(pos=np.array([[tx, ty, sz]]))
            # 隐藏连杆
            self.rod_lines[i].setData(pos=np.array([]))
            self.joint_points[i].setData(pos=np.array([]))

    def _set_alarm_state(self, is_alarm):
        """设置报警颜色"""
        color = (1, 0, 0, 1) if is_alarm else self.COLOR_PLATFORM
        self.platform_item.setData(color=color)

    def set_trajectory(self, trajectory):
        if hasattr(self, 'traj_plot'):
            self.view.removeItem(self.traj_plot)
        if trajectory is not None and len(trajectory) > 0:
            self.traj_plot = gl.GLLinePlotItem(pos=trajectory, color=self.COLOR_TRAJ, width=2)
            self.view.addItem(self.traj_plot)