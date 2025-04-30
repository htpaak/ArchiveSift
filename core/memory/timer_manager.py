"""
타이머 관리 모듈

애플리케이션에서 사용하는 타이머 객체들을 관리하는 모듈입니다.
메모리 누수를 방지하기 위한 타이머 추적 및 정리 기능을 제공합니다.
"""

from PyQt5.QtCore import QTimer

class TimerManager:
    """
    타이머 객체 관리를 위한 클래스
    
    일회성 타이머의 생성, 추적, 정리를 담당합니다.
    메모리 누수를 방지하기 위해 모든 타이머 객체를 관리합니다.
    """
    
    def __init__(self, viewer):
        """
        TimerManager 클래스를 초기화합니다.
        
        Args:
            viewer: ImageSortingPAAK 인스턴스
        """
        self.viewer = viewer
        self.singleshot_timers = []  # 일회성 타이머 추적을 위한 리스트
    
    def create_single_shot_timer(self, timeout, callback):
        """
        싱글샷 타이머를 생성하고 추적합니다.
        
        Args:
            timeout (int): 타이머 실행 지연 시간 (밀리초)
            callback (callable): 타이머 만료 시 실행할 콜백 함수
            
        Returns:
            QTimer: 생성된 타이머 객체
        """
        timer = QTimer(self.viewer)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self._handle_single_shot_timeout(timer, callback))
        timer.start(timeout)
        
        # 타이머 추적 리스트에 추가
        self.singleshot_timers.append(timer)
        return timer
    
    def _handle_single_shot_timeout(self, timer, callback):
        """
        싱글샷 타이머의 타임아웃을 처리합니다.
        
        Args:
            timer (QTimer): 만료된 타이머
            callback (callable): 실행할 콜백 함수
        """
        try:
            # 콜백 실행
            callback()
        finally:
            # 타이머 정리
            if timer in self.singleshot_timers:
                self.singleshot_timers.remove(timer)
            timer.deleteLater()
    
    def cancel_timer(self, timer):
        """
        특정 타이머를 취소하고 정리합니다.
        
        Args:
            timer (QTimer): 취소할 타이머 객체
        """
        if timer in self.singleshot_timers:
            timer.stop()
            self.singleshot_timers.remove(timer)
            timer.deleteLater()
    
    def cancel_all_timers(self):
        """모든 타이머를 취소하고 정리합니다."""
        for timer in self.singleshot_timers[:]:  # 복사본으로 반복 (수정 안전성)
            timer.stop()
            self.singleshot_timers.remove(timer)
            timer.deleteLater()
    
    def get_active_timer_count(self):
        """
        활성 타이머 수를 반환합니다.
        
        Returns:
            int: 활성 상태인 타이머 수
        """
        return len(self.singleshot_timers) 