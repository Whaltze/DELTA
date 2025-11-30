# -*- coding: utf-8 -*-
"""
手眼标定及配准流程模块
"""
from PySide6.QtWidgets import QMessageBox, QWidget

class CalibrationHandler:
    def __init__(self, ui, camera_thread, parent_window=None, logger=None):
        self.ui = ui
        self.camera_thread = camera_thread
        self.parent_window = parent_window
        self.logger = logger or (lambda msg: print(msg))

    def _get_parent_widget(self):
        """获取用于QMessageBox的父窗口"""
        if self.parent_window:
            return self.parent_window
        # 尝试从UI控件获取父窗口
        if hasattr(self.ui, 'trans_x') and self.ui.trans_x:
            widget = self.ui.trans_x.parent()
            while widget and not isinstance(widget, QWidget):
                widget = widget.parent()
            if widget:
                return widget
        return None

    def apply_hand_eye_transform(self):
        parent = self._get_parent_widget()
        if not self.camera_thread:
            QMessageBox.warning(parent, "提示", "请先打开摄像头再应用变换矩阵。")
            self.logger("手眼标定错误: 请先打开摄像头")
            return
        try:
            x = self.ui.trans_x.value()
            y = self.ui.trans_y.value()
            z = self.ui.trans_z.value()
            roll = self.ui.trans_r.value()
            pitch = self.ui.trans_p.value()
            yaw = self.ui.trans_y_2.value()
            self.camera_thread.set_transform_matrix(x, y, z, roll, pitch, yaw)
            QMessageBox.information(parent, "成功", "变换矩阵已成功应用！")
            self.logger(f"手眼标定矩阵已应用: T({x}, {y}, {z}), R({roll}, {pitch}, {yaw})")
        except Exception as e:
            QMessageBox.critical(parent, "错误", f"应用变换矩阵时出错: {e}")
            self.logger(f"手眼标定错误: {str(e)}")
