"""
창 관련 이벤트 처리 모듈

이 모듈은 창 이벤트(리사이징, 전체화면, 최대화 등)를 처리하는 WindowHandler 클래스를 정의합니다.
ImageViewer 클래스에서 창 이벤트 처리 코드를 분리하여 모듈화했습니다.
"""

from PyQt5.QtCore import QObject, QTimer, Qt
from PyQt5.QtWidgets import QApplication, QPushButton

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
            
    def resize_event(self, event):
        """창 크기가 변경될 때 호출되는 이벤트"""
        # 필수적인 UI 요소 즉시 조정
        window_width = self.parent.width()
        
        # 슬라이더 위젯의 너비를 창 너비와 동일하게 설정
        if hasattr(self.parent, 'slider_widget'):
            self.parent.slider_widget.setFixedWidth(window_width)
        
        if hasattr(self.parent, 'title_bar'):
            self.parent.title_bar.setGeometry(0, 0, self.parent.width(), 30)  # 제목표시줄 위치와 크기 조정
            self.parent.title_bar.raise_()  # 제목표시줄을 항상 맨 위로 유지
            # 제목표시줄 버튼 업데이트
            for child in self.parent.title_bar.children():
                if isinstance(child, QPushButton):
                    child.updateGeometry()
                    child.update()
        
        # 전체화면 오버레이 위치 조정
        if hasattr(self.parent, 'fullscreen_overlay') and not self.parent.fullscreen_overlay.isHidden():
            self.parent.fullscreen_overlay.move(
                (self.parent.width() - self.parent.fullscreen_overlay.width()) // 2,
                (self.parent.height() - self.parent.fullscreen_overlay.height()) // 2
            )
        
        # 버튼 크기 계산 및 조정
        self.parent.update_button_sizes()
        
        # 슬라이더 위젯 레이아웃 업데이트
        if hasattr(self.parent, 'playback_slider'):
            self.parent.playback_slider.updateGeometry()
        if hasattr(self.parent, 'volume_slider'):
            self.parent.volume_slider.updateGeometry()
        
        # 메시지 레이블 업데이트
        if hasattr(self.parent, 'message_label') and self.parent.message_label.isVisible():
            window_width = self.parent.width()
            font_size = max(12, min(32, int(window_width * 0.02)))
            padding = max(8, min(12, int(window_width * 0.008)))
            margin = max(10, min(30, int(window_width * 0.02)))
            
            self.parent.message_label.setStyleSheet(f"""
                QLabel {{
                    color: white;
                    background-color: rgba(52, 73, 94, 0.9);
                    font-size: {font_size}px;
                    padding: {padding}px {padding + 4}px;
                    border-radius: 3px;
                    font-weight: normal;
                }}
            """)
            self.parent.message_label.adjustSize()
            toolbar_height = 90  # 제목바(30) + 툴바(40) + 추가 여백(20)
            self.parent.message_label.move(margin, toolbar_height + margin)

        # resizeEvent 함수 내에 다음 코드 추가 (message_label 업데이트 코드 아래에)
        # 이미지 정보 레이블 즉시 업데이트 
        if hasattr(self.parent, 'image_info_label') and self.parent.image_info_label.isVisible():
            window_width = self.parent.width()
            font_size = max(12, min(32, int(window_width * 0.02)))
            padding = max(8, min(12, int(window_width * 0.008))) 
            margin = max(10, min(30, int(window_width * 0.02)))
            
            self.parent.image_info_label.setStyleSheet(f"""
                QLabel {{
                    color: white;
                    background-color: rgba(52, 73, 94, 0.9);
                    font-size: {font_size}px;
                    padding: {padding}px {padding + 4}px;
                    border-radius: 3px;
                    font-weight: normal;
                }}
            """)
            self.parent.image_info_label.adjustSize()
            
            # 우측 상단에 위치
            toolbar_height = 90  # 제목바(30) + 툴바(40) + 추가 여백(20)
            x = self.parent.width() - self.parent.image_info_label.width() - margin
            y = toolbar_height + margin
            
            self.parent.image_info_label.move(x, y)
            self.parent.image_info_label.show()
            self.parent.image_info_label.raise_()
        
        # 이미지 레이아웃 강제 업데이트
        if hasattr(self.parent, 'main_layout') and hasattr(self.parent, 'image_label'):
            self.parent.image_label.updateGeometry()
            self.parent.main_layout.update()
        
        # 슬라이더 위젯 자체의 패딩 조정
        if hasattr(self.parent, 'slider_widget'):
            padding = max(5, min(15, int(window_width * 0.01)))
            self.parent.slider_widget.setStyleSheet(f"background-color: rgba(52, 73, 94, 0.9); padding: {padding}px;")
        
        # 전체 레이아웃 강제 업데이트
        self.parent.updateGeometry()
        if self.parent.layout():
            self.parent.layout().update()
        
        # 나머지 무거운 작업은 타이머를 통해 지연 처리
        if self.parent.resize_timer.isActive():
            self.parent.resize_timer.stop()
        self.parent.resize_timer.start(150)  # 리사이징이 끝나고 150ms 후에 업데이트
        
        # 잠금 버튼과 북마크 버튼 상태 업데이트
        self.parent.update_ui_lock_button_state()
        self.parent.update_title_lock_button_state()
        self.parent.controls_layout.update_bookmark_button_state() 