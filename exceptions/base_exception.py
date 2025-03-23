"""
기본 예외 클래스 모듈

이 모듈은 애플리케이션 전체에서 사용되는 기본 예외 클래스를
정의합니다. 모든 애플리케이션 예외는 이 클래스를 상속받습니다.
"""
from typing import Dict, Any, Optional


class MediaViewerException(Exception):
    """
    이미지 뷰어 애플리케이션의 기본 예외 클래스
    
    모든 애플리케이션 관련 예외는 이 클래스를 상속받습니다.
    예외 발생 시 추가 정보를 포함할 수 있는 details 딕셔너리가 제공됩니다.
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        MediaViewerException 초기화
        
        Args:
            message: 예외 메시지
            details: 추가 정보를 담은 딕셔너리 (선택 사항)
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """예외를 문자열로 표현"""
        if self.details:
            details_str = ', '.join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} (세부 정보: {details_str})"
        return self.message
    
    def get_error_dict(self) -> Dict[str, Any]:
        """
        오류 정보를 딕셔너리로 반환
        
        Returns:
            오류 메시지와 세부 정보를 포함한 딕셔너리
        """
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'details': self.details
        }
    
    def add_detail(self, key: str, value: Any) -> 'MediaViewerException':
        """
        예외 세부 정보 추가
        
        Args:
            key: 세부 정보 키
            value: 세부 정보 값
            
        Returns:
            현재 예외 인스턴스 (메서드 체이닝 가능)
        """
        self.details[key] = value
        return self
    
    @classmethod
    def from_exception(cls, exception: Exception, message: Optional[str] = None) -> 'MediaViewerException':
        """
        기존 예외를 MediaViewerException으로 변환
        
        Args:
            exception: 원본 예외 객체
            message: 새 메시지 (없으면 원본 예외 메시지 사용)
            
        Returns:
            MediaViewerException 인스턴스
        """
        if isinstance(exception, MediaViewerException):
            return exception
        
        # 메시지가 지정되지 않았으면 원본 예외 메시지 사용
        if message is None:
            message = str(exception)
        
        return cls(message, {'original_exception': str(exception)})


class OperationCancelledError(MediaViewerException):
    """
    사용자가 작업을 취소한 경우 발생하는 예외
    
    이 예외는 중대한 오류로 간주되지 않으며, 정상적인 프로그램 흐름의
    일부로 처리될 수 있습니다.
    """
    
    def __init__(self, message: str = "작업이 취소되었습니다", details: Optional[Dict[str, Any]] = None):
        """
        OperationCancelledError 초기화
        
        Args:
            message: 예외 메시지
            details: 추가 정보를 담은 딕셔너리 (선택 사항)
        """
        super().__init__(message, details)


class ConfigurationError(MediaViewerException):
    """
    설정 오류 예외
    
    설정 파일 로드/저장 또는 환경 구성 관련 오류에 사용됩니다.
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        ConfigurationError 초기화
        
        Args:
            message: 예외 메시지
            details: 추가 정보를 담은 딕셔너리 (선택 사항)
        """
        super().__init__(message, details) 