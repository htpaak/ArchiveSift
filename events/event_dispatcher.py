"""
이벤트 디스패처 모듈

이 모듈은 애플리케이션 전체에서 발생하는 이벤트를 중앙에서 관리하고
적절한 핸들러에게 전달하는 역할을 담당합니다.
"""
from typing import Dict, List, Callable, Any, Optional, Union, Set
from .signals import get_signals, MediaViewerSignals


class EventDispatcher:
    """
    이벤트 디스패처 클래스
    
    이벤트 기반 통신을 위한 중앙 관리자로, 이벤트 핸들러 등록 및
    이벤트 발생(dispatch)을 담당합니다.
    """
    
    # 인스턴스 싱글톤
    _instance = None
    
    @classmethod
    def get_instance(cls) -> 'EventDispatcher':
        """
        EventDispatcher 인스턴스 반환 (싱글톤 패턴)
        
        Returns:
            EventDispatcher 인스턴스
        """
        if cls._instance is None:
            cls._instance = EventDispatcher()
        return cls._instance
    
    def __init__(self):
        """EventDispatcher 초기화"""
        # 이미 인스턴스가 있으면 싱글톤 패턴 강제
        if EventDispatcher._instance is not None:
            raise RuntimeError("EventDispatcher is a singleton. Use get_instance() instead.")
        
        # 기본 핸들러 맵 초기화
        self._handlers: Dict[str, List[Callable]] = {}
        
        # 신호 객체 가져오기
        self.signals = get_signals()
        
        # 신호 연결
        self._connect_signals()
    
    def _connect_signals(self) -> None:
        """내부 신호와 디스패처 연결"""
        # 예시: 애플리케이션 시작/종료 신호 연결
        self.signals.application.application_start.connect(
            lambda: self.dispatch('application:start')
        )
        self.signals.application.application_exit.connect(
            lambda: self.dispatch('application:exit')
        )
        
        # 미디어 관련 신호 연결
        self.signals.media.media_loaded.connect(
            lambda path: self.dispatch('media:loaded', path=path)
        )
        self.signals.media.media_loading_failed.connect(
            lambda path, error: self.dispatch('media:loading_failed', path=path, error=error)
        )
        
        # 네비게이션 관련 신호 연결
        self.signals.navigation.navigation_index_changed.connect(
            lambda index: self.dispatch('navigation:index_changed', index=index)
        )
        self.signals.navigation.directory_changed.connect(
            lambda path: self.dispatch('navigation:directory_changed', path=path)
        )
        
        # UI 관련 신호 연결
        self.signals.ui.ui_lock_changed.connect(
            lambda locked: self.dispatch('ui:lock_changed', locked=locked)
        )
        
        # 파일 작업 관련 신호 연결
        self.signals.file_operation.file_operation_completed.connect(
            lambda op_type, success, message: self.dispatch(
                'file:operation_completed', 
                operation_type=op_type, 
                success=success, 
                message=message
            )
        )
    
    def register_handler(self, event_type: str, handler: Callable) -> None:
        """
        이벤트 핸들러 등록
        
        Args:
            event_type: 이벤트 유형 (예: 'media:loaded', 'ui:lock_changed')
            handler: 이벤트 처리 콜백 함수
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
    
    def unregister_handler(self, event_type: str, handler: Callable) -> None:
        """
        이벤트 핸들러 등록 해제
        
        Args:
            event_type: 이벤트 유형
            handler: 제거할 핸들러 함수
        """
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            
            # 핸들러가 없으면 이벤트 유형 키 제거
            if not self._handlers[event_type]:
                del self._handlers[event_type]
    
    def dispatch(self, event_type: str, **kwargs) -> bool:
        """
        이벤트 발생 및 핸들러 호출
        
        Args:
            event_type: 이벤트 유형
            **kwargs: 이벤트 데이터
            
        Returns:
            이벤트 처리 성공 여부
        """
        handled = False
        
        # 직접 등록된 핸들러 실행
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    handler(**kwargs)
                    handled = True
                except Exception as e:
                    pass
        # Wildcard handler execution (receive all events)
        if '*' in self._handlers:
            for handler in self._handlers['*']:
                try:
                    handler(event_type=event_type, **kwargs)
                    handled = True
                except Exception as e:
                    pass
        return handled
    
    def get_registered_events(self) -> Set[str]:
        """
        등록된 모든 이벤트 유형 반환
        
        Returns:
            등록된 이벤트 유형 집합
        """
        return set(self._handlers.keys())


# 편의를 위한 글로벌 함수들
def get_dispatcher() -> EventDispatcher:
    """전역 이벤트 디스패처 인스턴스 반환"""
    return EventDispatcher.get_instance()


def register_handler(event_type: str, handler: Callable) -> None:
    """이벤트 핸들러 등록 (전역 함수)"""
    get_dispatcher().register_handler(event_type, handler)


def unregister_handler(event_type: str, handler: Callable) -> None:
    """이벤트 핸들러 등록 해제 (전역 함수)"""
    get_dispatcher().unregister_handler(event_type, handler)


def dispatch(event_type: str, **kwargs) -> bool:
    """이벤트 발생 (전역 함수)"""
    return get_dispatcher().dispatch(event_type, **kwargs) 