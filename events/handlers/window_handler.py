"""
창 관련 이벤트 처리 모듈

이 모듈은 창 이벤트(리사이징, 전체화면, 최대화 등)를 처리하는 WindowHandler 클래스를 정의합니다.
ImageViewer 클래스에서 창 이벤트 처리 코드를 분리하여 모듈화했습니다.
"""

from PyQt5.QtCore import QObject, QTimer, Qt
from PyQt5.QtWidgets import QApplication

class WindowHandler(QObject):
    """
    창 이벤트 처리 클래스
    
    이 클래스는 ImageViewer의 창 이벤트 처리를 담당합니다.
    """
    
    def __init__(self, parent=None):
        """
        WindowHandler 초기화
        
        Args:
            parent: 부모 객체 (ImageViewer 인스턴스)
        """
        super().__init__(parent)
        self.parent = parent
        
    def ensure_maximized(self):
        """창이 최대화 상태인지 확인하고, 최대화 상태가 아니면 최대화합니다."""
        if not self.parent.isMaximized():
            self.parent.showMaximized() 