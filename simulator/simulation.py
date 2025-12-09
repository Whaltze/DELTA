# -*- coding: utf-8 -*-
# simulator/simulation.py
import numpy as np
import pyqtgraph.opengl as gl
from PySide6.QtWidgets import QWidget, QVBoxLayout
import math
from PySide6.QtCore import Signal

class DeltaSimulator(QWidget):
    pose_changed = Signal(list, list) 
    def __init__(self, kinematics, parent=None):
        super().__init__(parent)
        self.kinematics = kinematics
        self.limit_visual_items = []  # 限位可视化项列表

        # --- 工业配色 ---
        self.COLOR_BG = '#1e1e1e'
        self.COLOR_GRID = (0.3, 0.3, 0.3, 1)
        self.COLOR_FRAME = (0.95, 0.95, 0.2, 1)
        self.COLOR_TOWER = (0.2, 0.8, 0.9, 1)
        self.COLOR_SLIDER = (1.0, 0.2, 0.6, 1)
        self.COLOR_ROD = (0.5, 0.0, 0.8, 1)
        self.COLOR_JOINT = (0.0, 1.0, 0.0, 1)
        self.COLOR_PLATFORM = (1.0, 0.4, 0.0, 1)
        self.COLOR_TRAJ = (1.0, 0.0, 1.0, 1.0)
        self.COLOR_ALARM = (1.0, 0.0, 0.0, 1)
        self.COLOR_LIMIT = (1.0, 0.5, 0.0, 0.5)  # 限位框颜色

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.view = gl.GLViewWidget()
        self.view.setBackgroundColor(self.COLOR_BG)
        self.view.setCameraPosition(distance=900, elevation=25, azimuth=45)
        self.view.pan(0, 0, -300)
        self.layout.addWidget(self.view)

        self.R = kinematics.R
        self.r = kinematics.r
        self.L = kinematics.L
        self.rod_spacing = 50.0
        self.frame_radius = self.R * 1.15
        
        # 滑块工作空间参数
        self.slider_min = -337.0  # 滑块下限
        self.slider_max = -30.0   # 滑块上限
        self.slider_mid = (self.slider_min + self.slider_max) / 2  # 滑块中间位置
        
        # Delta框架参数
        self.frame_top = 0.0      # 框架顶部
        self.frame_bottom = -590.0  # 框架底部
        
        # 动平台工作空间参数（基于运动学计算）
        self.platform_workspace = {
            'x_min': -200, 'x_max': 200,
            'y_min': -200, 'y_max': 200,
            'z_min': -590, 'z_max': -390  # 动平台工作空间
        }
        
        self.slider_items = []    
        self.rod_lines = []       
        self.joint_points = []    
        self.platform_item = None 
        self.detected_obj_items = [] 
        self.traj_plot = None
        
        # 初始化滑块位置为工作空间中间位置
        self.current_sliders_z = [self.slider_mid, self.slider_mid, self.slider_mid] 
        self._init_scene()

    def _init_scene(self):
        # 网格
        g = gl.GLGridItem()
        g.setSize(x=800, y=800, z=0)
        g.setSpacing(x=100, y=100, z=0)
        g.translate(0, 0, -400)  # 将网格调整到工作空间中心
        g.setColor(self.COLOR_GRID)
        self.view.addItem(g)
        
        # 坐标轴
        axis = gl.GLAxisItem()
        axis.setSize(50, 50, 50)
        self.view.addItem(axis)

        # 绘制结构和限位
        self._draw_frame_structure()
        self._draw_slider_limit_indicators()  # 绘制滑块限位指示器
        self._draw_workspace_limits()  # 绘制工作空间限位
        self._init_movable_parts()
        
        # [核心修复] 初始化时使用明确的 shape (0,3) 防止 OpenGL 报错
        empty_data = np.zeros((0, 3), dtype=np.float32)
        self.traj_plot = gl.GLLinePlotItem(pos=empty_data, color=self.COLOR_TRAJ, width=2, antialias=True)
        self.view.addItem(self.traj_plot)

    def _draw_frame_structure(self):
        """绘制框架结构"""
        h_top, h_bottom = self.frame_top, self.frame_bottom
        angles = self.kinematics.towers_angle
        start_angle = angles[0]
        
        # 绘制六边形顶底
        def draw_hex_ring(z, color, w):
            pts = []
            for i in range(7):
                ang = start_angle + math.radians(i * 60)
                pts.append([self.frame_radius * math.cos(ang), self.frame_radius * math.sin(ang), z])
            self.view.addItem(gl.GLLinePlotItem(pos=np.array(pts), width=w, color=color, antialias=True))

        draw_hex_ring(h_top, self.COLOR_FRAME, 8)
        draw_hex_ring(h_bottom, self.COLOR_FRAME, 8)
        
        # 绘制立柱
        for angle in angles:
            x, y = self.R * math.cos(angle), self.R * math.sin(angle)
            # 立柱主体
            self.view.addItem(gl.GLLinePlotItem(pos=np.array([[x, y, h_bottom], [x, y, h_top]]), 
                                                width=10, color=self.COLOR_TOWER, antialias=True))
            # 立柱端点
            self.view.addItem(gl.GLScatterPlotItem(pos=np.array([[x, y, h_bottom], [x, y, h_top]]), 
                                                   size=10, color=self.COLOR_FRAME, pxMode=True))

    def _draw_slider_limit_indicators(self):
        """在每个立柱上绘制滑块限位指示器"""
        try:
            angles = self.kinematics.towers_angle
            
            for angle in angles:
                x, y = self.R * math.cos(angle), self.R * math.sin(angle)
                
                # 绘制滑块下限指示器（红色）
                self.view.addItem(gl.GLScatterPlotItem(
                    pos=np.array([[x, y, self.slider_min]]), 
                    size=15, color=(1.0, 0.0, 0.0, 0.8), pxMode=True
                ))
                
                # 绘制滑块上限指示器（绿色）
                self.view.addItem(gl.GLScatterPlotItem(
                    pos=np.array([[x, y, self.slider_max]]), 
                    size=15, color=(0.0, 1.0, 0.0, 0.8), pxMode=True
                ))
                
                # 绘制限位范围线（黄色虚线）
                limit_line = gl.GLLinePlotItem(
                    pos=np.array([[x, y, self.slider_min], [x, y, self.slider_max]]),
                    width=3, color=(1.0, 1.0, 0.0, 0.6), 
                    mode='lines', antialias=True
                )
                self.view.addItem(limit_line)
                self.limit_visual_items.append(limit_line)
                
        except Exception as e:
            print(f"绘制滑块限位指示器失败: {e}")

    def _init_movable_parts(self):
        """初始化可动部件（滑块、连杆、动平台）"""
        angles = self.kinematics.towers_angle
        
        for i in range(3):
            tx, ty = self.R * math.cos(angles[i]), self.R * math.sin(angles[i])
            
            # 滑块（初始位置在中间）
            slider = gl.GLScatterPlotItem(
                pos=np.array([[tx, ty, self.slider_mid]]), 
                size=25, color=self.COLOR_SLIDER, pxMode=True
            )
            self.view.addItem(slider)
            self.slider_items.append(slider)
            
            # 连杆
            rods = gl.GLLinePlotItem(width=8, color=self.COLOR_ROD, mode='lines', antialias=True)
            self.view.addItem(rods)
            self.rod_lines.append(rods)
            
            # 关节
            joints = gl.GLScatterPlotItem(size=8, color=self.COLOR_JOINT, pxMode=True)
            self.view.addItem(joints)
            self.joint_points.append(joints)
            
        # 动平台
        self.platform_item = gl.GLLinePlotItem(width=8, color=self.COLOR_PLATFORM, 
                                               mode='line_strip', antialias=True)
        self.view.addItem(self.platform_item)
        
        # 初始更新一次图形
        initial_pos = self.kinematics.forward_kinematics(self.current_sliders_z)
        if initial_pos is not None:
            self._update_graphics(initial_pos, self.current_sliders_z)

    # ================== [关键修复] 轨迹绘制 ==================
    def set_trajectory(self, trajectory):
        """
        更新轨迹显示
        修复: 使用 np.zeros((0, 3)) 替代 np.array([]) 以避免 glVertexPointer 错误
        """
        if trajectory is not None and len(trajectory) > 0:
            try:
                pts = np.array(trajectory, dtype=np.float32)
                # 确保是 Nx3 维度
                if pts.shape[1] >= 3:
                    pts = pts[:, :3]  # 只取前3列(XYZ)
                    self.traj_plot.setData(pos=pts, color=self.COLOR_TRAJ, width=2)
            except Exception as e:
                print(f"轨迹数据错误: {e}")
        else:
            # 安全清空
            empty = np.zeros((0, 3), dtype=np.float32)
            self.traj_plot.setData(pos=empty)

    # ================== 视觉物体显示 ==================
    def add_detected_object(self, x, y, z, color_name):
        """添加检测到的物体"""
        color_map = {
            'Red': (1, 0, 0, 1), 
            'Yellow': (1, 1, 0, 1), 
            'Blue': (0, 0, 1, 1), 
            'Green': (0, 1, 0, 1)
        }
        c = color_map.get(color_name, (0.8, 0.8, 0.8, 1))
        
        # 修正: z 轴稍作调整防止穿模
        obj_item = gl.GLScatterPlotItem(pos=np.array([[x, y, z]]), size=25, color=c, pxMode=True)
        self.view.addItem(obj_item)
        self.detected_obj_items.append(obj_item)

    def clear_detected_objects(self):
        """清除检测到的物体"""
        for item in self.detected_obj_items:
            try:
                self.view.removeItem(item)
            except:
                pass
        self.detected_obj_items.clear()

    # ================== 运动更新 ==================
    def set_emergency_state(self, is_emergency):
        """设置急停状态"""
        color = self.COLOR_ALARM if is_emergency else self.COLOR_PLATFORM
        self.platform_item.setData(color=color)

    def update_robot_state(self, pos, redraw=True):
        """通过末端坐标更新"""
        sliders_z = self.kinematics.inverse_kinematics(pos)
        if sliders_z is None: 
            return False
            
        # 检查滑块限位
        for i, slider_z in enumerate(sliders_z):
            if slider_z < self.slider_min or slider_z > self.slider_max:
                print(f"警告: 滑块{i+1}超出限位: {slider_z:.1f}")
                return False
                
        self.current_sliders_z = sliders_z
        self._update_graphics(pos, sliders_z)
        return True

    def update_by_sliders(self, sliders_z):
        """
        通过滑块位置更新 (用于电机调试仿真)
        """
        # 检查滑块限位
        for i, slider_z in enumerate(sliders_z):
            if slider_z < self.slider_min or slider_z > self.slider_max:
                print(f"警告: 滑块{i+1}超出限位: {slider_z:.1f}")
                return False
                
        pos = self.kinematics.forward_kinematics(sliders_z)
        self.current_sliders_z = sliders_z
        
        if pos is None:
            # 如果正解失败(不可达)，只更新滑块，不更新连杆和平台(断开状态)
            self._update_graphics_sliders_only(sliders_z)
            return False
            
        # 正解成功，更新整体
        self._update_graphics(pos, sliders_z)
        return True

    def _update_graphics(self, pos, sliders_z):
        """更新图形显示"""
        x, y, z = pos
        angles = self.kinematics.towers_angle
        plat_pts = []
        half_spacing = self.rod_spacing / 2.0
        
        for i, angle in enumerate(angles):
            # 几何计算
            off_x, off_y = half_spacing * math.cos(angle + math.pi/2), half_spacing * math.sin(angle + math.pi/2)
            tx, ty = self.R * math.cos(angle), self.R * math.sin(angle)
            sz = sliders_z[i]
            px, py, pz = x + self.r * math.cos(angle), y + self.r * math.sin(angle), z
            plat_pts.append([px, py, pz])
            
            # 更新滑块
            self.slider_items[i].setData(pos=np.array([[tx, ty, sz]]))
            
            # 更新连杆 (平行四边形)
            p_up_1 = [tx + off_x, ty + off_y, sz]
            p_up_2 = [tx - off_x, ty - off_y, sz]
            p_low_1 = [px + off_x, py + off_y, pz]
            p_low_2 = [px - off_x, py - off_y, pz]
            
            rods_data = np.array([p_up_1, p_low_1, p_up_2, p_low_2])
            
            self.rod_lines[i].setData(pos=rods_data)
            self.joint_points[i].setData(pos=rods_data)

        # 闭合动平台
        plat_pts.append(plat_pts[0])
        self.platform_item.setData(pos=np.array(plat_pts))

    def _update_graphics_sliders_only(self, sliders_z):
        """仅更新滑块(用于正解无解时)"""
        angles = self.kinematics.towers_angle
        for i, angle in enumerate(angles):
            tx, ty = self.R * math.cos(angle), self.R * math.sin(angle)
            self.slider_items[i].setData(pos=np.array([[tx, ty, sliders_z[i]]]))
            self.rod_lines[i].setData(pos=np.zeros((0, 3)))  # 隐藏连杆
            self.joint_points[i].setData(pos=np.zeros((0, 3)))

    def on_slider_value_changed(self):
        """滑块值变化回调"""
        # 获取所有滑块的当前值
        new_sliders_z = [self.slider_A.value(), self.slider_B.value(), self.slider_C.value()]
        
        # 检查滑块限位
        for i, slider_z in enumerate(new_sliders_z):
            if slider_z < self.slider_min or slider_z > self.slider_max:
                print(f"滑块{i+1}超出限位: {slider_z:.1f}")
                return
        
        # 更新仿真图形
        success = self.update_by_sliders(new_sliders_z)

        # 计算动平台位置
        if success:
            platform_pos = self.kinematics.forward_kinematics(new_sliders_z)
            # 发出信号，携带滑块位置和平台位置
            self.pose_changed.emit(new_sliders_z, platform_pos)
        else:
            # 如果正解失败，平台位置无效，可以发None
            self.pose_changed.emit(new_sliders_z, None)

    # ================== 限位可视化方法 ==================
    def _draw_workspace_limits(self):
        """绘制工作空间限位"""
        try:
            # 清除现有的限位可视化
            for item in self.limit_visual_items:
                self.view.removeItem(item)
            self.limit_visual_items.clear()
            
            # 动平台工作空间限位（立方体边框）
            x_min, x_max = self.platform_workspace['x_min'], self.platform_workspace['x_max']
            y_min, y_max = self.platform_workspace['y_min'], self.platform_workspace['y_max']
            z_min, z_max = self.platform_workspace['z_min'], self.platform_workspace['z_max']
            
            # 绘制限位立方体边框
            points = []
            # 底部
            points.extend([[x_min, y_min, z_min], [x_max, y_min, z_min]])
            points.extend([[x_max, y_min, z_min], [x_max, y_max, z_min]])
            points.extend([[x_max, y_max, z_min], [x_min, y_max, z_min]])
            points.extend([[x_min, y_max, z_min], [x_min, y_min, z_min]])
            # 顶部
            points.extend([[x_min, y_min, z_max], [x_max, y_min, z_max]])
            points.extend([[x_max, y_min, z_max], [x_max, y_max, z_max]])
            points.extend([[x_max, y_max, z_max], [x_min, y_max, z_max]])
            points.extend([[x_min, y_max, z_max], [x_min, y_min, z_max]])
            # 侧边
            points.extend([[x_min, y_min, z_min], [x_min, y_min, z_max]])
            points.extend([[x_max, y_min, z_min], [x_max, y_min, z_max]])
            points.extend([[x_max, y_max, z_min], [x_max, y_max, z_max]])
            points.extend([[x_min, y_max, z_min], [x_min, y_max, z_max]])
            
            points = np.array(points, dtype=np.float32)
            limit_item = gl.GLLinePlotItem(pos=points, width=1, color=self.COLOR_LIMIT, antialias=True)
            self.view.addItem(limit_item)
            self.limit_visual_items.append(limit_item)
            
        except Exception as e:
            print(f"绘制限位可视化失败: {e}")
    
    def get_slider_limits(self):
        """获取滑块限位"""
        return {'min': self.slider_min, 'max': self.slider_max}
    
    def get_workspace_limits(self):
        """获取工作空间限位"""
        return self.platform_workspace.copy()