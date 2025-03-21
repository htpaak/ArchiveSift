from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QSlider, QMenu, QAction
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon

class ControlsLayout(QWidget):
    """
    컨트롤 패널 레이아웃을 관리하는 클래스
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
    def update_play_button(self):
        """재생 상태에 따라 버튼 텍스트 업데이트"""
        # 미디어 타입에 따른 버튼 텍스트 업데이트
        if self.parent.current_media_type in ['gif_animation', 'webp_animation'] and hasattr(self.parent, 'animation_handler'):
            # 애니메이션 핸들러를 통해 재생 상태 확인
            is_playing = self.parent.animation_handler.is_playing()
            self.parent.play_button.set_play_state(is_playing)
        elif self.parent.current_media_type == 'video':
            # 비디오 재생 상태 확인
            try:
                is_playing = self.parent.video_handler.is_video_playing()
                self.parent.play_button.set_play_state(is_playing)
                self.parent.update_video_playback()  # 슬라이더 업데이트 호출
            except Exception as e:
                print(f"재생 버튼 업데이트 오류: {e}")
                self.parent.play_button.setEnabled(False)  # 버튼 비활성화

    # 여기에 main.py에서 옮겨올 메서드들이 추가될 예정 