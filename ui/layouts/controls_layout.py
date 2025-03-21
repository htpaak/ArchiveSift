from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QSlider, QMenu, QAction, QLabel
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon
from media.handlers.animation_handler import AnimationHandler  # AnimationHandler 클래스 임포트
from core.utils.time_utils import format_time  # format_time 함수 추가 임포트

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

    def toggle_title_ui_lock(self):
        """타이틀바 잠금을 토글: UI 잠금 관리자에 위임"""
        self.parent.ui_lock_manager.toggle_title_lock()

    def update_ui_lock_button_state(self):
        """UI 잠금 버튼 상태 업데이트 - 이제 UILockUI 클래스에서 관리합니다."""
        if hasattr(self.parent, 'ui_lock_ui'):
            self.parent.ui_lock_ui.update_ui_lock_button_state()

    def update_title_lock_button_state(self):
        """타이틀 잠금 버튼 상태 업데이트 - 이제 UILockUI 클래스에서 관리합니다."""
        if hasattr(self.parent, 'ui_lock_ui'):
            self.parent.ui_lock_ui.update_title_lock_button_state()

    def setup_custom_ui(self):
        """초기 및 resizeEvent에서 동적으로 호출되는 커스텀 UI 설정 메서드"""
        # 버튼 높이 측정 (open_button 기준)
        button_height = 50  # 실측으로 확인한 버튼 높이
        
        # 슬라이더 스타일 적용 (UI 일관성)
        self.parent.playback_slider.setStyleSheet(self.parent.slider_style)  # 재생 슬라이더 스타일 적용
        self.parent.volume_slider.setStyleSheet(self.parent.slider_style)  # 음량 조절 슬라이더 스타일 적용
        
        # 슬라이더를 버튼과 동일한 높이로 직접 설정
        self.parent.playback_slider.setFixedHeight(button_height)  # 재생 슬라이더 높이 설정
        self.parent.volume_slider.setFixedHeight(button_height)    # 볼륨 슬라이더 높이 설정
        
        # 슬라이더의 부모 위젯인 slider_widget에 배경 스타일을 적용
        self.parent.slider_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        
        # 슬라이더 컨테이너에 대한 스타일 설정
        playback_container = self.parent.playback_slider.parentWidget()
        volume_container = self.parent.volume_slider.parentWidget()
        if playback_container:
            playback_container.setStyleSheet("""
                QWidget {
                    background-color: rgba(52, 73, 94, 0.6);
                    border-radius: 3px;
                }
                QWidget:hover {
                    background-color: rgba(52, 73, 94, 1.0);
                }
            """)
            
        if volume_container:
            volume_container.setStyleSheet("""
                QWidget {
                    background-color: rgba(52, 73, 94, 0.6);
                    border-radius: 3px;
                }
                QWidget:hover {
                    background-color: rgba(52, 73, 94, 1.0);
                }
            """)
        
        # 연결 추가 (이벤트와 함수 연결)
        self.parent.volume_slider.connect_to_volume_control(self.adjust_volume)
        # AnimationHandler 초기화 (UI 설정 완료 후)
        self.parent.animation_handler = AnimationHandler(self.parent.image_label, self.parent)

    def update_button_sizes(self):
        """버튼 및 컨트롤 요소의 크기를 창 크기에 맞게 업데이트"""
        # 창 너비 가져오기
        total_width = self.parent.width()
        
        # 1. 폴더 버튼 행 처리
        if hasattr(self.parent, 'buttons'):
            # 각 행 위젯의 최대 너비를 현재 창 너비로 업데이트
            for row in self.parent.buttons:
                row_widget = row[0].parent()  # 버튼의 부모 위젯(row_widget) 가져오기
                row_widget.setMaximumWidth(total_width)
                
                # 버튼 너비 계산
                button_width = total_width / 20
                
                # 각 버튼의 너비 설정
                for i, button in enumerate(row):
                    if i == 19:  # 마지막 버튼
                        remaining_width = total_width - (int(button_width) * 19)
                        button.setFixedWidth(remaining_width)
                    else:
                        button.setFixedWidth(int(button_width))
                
                # 레이아웃 업데이트
                row_widget.updateGeometry()
        
        # 2. 슬라이더바 컨트롤 처리 (통합 로직)
        if hasattr(self.parent, 'slider_controls'):
            # 기본 버튼 크기 계산 (모든 컨트롤에 동일하게 적용)
            button_width = max(60, min(150, int(total_width * 0.08)))
            button_height = max(30, min(50, int(button_width * 0.6)))
            
            # 모든 슬라이더 컨트롤에 동일한 로직 적용
            for control in self.parent.slider_controls:
                # 시간 레이블은 너비만 다르게 설정 (내용이 더 길기 때문)
                if control == self.parent.time_label:
                    control_width = int(button_width * 1.5)  # 시간 레이블은 1.5배 넓게
                else:
                    control_width = button_width
                
                # 크기 설정
                control.setFixedSize(control_width, button_height)
                
                # 폰트 크기 계산 (모든 컨트롤에 동일한 로직 적용)
                font_size = max(9, min(14, int(button_width * 0.25)))
                
                # 북마크 버튼은 특별하게 처리: update_bookmark_button_state 함수에서 색상 처리
                if control == self.parent.slider_bookmark_btn:
                    # 크기만 설정하고 스타일은 건드리지 않음 (북마크 상태에 따라 다르게 표시해야 하므로)
                    continue
                    
                # 컨트롤 유형에 따라 적절한 스타일시트 적용
                if isinstance(control, QLabel):  # 레이블인 경우
                    control.setStyleSheet(f"""
                        QLabel {{
                            background-color: rgba(52, 73, 94, 0.6);
                            color: white;
                            border: none;
                            padding: 8px;
                            border-radius: 3px;
                            font-size: {font_size}px;
                            qproperty-alignment: AlignCenter;
                        }}
                        QLabel:hover {{
                            background-color: rgba(52, 73, 94, 1.0);
                        }}
                    """)
                else:  # 일반 버튼
                    control.setStyleSheet(f"""
                        QPushButton {{
                            background-color: rgba(52, 73, 94, 0.6);
                            color: white;
                            border: none;
                            padding: 8px;
                            border-radius: 3px;
                            font-size: {font_size}px;
                        }}
                        QPushButton:hover {{
                            background-color: rgba(52, 73, 94, 1.0);
                        }}
                    """)
            
            # 북마크 버튼 상태 업데이트 (별도로 호출)
            self.update_bookmark_button_state()

    def on_button_click(self):
        """하위 폴더 버튼 클릭 처리 - 현재 이미지를 선택된 폴더로 복사"""
        button = self.sender()  # 클릭된 버튼 객체 참조
        folder_path = button.toolTip()  # 버튼 툴팁에서 폴더 경로 가져오기
        print(f"Selected folder: {folder_path}")  # 선택된 폴더 경로 출력

        # 커서를 일반 모양으로 복원
        from PyQt5.QtWidgets import QApplication
        QApplication.restoreOverrideCursor()  # 모래시계에서 일반 커서로 복원

        # 현재 이미지를 선택된 폴더로 복사
        self.parent.copy_image_to_folder(folder_path)
        
        # 버튼 클릭 후 약간의 지연을 두고 창에 포커스를 돌려줌
        self.parent.create_single_shot_timer(50, self.parent.setFocus)

    def slider_clicked(self, value):
        """슬라이더를 클릭하면 해당 위치로 이동"""
        # 비디오 처리
        if self.parent.current_media_type == 'video':
            # 슬라이더 값을 초 단위로 변환 (value는 밀리초 단위)
            seconds = value / 1000.0  # 밀리초를 초 단위로 변환
            self.parent.video_handler.seek(seconds)
        # 애니메이션 처리
        elif self.parent.current_media_type in ['gif_animation', 'webp_animation'] and hasattr(self.parent, 'animation_handler'):
            # AnimationHandler를 통해 프레임 이동
            self.parent.animation_handler.seek_to_frame(value)
        
        # 슬라이더 클릭 후 포커스를 다시 메인 창으로 설정
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(50, self.parent.setFocus)

    def slider_pressed(self):
        """슬라이더를 드래그하기 시작할 때 호출됩니다."""
        self.parent.is_slider_dragging = True

    def slider_released(self):
        """슬라이더 드래그 종료 처리"""
        self.parent.is_slider_dragging = False
        
        # 비디오 처리
        if self.parent.current_media_type == 'video':
            try:
                value = self.parent.playback_slider.value()
                seconds = value / 1000.0  # 밀리초를 초 단위로 변환
                self.parent.video_handler.seek(seconds)
            except Exception as e:
                print(f"비디오 Seek 오류: {e}")
        
        # 애니메이션 처리
        elif self.parent.current_media_type in ['gif_animation', 'webp_animation'] and hasattr(self.parent, 'animation_handler'):
            try:
                value = self.parent.playback_slider.value()
                self.parent.animation_handler.seek_to_frame(value)
            except Exception as e:
                print(f"애니메이션 Seek 오류: {e}")

    def seek_video(self, value):
        """슬라이더 값에 따라 비디오 재생 위치를 변경합니다."""
        if self.parent.is_slider_dragging:
            # 슬라이더 값을 초 단위로 변환 (value는 밀리초 단위)
            seconds = value / 1000.0  # 밀리초를 초 단위로 변환
            # VideoHandler의 seek 함수를 사용하여 정확한 위치로 이동
            self.parent.video_handler.seek(seconds)

    def seek_animation(self, value):
        """슬라이더 값에 따라 애니메이션 재생 위치를 변경합니다."""
        # AnimationHandler만 사용
        if self.parent.current_media_type in ['gif_animation', 'webp_animation'] and hasattr(self.parent, 'animation_handler'):
            self.parent.animation_handler.seek_to_frame(value)

    def update_video_playback(self):
        """VideoHandler를 사용하여 비디오의 재생 위치에 따라 슬라이더 값을 업데이트합니다."""
        if not self.parent.is_slider_dragging:
            try:
                position = self.parent.video_handler.get_position()  # 현재 재생 위치
                duration = self.parent.video_handler.get_duration()  # 총 길이
                
                # 재생 위치 값이 None인 경우 처리
                if position is None:
                    return  # 슬라이더 업데이트를 건너뜁니다.

                # 슬라이더 범위 설정
                if duration is not None and duration > 0:
                    # 슬라이더 범위를 밀리초 단위로 설정 (1000으로 곱해서 더 세밀하게)
                    self.parent.playback_slider.setRange(0, int(duration * 1000))
                    
                    # 현재 위치가 duration을 초과하면 0으로 리셋
                    if position >= duration:
                        self.parent.playback_slider.setValue(0)
                        self.parent.video_handler.seek(0)
                    else:
                        # 슬라이더 값을 밀리초 단위로 설정 (1000으로 곱해서 더 세밀하게)
                        self.parent.playback_slider.setValue(int(position * 1000))
                    
                    self.parent.time_label.setText(f"{self.format_time(position)} / {self.format_time(duration)}")

                self.parent.previous_position = position  # 현재 위치를 이전 위치로 저장

            except Exception as e:
                print(f"비디오 업데이트 에러: {e}")
                if hasattr(self.parent, 'video_timer') and self.parent.video_timer.isActive():
                    self.parent.video_timer.stop()  # 타이머 중지

    def format_time(self, seconds):
        """초를 'MM:SS' 형식으로 변환합니다."""
        # 이미 임포트된 core.utils.time_utils의 format_time 함수를 사용합니다
        return format_time(seconds)

    # 여기에 main.py에서 옮겨올 메서드들이 추가될 예정 