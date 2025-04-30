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
        self.setPlaceholderText("Click here and press a key")  # Set placeholder text
        
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


class KeyboardHandler:
    """
    키보드 입력을 처리하는 핸들러 클래스
    
    이 클래스는 메인 애플리케이션의 키보드 이벤트를 처리하고
    각 기능별로 적절한 메서드를 직접 실행합니다.
    """
    
    def __init__(self, parent):
        """
        KeyboardHandler 초기화
        
        매개변수:
            parent: 부모 객체 (ImageSortingPAAK 인스턴스)
        """
        self.parent = parent  # ImageSortingPAAK 인스턴스 참조
    
    def handle_key_press(self, event):
        """
        키 입력 이벤트를 처리합니다.
        
        매개변수:
            event: 키보드 이벤트 객체
        """
        key = event.key()
        modifiers = event.modifiers()
        
        # 1. 특수 키 처리 (ESC, Ctrl+D, Ctrl+G 등)
        if self.handle_special_keys(key, modifiers):
            return
        
        # 2. 이미지 전환 전 준비 작업
        self.prepare_media_transition(key)
        
        # 3. 이미지 탐색 처리 (이전/다음 이미지)
        if self.handle_image_navigation(key):
            return
        
        # 4. 이미지 조작 처리 (회전 등)
        if self.handle_image_manipulation(key):
            return
        
        # 5. 미디어 컨트롤 처리 (재생/일시정지, 볼륨 등)
        if self.handle_media_controls(key):
            return
        
        # 6. 창 관리 처리 (전체화면, 최대화 등)
        if self.handle_window_management(key, modifiers):
            return
        
        # 7. 파일 관리 처리 (삭제 등)
        if self.handle_file_management(key):
            return

    def handle_special_keys(self, key, modifiers):
        """특수 키 조합을 처리합니다."""
        # ESC 키로 전체화면 모드 종료
        if key == Qt.Key_Escape and self.parent.isFullScreen():
            self.parent.toggle_fullscreen()
            return True  # 키 처리 완료
        
        # Ctrl+D: 디버깅 모드 켜기/끄기
        elif key == Qt.Key_D and modifiers == Qt.ControlModifier:
            self.parent.toggle_debug_mode()
            return True
            
        # Ctrl+G: QMovie 참조 그래프 생성
        elif key == Qt.Key_G and modifiers == Qt.ControlModifier:
            self.parent.generate_qmovie_reference_graph()
            return True
            
        return False  # 키 처리 안됨

    def prepare_media_transition(self, key):
        """이미지 전환 전 미디어 상태를 정리합니다."""
        # 이전/다음 이미지 키인지 확인
        if (key == self.parent.key_settings.get("prev_image", Qt.Key_Left) or 
            key == self.parent.key_settings.get("next_image", Qt.Key_Right)):
            
            # 현재 미디어 타입 확인
            current_media_type = getattr(self.parent, 'current_media_type', 'unknown')
            
            # 비디오 플레이어 정지만 수행 (정리는 show_image 내부에서 처리)
            if current_media_type == 'video':
                # 비디오 중지
                self.parent.stop_video()
            
            return True  # 준비 작업 수행됨
        
        return False  # 준비 작업 불필요

    def handle_image_navigation(self, key):
        """이미지 탐색 관련 키를 처리합니다."""
        if key == self.parent.key_settings.get("prev_image", Qt.Key_Left):  # 이전 이미지 키
            self.parent.show_previous_image()  # 이전 이미지로 이동
            return True
        elif key == self.parent.key_settings.get("next_image", Qt.Key_Right):  # 다음 이미지 키
            self.parent.show_next_image()  # 다음 이미지로 이동
            return True
        
        return False  # 키 처리 안됨

    def handle_image_manipulation(self, key):
        """이미지 조작 관련 키를 처리합니다."""
        if key == self.parent.key_settings.get("rotate_clockwise", Qt.Key_R):  # 시계 방향 회전 키
            self.parent.rotate_image(True)  # 시계 방향 회전
            return True
        elif key == self.parent.key_settings.get("rotate_counterclockwise", Qt.Key_L):  # 반시계 방향 회전 키
            self.parent.rotate_image(False)  # 반시계 방향 회전
            return True
            
        return False  # 키 처리 안됨

    def handle_media_controls(self, key):
        """미디어 제어 관련 키를 처리합니다."""
        if key == self.parent.key_settings.get("play_pause", Qt.Key_Space):  # 재생/일시정지 키
            self.parent.toggle_animation_playback()  # 재생/일시정지 토글
            return True
        elif key == self.parent.key_settings.get("volume_up", Qt.Key_Up):  # 볼륨 증가 키
            # 볼륨 슬라이더 값을 가져와서 5씩 증가 (0-100 범위)
            current_volume = self.parent.volume_slider.value()
            new_volume = min(current_volume + 5, 100)  # 최대 100을 넘지 않도록
            self.parent.volume_slider.setValue(new_volume)
            self.parent.adjust_volume(new_volume)
            return True
        elif key == self.parent.key_settings.get("volume_down", Qt.Key_Down):  # 볼륨 감소 키
            # 볼륨 슬라이더 값을 가져와서 5씩 감소 (0-100 범위)
            current_volume = self.parent.volume_slider.value()
            new_volume = max(current_volume - 5, 0)  # 최소 0 미만으로 내려가지 않도록
            self.parent.volume_slider.setValue(new_volume)
            self.parent.adjust_volume(new_volume)
            return True
        elif key == self.parent.key_settings.get("toggle_mute", Qt.Key_M):  # 음소거 토글 키
            self.parent.toggle_mute()  # 음소거 토글 함수 호출
            return True
            
        return False  # 키 처리 안됨

    def handle_window_management(self, key, modifiers):
        """창 관리 관련 키를 처리합니다."""
        # 전체화면 토글 - 설정된 단축키 사용
        toggle_fullscreen_key = self.parent.key_settings.get("toggle_fullscreen", Qt.ControlModifier | Qt.Key_Return)
        
        # 단축키가 Ctrl+Enter 형태인지 확인
        is_ctrl_key = (toggle_fullscreen_key & 0x04000000) > 0  # Qt.ControlModifier는 0x04000000
        is_alt_key = (toggle_fullscreen_key & 0x08000000) > 0   # Qt.AltModifier는 0x08000000
        is_shift_key = (toggle_fullscreen_key & 0x02000000) > 0 # Qt.ShiftModifier는 0x02000000
        
        # 실제 키 코드 (Ctrl, Alt, Shift 제외)
        fullscreen_key_code = toggle_fullscreen_key & 0x01FFFFFF
        
        # 현재 입력된 모디파이어와 설정된 모디파이어가 일치하는지 확인
        modifiers_match = True
        if is_ctrl_key and not (modifiers & Qt.ControlModifier):
            modifiers_match = False
        if is_alt_key and not (modifiers & Qt.AltModifier):
            modifiers_match = False
        if is_shift_key and not (modifiers & Qt.ShiftModifier):
            modifiers_match = False
        if not is_ctrl_key and (modifiers & Qt.ControlModifier):
            modifiers_match = False
        if not is_alt_key and (modifiers & Qt.AltModifier):
            modifiers_match = False
        if not is_shift_key and (modifiers & Qt.ShiftModifier):
            modifiers_match = False
        
        # 전체화면 단축키 확인
        if key == fullscreen_key_code and modifiers_match:
            self.parent.toggle_fullscreen()  # 전체화면 모드 전환
            return True
        
        # ESC 키로 전체화면 종료
        elif key == Qt.Key_Escape and self.parent.isFullScreen():
            self.parent.toggle_fullscreen()  # 전체화면 모드 종료
            return True
            
        # 최대화 상태 토글 - 설정된 단축키 사용
        elif key == self.parent.key_settings.get("toggle_maximize_state", Qt.Key_Return):
            self.parent.toggle_maximize_state()  # 최대화 상태 전환
            return True
            
        return False  # 키 처리 안됨

    def handle_file_management(self, key):
        """파일 관리 관련 키를 처리합니다."""
        if key == self.parent.key_settings.get("delete_file", Qt.Key_Delete):  # 파일 삭제 키
            self.parent.delete_current_image()  # 현재 파일 삭제
            return True
            
        return False  # 키 처리 안됨 