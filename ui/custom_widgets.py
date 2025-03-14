# 사용자 정의 UI 위젯 모듈
# 기본 Qt 위젯을 확장해서 더 편리하게 사용할 수 있는 컨트롤들이에요.
# 클릭 가능한 슬라이더와 스크롤 가능한 메뉴 등이 포함되어 있어요.

from PyQt5.QtWidgets import QSlider, QStyle, QStyleOptionSlider  # 슬라이더 관련 위젯
from PyQt5.QtCore import Qt, pyqtSignal  # Qt 기본 기능과 신호 전달

# 사용자 정의 UI 위젯 모듈
# 기본 Qt 위젯을 확장해서 더 편리하게 사용할 수 있는 컨트롤들이에요.
# 클릭 가능한 슬라이더와 스크롤 가능한 메뉴 등이 포함되어 있어요.

from PyQt5.QtWidgets import QSlider, QStyle, QStyleOptionSlider, QMenu, QApplication  # UI 위젯
from PyQt5.QtCore import Qt, pyqtSignal  # Qt 기본 기능과 신호 전달

class ClickableSlider(QSlider):
    """
    클릭 가능한 슬라이더 클래스예요.
    
    일반 슬라이더와 달리 슬라이더 바의 아무 곳이나 클릭하면
    그 위치로 바로 이동할 수 있어요. 비디오나 애니메이션의
    재생 위치를 조절할 때 사용해요.
    
    신호(Signals):
        clicked: 슬라이더가 클릭됐을 때 발생 (값)
    """
    clicked = pyqtSignal(int)  # 슬라이더 클릭 위치 값을 전달하는 사용자 정의 시그널
    
    def __init__(self, *args, **kwargs):
        """
        클릭 가능한 슬라이더 초기화
        """
        super().__init__(*args, **kwargs)  # 부모 클래스 초기화 (QSlider 기본 기능 상속)
        self.is_dragging = False  # 드래그 상태 추적 변수 (마우스 누름+이동 상태 확인용)
        
    def mousePressEvent(self, event):
        """
        마우스 클릭 이벤트 처리
        
        슬라이더의 핸들이 아닌 곳을 클릭하면 해당 위치로 슬라이더가 이동해요.
        
        매개변수:
            event: 마우스 이벤트 정보
        """
        if event.button() == Qt.LeftButton:  # 좌클릭 이벤트만 처리 (다른 마우스 버튼은 무시)
            # 클릭한 위치가 핸들 영역인지 확인
            handle_rect = self.handleRect()
            
            if handle_rect.contains(event.pos()):
                # 핸들을 직접 클릭한 경우 기본 드래그 기능 활성화
                self.is_dragging = True
                return super().mousePressEvent(event)
            
            # 핸들이 아닌 슬라이더 영역 클릭 시 해당 위치로 핸들 이동
            option = QStyleOptionSlider()
            self.initStyleOption(option)
            
            # 슬라이더의 그루브(홈) 영역 계산
            groove_rect = self.style().subControlRect(
                QStyle.CC_Slider, option, QStyle.SC_SliderGroove, self
            )
            # 슬라이더의 핸들 영역 계산
            handle_rect = self.style().subControlRect(
                QStyle.CC_Slider, option, QStyle.SC_SliderHandle, self
            )
            
            # 슬라이더의 유효 길이 계산
            slider_length = groove_rect.width()
            slider_start = groove_rect.x()
            
            # 핸들 중앙 위치 계산을 위한 핸들 너비의 절반
            handle_half_width = handle_rect.width() / 2
            
            # 클릭 위치 계산 (슬라이더 시작점 기준)
            pos = event.pos().x() - slider_start
            
            # 슬라이더 길이에서 핸들 너비 고려 (실제 이동 가능 영역 조정)
            effective_length = slider_length - handle_rect.width()
            effective_pos = max(0, min(pos, effective_length))
            
            # 클릭 위치에 대응하는 슬라이더 값 계산
            value_range = self.maximum() - self.minimum()
            
            if value_range > 0:
                # 클릭 위치 비율을 슬라이더 값으로 변환
                value = self.minimum() + (effective_pos * value_range) / effective_length
                # 슬라이더가 반전되어 있는 경우 값 조정
                if self.invertedAppearance():
                    value = self.maximum() - value + self.minimum()
                
                # 계산된 값으로 슬라이더 설정 및 시그널 발생
                self.setValue(int(value))
                self.clicked.emit(int(value))
                
                # 그루브 영역 클릭 시에도 드래그 상태로 설정
                self.is_dragging = True
        
        # 부모 클래스의 이벤트 처리기 호출
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """
        마우스 이동 이벤트 처리
        
        드래그 중일 때 슬라이더 값을 업데이트해요.
        
        매개변수:
            event: 마우스 이벤트 정보
        """
        # 마우스 왼쪽 버튼을 누른 상태에서 드래그 중인 경우
        if self.is_dragging and event.buttons() & Qt.LeftButton:
            # 드래그 위치에 따라 슬라이더 값 계산 및 설정
            option = QStyleOptionSlider()
            self.initStyleOption(option)
            
            # 슬라이더 그루브 영역 계산
            groove_rect = self.style().subControlRect(
                QStyle.CC_Slider, option, QStyle.SC_SliderGroove, self
            )
            handle_rect = self.style().subControlRect(
                QStyle.CC_Slider, option, QStyle.SC_SliderHandle, self
            )
            
            # 슬라이더의 유효 길이 계산
            slider_length = groove_rect.width()
            slider_start = groove_rect.x()
            
            # 드래그 위치 계산 (슬라이더 시작점 기준)
            pos = event.pos().x() - slider_start
            
            # 슬라이더 길이에서 핸들 너비 고려
            effective_length = slider_length - handle_rect.width()
            effective_pos = max(0, min(pos, effective_length))
            
            # 드래그 위치에 대응하는 슬라이더 값 계산
            value_range = self.maximum() - self.minimum()
            
            if value_range > 0:
                # 드래그 위치 비율을 슬라이더 값으로 변환
                value = self.minimum() + (effective_pos * value_range) / effective_length
                # 슬라이더가 반전되어 있는 경우 값 조정
                if self.invertedAppearance():
                    value = self.maximum() - value + self.minimum()
                
                # 계산된 값으로 슬라이더 설정 및 시그널 발생
                self.setValue(int(value))
                self.clicked.emit(int(value))
                return
        
        # 드래그 상태가 아니거나 다른 마우스 버튼을 사용하는 경우 기본 동작 수행
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """
        마우스 버튼 놓기 이벤트 처리
        
        드래그 상태를 종료해요.
        
        매개변수:
            event: 마우스 이벤트 정보
        """
        if event.button() == Qt.LeftButton:
            self.is_dragging = False  # 드래그 상태 해제 (마우스 버튼 뗌)
        super().mouseReleaseEvent(event)  # 부모 클래스의 이벤트 처리기 호출

    def handleRect(self):
        """
        슬라이더 핸들의 사각형 영역을 계산하여 반환해요.
        
        반환값:
            핸들의 사각형 영역
        """
        option = QStyleOptionSlider()
        self.initStyleOption(option)  # 슬라이더 스타일 옵션 초기화
        
        # 현재 스타일에서 핸들 영역 계산
        handle_rect = self.style().subControlRect(
            QStyle.CC_Slider, option, QStyle.SC_SliderHandle, self
        )
        
        return handle_rect  # 핸들 영역 반환

