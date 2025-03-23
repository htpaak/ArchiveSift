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
            viewer: ImageViewer 인스턴스
        """
        self.viewer = viewer
    
    def cleanup_current_media(self):
        """현재 로드된 미디어 리소스를 정리합니다."""
        # 디버깅 모드가 활성화된 경우 정리 전 상태 출력
        if self.viewer.qmovie_debugger.is_debug_mode():
            self.viewer.qmovie_debugger.debug_qmovie_before_cleanup()
        
        print("미디어 리소스 정리 시작...")
        
        # 비디오 리소스 정리
        self.cleanup_video_resources()
        
        # 애니메이션 리소스 정리
        self.cleanup_animation_resources()
        
        # UI 컴포넌트 초기화
        self.cleanup_ui_components()
        
        # 가비지 컬렉션 수행
        self.viewer.perform_garbage_collection()
            
        print("미디어 리소스 정리 완료")

        # 디버깅을 위한 정리 후 상태 확인
        if self.viewer.qmovie_debugger.is_debug_mode():
            self.viewer.qmovie_debugger.debug_qmovie_after_cleanup()
        
    def cleanup_video_resources(self):
        """비디오 관련 리소스 정리"""
        # 비디오 재생 중지
        self.viewer.stop_video()
        
    def cleanup_animation_resources(self):
        """애니메이션 관련 리소스 정리"""
        # 애니메이션 핸들러 존재 여부 확인
        animation_handler_exists = hasattr(self.viewer, 'animation_handler')

        # 애니메이션 핸들러 리소스 정리 (current_movie 포함)
        if animation_handler_exists:
            print("애니메이션 핸들러 정리 시작...")
            self.viewer.animation_handler.cleanup()
            
            # 이벤트 처리 루프 실행으로 UI 갱신 및 정리 작업 완료 유도
            QApplication.processEvents()
            
    def cleanup_ui_components(self):
        """UI 컴포넌트 초기화"""
        # 이미지 라벨 초기화 - MediaDisplay의 clear_media 메서드 사용
        if hasattr(self.viewer, 'image_label'):
            print("MediaDisplay 초기화...")
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