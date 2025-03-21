"""
클릭 가능한 슬라이더 모듈

이 모듈은 클릭 가능한 슬라이더 컨트롤을 제공합니다.
비디오나 애니메이션의 재생 위치를 조절할 때 유용합니다.
"""

from PyQt5.QtWidgets import QSlider, QStyle, QStyleOptionSlider  # 슬라이더 관련 위젯
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
        
    def disconnect_all_signals(self):
        """슬라이더의 모든 신호 연결을 해제합니다."""
        try:
            # valueChanged 시그널 연결 해제
            self.valueChanged.disconnect()
        except (TypeError, RuntimeError):
            pass  # 연결된 슬롯이 없으면 무시
            
        try:
            # sliderPressed 시그널 연결 해제
            self.sliderPressed.disconnect()
        except (TypeError, RuntimeError):
            pass  # 연결된 슬롯이 없으면 무시
            
        try:
            # sliderReleased 시그널 연결 해제
            self.sliderReleased.disconnect()
        except (TypeError, RuntimeError):
            pass  # 연결된 슬롯이 없으면 무시
            
        try:
            # clicked 시그널 연결 해제
            self.clicked.disconnect()
        except (TypeError, RuntimeError):
            pass  # 연결된 슬롯이 없으면 무시
    
    def connect_to_video_control(self, value_changed_slot, pressed_slot, released_slot, clicked_slot):
        """비디오 컨트롤에 필요한 모든 신호를 연결합니다."""
        self.disconnect_all_signals()  # 기존 연결 해제
        
        # 슬라이더 값 변경 시그널 연결
        self.valueChanged.connect(value_changed_slot)
        
        # 슬라이더 조작 관련 시그널 연결
        self.sliderPressed.connect(pressed_slot)
        self.sliderReleased.connect(released_slot)
        self.clicked.connect(clicked_slot)
    
    def connect_to_animation_control(self, value_changed_slot, pressed_slot=None, released_slot=None):
        """애니메이션 컨트롤에 필요한 신호를 연결합니다."""
        self.disconnect_all_signals()  # 기존 연결 해제
        
        # 값 변경 시그널 연결 (필수)
        self.valueChanged.connect(value_changed_slot)
        
        # 선택적 시그널 연결
        if pressed_slot:
            self.sliderPressed.connect(pressed_slot)
        
        if released_slot:
            self.sliderReleased.connect(released_slot)
    
    def connect_to_volume_control(self, value_changed_slot):
        """볼륨 컨트롤에 필요한 신호를 연결합니다."""
        self.disconnect_all_signals()  # 기존 연결 해제
        
        # 볼륨 슬라이더는 값 변경과 클릭 시그널을 동일한 슬롯에 연결
        self.valueChanged.connect(value_changed_slot)
        self.clicked.connect(value_changed_slot)
    
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