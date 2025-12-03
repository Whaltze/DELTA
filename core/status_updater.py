# 新建文件: core/status_updater.py
from PySide6.QtCore import QThread, Signal
import time

class StatusUpdaterThread(QThread):
    """定时更新机器人状态的线程"""
    position_updated = Signal(list, list)  # 末端位置, 滑块位置
    status_updated = Signal(str)
    
    def __init__(self, motion_controller):
        super().__init__()
        self.motion_controller = motion_controller
        self.running = False
        self.update_interval = 0.1  # 秒
        
    def run(self):
        self.running = True
        self.status_updated.emit("状态更新线程开始运行")
        
        while self.running:
            try:
                if self.motion_controller.is_connected:
                    # 获取滑块位置（从控制卡读取）
                    sliders_z = self.motion_controller.get_current_sliders_z()
                    
                    if sliders_z:
                        # 计算末端位置
                        end_pos = self.motion_controller.kinematics.forward_kinematics(sliders_z)
                        
                        if end_pos:
                            # 发射位置更新信号
                            self.position_updated.emit(end_pos, sliders_z)
                    else:
                        # 尝试从仿真器获取当前位置
                        if hasattr(self.motion_controller, 'current_position'):
                            end_pos = self.motion_controller.current_position
                            if end_pos:
                                # 计算滑块位置
                                sliders_z = self.motion_controller.kinematics.inverse_kinematics(end_pos)
                                if sliders_z:
                                    self.position_updated.emit(end_pos, sliders_z)
                else:
                    # 控制卡未连接，等待重试
                    pass
                    
            except Exception as e:
                self.status_updated.emit(f"状态更新错误: {str(e)}")
                
            time.sleep(self.update_interval)
    
    def stop(self):
        self.running = False
        self.wait(500)