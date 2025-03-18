"""
회전 상태 관리를 위한 모듈
"""
from PyQt5.QtGui import QTransform
from PyQt5.QtCore import QObject, pyqtSignal

# 회전 상수 정의
ROTATE_0 = 0
ROTATE_90 = 90
ROTATE_180 = 180
ROTATE_270 = 270

class RotationManager(QObject):
    """
    이미지 회전 상태를 관리하는 클래스
    """
    # 회전 상태가 변경되었을 때 발생하는 시그널
    rotation_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        """
        RotationManager 초기화
        
        Args:
            parent: 부모 객체
        """
        super().__init__(parent)
        self._rotation_angle = ROTATE_0  # 현재 회전 각도
    
    @property
    def rotation_angle(self):
        """현재 회전 각도 반환"""
        return self._rotation_angle
    
    def set_rotation(self, angle):
        """
        회전 각도 설정
        
        Args:
            angle: 회전 각도 (0, 90, 180, 270)
        """
        # 각도를 0, 90, 180, 270 중 하나로 정규화
        angle = angle % 360
        if angle not in (ROTATE_0, ROTATE_90, ROTATE_180, ROTATE_270):
            angle = ROTATE_0
            
        if self._rotation_angle != angle:
            self._rotation_angle = angle
            self.rotation_changed.emit(angle)
    
    def get_transform(self):
        """현재 회전 각도에 따른 QTransform 객체 반환"""
        transform = QTransform()
        transform.rotate(self._rotation_angle)
        return transform
    
    def rotate_clockwise(self):
        """시계 방향으로 90도 회전"""
        new_angle = (self._rotation_angle + 90) % 360
        self.set_rotation(new_angle)
    
    def rotate_counterclockwise(self):
        """반시계 방향으로 90도 회전"""
        new_angle = (self._rotation_angle - 90) % 360
        self.set_rotation(new_angle)
    
    def reset_rotation(self):
        """회전 각도를 0으로 리셋"""
        self.set_rotation(ROTATE_0) 