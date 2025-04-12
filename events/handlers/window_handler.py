"""
창 관련 이벤트 처리 모듈

이 모듈은 창 이벤트(리사이징, 전체화면, 최대화 등)를 처리하는 WindowHandler 클래스를 정의합니다.
ArchiveSift 클래스에서 창 이벤트 처리 코드를 분리하여 모듈화했습니다.
"""

from PyQt5.QtCore import QObject, QTimer, Qt
from PyQt5.QtWidgets import QApplication, QPushButton
from PyQt5.QtGui import QPixmap
import os

# media/handlers/image_handler.py 모듈에서 RAW 확장자 목록 가져오기
from media.handlers.image_handler import RAW_EXTENSIONS

class WindowHandler(QObject):
    """
    창 이벤트 처리 클래스
    
    이 클래스는 ArchiveSift의 창 이벤트 처리를 담당합니다.
    """
    
    def __init__(self, parent=None):
        """
        WindowHandler 초기화
        
        Args:
            parent: 부모 객체 (ArchiveSift 인스턴스)
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
        window_height = self.parent.height()
        
        # 슬라이더 위젯의 너비 설정 제거 - 레이아웃에서 자동으로 처리되도록 함
        # if hasattr(self.parent, 'slider_widget'):
        #     self.parent.slider_widget.setFixedWidth(window_width)
        
        if hasattr(self.parent, 'title_bar'):
            # 창 높이에 따라 제목표시줄 높이 계산 (2% 비율)
            title_height = int(window_height * 0.02)
            # 최소 높이 보장 (너무 작지 않도록)
            title_height = max(title_height, 25)
            self.parent.title_bar.setGeometry(0, 0, window_width, title_height)
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
            # 창 높이 비율에 맞춰 패딩 계산
            slider_height = int(window_height * 0.02)  # 창 높이의 2%
            slider_height = max(slider_height, 25)  # 최소 높이 보장
            padding = max(2, min(10, int(slider_height * 0.2)))  # 슬라이더 높이의 20%, 최소 2px, 최대 10px
            
            self.parent.slider_widget.setStyleSheet(f"""
                QWidget {{
                    background-color: rgba(52, 73, 94, 0.9);
                    padding: {padding}px;
                }}
            """)
        
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
        """Handle delayed UI update after resizing is complete"""
        try:
            # Adjust the currently displayed media size
            if hasattr(self.parent, 'current_image_path') and self.parent.current_image_path:
                file_ext = os.path.splitext(self.parent.current_image_path)[1].lower()
                
                # List of file extensions for each image type (categorized by library)
                # 1. Standard images (can be handled with standard library)
                normal_img_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.ico',
                                      '.jfif', '.jp2', '.jpe', '.jps', '.tga']
                
                # 2. Images requiring special libraries
                heic_heif_extensions = ['.heic', '.heif']
                avif_extensions = ['.avif']
                
                # 3. All static image extensions (processable by all image handlers)
                all_static_img_extensions = normal_img_extensions + heic_heif_extensions + avif_extensions + RAW_EXTENSIONS
                
                # Resize handling based on image type
                if file_ext in all_static_img_extensions:
                    # Special handling for RAW files
                    is_raw_file = file_ext in RAW_EXTENSIONS
                    
                    if is_raw_file:
                        # Check if the UI is hidden
                        ui_is_hidden = False
                        if hasattr(self.parent, 'ui_state_manager'):
                            ui_is_hidden = not self.parent.ui_state_manager.get_ui_visibility('controls') or not self.parent.ui_state_manager.get_ui_visibility('title_bar')
                        
                        # If the UI is hidden, use full window
                        if ui_is_hidden:
                            # Set flag to use the full window area
                            self.parent.image_handler.use_full_window = True
                        
                        # Refresh screen via forced event processing
                        QApplication.processEvents()
                    
                    # Resize image using ImageHandler
                    self.parent.image_handler.resize()
                    
                    # Post-process RAW files
                    if is_raw_file:
                        # Reset flag
                        self.parent.image_handler.use_full_window = False
                        
                        # Force update of image label
                        QApplication.processEvents()
                        self.parent.image_label.repaint()
                        self.parent.image_label.update()
                elif file_ext == '.psd':
                    # Resize PSD file using PSDHandler
                    self.parent.psd_handler.resize()
                elif (file_ext == '.gif' or file_ext == '.webp') and self.parent.current_media_type in ['gif_animation', 'webp_animation']:
                    # Resize animation using animation handler
                    if hasattr(self.parent, 'animation_handler'):
                        self.parent.animation_handler.scale_animation()
                    else:
                        # Process using legacy method (for compatibility)
                        if file_ext == '.gif':
                            self.parent.scale_gif()
                        elif file_ext == '.webp':
                            self.parent.scale_webp()
                        # Force frame update for proper display of animation after UI processing
                        QApplication.processEvents()
                elif file_ext == '.webp' and self.parent.current_media_type == 'webp_image':
                    # Process static WEBP image
                    if hasattr(self.parent, 'animation_handler'):
                        self.parent.animation_handler.rotate_static_image(self.parent.current_image_path)
                    else:
                        # Process normal WEBP image (if not animated)
                        pixmap = QPixmap(self.parent.current_image_path)
                        if not pixmap.isNull():
                            scaled_pixmap = pixmap.scaled(self.parent.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            self.parent.image_label.setPixmap(scaled_pixmap)
                elif file_ext in ['.mp4', '.avi', '.wmv', '.ts', '.m2ts', '.mov', '.qt', '.mkv', '.flv', '.webm', '.3gp', '.m4v', '.mpg', '.mpeg', '.vob', '.wav', '.flac', '.mp3', '.aac', '.m4a', '.ogg']:
                    # Update MPV player's window ID
                    if hasattr(self.parent, 'player'):
                        self.parent.player.wid = int(self.parent.image_label.winId())
            
            # Update image info label
            if hasattr(self.parent, 'image_info_label') and self.parent.image_files:
                self.parent.update_image_info()

            # Update lock and bookmark button states (restore style after resizing)
            self.parent.update_ui_lock_button_state()
            self.parent.update_title_lock_button_state()
            self.parent.controls_layout.update_bookmark_button_state()
                    
        except Exception as e:
            pass
            
    def toggle_fullscreen(self):
        """전체화면 모드를 전환합니다."""
        if self.parent.isFullScreen():
            # 전체화면 모드에서 일반 모드로 전환
            self.parent.showNormal()
            
            # 풀스크린 버튼 텍스트 업데이트
            if hasattr(self.parent, 'fullscreen_btn'):
                self.parent.fullscreen_btn.setText("🗖")  # 전체화면 아이콘
            
            # 전체화면 모드 상태 업데이트 - UI 상태 관리자에 위임
            if hasattr(self.parent, 'ui_state_manager'):
                self.parent.ui_state_manager.update_fullscreen_state(False)
            else:
                # 이전 코드와의 호환성을 위해 유지
                self.parent.is_in_fullscreen = False
                
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
            
            # 전체화면에서 일반 모드로 전환 후 모든 미디어 타입에 대해 리사이징 적용
            QTimer.singleShot(100, self.parent.delayed_resize)

            # 잠금 버튼 상태 갱신 - 각각 개별적으로 갱신
            QTimer.singleShot(150, self.parent.update_title_lock_button_state)
            QTimer.singleShot(150, self.parent.update_ui_lock_button_state)
                
        else:
            # 현재 비디오 상태 저장 (있는 경우)
            was_playing = False
            position = 0
            if hasattr(self.parent, 'current_media_type') and self.parent.current_media_type == 'video' and hasattr(self.parent, 'player') and self.parent.player:
                try:
                    was_playing = not self.parent.player.pause
                    position = self.parent.player.playback_time or 0
                except:
                    pass
            
            # 일반 모드에서 전체화면 모드로 전환
            self.parent.showFullScreen()

            # 전체화면 모드 상태 업데이트 - UI 상태 관리자에 위임
            if hasattr(self.parent, 'ui_state_manager'):
                self.parent.ui_state_manager.update_fullscreen_state(True)
            else:
                # 이전 코드와의 호환성을 위해 유지
                self.parent.is_in_fullscreen = True
                
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
            
            # 전체화면 모드로 전환 후 모든 미디어 타입에 대해 리사이징 적용
            QTimer.singleShot(100, self.parent.delayed_resize)

            # 잠금 버튼 상태 갱신 - 각각 개별적으로 갱신
            QTimer.singleShot(150, self.parent.update_title_lock_button_state)
            QTimer.singleShot(150, self.parent.update_ui_lock_button_state)
                
            # 비디오 복구 (필요한 경우)
            if hasattr(self.parent, 'current_media_type') and self.parent.current_media_type == 'video' and position > 0:
                QTimer.singleShot(500, lambda: self.parent.restore_video_state(was_playing, position))

    def toggle_maximize_state(self):
        """Toggle between maximized and normal state."""
        if self.parent.isMaximized():
            self.parent.showNormal()
            self.parent.max_btn.setText("□")  # When in normal state, display □
            # Removed debug print for normal state.
        else:
            self.parent.showMaximized()
            self.parent.max_btn.setText("❐")  # When in maximized state, display ❐
            # Removed debug print for maximized state.
        
        # Set window focus (improve event handling)
        QTimer.singleShot(50, self.parent.setFocus) 

    def close_event(self, event):
        """
        Perform necessary cleanup tasks when the application terminates.
        """
        # Removed debug print for program shutdown cleanup start.
        
        # Check initial state for debugging
        if hasattr(self.parent, 'qmovie_debugger') and self.parent.qmovie_debugger.is_debug_mode():
            self.parent.qmovie_debugger.debug_qmovie_before_cleanup()
        
        # Clean up current media resources
        self.parent.cleanup_current_media()
        
        # Clean up ImageLoader (image loader thread cleanup)
        if hasattr(self.parent, 'image_loader') and self.parent.image_loader:
            # Removed debug print for ImageLoader cleanup start.
            self.parent.image_loader.cleanup()
            # Removed debug print for ImageLoader cleanup complete.
        
        # Unload PSD handler
        if hasattr(self.parent, 'psd_handler') and self.parent.psd_handler:
            self.parent.psd_handler.unload()
            
        # Clean up image cache
        if hasattr(self.parent, 'image_cache') and self.parent.image_cache:
            # Removed debug print for image cache cleanup start.
            self.parent.image_cache.clear()
            # Removed debug print for image cache cleanup complete.
            
        # Clean up PSD cache
        if hasattr(self.parent, 'psd_cache') and self.parent.psd_cache:
            # Removed debug print for PSD cache cleanup start.
            self.parent.psd_cache.clear()
            # Removed debug print for PSD cache cleanup complete.
            
        # Clean up GIF cache
        if hasattr(self.parent, 'gif_cache') and self.parent.gif_cache:
            # Removed debug print for GIF cache cleanup start.
            # Simplified QMovie cleanup process
            try:
                from PyQt5.QtGui import QMovie
                from PyQt5.QtWidgets import QApplication
                
                # Check and clean up QMovie objects in the cache
                for key, item in list(self.parent.gif_cache.cache.items()):
                    if isinstance(item, QMovie):
                        # Perform basic cleanup steps
                        item.stop()
                        item.deleteLater()
                
                # Process events once
                QApplication.processEvents()
                
                # Clear cache
                self.parent.gif_cache.clear()
                self.parent.gif_cache = None  # Release reference
            except Exception as e:
                # Removed debug print for error during GIF cache cleanup.
                pass
            # Removed debug print for GIF cache cleanup complete.
            
        # Clean up active timers
        for timer in list(self.parent.timers):
            try:
                if timer.isActive():
                    timer.stop()
                timer.deleteLater()
            except Exception as e:
                # Removed debug print for timer cleanup error.
                pass
        self.parent.timers.clear()  # Clear timer list
        
        # Additional cleanup for singleshot timers
        for timer in list(self.parent.singleshot_timers):
            try:
                if timer.isActive():
                    timer.stop()
                timer.deleteLater()
            except Exception as e:
                # Removed debug print for singleshot timer cleanup error.
                pass
        self.parent.singleshot_timers.clear()
                
        # Save bookmarks
        self.parent.save_bookmarks()
        
        # Check state after cleanup for debugging
        if hasattr(self.parent, 'qmovie_debugger') and self.parent.qmovie_debugger.is_debug_mode():
            self.parent.qmovie_debugger.debug_qmovie_after_cleanup()
            
        # Force event processing after final cleanup to ensure all tasks are completed
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
        
        # Continue processing event (close window)
        event.accept() 