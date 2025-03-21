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
                
    def toggle_mute(self):
        """음소거 상태를 토글합니다."""
        try:
            # VideoHandler의 toggle_mute 메서드 사용
            is_muted = self.parent.video_handler.toggle_mute()
            
            # 버튼 아이콘 변경 (음소거 상태에 따라)
            self.parent.mute_button.set_mute_state(is_muted)
        except Exception as e:
            print(f"음소거 토글 오류: {e}")
            pass
            
    def adjust_volume(self, volume):
        """음량을 조절합니다."""
        try:
            # 현재 슬라이더 값을 가져와서 볼륨을 설정
            volume_value = self.parent.volume_slider.value()  # 슬라이더의 현재 값
            # VideoHandler의 set_volume 메서드 사용
            self.parent.video_handler.set_volume(volume_value)
        except Exception as e:
            print(f"볼륨 조절 오류: {e}")
            pass
            
    def toggle_animation_playback(self):
        """애니메이션(GIF, WEBP) 또는 비디오 재생/일시정지 토글"""
        
        # 현재 열려있는 파일 확인
        if not self.parent.current_image_path:
            return
            
        # 미디어 타입에 따라 처리
        if self.parent.current_media_type in ['gif_animation', 'webp_animation']:
            # AnimationHandler 사용
            if hasattr(self.parent, 'animation_handler'):
                self.parent.animation_handler.toggle_playback()
                # 버튼 텍스트는 animation_handler 내에서 직접 업데이트됨
                
        # 비디오 처리
        elif self.parent.current_media_type == 'video':
            try:
                # VideoHandler를 사용하여 재생 상태 확인 및 토글
                is_playing = self.parent.video_handler.is_video_playing()
                if is_playing:
                    self.parent.video_handler.pause()  # 재생 중이면 일시정지
                else:
                    self.parent.video_handler.play()  # 일시정지 중이면 재생
                # 버튼 상태 업데이트
                self.update_play_button()
            except Exception as e:
                print(f"비디오 재생/일시정지 토글 오류: {e}")
                pass  # 예외 발생 시 무시
                
    def toggle_bookmark(self):
        """북마크 토글: 북마크 관리자에 위임"""
        self.parent.bookmark_manager.toggle_bookmark()
        
    def update_bookmark_menu(self):
        """북마크 메뉴 업데이트: 북마크 관리자에 위임"""
        self.parent.bookmark_manager.update_bookmark_menu()
        
    def load_bookmarked_image(self, path):
        """북마크된 이미지 로드: 북마크 관리자에 위임"""
        self.parent.bookmark_manager.load_bookmarked_image(path)
        
    def clear_bookmarks(self):
        """모든 북마크 삭제: 북마크 관리자에 위임"""
        self.parent.bookmark_manager.clear_bookmarks()
        
    def update_bookmark_button_state(self):
        """북마크 버튼 상태 업데이트: 북마크 관리자에 위임"""
        self.parent.bookmark_manager.update_bookmark_button_state()

    def toggle_ui_lock(self):
        """UI 잠금을 토글: UI 잠금 관리자에 위임"""
        self.parent.ui_lock_manager.toggle_ui_lock()

    # 여기에 main.py에서 옮겨올 메서드들이 추가될 예정 