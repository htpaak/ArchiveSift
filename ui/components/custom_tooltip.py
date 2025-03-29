from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QTimer, QPoint, QEvent, QObject
from PyQt5.QtGui import QPainter, QColor, QPen, QPalette

class CustomTooltip(QLabel):
    """
    어두운 배경과 흰색 글씨의 커스텀 툴팁 클래스
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 툴팁 스타일 설정
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        # 투명 속성 제거
        # self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # 폰트 및 색상 설정
        font = self.font()
        font.setPointSize(9)
        self.setFont(font)
        
        # 스타일시트 설정 - 어두운 배경에 흰색 글씨로 변경
        self.setStyleSheet("""
            QLabel {
                background-color: #34495e;
                color: white;
                border: 1px solid #2c3e50;
                border-radius: 3px;
                padding: 5px 8px;
            }
        """)
        
        # 숨김 타이머
        self.hideTimer = QTimer(self)
        self.hideTimer.setSingleShot(True)
        self.hideTimer.timeout.connect(self.hide)
        
        # 현재 표시 중인 위젯
        self.currentWidget = None
        
    def showText(self, pos, text, widget, duration=3000):
        """
        지정된 위치에 툴팁 텍스트를 표시합니다.
        
        Args:
            pos (QPoint): 툴팁을 표시할 화면 위치
            text (str): 툴팁에 표시할 텍스트
            widget (QWidget): 툴팁과 연결된 위젯
            duration (int): 툴팁 표시 지속 시간 (밀리초)
        """
        if not text:
            return
            
        self.setText(text)
        self.adjustSize()
        
        # 화면 정보 가져오기
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        
        # 툴팁의 크기
        tooltip_width = self.width()
        tooltip_height = self.height()
        
        # 마우스 커서 기준으로 위치 결정
        # 기본적으로 커서 오른쪽 아래에 표시하지만, 화면 경계를 넘어가지 않도록 조정
        x = pos.x() + 10  # 커서에서 약간 오른쪽으로 이동
        y = pos.y() + 20  # 커서에서 약간 아래로 이동
        
        # 툴팁이 화면 오른쪽을 넘어가면 왼쪽에 표시
        if x + tooltip_width > screen.width():
            x = pos.x() - tooltip_width - 5
        
        # 툴팁이 화면 아래를 넘어가면 위에 표시
        if y + tooltip_height > screen.height():
            y = pos.y() - tooltip_height - 5
        
        self.move(x, y)
        self.show()
        
        # 이전 타이머 중지 및 새 타이머 시작
        self.hideTimer.stop()
        self.hideTimer.start(duration)
        
        # 현재 위젯 저장
        self.currentWidget = widget
        
    def hideTooltip(self):
        """툴팁을 즉시 숨깁니다."""
        self.hideTimer.stop()
        self.hide()
        self.currentWidget = None

    def paintEvent(self, event):
        """그림자 효과를 위한 페인트 이벤트 오버라이드"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 불투명한 배경 그리기
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#34495e"))  # 메인 배경색과 동일한 색상
        painter.drawRoundedRect(self.rect(), 3, 3)
        
        super().paintEvent(event)

class TooltipManager(QObject):
    """
    여러 위젯에 대한 툴팁을 관리하는 클래스
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tooltip = CustomTooltip(parent)
        self.active = True
        
    def register(self, widget, text):
        """
        위젯에 툴팁을 등록합니다.
        
        Args:
            widget (QWidget): 툴팁을 표시할 위젯
            text (str): 툴팁 텍스트
        """
        if not widget:
            return
            
        # 내장 툴팁 비활성화 (Qt 기본 툴팁과의 충돌 방지)
        widget.setToolTip("")
        
        # 커스텀 툴팁 텍스트 설정
        widget._tooltip_text = text
        
        # 마우스 추적 활성화
        widget.setMouseTracking(True)
        
        # 이벤트 필터 설치 (이미 설치되어 있지 않은 경우)
        if not widget.eventFilter == self.eventFilter:
            widget.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """이벤트 필터 - 마우스 이벤트 처리"""
        if not self.active or not hasattr(obj, "_tooltip_text"):
            return False
            
        if event.type() == QEvent.Enter:
            # 기존 내장 툴팁을 비활성화
            obj.setToolTip("")
            # 마우스 포인터 위치에 툴팁 표시
            try:
                # 제목표시줄 버튼인 경우 중앙 아래에 표시
                from ui.components.control_buttons import TitleBarButton
                if isinstance(obj, TitleBarButton):
                    pos = obj.mapToGlobal(QPoint(obj.width() // 2, obj.height()))
                else:
                    pos = obj.mapToGlobal(QPoint(event.pos().x(), event.pos().y()))
                self.tooltip.showText(pos, obj._tooltip_text, obj)
            except Exception as e:
                pos = obj.mapToGlobal(QPoint(0, obj.height()))
                self.tooltip.showText(pos, obj._tooltip_text, obj)
            return False  # 이벤트를 계속 전파하여 다른 이벤트도 처리될 수 있게 함
            
        elif event.type() == QEvent.Leave:
            self.tooltip.hideTooltip()
            return False  # 이벤트를 계속 전파
        
        # 마우스 이동 시 툴팁 위치 업데이트 (마우스를 따라다니게)
        elif event.type() == QEvent.MouseMove and self.tooltip.isVisible() and self.tooltip.currentWidget == obj:
            pos = obj.mapToGlobal(QPoint(event.pos().x(), event.pos().y()))
            self.tooltip.move(pos.x() + 15, pos.y() + 15)  # 약간 오프셋 적용
            return False
            
        return False  # 기본적으로 모든 이벤트를 통과시킴
        
    def setActive(self, active):
        """툴팁 활성화 상태 설정"""
        self.active = active
        if not active:
            self.tooltip.hideTooltip() 