"""
리소스 클리너 모듈

미디어 리소스, UI 컴포넌트 등의 정리를 담당하는 모듈입니다.
메모리 누수 방지와 리소스 관리를 위한 기능을 제공합니다.
"""

from PyQt5.QtWidgets import QApplication

class ResourceCleaner:
    """
    애플리케이션 리소스 정리를 위한 클래스
    
    미디어 파일(이미지, 비디오, 애니메이션) 및 UI 컴포넌트의 리소스 정리를 담당합니다.
    """
    
    def __init__(self, viewer):
        """
        ResourceCleaner 클래스를 초기화합니다.
        
        Args:
            viewer: ArchiveSift 인스턴스
        """
        self.viewer = viewer
    
    def cleanup_current_media(self):
        """Clean up the currently loaded media resources."""
        print("Media resource cleanup started...")
        
        # Clean up video resources
        self.cleanup_video_resources()
        
        # Clean up audio resources
        self.cleanup_audio_resources()
        
        # Clean up animation resources
        self.cleanup_animation_resources()
        
        # Initialize UI components
        self.cleanup_ui_components()
        
        # Perform garbage collection
        self.viewer.perform_garbage_collection()
            
        print("Media resource cleanup completed")
        
    def cleanup_video_resources(self):
        """Clean up video related resources"""
        # Stop video playback
        self.viewer.stop_video()
        
    def cleanup_audio_resources(self):
        """Clean up audio related resources"""
        # Check if audio handler exists
        if hasattr(self.viewer, 'audio_handler'):
            # Stop audio playback and clean up resources
            self.viewer.cleanup_audio_resources()
        
    def cleanup_animation_resources(self):
        """Clean up animation related resources"""
        # Check if animation handler exists
        animation_handler_exists = hasattr(self.viewer, 'animation_handler')

        # Clean up animation handler resources (including current_movie)
        if animation_handler_exists:
            print("Animation handler cleanup started...")
            self.viewer.animation_handler.cleanup()
            
            # Execute event processing loop to update UI and finalize cleanup
            QApplication.processEvents()
            
    def cleanup_ui_components(self):
        """UI 컴포넌트 초기화"""
        # 이미지 라벨 초기화 - MediaDisplay의 clear_media 메서드 사용
        if hasattr(self.viewer, 'image_label'):
            print("Initializing MediaDisplay...")
            # MediaDisplay의 clear_media 메서드 호출
            self.viewer.image_label.clear_media()
            # 이벤트 프로세싱
            QApplication.processEvents()
        
        # 슬라이더 신호 연결 해제 및 초기화
        self.viewer.disconnect_all_slider_signals()
        if hasattr(self.viewer, 'playback_slider'):
            self.viewer.playback_slider.setRange(0, 0)
            self.viewer.playback_slider.setValue(0)

        # 재생 버튼 상태 초기화
        if hasattr(self.viewer, 'play_button'):
            self.viewer.play_button.set_play_state(True)  # 일시정지 아이콘으로 설정
        
        # 시간 레이블 초기화
        if hasattr(self.viewer, 'time_label'):
            self.viewer.time_label.setText("00:00 / 00:00")
            self.viewer.time_label.show() 