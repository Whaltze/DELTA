# -*- coding: utf-8 -*-
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import Qt, QTimer, QSize, QPointF
from PySide6.QtGui import QImage, QPixmap, QKeyEvent, QPainter, QPen, QColor, QMouseEvent

class WritingCanvas(QtWidgets.QLabel):
    """自定义写字画布，支持轨迹预览和鼠标手写"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.trajectory_points = []
        self.current_point_index = -1
        self.handwriting_points = []  # 手写轨迹点
        self.is_drawing = False       # 是否正在绘制
        self.last_point = None
        self.setMinimumSize(340, 245)  # 增加画布尺寸
        self.setMouseTracking(True)
               # 样式设置
        self.setStyleSheet("background-color: white; border: 1px solid gray;")

    def get_handwriting_trajectory(self, z_height=-280, area_size=150, flip_vertical=True):
        if not self.handwriting_points:
            return []
        all_x = [p.x() for p in self.handwriting_points]
        all_y = [p.y() for p in self.handwriting_points]
        if not all_x or not all_y:
            return []
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        scale_x = area_size / (max_x - min_x) if max_x != min_x else 1
        scale_y = area_size / (max_y - min_y) if max_y != min_y else 1
        scale = min(scale_x, scale_y) * 0.8
        offset_x = -area_size / 2 - (min_x + (max_x - min_x) / 2) * scale
        offset_y = -area_size / 2 - (min_y + (max_y - min_y) / 2) * scale
        trajectory = []
        first_point = self.handwriting_points[0]
        x = first_point.x() * scale + offset_x
        y = -(first_point.y() * scale + offset_y) if flip_vertical else first_point.y() * scale + offset_y
        trajectory.append((x, y, z_height + 10, False))
        for point in self.handwriting_points:
            x = point.x() * scale + offset_x
            y = -(point.y() * scale + offset_y) if flip_vertical else point.y() * scale + offset_y
            trajectory.append((x, y, z_height, True))
        return trajectory

    def set_trajectory(self, trajectory):
        self.trajectory_points = trajectory
        self.current_point_index = -1
        self.update()

    def set_current_point(self, index):
        self.current_point_index = index
        self.update()

    def clear_handwriting(self):
        self.handwriting_points = []
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.is_drawing = True
            self.last_point = event.position()
            self.handwriting_points.append(self.last_point)
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_drawing and event.buttons() & Qt.LeftButton:
            current_point = event.position()
            self.handwriting_points.append(current_point)
            self.last_point = current_point
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.is_drawing = False
            self.last_point = None

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        if self.handwriting_points:
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0), 3))
            for i in range(1, len(self.handwriting_points)):
                painter.drawLine(self.handwriting_points[i-1], self.handwriting_points[i])
        if not self.trajectory_points:
            return
        all_x = [p[0] for p in self.trajectory_points]
        all_y = [p[1] for p in self.trajectory_points]
        if not all_x or not all_y:
            return
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        margin = 20
        range_x = max_x - min_x + 2 * margin
        range_y = max_y - min_y + 2 * margin
        scale_x = (self.width() - 20) / range_x if range_x > 0 else 1
        scale_y = (self.height() - 20) / range_y if range_y > 0 else 1
        scale = min(scale_x, scale_y)
        offset_x = (self.width() - range_x * scale) / 2 - min_x * scale + margin * scale
        offset_y = (self.height() - range_y * scale) / 2 - min_y * scale + margin * scale
        def to_canvas_coords(x, y):
            return QtCore.QPointF(x * scale + offset_x, self.height() - (y * scale + offset_y))
        pen_down = False
        path_points = []
        for i, point in enumerate(self.trajectory_points):
            x, y, z, is_pen_down = point
            canvas_point = to_canvas_coords(x, y)
            if i == self.current_point_index:
                painter.setPen(QtGui.QPen(QtGui.QColor(0, 255, 0), 4))
                painter.drawEllipse(canvas_point, 4, 4)
            if is_pen_down:
                if not pen_down:
                    pen_down = True
                    path_points = [canvas_point]
                else:
                    path_points.append(canvas_point)
            else:
                if pen_down and len(path_points) > 1:
                    painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 255), 2))
                    for j in range(1, len(path_points)):
                        painter.drawLine(path_points[j-1], path_points[j])
                pen_down = False
                path_points = []
                painter.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0), 1))
                painter.drawEllipse(canvas_point, 2, 2)
        if pen_down and len(path_points) > 1:
            painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 255), 2))
            for j in range(1, len(path_points)):
                painter.drawLine(path_points[j-1], path_points[j])
