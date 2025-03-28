"""
애플리케이션 상태 관리 모듈

이 모듈은 애플리케이션의 전체 상태를 관리하고 옵저버 패턴을 통해
상태 변경 시 알림을 제공합니다.
"""
from typing import Dict, List, Any, Callable, Optional


class StateManager:
    """
    애플리케이션 상태 관리 클래스
    
    모든 컴포넌트가 공유하는 중앙 집중식 상태 저장소로 작동하며,
    상태 변경 시 등록된 옵저버에게 알림을 보냅니다.
    """
    
    def __init__(self):
        """StateManager 초기화"""
        self._states: Dict[str, Any] = {}
        self._observers: Dict[str, List[Callable]] = {}
    
    def set_state(self, key: str, value: Any) -> None:
        """
        상태값을 설정하고 관련 옵저버에게 알림
        
        Args:
            key: 상태 키
            value: 설정할 값
        """
        old_value = self._states.get(key)
        self._states[key] = value
        
        # 값이 변경된 경우에만 옵저버에게 알림
        if old_value != value:
            self._notify_observers(key, value, old_value)
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """
        상태값을 조회
        
        Args:
            key: 상태 키
            default: 키가 없을 경우 반환할 기본값
            
        Returns:
            저장된 상태값 또는 기본값
        """
        return self._states.get(key, default)
    
    def register_observer(self, key: str, callback: Callable[[Any, Any], None]) -> None:
        """
        상태 변경 옵저버 등록
        
        Args:
            key: 관찰할 상태 키
            callback: 상태 변경 시 호출할 콜백 함수 (매개변수: 새 값, 이전 값)
        """
        if key not in self._observers:
            self._observers[key] = []
        
        if callback not in self._observers[key]:
            self._observers[key].append(callback)
    
    def unregister_observer(self, key: str, callback: Callable) -> None:
        """
        상태 변경 옵저버 등록 해제
        
        Args:
            key: 관찰 중인 상태 키
            callback: 제거할 콜백 함수
        """
        if key in self._observers and callback in self._observers[key]:
            self._observers[key].remove(callback)
            
            # 옵저버가 없으면 키 제거
            if not self._observers[key]:
                del self._observers[key]
    
    def _notify_observers(self, key: str, new_value: Any, old_value: Any) -> None:
        """
        Notify observers when the state changes
        상태 변경 시 옵저버에게 알림
        
        Args:
            key: key of the changed state
                  변경된 상태 키
            new_value: new state value
                       새 상태값
            old_value: previous state value
                       이전 상태값
        """
        if key in self._observers:
            for callback in self._observers[key]:
                try:
                    callback(new_value, old_value)
                except Exception as e:
                    # Continue calling other observers even if an exception occurs
                    # 예외가 발생해도 다른 옵저버 호출을 계속 진행
                    pass
    
    def reset_state(self, key: str) -> None:
        """
        특정 상태를 초기화(제거)
        
        Args:
            key: 초기화할 상태 키
        """
        if key in self._states:
            old_value = self._states[key]
            del self._states[key]
            self._notify_observers(key, None, old_value)
    
    def reset_all_states(self) -> None:
        """모든 상태를 초기화"""
        keys = list(self._states.keys())
        for key in keys:
            self.reset_state(key)
    
    def has_state(self, key: str) -> bool:
        """
        상태 키가 존재하는지 확인
        
        Args:
            key: 확인할 상태 키
            
        Returns:
            상태 키 존재 여부
        """
        return key in self._states 