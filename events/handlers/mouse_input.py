"""
마우스 입력 편집 위젯

이 모듈은 마우스 버튼 액션 설정을 위한 커스텀 위젯을 제공합니다.
환경 설정 대화상자에서 마우스 버튼 설정 시 사용됩니다.
"""

from PyQt5.QtWidgets import QComboBox, QLabel, QWidget, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal

class MouseActionCombo(QComboBox):
    """
    마우스 액션을 선택할 수 있는 콤보박스
    
    이 클래스는 마우스 버튼에 할당할 액션을 선택하는 콤보박스를 제공합니다.
    """
    
    def __init__(self, parent=None):
        """
        Initialize mouse action combo box
        
        Args:
            parent: parent widget
        """
        super().__init__(parent)
        
        # Add available actions list
        self.addItem("Play/Pause", "toggle_play")
        self.addItem("Previous Image", "prev_image")
        self.addItem("Next Image", "next_image")
        self.addItem("Rotate Clockwise", "rotate_clockwise")
        self.addItem("Rotate Counterclockwise", "rotate_counterclockwise")
        self.addItem("Volume Up", "volume_up")
        self.addItem("Volume Down", "volume_down")
        self.addItem("Toggle Mute", "toggle_mute")
        self.addItem("Toggle Fullscreen", "toggle_fullscreen")
        self.addItem("Toggle Maximize State", "toggle_maximize_state")
        self.addItem("Context Menu", "context_menu")
        
        # Set style configuration
        self.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 5px;
                min-height: 25px;
            }
            
            QComboBox:hover {
                border: 1px solid #aaa;
            }
            
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #ccc;
            }
        """)
        
    def hidePopup(self):
        """
        드롭다운 메뉴가 닫힐 때 호출되는 메서드
        콤보박스도 함께 숨깁니다.
        """
        super().hidePopup()
        self.hide()  # 콤보박스 자체도 숨김
        
    def focusOutEvent(self, event):
        """
        포커스를 잃을 때 호출되는 이벤트 핸들러
        
        Args:
            event: 포커스 이벤트
        """
        super().focusOutEvent(event)
        self.hide()  # 콤보박스 숨기기
        
    def set_current_action(self, action_code):
        """
        현재 액션 설정
        
        Args:
            action_code: 액션 코드 (예: "toggle_play")
        """
        # 액션 코드에 해당하는 인덱스 찾기
        index = self.findData(action_code)
        if index >= 0:
            self.setCurrentIndex(index)
        else:
            # 기본값 설정
            default_index = self.findData("toggle_play")
            if default_index >= 0:
                self.setCurrentIndex(default_index)
    
    def get_current_action(self):
        """
        현재 선택된 액션 코드 반환
        
        Returns:
            str: 액션 코드 (예: "toggle_play")
        """
        return self.currentData()


class MouseButtonWidget(QWidget):
    """
    마우스 버튼과 그 액션을 설정하는 위젯
    
    이 클래스는 마우스 버튼과 그에 연결된 액션을 설정하는 UI를 제공합니다.
    """
    
    action_changed = pyqtSignal(str, str)  # 버튼 이름, 새 액션
    
    def __init__(self, button_name, button_display_name, initial_action=None, parent=None):
        """
        마우스 버튼 위젯 초기화
        
        Args:
            button_name: 버튼 식별자 (예: "middle_click")
            button_display_name: 버튼 표시 이름 (예: "중간 버튼 클릭")
            initial_action: 초기 액션 (없으면 기본값 사용)
            parent: 부모 위젯
        """
        super().__init__(parent)
        
        self.button_name = button_name
        
        # 레이아웃 설정
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 버튼 레이블 추가
        self.label = QLabel(button_display_name)
        self.label.setStyleSheet("""
            QLabel {
                min-width: 120px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.label)
        
        # 액션 콤보박스 추가
        self.action_combo = MouseActionCombo(self)
        layout.addWidget(self.action_combo)
        
        # 초기 액션 설정
        if initial_action:
            self.action_combo.set_current_action(initial_action)
        
        # 액션 변경 시그널 연결
        self.action_combo.currentIndexChanged.connect(self._on_action_changed)
    
    def _on_action_changed(self, index):
        """
        액션 변경 시 호출되는 메서드
        
        Args:
            index: 콤보박스에서 선택된 항목의 인덱스
        """
        new_action = self.action_combo.get_current_action()
        self.action_changed.emit(self.button_name, new_action)
    
    def get_button_action(self):
        """
        현재 설정된 버튼과 액션 반환
        
        Returns:
            tuple: (버튼 이름, 액션 코드)
        """
        return (self.button_name, self.action_combo.get_current_action()) 