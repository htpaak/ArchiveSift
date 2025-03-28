"""
회전 기능 UI 요소를 관리하는 모듈
"""
from PyQt5.QtWidgets import QAction, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

class RotationUI:
    """
    회전 기능 관련 UI 요소를 관리하는 클래스
    """
    
    def __init__(self, main_window, rotation_manager):
        """
        RotationUI 초기화
        
        Args:
            main_window: 메인 윈도우 객체 (UI 컴포넌트 접근용)
            rotation_manager: RotationManager 인스턴스
        """
        self.main_window = main_window
        self.rotation_manager = rotation_manager
        
        # UI 액션 참조 저장
        self.rotate_cw_action = None
        self.rotate_ccw_action = None
        self.reset_rotation_action = None
        
        # 버튼 참조 저장
        self.rotate_cw_button = None
        self.rotate_ccw_button = None
        
        # 초기 설정
        self.setup_actions()
        self.setup_connections()
        
    def setup_buttons(self):
        """회전 관련 버튼 설정"""
        # 기존에 버튼이 이미 생성되어 있다면 참조만 가져옴
        if hasattr(self.main_window, 'rotate_cw_button'):
            self.rotate_cw_button = self.main_window.rotate_cw_button
        
        if hasattr(self.main_window, 'rotate_ccw_button'):
            self.rotate_ccw_button = self.main_window.rotate_ccw_button
            
    def setup_actions(self):
        """Set up actions for rotation"""
        # Rotate Clockwise Action
        self.rotate_cw_action = QAction("Rotate Clockwise (&R)", self.main_window)
        self.rotate_cw_action.setShortcut(self.main_window.key_settings["rotate_clockwise"])
        self.rotate_cw_action.triggered.connect(self.rotate_clockwise)
        
        # Rotate Counterclockwise Action
        self.rotate_ccw_action = QAction("Rotate Counterclockwise (&L)", self.main_window)
        self.rotate_ccw_action.setShortcut(self.main_window.key_settings["rotate_counterclockwise"])
        self.rotate_ccw_action.triggered.connect(self.rotate_counterclockwise)
        
        # Reset Rotation Action
        self.reset_rotation_action = QAction("Reset Rotation", self.main_window)
        self.reset_rotation_action.triggered.connect(self.reset_rotation)
        
    def setup_connections(self):
        """시그널-슬롯 연결 설정"""
        # 기존 버튼에 대한 연결 설정
        self.setup_buttons()
        
        # 회전 관리자에 회전 변경 시그널 연결
        self.rotation_manager.rotation_changed.connect(self.update_ui)
        
    def rotate_clockwise(self):
        """시계 방향으로 회전"""
        self.rotation_manager.rotate_clockwise()
        
    def rotate_counterclockwise(self):
        """반시계 방향으로 회전"""
        self.rotation_manager.rotate_counterclockwise()
        
    def reset_rotation(self):
        """회전 초기화"""
        self.rotation_manager.reset_rotation()
    
    def update_ui(self, angle=None):
        """
        UI 상태 업데이트
        
        Args:
            angle: 회전 각도 (None일 경우 rotation_manager에서 가져옴)
        """
        if angle is None:
            angle = self.rotation_manager.rotation_angle
            
        # 활성화 상태 업데이트 등 추가 기능 구현 가능
        print(f"회전 UI 업데이트: {angle}°")
        
    def connect_to_menu(self, menu):
        """
        메뉴에 회전 액션 추가
        
        Args:
            menu: 회전 액션을 추가할 QMenu 객체
        """
        if menu:
            menu.addAction(self.rotate_cw_action)
            menu.addAction(self.rotate_ccw_action)
            menu.addAction(self.reset_rotation_action) 