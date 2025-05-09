"""
툴팁 관리자 모듈

이 모듈은 위젯에 툴팁을 관리하는 기능을 제공합니다.
커스텀 툴팁 표시 및 숨기기 로직을 포함합니다.
"""

from PyQt5.QtCore import QObject, QEvent, QTimer, QPoint
from PyQt5.QtWidgets import QLabel, QApplication


class TooltipManager(QObject):
    """
    툴팁 관리자 클래스
    
    위젯에 대한 툴팁을 관리하고 표시합니다.
    """
    
    def __init__(self, parent=None):
        """
        TooltipManager 초기화
        
        Args:
            parent: 부모 객체 (일반적으로 MediaSorterPAAK 인스턴스)
        """
        super().__init__(parent)
        self.parent = parent
        self.tooltip_widgets = {}  # 등록된 위젯 목록
        self.tooltip_label = None  # 툴팁 표시를 위한 라벨
        self.tooltip_timer = QTimer()  # 툴팁 표시 지연을 위한 타이머
        self.tooltip_timer.setSingleShot(True)
        self.tooltip_timer.timeout.connect(self.show_tooltip)
        
        # 툴팁 라벨 생성
        self.create_tooltip_label()
    
    def create_tooltip_label(self):
        """
        툴팁 표시용 라벨 생성
        """
        self.tooltip_label = QLabel(self.parent)
        self.tooltip_label.setStyleSheet("""
            background-color: rgba(52, 73, 94, 0.9);
            color: white;
            border: none;
            padding: 5px;
            border-radius: 3px;
        """)
        self.tooltip_label.setWordWrap(True)
        self.tooltip_label.hide()
    
    def register(self, widget, tooltip_text):
        """
        위젯에 툴팁 등록
        
        Args:
            widget: 툴팁을 표시할 위젯
            tooltip_text: 툴팁 텍스트
        """
        self.tooltip_widgets[widget] = tooltip_text
        
        # 기본 툴팁 비활성화 (커스텀 툴팁 사용)
        widget.setToolTip("")
        
        # 이벤트 필터 설치
        widget.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """
        이벤트 필터
        
        Args:
            obj: 이벤트가 발생한 객체
            event: 발생한 이벤트
            
        Returns:
            bool: 이벤트 처리 여부
        """
        if obj in self.tooltip_widgets:
            if event.type() == QEvent.Enter:
                # 마우스가 위젯에 들어왔을 때 툴팁 표시 준비
                self.tooltip_timer.start(500)  # 500ms 후에 툴팁 표시
                self.current_widget = obj
                return False
            elif event.type() == QEvent.Leave:
                # 마우스가 위젯에서 나갔을 때 툴팁 숨김
                self.tooltip_timer.stop()
                self.hide_tooltip()
                return False
            elif event.type() == QEvent.MouseMove:
                # 마우스 이동 시 툴팁 위치 업데이트
                if self.tooltip_label.isVisible():
                    self.update_tooltip_position(obj, event.globalPos())
                return False
        
        # 기본 이벤트 처리
        return super().eventFilter(obj, event)
    
    def show_tooltip(self):
        """
        툴팁 표시
        """
        if hasattr(self, 'current_widget') and self.current_widget in self.tooltip_widgets:
            text = self.tooltip_widgets[self.current_widget]
            if text:
                self.tooltip_label.setText(text)
                
                # 툴팁 크기 조정
                self.tooltip_label.adjustSize()
                
                # 마우스 위치 가져오기
                cursor_pos = QApplication.desktop().cursor().pos()
                
                # 툴팁 위치 설정
                self.update_tooltip_position(self.current_widget, cursor_pos)
                
                # 툴팁 표시
                self.tooltip_label.show()
                self.tooltip_label.raise_()
    
    def update_tooltip_position(self, widget, cursor_pos):
        """
        툴팁 위치 업데이트
        
        Args:
            widget: 툴팁을 표시할 위젯
            cursor_pos: 마우스 커서의 전역 위치
        """
        # 툴팁이 화면을 벗어나지 않도록 위치 조정
        x = cursor_pos.x() + 15
        y = cursor_pos.y() + 15
        
        # 화면 경계 확인
        screen_rect = QApplication.desktop().screenGeometry()
        tooltip_width = self.tooltip_label.width()
        tooltip_height = self.tooltip_label.height()
        
        # 오른쪽 경계 체크
        if x + tooltip_width > screen_rect.right():
            x = screen_rect.right() - tooltip_width
        
        # 아래쪽 경계 체크
        if y + tooltip_height > screen_rect.bottom():
            y = cursor_pos.y() - tooltip_height - 5
        
        # 툴팁 위치 설정
        self.tooltip_label.move(x, y)
    
    def hide_tooltip(self):
        """
        툴팁 숨기기
        """
        self.tooltip_label.hide()
    
    def cleanup(self):
        """
        정리 작업
        """
        self.tooltip_timer.stop()
        self.hide_tooltip()
        
        # 이벤트 필터 제거
        for widget in self.tooltip_widgets:
            if not widget.isDestroyed():
                widget.removeEventFilter(self) 