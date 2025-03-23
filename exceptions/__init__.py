"""
예외 처리 모듈

이 패키지는 애플리케이션 전체에서 사용되는 예외 클래스와
예외 처리 메커니즘을 제공합니다.
"""

# 편의를 위해 주요 예외 클래스 임포트
from .base_exception import MediaViewerException
from .media_exceptions import MediaLoadError, UnsupportedFormatError
from .file_exceptions import FileAccessError, FileOperationError
from .error_handler import ErrorHandler 