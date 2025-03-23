"""
파일 작업 관련 예외 클래스 모듈

이 모듈은 파일 시스템 접근, 파일 작업(복사, 이동, 삭제 등),
파일 탐색 등 파일 관련 작업 예외 클래스를 정의합니다.
"""
from typing import Dict, Any, Optional, List
from .base_exception import MediaViewerException


class FileError(MediaViewerException):
    """
    파일 관련 기본 예외 클래스
    
    모든 파일 작업 관련 예외는 이 클래스를 상속받습니다.
    """
    pass


class FileAccessError(FileError):
    """
    파일 접근 오류 예외
    
    파일 읽기/쓰기 권한 문제, 잠긴 파일 등의 상황에서 발생합니다.
    """
    
    def __init__(self, message: str = "파일에 접근할 수 없습니다", 
                 file_path: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        """
        FileAccessError 초기화
        
        Args:
            message: 예외 메시지
            file_path: 접근하려고 시도한 파일 경로
            details: 추가 정보를 담은 딕셔너리 (선택 사항)
        """
        if details is None:
            details = {}
        
        if file_path:
            details['file_path'] = file_path
        
        super().__init__(message, details)


class FileNotFoundError(FileError):
    """
    파일을 찾을 수 없는 경우의 예외
    
    지정된 경로에 파일이 존재하지 않을 때 발생합니다.
    """
    
    def __init__(self, message: str = "파일을 찾을 수 없습니다", 
                 file_path: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        """
        FileNotFoundError 초기화
        
        Args:
            message: 예외 메시지
            file_path: 찾을 수 없는 파일 경로
            details: 추가 정보를 담은 딕셔너리 (선택 사항)
        """
        if details is None:
            details = {}
        
        if file_path:
            details['file_path'] = file_path
        
        super().__init__(message, details)


class DirectoryNotFoundError(FileError):
    """
    디렉토리를 찾을 수 없는 경우의 예외
    
    지정된 경로에 디렉토리가 존재하지 않을 때 발생합니다.
    """
    
    def __init__(self, message: str = "디렉토리를 찾을 수 없습니다", 
                 dir_path: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        """
        DirectoryNotFoundError 초기화
        
        Args:
            message: 예외 메시지
            dir_path: 찾을 수 없는 디렉토리 경로
            details: 추가 정보를 담은 딕셔너리 (선택 사항)
        """
        if details is None:
            details = {}
        
        if dir_path:
            details['directory_path'] = dir_path
        
        super().__init__(message, details)


class FileOperationError(FileError):
    """
    파일 작업 오류 예외
    
    파일 복사, 이동, 삭제 등의 작업 중 발생한 오류입니다.
    """
    
    def __init__(self, message: str = "파일 작업 중 오류가 발생했습니다", 
                 operation: Optional[str] = None,
                 src_path: Optional[str] = None,
                 dest_path: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        """
        FileOperationError 초기화
        
        Args:
            message: 예외 메시지
            operation: 수행 중이던 작업 이름 (예: 'copy', 'move', 'delete')
            src_path: 작업 중이던 소스 파일 경로
            dest_path: 작업 중이던 대상 파일 경로 (해당되는 경우)
            details: 추가 정보를 담은 딕셔너리 (선택 사항)
        """
        if details is None:
            details = {}
        
        if operation:
            details['operation'] = operation
        
        if src_path:
            details['source_path'] = src_path
        
        if dest_path:
            details['destination_path'] = dest_path
        
        super().__init__(message, details)


class NavigationError(FileError):
    """
    파일 탐색 관련 예외
    
    파일 목록 탐색, 다음/이전 파일 이동 등의 작업 중 발생한 오류입니다.
    """
    
    def __init__(self, message: str = "파일 탐색 중 오류가 발생했습니다", 
                 current_index: Optional[int] = None,
                 file_count: Optional[int] = None,
                 details: Optional[Dict[str, Any]] = None):
        """
        NavigationError 초기화
        
        Args:
            message: 예외 메시지
            current_index: 현재 탐색 인덱스
            file_count: 전체 파일 수
            details: 추가 정보를 담은 딕셔너리 (선택 사항)
        """
        if details is None:
            details = {}
        
        if current_index is not None:
            details['current_index'] = current_index
        
        if file_count is not None:
            details['file_count'] = file_count
        
        super().__init__(message, details)


class EmptyDirectoryError(FileError):
    """
    디렉토리가 비어있는 경우의 예외
    
    지정된 디렉토리에 표시할 파일이 없을 때 발생합니다.
    """
    
    def __init__(self, message: str = "디렉토리에 표시할 파일이 없습니다", 
                 dir_path: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        """
        EmptyDirectoryError 초기화
        
        Args:
            message: 예외 메시지
            dir_path: 비어있는 디렉토리 경로
            details: 추가 정보를 담은 딕셔너리 (선택 사항)
        """
        if details is None:
            details = {}
        
        if dir_path:
            details['directory_path'] = dir_path
        
        super().__init__(message, details) 