class ScrollableMenu(QMenu):
    """
    스크롤 가능한 메뉴 클래스예요.
    
    일반 메뉴와 달리 항목이 많을 때 스크롤바가 나타나서
    모든 항목을 볼 수 있어요. 북마크 메뉴 등에 사용해요.
    """
    def __init__(self, parent=None):
        """
        스크롤 가능한 메뉴 초기화
        
        매개변수:
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # 스크롤 지원을 위한 설정
        self.setProperty("_q_scrollable", True)
        # 최대 높이 제한 - 항목을 더 많이 표시하기 위해 높이 증가
        self.setMaximumHeight(800)
        self.setStyleSheet("""
            QMenu {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                padding: 5px;
                min-width: 300px;
                max-height: 800px;
            }
            QMenu::item {
                padding: 3px 20px 3px 20px;  /* 패딩 줄여서 항목 높이 감소 */
                border: 1px solid transparent;
                color: #ecf0f1;
                max-width: 600px;
                font-size: 9pt;  /* 글자 크기 축소 */
            }
            QMenu::item:selected {
                background-color: #34495e;
                color: #ecf0f1;
            }
            QMenu::separator {
                height: 1px;
                background: #34495e;
                margin: 3px 0;  /* 구분선 간격 축소 */
            }
            QMenu::item:disabled {
                color: #7f8c8d;
            }
            QScrollBar:vertical {
                background: #2c3e50;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #34495e;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
    
    def wheelEvent(self, event):
        """
        마우스 휠 이벤트 처리
        
        메뉴 내용을 스크롤할 수 있게 해줘요.
        
        매개변수:
            event: 휠 이벤트 정보
        """
        # 마우스 휠 이벤트 처리
        super().wheelEvent(event)
        # 이벤트가 처리되었음을 표시
        event.accept()
        
    def showEvent(self, event):
        """
        메뉴가 표시될 때 호출되는 이벤트
        
        메뉴가 화면에 나타날 때 스크롤 속성을 설정해요.
        
        매개변수:
            event: 표시 이벤트 정보
        """
        # 메뉴가 표시될 때 호출되는 이벤트
        super().showEvent(event)
        # 스크롤을 지원하도록 다시 설정
        self.setProperty("_q_scrollable", True)
        # 스타일시트 재적용
        self.setStyle(self.style())
        
        # 화면 크기에 맞게 최대 높이 조절
        desktop = QApplication.desktop().availableGeometry()
        self.setMaximumHeight(min(800, desktop.height() * 0.7))
    
    def addMultipleActions(self, actions):
        """
        여러 액션을 메뉴에 한번에 추가해요.
        
        많은 항목을 추가할 때 스크롤바가 자동으로 나타나요.
        
        매개변수:
            actions: 추가할 액션 목록
        """
        for action in actions:
            self.addAction(action)
        
        # 액션이 많으면 스크롤 속성을 다시 설정
        if len(actions) > 7:
            self.setProperty("_q_scrollable", True)
            self.setStyle(self.style())