# -*- coding: utf-8 -*-
# core/calibration.py
from PySide6.QtWidgets import QMessageBox, QWidget

class CalibrationHandler:
    def __init__(self, ui, camera_thread, parent_window=None, logger=None):
        self.ui = ui
        # 这里保存 parent_window 是关键，确保能访问主窗口的最新属性
        self.parent_window = parent_window 
        self.logger = logger or (lambda msg: print(msg))

    def _get_parent_widget(self):
        """获取用于弹窗的父组件"""
        if self.parent_window:
            return self.parent_window
        # 尝试通过UI控件查找
        if hasattr(self.ui, 'trans_x') and self.ui.trans_x:
            widget = self.ui.trans_x.parent()
            while widget and not isinstance(widget, QWidget):
                widget = widget.parent()
            if widget:
                return widget
        return None

    def _get_current_camera_thread(self):
        """
        动态获取 MainWindow 中最新的 camera_thread 实例。
        解决了 main.py 重新实例化 Camera 后引用失效的问题。
        """
        if self.parent_window:
            # 优先尝试直接从主窗口属性获取
            if hasattr(self.parent_window, 'camera_thread'):
                return self.parent_window.camera_thread
        return None

    def apply_hand_eye_transform(self):
        parent = self._get_parent_widget()
        current_cam = self._get_current_camera_thread()
        
        # 调试信息：打印当前获取到的线程对象状态
        print(f"[DEBUG] CalibrationHandler attempting to access camera thread: {current_cam}")
        
        # [修改] 仅检查线程是否存活，防止因内部标志位延迟导致的误判
        if current_cam is None or not current_cam.isRunning():
            QMessageBox.warning(parent, "提示", "检测到摄像头未运行！\n请先点击'打开摄像头'，等待图像出现后再试。")
            self.logger("错误: 无法获取有效的摄像头线程")
            return

        try:
            x = self.ui.trans_x.value()
            y = self.ui.trans_y.value()
            z = self.ui.trans_z.value()
            roll = self.ui.trans_r.value()
            pitch = self.ui.trans_p.value()
            yaw = self.ui.trans_y_2.value()
            
            # 调用 Camera 类的方法
            # 确保 camera.py 中存在 set_transform_matrix 函数
            if hasattr(current_cam, 'set_transform_matrix'):
                current_cam.set_transform_matrix(x, y, z, roll, pitch, yaw)
                QMessageBox.information(parent, "成功", "变换矩阵已成功应用！\n(已链接至当前摄像头)")
                self.logger(f"手眼标定矩阵已更新: T=({x}, {y}, {z}) R=({roll}, {pitch}, {yaw})")
            else:
                raise AttributeError("Camera类缺少 set_transform_matrix 方法")
                
        except Exception as e:
            QMessageBox.critical(parent, "错误", f"应用变换矩阵时出错: {e}")
            self.logger(f"手眼标定系统异常: {str(e)}")