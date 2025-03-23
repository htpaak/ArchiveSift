"""
미디어 처리 관련 예외 클래스 모듈

이 모듈은 미디어 파일 로딩, 표시, 처리 등 미디어 작업 관련
예외 클래스를 정의합니다.
"""
from typing import Dict, Any, Optional
from .base_exception import MediaViewerException


class MediaError(MediaViewerException):
    """
    미디어 관련 기본 예외 클래스
    
    모든 미디어 처리 관련 예외는 이 클래스를 상속받습니다.
    """
    pass


class MediaLoadError(MediaError):
    """
    미디어 로드 실패 예외
    
    미디어 파일을 로드할 수 없을 때 발생합니다.
    """
    
    def __init__(self, message: str = "미디어를 로드할 수 없습니다", 
                 file_path: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        """
        MediaLoadError 초기화
        
        Args:
            message: 예외 메시지
            file_path: 로드하려고 시도한 파일 경로
            details: 추가 정보를 담은 딕셔너리 (선택 사항)
        """
        if details is None:
            details = {}
        
        if file_path:
            details['file_path'] = file_path
        
        super().__init__(message, details)


class UnsupportedFormatError(MediaError):
    """
    지원되지 않는 미디어 형식 예외
    
    지원되지 않는 파일 형식을 로드하려고 할 때 발생합니다.
    """
    
    def __init__(self, message: str = "지원되지 않는 미디어 형식입니다", 
                 file_path: Optional[str] = None, 
                 format_name: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        """
        UnsupportedFormatError 초기화
        
        Args:
            message: 예외 메시지
            file_path: 로드하려고 시도한 파일 경로
            format_name: 파일 형식 이름
            details: 추가 정보를 담은 딕셔너리 (선택 사항)
        """
        if details is None:
            details = {}
        
        if file_path:
            details['file_path'] = file_path
        
        if format_name:
            details['format'] = format_name
        
        super().__init__(message, details)


class MediaProcessingError(MediaError):
    """
    미디어 처리 과정에서 발생한 예외
    
    이미지 처리, 비디오 프레임 추출 등의 작업 중 발생한 오류입니다.
    """
    
    def __init__(self, message: str = "미디어 처리 중 오류가 발생했습니다", 
                 operation: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        """
        MediaProcessingError 초기화
        
        Args:
            message: 예외 메시지
            operation: 수행 중이던 작업 이름
            details: 추가 정보를 담은 딕셔너리 (선택 사항)
        """
        if details is None:
            details = {}
        
        if operation:
            details['operation'] = operation
        
        super().__init__(message, details)


class MediaDisplayError(MediaError):
    """
    미디어 표시 과정에서 발생한 예외
    
    UI에 미디어를 표시하는 과정에서 발생한 오류입니다.
    """
    
    def __init__(self, message: str = "미디어를 표시할 수 없습니다", 
                 details: Optional[Dict[str, Any]] = None):
        """
        MediaDisplayError 초기화
        
        Args:
            message: 예외 메시지
            details: 추가 정보를 담은 딕셔너리 (선택 사항)
        """
        super().__init__(message, details)


class CacheError(MediaError):
    """
    미디어 캐시 관련 예외
    
    캐시 저장, 로드, 관리 등의 작업 중 발생한 오류입니다.
    """
    
    def __init__(self, message: str = "미디어 캐시 작업 중 오류가 발생했습니다", 
                 cache_key: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        """
        CacheError 초기화
        
        Args:
            message: 예외 메시지
            cache_key: 관련 캐시 키
            details: 추가 정보를 담은 딕셔너리 (선택 사항)
        """
        if details is None:
            details = {}
        
        if cache_key:
            details['cache_key'] = cache_key
        
        super().__init__(message, details) 