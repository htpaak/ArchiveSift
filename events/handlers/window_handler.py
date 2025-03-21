"""
창 관련 이벤트 처리 모듈

이 모듈은 창 이벤트(리사이징, 전체화면, 최대화 등)를 처리하는 WindowHandler 클래스를 정의합니다.
ImageViewer 클래스에서 창 이벤트 처리 코드를 분리하여 모듈화했습니다.
"""

from PyQt5.QtCore import QObject, QTimer, Qt
from PyQt5.QtWidgets import QApplication, QPushButton
from PyQt5.QtGui import QPixmap
import os

class WindowHandler(QObject):
    """
    창 이벤트 처리 클래스
    
    이 클래스는 ImageViewer의 창 이벤트 처리를 담당합니다.
    """
    
    def __init__(self, parent=None):
        """
        WindowHandler 초기화
        
        Args:
            parent: 부모 객체 (ImageViewer 인스턴스)
        """
        super().__init__(parent)
        self.parent = parent
        
    def ensure_maximized(self):
        """창이 최대화 상태인지 확인하고, 최대화 상태가 아니면 최대화합니다."""
        if not self.parent.isMaximized():
            self.parent.showMaximized()
            
    def resize_event(self, event):
        """창 크기가 변경될 때 호출되는 이벤트"""
        # 필수적인 UI 요소 즉시 조정
        window_width = self.parent.width()
        
        # 슬라이더 위젯의 너비를 창 너비와 동일하게 설정
        if hasattr(self.parent, 'slider_widget'):
            self.parent.slider_widget.setFixedWidth(window_width)
        
        if hasattr(self.parent, 'title_bar'):
            self.parent.title_bar.setGeometry(0, 0, self.parent.width(), 30)  # 제목표시줄 위치와 크기 조정
            self.parent.title_bar.raise_()  # 제목표시줄을 항상 맨 위로 유지
            # 제목표시줄 버튼 업데이트
            for child in self.parent.title_bar.children():
                if isinstance(child, QPushButton):
                    child.updateGeometry()
                    child.update()
        
        # 전체화면 오버레이 위치 조정
        if hasattr(self.parent, 'fullscreen_overlay') and not self.parent.fullscreen_overlay.isHidden():
            self.parent.fullscreen_overlay.move(
                (self.parent.width() - self.parent.fullscreen_overlay.width()) // 2,
                (self.parent.height() - self.parent.fullscreen_overlay.height()) // 2
            )
        
        # 버튼 크기 계산 및 조정
        self.parent.update_button_sizes()
        
        # 슬라이더 위젯 레이아웃 업데이트
        if hasattr(self.parent, 'playback_slider'):
            self.parent.playback_slider.updateGeometry()
        if hasattr(self.parent, 'volume_slider'):
            self.parent.volume_slider.updateGeometry()
        
        # 메시지 레이블 업데이트
        if hasattr(self.parent, 'message_label') and self.parent.message_label.isVisible():
            window_width = self.parent.width()
            font_size = max(12, min(32, int(window_width * 0.02)))
            padding = max(8, min(12, int(window_width * 0.008)))
            margin = max(10, min(30, int(window_width * 0.02)))
            
            self.parent.message_label.setStyleSheet(f"""
                QLabel {{
                    color: white;
                    background-color: rgba(52, 73, 94, 0.9);
                    font-size: {font_size}px;
                    padding: {padding}px {padding + 4}px;
                    border-radius: 3px;
                    font-weight: normal;
                }}
            """)
            self.parent.message_label.adjustSize()
            toolbar_height = 90  # 제목바(30) + 툴바(40) + 추가 여백(20)
            self.parent.message_label.move(margin, toolbar_height + margin)

        # resizeEvent 함수 내에 다음 코드 추가 (message_label 업데이트 코드 아래에)
        # 이미지 정보 레이블 즉시 업데이트 
        if hasattr(self.parent, 'image_info_label') and self.parent.image_info_label.isVisible():
            window_width = self.parent.width()
            font_size = max(12, min(32, int(window_width * 0.02)))
            padding = max(8, min(12, int(window_width * 0.008))) 
            margin = max(10, min(30, int(window_width * 0.02)))
            
            self.parent.image_info_label.setStyleSheet(f"""
                QLabel {{
                    color: white;
                    background-color: rgba(52, 73, 94, 0.9);
                    font-size: {font_size}px;
                    padding: {padding}px {padding + 4}px;
                    border-radius: 3px;
                    font-weight: normal;
                }}
            """)
            self.parent.image_info_label.adjustSize()
            
            # 우측 상단에 위치
            toolbar_height = 90  # 제목바(30) + 툴바(40) + 추가 여백(20)
            x = self.parent.width() - self.parent.image_info_label.width() - margin
            y = toolbar_height + margin
            
            self.parent.image_info_label.move(x, y)
            self.parent.image_info_label.show()
            self.parent.image_info_label.raise_()
        
        # 이미지 레이아웃 강제 업데이트
        if hasattr(self.parent, 'main_layout') and hasattr(self.parent, 'image_label'):
            self.parent.image_label.updateGeometry()
            self.parent.main_layout.update()
        
        # 슬라이더 위젯 자체의 패딩 조정
        if hasattr(self.parent, 'slider_widget'):
            padding = max(5, min(15, int(window_width * 0.01)))
            self.parent.slider_widget.setStyleSheet(f"background-color: rgba(52, 73, 94, 0.9); padding: {padding}px;")
        
        # 전체 레이아웃 강제 업데이트
        self.parent.updateGeometry()
        if self.parent.layout():
            self.parent.layout().update()
        
        # 나머지 무거운 작업은 타이머를 통해 지연 처리
        if self.parent.resize_timer.isActive():
            self.parent.resize_timer.stop()
        self.parent.resize_timer.start(150)  # 리사이징이 끝나고 150ms 후에 업데이트
        
        # 잠금 버튼과 북마크 버튼 상태 업데이트
        self.parent.update_ui_lock_button_state()
        self.parent.update_title_lock_button_state()
        self.parent.controls_layout.update_bookmark_button_state()
        
    def delayed_resize(self):
        """리사이징 완료 후 지연된 UI 업데이트 처리"""
        try:
            print("delayed_resize 실행")  # 디버깅용 메시지 추가
            
            # 현재 표시 중인 미디어 크기 조절
            if hasattr(self.parent, 'current_image_path') and self.parent.current_image_path:
                file_ext = os.path.splitext(self.parent.current_image_path)[1].lower()
                
                # 이미지 타입에 따른 리사이징 처리
                if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.ico', '.heic', '.heif']:
                    # ImageHandler를 사용하여 이미지 크기 조정
                    self.parent.image_handler.resize()
                elif file_ext == '.psd':
                    # PSDHandler를 사용하여 PSD 파일 크기 조정
                    self.parent.psd_handler.resize()
                elif (file_ext == '.gif' or file_ext == '.webp') and self.parent.current_media_type in ['gif_animation', 'webp_animation']:
                    # 애니메이션 핸들러를 통해 애니메이션 크기 조정
                    if hasattr(self.parent, 'animation_handler'):
                        print(f"{file_ext.upper()} 애니메이션 핸들러를 통한 리사이징")
                        self.parent.animation_handler.scale_animation()
                    else:
                        # 기존 방식으로 처리 (호환성 유지)
                        if file_ext == '.gif':
                            print("GIF 애니메이션 직접 리사이징")
                            self.parent.scale_gif()
                        elif file_ext == '.webp':
                            print("WEBP 애니메이션 직접 리사이징")
                            self.parent.scale_webp()
                        # UI 처리 완료 후 애니메이션이 제대로 보이도록 강제 프레임 업데이트
                        QApplication.processEvents()
                elif file_ext == '.webp' and self.parent.current_media_type == 'webp_image':
                    # 정적 WEBP 이미지 처리
                    if hasattr(self.parent, 'animation_handler'):
                        print("정적 WEBP 이미지 핸들러를 통한 리사이징")
                        self.parent.animation_handler.rotate_static_image(self.parent.current_image_path)
                    else:
                        # 일반 WEBP 이미지 처리 (애니메이션이 아닌 경우)
                        pixmap = QPixmap(self.parent.current_image_path)
                        if not pixmap.isNull():
                            scaled_pixmap = pixmap.scaled(self.parent.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            self.parent.image_label.setPixmap(scaled_pixmap)
                elif file_ext in ['.mp4', '.avi', '.wmv', '.ts', '.m2ts', '.mov', '.qt', '.mkv', '.flv', '.webm', '.3gp', '.m4v', '.mpg', '.mpeg', '.vob', '.wav', '.flac', '.mp3', '.aac', '.m4a', '.ogg']:
                    # MPV 플레이어 윈도우 ID 업데이트
                    if hasattr(self.parent, 'player'):
                        self.parent.player.wid = int(self.parent.image_label.winId())
            
            # 이미지 정보 레이블 업데이트
            if hasattr(self.parent, 'image_info_label') and self.parent.image_files:
                self.parent.update_image_info()

            # 잠금 버튼과 북마크 버튼 상태 업데이트 (리사이징 후 스타일 복원)
            self.parent.update_ui_lock_button_state()
            self.parent.update_title_lock_button_state()
            self.parent.controls_layout.update_bookmark_button_state()
                    
        except Exception as e:
            print(f"지연된 리사이징 처리 중 오류 발생: {e}")
            
    def toggle_fullscreen(self):
        """전체화면 모드를 전환합니다."""
        if self.parent.isFullScreen():
            # 전체화면 모드에서 일반 모드로 전환
            self.parent.showNormal()
            
            # UI 고정 상태에 따라 UI 요소 표시 여부 결정 - 각각 독립적으로 확인
            if hasattr(self.parent, 'is_title_ui_locked') and self.parent.is_title_ui_locked:
                # 상단 UI가 고정된 상태라면 타이틀바 표시
                if hasattr(self.parent, 'title_bar'):
                    self.parent.title_bar.show()
            else:
                # 상단 UI가 고정되지 않은 상태라면 타이틀바 숨김
                if hasattr(self.parent, 'title_bar'):
                    self.parent.title_bar.hide()
            
            if hasattr(self.parent, 'is_bottom_ui_locked') and self.parent.is_bottom_ui_locked:
                # 하단 UI가 고정된 상태라면 UI 요소들을 표시
                if hasattr(self.parent, 'slider_widget'):
                    self.parent.slider_widget.show()
                
                for row in self.parent.buttons:
                    for button in row:
                        button.show()
            else:
                # 하단 UI가 고정되지 않은 상태라면 UI 요소들을 숨김
                if hasattr(self.parent, 'slider_widget'):
                    self.parent.slider_widget.hide()
                
                for row in self.parent.buttons:
                    for button in row:
                        button.hide()
            
            # 전체화면 오버레이 숨기기
            if hasattr(self.parent, 'fullscreen_overlay') and self.parent.fullscreen_overlay.isVisible():
                self.parent.fullscreen_overlay.hide()
                
            # 풀스크린 버튼 텍스트 업데이트
            if hasattr(self.parent, 'fullscreen_btn'):
                self.parent.fullscreen_btn.setText("🗖")  # 전체화면 아이콘
            
            # 전체화면 모드 상태 업데이트
            self.parent.is_in_fullscreen = False
            
            # 전체화면에서 일반 모드로 전환 후 모든 미디어 타입에 대해 리사이징 적용
            QTimer.singleShot(100, self.parent.delayed_resize)

            # 잠금 버튼 상태 갱신 - 각각 개별적으로 갱신
            QTimer.singleShot(150, self.parent.update_title_lock_button_state)
            QTimer.singleShot(150, self.parent.update_ui_lock_button_state)
                
        else:
            # 현재 비디오 상태 저장 (있는 경우)
            was_playing = False
            position = 0
            if self.parent.current_media_type == 'video' and hasattr(self.parent, 'player') and self.parent.player:
                try:
                    was_playing = not self.parent.player.pause
                    position = self.parent.player.playback_time or 0
                except:
                    pass
            
            # 일반 모드에서 전체화면 모드로 전환
            self.parent.showFullScreen()

            # 상단 UI 및 하단 UI 잠금 상태에 따라 개별적으로 처리
            if not hasattr(self.parent, 'is_title_ui_locked') or not self.parent.is_title_ui_locked:
                if hasattr(self.parent, 'title_bar'):
                    self.parent.title_bar.hide()
            
            if not hasattr(self.parent, 'is_bottom_ui_locked') or not self.parent.is_bottom_ui_locked:
                if hasattr(self.parent, 'slider_widget'):
                    self.parent.slider_widget.hide()
                
                for row in self.parent.buttons:
                    for button in row:
                        button.hide()
            
            # 풀스크린 버튼 텍스트 업데이트
            if hasattr(self.parent, 'fullscreen_btn'):
                self.parent.fullscreen_btn.setText("🗗")  # 창 모드 아이콘
            
            # 전체화면 모드 상태 업데이트
            self.parent.is_in_fullscreen = True
            
            # 전체화면 모드로 전환 후 모든 미디어 타입에 대해 리사이징 적용
            QTimer.singleShot(100, self.parent.delayed_resize)

            # 잠금 버튼 상태 갱신 - 각각 개별적으로 갱신
            QTimer.singleShot(150, self.parent.update_title_lock_button_state)
            QTimer.singleShot(150, self.parent.update_ui_lock_button_state)
                
            # 비디오 복구 (필요한 경우)
            if self.parent.current_media_type == 'video' and position > 0:
                QTimer.singleShot(500, lambda: self.parent.restore_video_state(was_playing, position)) 