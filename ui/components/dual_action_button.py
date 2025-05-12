from PyQt5.QtWidgets import QPushButton, QSizePolicy, QApplication
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QColor, QPainter, QBrush

class DualActionButton(QPushButton):
    """
    듀얼 액션 버튼 클래스
    
    하나의 버튼에 두 가지 기능을 제공합니다.
    왼쪽 영역 클릭: 복사 기능
    오른쪽 영역 클릭: 이동 기능
    
    마우스 호버 시 영역에 따라 다른 색상과 툴팁을 표시합니다.
    """
    
    def __init__(self, text='', parent=None):
        """
        듀얼 액션 버튼 초기화
        
        Args:
            text: 버튼에 표시할 텍스트
            parent: 부모 위젯
        """
        super().__init__(text, parent)
        # 가로 방향으로는 확장 가능하지만 세로 방향으로는 부모 레이아웃에서 제공하는 크기에 맞춤
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        # 모든 고정 크기 제한 제거 (setMinimumSize/setMaximumSize 없앰)
        self.setup_style()
        
        # 버튼 상태 추적
        self.hover_region = None  # 'left', 'right', None
        self.folder_path = ""     # 폴더 경로 (툴팁)
        self.folder_name = ""     # 폴더 이름 (표시 텍스트)
        self.last_click_region = None  # 마지막 클릭 영역
        
        # 이벤트 필터 설치
        self.setMouseTracking(True)  # 마우스 움직임 감지 활성화
        
    def setup_style(self):
        """
        기본 버튼 스타일 설정
        """
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(52, 73, 94, 0.9);
                color: white;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: rgba(52, 73, 94, 1.0);
            }
        """)
    
    def enterEvent(self, event):
        """
        마우스가 버튼 위로 들어왔을 때 발생하는 이벤트
        """
        super().enterEvent(event)
        cursor_pos = self.mapFromGlobal(QApplication.desktop().cursor().pos())
        self._update_hover_state(cursor_pos)
    
    def leaveEvent(self, event):
        """
        마우스가 버튼에서 나갔을 때 발생하는 이벤트
        """
        super().leaveEvent(event)
        self.hover_region = None
        self.update()  # 버튼 상태 업데이트 (다시 그리기)
    
    def mouseMoveEvent(self, event):
        """
        마우스가 버튼 위에서 움직일 때 발생하는 이벤트
        """
        super().mouseMoveEvent(event)
        self._update_hover_state(event.pos())
    
    def mousePressEvent(self, event):
        """
        마우스 버튼이 눌렸을 때 발생하는 이벤트
        """
        if event.button() == Qt.LeftButton:
            # 클릭 위치에 따라 다른 신호 발생
            button_width = self.width()
            click_pos = event.x()
            
            # 클릭 위치 저장 (clicked 시그널 발생 후 참조용)
            self.last_click_region = 'left' if click_pos < button_width / 2 else 'right'
            
            # 일반적인 클릭 이벤트 처리 (clicked 시그널 발생)
            super().mousePressEvent(event)
    
    def _update_hover_state(self, pos):
        """
        마우스 위치에 따라 호버 상태 업데이트
        
        Args:
            pos: 마우스 위치 (QPoint)
        """
        button_width = self.width()
        mouse_x = pos.x()
        
        # 마우스 위치에 따라 왼쪽/오른쪽 영역 판단
        old_region = self.hover_region
        self.hover_region = 'left' if mouse_x < button_width / 2 else 'right'
        
        # 호버 상태가 변경된 경우에만 업데이트 및 툴팁 변경
        if old_region != self.hover_region:
            self._update_tooltip()
            self.update()  # 버튼 다시 그리기
    
    def _update_tooltip(self):
        """
        현재 호버 영역에 따라 툴팁 업데이트
        """
        if not self.folder_path:
            self.setToolTip('') # 폴더 경로가 없으면 툴팁을 비웁니다.
            return
            
        if self.hover_region == 'left':
            self.setToolTip(f"Copy: {self.folder_path}")
        elif self.hover_region == 'right':
            self.setToolTip(f"Move: {self.folder_path}")
        else:
            self.setToolTip(self.folder_path)  # 기본 툴팁은 경로만 표시
    
    def paintEvent(self, event):
        """
        버튼 그리기 이벤트
        호버 상태에 따라 버튼의 일부분만 색상 변경
        """
        super().paintEvent(event)
        
        if not self.hover_region:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        button_width = rect.width()
        half_width = button_width / 2
        
        # 호버 영역에 따라 다른 색상 적용
        if self.hover_region == 'left':
            # 왼쪽 영역 강조
            highlight_rect = QRect(0, 0, int(half_width), rect.height())
            painter.fillRect(highlight_rect, QBrush(QColor(41, 128, 185, 150)))  # 파란색 (복사)
            
        elif self.hover_region == 'right':
            # 오른쪽 영역 강조
            highlight_rect = QRect(int(half_width), 0, int(half_width), rect.height())
            painter.fillRect(highlight_rect, QBrush(QColor(231, 76, 60, 150)))  # 빨간색 (이동)
            
        painter.end()
    
    def set_folder_info(self, folder_path, folder_name):
        """
        버튼에 표시할 폴더 정보 설정
        
        Args:
            folder_path: 대상 폴더 전체 경로 (툴팁용)
            folder_name: 표시할 폴더 이름
        """
        self.folder_path = folder_path
        self.folder_name = folder_name
        self.setText(folder_name)
        if not self.folder_path: # 폴더 경로가 비어있으면
            self.setToolTip('')   # 툴팁을 즉시 비웁니다.
        self._update_tooltip() # 그 후 _update_tooltip을 호출하여 호버 상태에 따른 툴팁을 설정 (경로가 있으면)하거나 비웁니다 (경로가 없으면). 