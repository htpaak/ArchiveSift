"""
오류 처리 모듈

이 모듈은 애플리케이션 전체에서 발생하는 예외를 중앙에서 처리하고
로깅하는 기능을 제공합니다.
"""
import sys
import traceback
from typing import Dict, Any, Optional, Callable, List, Tuple, Type
from PyQt5.QtWidgets import QMessageBox, QApplication

from .base_exception import MediaViewerException, OperationCancelledError
try:
    from core.logger import Logger
except ImportError:
    # Logger 클래스가 아직 로드되지 않은 경우 (초기 로딩 중 발생 가능)
    class Logger:
        def __init__(self, name):
            self.name = name
        
        def error(self, message, **kwargs):
            print(f"[ERROR] {message}", kwargs)
        
        def warning(self, message, **kwargs):
            print(f"[WARNING] {message}", kwargs)
        
        def info(self, message, **kwargs):
            print(f"[INFO] {message}", kwargs)


class ErrorHandler:
    """
    애플리케이션 예외 중앙 처리 클래스
    
    애플리케이션 전체에서 발생하는 예외를 일관된 방식으로 처리하고
    로깅합니다. 사용자에게 적절한 오류 메시지를 표시할 수 있습니다.
    """
    
    # 싱글톤 인스턴스
    _instance = None
    
    @classmethod
    def get_instance(cls) -> 'ErrorHandler':
        """
        ErrorHandler 인스턴스 반환 (싱글톤 패턴)
        
        Returns:
            ErrorHandler 인스턴스
        """
        if cls._instance is None:
            cls._instance = ErrorHandler()
        return cls._instance
    
    def __init__(self):
        """ErrorHandler 초기화"""
        # 싱글톤 패턴 강제
        if ErrorHandler._instance is not None:
            raise RuntimeError("ErrorHandler는 싱글톤입니다. get_instance()를 사용하세요.")
        
        # 로거 초기화
        self.logger = Logger("error_handler")
        
        # 특정 예외 타입에 대한 커스텀 핸들러 맵
        self._custom_handlers: Dict[Type[Exception], Callable] = {}
        
        # 무시할 예외 타입 리스트
        self._ignored_exceptions: List[Type[Exception]] = [
            OperationCancelledError  # 작업 취소는 오류가 아님
        ]
        
        # 마지막 오류 저장
        self._last_error: Optional[Dict[str, Any]] = None
    
    def handle_exception(self, exception: Exception, show_ui: bool = True,
                         context: Optional[Dict[str, Any]] = None) -> bool:
        """
        예외 처리
        
        Args:
            exception: 처리할 예외 객체
            show_ui: 사용자 UI에 오류 메시지 표시 여부
            context: 추가 컨텍스트 정보 딕셔너리
            
        Returns:
            처리 성공 여부 (특수 처리된 예외는 True, 그 외에는 False)
        """
        # 무시할 예외 확인
        if any(isinstance(exception, ignored_type) for ignored_type in self._ignored_exceptions):
            return True
        
        # 컨텍스트 기본값
        if context is None:
            context = {}
        
        # 예외 정보 수집
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        # MediaViewerException이 아닌 경우 변환
        if not isinstance(exception, MediaViewerException):
            wrapped_exception = MediaViewerException.from_exception(exception)
        else:
            wrapped_exception = exception
        
        # 오류 정보 생성
        error_info = wrapped_exception.get_error_dict()
        error_info['traceback'] = traceback_str
        error_info.update(context)
        
        # 마지막 오류 저장
        self._last_error = error_info
        
        # 오류 로깅
        self.logger.error(
            f"예외 발생: {wrapped_exception}",
            error_type=error_info['error_type'],
            details=error_info['details'],
            traceback=traceback_str
        )
        
        # 커스텀 핸들러가 있는 경우 실행
        for exc_type, handler in self._custom_handlers.items():
            if isinstance(exception, exc_type):
                try:
                    return handler(wrapped_exception, error_info, context)
                except Exception as handler_exc:
                    self.logger.error(f"커스텀 예외 핸들러 실행 중 오류: {handler_exc}")
        
        # UI에 오류 메시지 표시
        if show_ui:
            self._show_error_message(wrapped_exception, error_info, context)
        
        return False
    
    def _show_error_message(self, exception: MediaViewerException,
                           error_info: Dict[str, Any],
                           context: Dict[str, Any]) -> None:
        """
        사용자 UI에 오류 메시지 표시
        
        Args:
            exception: 처리할 예외 객체
            error_info: 오류 정보 딕셔너리
            context: 추가 컨텍스트 정보
        """
        # 기본 제목과 메시지
        title = f"오류: {error_info['error_type']}"
        message = str(exception)
        
        # 애플리케이션이 초기화되었는지 확인
        app = QApplication.instance()
        if app is not None:
            QMessageBox.critical(None, title, message)
        else:
            # 콘솔 출력 (GUI 없을 때)
            print(f"\n{title}\n{message}\n")
    
    def register_custom_handler(self, exception_type: Type[Exception],
                               handler: Callable[[MediaViewerException, Dict[str, Any], Dict[str, Any]], bool]) -> None:
        """
        특정 예외 타입에 대한 커스텀 핸들러 등록
        
        Args:
            exception_type: 처리할 예외 타입
            handler: 핸들러 함수 (매개변수: 예외 객체, 오류 정보, 컨텍스트)
                     반환값이 True면 처리 완료로 간주
        """
        self._custom_handlers[exception_type] = handler
    
    def unregister_custom_handler(self, exception_type: Type[Exception]) -> None:
        """
        커스텀 핸들러 등록 해제
        
        Args:
            exception_type: 등록 해제할 예외 타입
        """
        if exception_type in self._custom_handlers:
            del self._custom_handlers[exception_type]
    
    def add_ignored_exception(self, exception_type: Type[Exception]) -> None:
        """
        무시할 예외 타입 추가
        
        Args:
            exception_type: 무시할 예외 타입
        """
        if exception_type not in self._ignored_exceptions:
            self._ignored_exceptions.append(exception_type)
    
    def remove_ignored_exception(self, exception_type: Type[Exception]) -> None:
        """
        무시할 예외 타입 제거
        
        Args:
            exception_type: 무시 해제할 예외 타입
        """
        if exception_type in self._ignored_exceptions:
            self._ignored_exceptions.remove(exception_type)
    
    def get_last_error(self) -> Optional[Dict[str, Any]]:
        """
        마지막으로 처리된 오류 정보 반환
        
        Returns:
            마지막 오류 정보 딕셔너리 또는 None
        """
        return self._last_error
    
    def clear_last_error(self) -> None:
        """마지막 오류 정보 초기화"""
        self._last_error = None


# 편의를 위한 글로벌 함수들
def get_error_handler() -> ErrorHandler:
    """전역 오류 핸들러 인스턴스 반환"""
    return ErrorHandler.get_instance()


def handle_exception(exception: Exception, show_ui: bool = True,
                    context: Optional[Dict[str, Any]] = None) -> bool:
    """예외 처리 (전역 함수)"""
    return get_error_handler().handle_exception(exception, show_ui, context)


def exception_handler(func: Callable) -> Callable:
    """
    함수에 자동 예외 처리를 추가하는 데코레이터
    
    Args:
        func: 데코레이트할 함수
        
    Returns:
        래핑된 함수
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            handle_exception(e)
            return None
    
    return wrapper
