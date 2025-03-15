"""
키보드 이벤트 처리 모듈

이 모듈은 키보드 이벤트를 처리하는 클래스와 유틸리티를 제공합니다.
특히 KeyInputEdit 클래스는 키보드 단축키 설정에 사용됩니다.
"""

from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence

class KeyInputEdit(QLineEdit):
    """
    키 입력을 위한 특별한 텍스트 상자
    
    이 클래스는 사용자가 키보드로 단축키를 입력할 때 사용해요.
    사용자가 눌러준 키 조합(예: Ctrl+S)을 인식하고 텍스트로 보여줘요.
    설정 창에서 단축키를 바꿀 때 사용돼요.
    """
    
    def __init__(self, parent=None):
        """
        키 입력 텍스트 상자를 초기화해요.
        
        매개변수:
            parent: 이 위젯의 부모 위젯
        """
        super().__init__(parent)
        self.key_value = None  # 입력된 키 값을 저장할 변수
        self.setReadOnly(True)  # 직접 텍스트를 입력할 수 없게 해요
        self.setPlaceholderText("여기를 클릭하고 키를 누르세요")  # 안내 텍스트를 설정해요
        
        # 예쁜 스타일을 추가해요
        self.setStyleSheet("""
            QLineEdit {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
                color: #333;
            }
            
            QLineEdit:focus {
                background-color: #e0e8f0;
                border: 1px solid rgba(52, 73, 94, 1.0);
            }
        """)
        
        # 텍스트를 가운데 정렬해요
        self.setAlignment(Qt.AlignCenter)
        
    def keyPressEvent(self, event):
        """
        키가 눌렸을 때 호출되는 함수에요.
        눌린 키를 기억하고 화면에 표시해요.
        
        매개변수:
            event: 키 이벤트 정보(어떤 키가 눌렸는지 등)
        """
        modifiers = event.modifiers()  # Ctrl, Alt, Shift 같은 조합키가 눌렸는지 확인해요
        key = event.key()  # 어떤 키가 눌렸는지 가져와요
        
        # ESC, Tab 등의 특수 키는 무시해요
        # 이 키들은 대화상자나 프로그램 제어에 사용되므로 단축키로 설정하면 안 돼요
        if key in (Qt.Key_Escape, Qt.Key_Tab):
            return
        
        # 모디파이어(Ctrl, Alt, Shift)만 눌렀을 때는 처리하지 않아요
        # 단축키는 보통 모디파이어 + 일반 키의 조합이니까요
        if key in (Qt.Key_Control, Qt.Key_Alt, Qt.Key_Shift, Qt.Key_Meta):
            return
        
        # 키 조합을 만들어요
        # 예: Ctrl+S는 Ctrl 모디파이어와 S 키의 조합이에요
        self.key_value = key  # 기본 키를 저장해요
        
        # 조합키가 함께 눌렸으면 추가해요
        if modifiers & Qt.ControlModifier:  # Ctrl 키가
            self.key_value |= Qt.ControlModifier
        if modifiers & Qt.AltModifier:  # Alt 키가 눌렸는지 확인하고 추가해요
            self.key_value |= Qt.AltModifier
        if modifiers & Qt.ShiftModifier:  # Shift 키가 눌렸는지 확인하고 추가해요
            self.key_value |= Qt.ShiftModifier
        
        # 눌린 키 조합을 사람이 읽을 수 있는 텍스트로 만들어요
        # 예: "Ctrl+S"
        text = ""
        
        # 각 모디파이어가 눌렸는지 확인하고 텍스트에 추가해요
        if modifiers & Qt.ControlModifier:
            text += "Ctrl+"
        if modifiers & Qt.AltModifier:
            text += "Alt+"
        if modifiers & Qt.ShiftModifier:
            text += "Shift+"
        
        # 일반 키의 이름을 가져와서 추가해요
        # 예: A, B, 1, F1 등
        key_text = QKeySequence(key).toString()
        
        # Enter/Return 키인 경우 특별히 처리
        if key == Qt.Key_Return or key == Qt.Key_Enter:
            key_text = "Enter"  # 화면에는 'Enter'로 표시
            
        text += key_text
        self.setText(text)  # 만든 텍스트를 화면에 표시해요
        
        # 이벤트를 처리했다고 표시해요
        # 이렇게 하면 다른 곳에서 이 키 이벤트를 다시 처리하지 않아요
        event.accept() 